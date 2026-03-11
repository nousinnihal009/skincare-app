"""
chatbot.py — Stateful, Tool-Augmented LLM Agent for DermAI

Organized into clearly separated sections:
  1. Pydantic Schemas
  2. Redis Helpers
  3. Tool Definitions
  4. Tool Dispatcher
  5. LLM Orchestrator
  6. SSE Generator
  7. FastAPI Router
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from enum import Enum
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# ─── Services we consume (do not rewrite) ───────────────────────────
from app.services.weather import get_weather_context, WeatherContext
from app.services.vision import get_vision_risk_flag, RiskLevel

# ─── Auth dependency (existing) ─────────────────────────────────────
from app.routes.auth import verify_token

logger = logging.getLogger("dermai.chatbot")

# ─── OpenAI client ──────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

GPT_MODEL = "gpt-4o"
GPT_MINI_MODEL = "gpt-4o-mini"

# =====================================================================
# 1. PYDANTIC SCHEMAS
# =====================================================================


class LocationPayload(BaseModel):
    lat: float
    lon: float


class ChatMessageRequest(BaseModel):
    session_id: str = Field(description="Client-generated UUID for the conversation")
    message: str = Field(min_length=1, max_length=4000)
    location: Optional[LocationPayload] = None
    image_id: Optional[str] = None


class RoutineStep(BaseModel):
    step: int
    action: str
    ingredient_target: str
    notes: str


class SkincareRoutineOutput(BaseModel):
    am_routine: list[RoutineStep]
    pm_routine: list[RoutineStep]
    weekly_treatments: list[RoutineStep]


class SSETextDelta(BaseModel):
    type: str = "text_delta"
    content: str


class SSEToolCall(BaseModel):
    type: str = "tool_call"
    tool_name: str
    status: str  # "running" | "complete" | "failed"


class SSEStructuredRoutine(BaseModel):
    type: str = "structured_routine"
    payload: dict[str, Any]


class SSESuggestionChips(BaseModel):
    type: str = "suggestion_chips"
    chips: list[str]


class SSEDone(BaseModel):
    type: str = "done"


class SSEError(BaseModel):
    type: str = "error"
    message: str


class SessionInfo(BaseModel):
    session_id: str
    created_at: Optional[str] = None
    message_count: int = 0


class ToolExecutionError(Exception):
    """Raised when a tool execution fails with a user-friendly message."""
    pass


# =====================================================================
# 2. REDIS HELPERS
# =====================================================================

# We try to use redis.asyncio. If Redis is unavailable we fall back to
# a process-local dict so the app doesn't crash.

_in_memory_store: dict[str, Any] = {}
_in_memory_sessions: dict[str, set[str]] = {}
_rate_limit_counters: dict[str, list[float]] = {}

try:
    import redis.asyncio as aioredis

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_pool: Optional[aioredis.Redis] = aioredis.from_url(
        REDIS_URL, decode_responses=True
    )
except Exception:
    _redis_pool = None
    logger.warning("Redis unavailable — falling back to in-memory session store.")


def _chat_key(user_id: str, session_id: str) -> str:
    return f"dermai:chat:{user_id}:{session_id}"


def _sessions_key(user_id: str) -> str:
    return f"dermai:sessions:{user_id}"


def _rate_key(user_id: str) -> str:
    return f"dermai:rate:{user_id}"


HISTORY_TTL_SECONDS = 86400  # 24 hours
MAX_PAIRS = 20  # maximum message pairs to keep
RATE_LIMIT_RPM = 30  # requests per minute


async def _redis_available() -> bool:
    if _redis_pool is None:
        return False
    try:
        await _redis_pool.ping()
        return True
    except Exception:
        return False


async def load_history(user_id: str, session_id: str) -> list[dict[str, str]]:
    """Load conversation history from Redis or in-memory fallback."""
    key = _chat_key(user_id, session_id)
    if await _redis_available():
        assert _redis_pool is not None
        raw = await _redis_pool.get(key)
        if raw:
            return json.loads(raw)
        return []
    return _in_memory_store.get(key, [])


async def save_history(
    user_id: str, session_id: str, history: list[dict[str, str]]
) -> None:
    """Persist conversation history, trimming to MAX_PAIRS oldest messages."""
    # Keep system prompt + last MAX_PAIRS*2 messages
    system_msgs = [m for m in history if m.get("role") == "system"]
    non_system = [m for m in history if m.get("role") != "system"]
    if len(non_system) > MAX_PAIRS * 2:
        non_system = non_system[-(MAX_PAIRS * 2) :]
    trimmed = system_msgs + non_system

    key = _chat_key(user_id, session_id)
    if await _redis_available():
        assert _redis_pool is not None
        await _redis_pool.set(key, json.dumps(trimmed), ex=HISTORY_TTL_SECONDS)
        await _redis_pool.sadd(_sessions_key(user_id), session_id)
        await _redis_pool.expire(_sessions_key(user_id), HISTORY_TTL_SECONDS)
    else:
        _in_memory_store[key] = trimmed
        _in_memory_sessions.setdefault(user_id, set()).add(session_id)


async def delete_session(user_id: str, session_id: str) -> bool:
    """Delete a chat session. Returns True if something was deleted."""
    key = _chat_key(user_id, session_id)
    if await _redis_available():
        assert _redis_pool is not None
        deleted = await _redis_pool.delete(key)
        await _redis_pool.srem(_sessions_key(user_id), session_id)
        return deleted > 0
    existed = key in _in_memory_store
    _in_memory_store.pop(key, None)
    _in_memory_sessions.get(user_id, set()).discard(session_id)
    return existed


async def list_sessions(user_id: str) -> list[str]:
    """List all session IDs for a user."""
    if await _redis_available():
        assert _redis_pool is not None
        members = await _redis_pool.smembers(_sessions_key(user_id))
        return list(members)
    return list(_in_memory_sessions.get(user_id, set()))


async def check_rate_limit(user_id: str) -> bool:
    """
    Returns True if the request should be BLOCKED (rate limit exceeded).
    Enforces RATE_LIMIT_RPM requests per minute per user.
    """
    now = time.time()
    window_start = now - 60.0

    if await _redis_available():
        assert _redis_pool is not None
        rkey = _rate_key(user_id)
        pipe = _redis_pool.pipeline()
        await pipe.zremrangebyscore(rkey, 0, window_start)
        await pipe.zadd(rkey, {str(now): now})
        await pipe.zcard(rkey)
        await pipe.expire(rkey, 120)
        results = await pipe.execute()
        count = results[2]
        return count > RATE_LIMIT_RPM
    else:
        entries = _rate_limit_counters.get(user_id, [])
        entries = [t for t in entries if t > window_start]
        entries.append(now)
        _rate_limit_counters[user_id] = entries
        return len(entries) > RATE_LIMIT_RPM


# =====================================================================
# 3. TOOL DEFINITIONS (OpenAI function schemas)
# =====================================================================

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_advice",
            "description": (
                "Fetches climate context for the user's location and returns "
                "skincare-relevant environmental data including UV index, humidity, "
                "temperature, and weather conditions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the user's location",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the user's location",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_vision_risk_assessment",
            "description": (
                "Retrieves a pre-computed risk flag from the vision model for a "
                "previously uploaded skin image. Use this when the user has shared "
                "an image and wants to know the risk level."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "image_id": {
                        "type": "string",
                        "description": "Unique identifier for the uploaded image",
                    },
                },
                "required": ["image_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_skincare_routine",
            "description": (
                "Generates a structured AM/PM/Weekly skincare routine as a JSON "
                "payload. Only call this after gathering the user's skin type, "
                "age range, primary goals, budget tier, and climate information "
                "through conversation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skin_type": {
                        "type": "string",
                        "description": "User's skin type (e.g., oily, dry, combination, sensitive, normal)",
                    },
                    "age_range": {
                        "type": "string",
                        "description": "User's age range (e.g., 18-25, 26-35, 36-45, 46-55, 55+)",
                    },
                    "primary_goals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "User's skincare goals (e.g., anti-aging, acne control, hydration, brightening)",
                    },
                    "budget_tier": {
                        "type": "string",
                        "enum": ["budget", "mid", "premium"],
                        "description": "User's budget preference",
                    },
                    "climate": {
                        "type": "string",
                        "description": "User's climate/environment (e.g., tropical, arid, temperate, cold)",
                    },
                },
                "required": [
                    "skin_type",
                    "age_range",
                    "primary_goals",
                    "budget_tier",
                    "climate",
                ],
            },
        },
    },
]


# =====================================================================
# 4. TOOL DISPATCHER
# =====================================================================


async def _execute_get_weather_advice(
    latitude: float, longitude: float
) -> str:
    """Execute the weather advice tool and return a formatted string."""
    ctx: WeatherContext = await get_weather_context(latitude, longitude)

    uv_label = "low"
    if ctx.uv_index >= 3:
        uv_label = "moderate"
    if ctx.uv_index >= 6:
        uv_label = "high"
    if ctx.uv_index >= 8:
        uv_label = "very high"
    if ctx.uv_index >= 11:
        uv_label = "extreme"

    climate_type = "temperate"
    if ctx.temperature_c >= 30 and ctx.is_humid:
        climate_type = "tropical/humid"
    elif ctx.temperature_c >= 30:
        climate_type = "hot/arid"
    elif ctx.temperature_c <= 5:
        climate_type = "cold"
    elif ctx.is_humid:
        climate_type = "humid"

    return (
        f"UV index is {ctx.uv_index} ({uv_label}), "
        f"humidity is {ctx.humidity_pct}%, "
        f"temperature is {ctx.temperature_c}°C — "
        f"{climate_type} conditions. "
        f"Weather: {ctx.condition}."
    )


async def _execute_get_vision_risk_assessment(image_id: str) -> str:
    """Execute the vision risk assessment tool and return a formatted string."""
    risk: RiskLevel = await get_vision_risk_flag(image_id)

    messages = {
        RiskLevel.LOW: (
            f"The vision model has assessed image '{image_id}' as LOW risk. "
            "No immediate concerns detected, but routine monitoring is recommended."
        ),
        RiskLevel.MEDIUM: (
            f"The vision model has assessed image '{image_id}' as MEDIUM risk. "
            "Some features warrant attention. A follow-up with a dermatologist "
            "is recommended for a definitive evaluation."
        ),
        RiskLevel.HIGH: (
            f"The vision model has assessed image '{image_id}' as HIGH risk. "
            "MANDATORY_DISCLAIMER: This lesion has been flagged as high-risk by our vision model."
        ),
    }
    return messages[risk]


async def _execute_generate_skincare_routine(
    skin_type: str,
    age_range: str,
    primary_goals: list[str],
    budget_tier: str,
    climate: str,
) -> str:
    """
    Generate a structured skincare routine via a secondary LLM call.
    Returns JSON string that the frontend can parse into a RoutineCard.
    """
    routine_prompt = f"""Generate a detailed, personalized skincare routine as JSON.

Patient profile:
- Skin type: {skin_type}
- Age range: {age_range}
- Primary goals: {', '.join(primary_goals)}
- Budget tier: {budget_tier}
- Climate: {climate}

Return ONLY valid JSON with this exact structure:
{{
  "am_routine": [
    {{"step": 1, "action": "...", "ingredient_target": "...", "notes": "..."}},
    ...
  ],
  "pm_routine": [
    {{"step": 1, "action": "...", "ingredient_target": "...", "notes": "..."}},
    ...
  ],
  "weekly_treatments": [
    {{"step": 1, "action": "...", "ingredient_target": "...", "notes": "..."}},
    ...
  ]
}}

Guidelines:
- AM routine: 4-6 steps (cleanser, toner/essence, serum, moisturizer, sunscreen, etc.)
- PM routine: 4-6 steps (double cleanse, treatment, serum, moisturizer, etc.)
- Weekly treatments: 2-3 steps (exfoliation, masks, special treatments)
- For "ingredient_target", name specific active ingredients (e.g., "Niacinamide 5%", "Hyaluronic Acid", "Salicylic Acid 2%")
- Use "I'd recommend looking for products containing..." phrasing in notes instead of specific brand names
- Tailor to the budget tier (budget = drugstore-accessible actives, premium = clinical-grade concentrations)
- Adapt to climate conditions (more hydration for arid, lighter formulas for humid)
"""
    try:
        resp = await openai_client.chat.completions.create(
            model=GPT_MINI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a skincare formulation expert. Return ONLY valid JSON, no markdown.",
                },
                {"role": "user", "content": routine_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000,
        )

        raw_content = resp.choices[0].message.content or "{}"
        # Validate the structure with Pydantic v2 model_validate_json
        from pydantic import ValidationError as PydanticValidationError
        try:
            validated = SkincareRoutineOutput.model_validate_json(raw_content)
            return validated.model_dump_json()
        except PydanticValidationError as ve:
            logger.error(f"Routine validation failed: {ve}")
            raise ToolExecutionError(
                "The generated routine had an unexpected format. "
                "Please try again — I'll create a fresh routine for you."
            )
    except Exception as e:
        logger.error(f"Routine generation failed: {e}")
        # Return a minimal valid routine on failure
        fallback = {
            "am_routine": [
                {
                    "step": 1,
                    "action": "Gentle Cleanser",
                    "ingredient_target": "Ceramides, Glycerin",
                    "notes": "Use lukewarm water, massage gently for 60 seconds",
                },
                {
                    "step": 2,
                    "action": "Moisturizer",
                    "ingredient_target": "Hyaluronic Acid, Niacinamide",
                    "notes": "Apply on damp skin for better absorption",
                },
                {
                    "step": 3,
                    "action": "Sunscreen SPF 30+",
                    "ingredient_target": "Zinc Oxide or Chemical SPF filters",
                    "notes": "Reapply every 2 hours when outdoors — non-negotiable",
                },
            ],
            "pm_routine": [
                {
                    "step": 1,
                    "action": "Gentle Cleanser",
                    "ingredient_target": "Micellar water or cream cleanser",
                    "notes": "Double cleanse if wearing sunscreen or makeup",
                },
                {
                    "step": 2,
                    "action": "Treatment Serum",
                    "ingredient_target": "Retinol 0.3% or Niacinamide 10%",
                    "notes": "Start low and slow with retinol, 2-3 times per week",
                },
                {
                    "step": 3,
                    "action": "Night Moisturizer",
                    "ingredient_target": "Ceramides, Peptides, Squalane",
                    "notes": "Can use a slightly richer formula than AM",
                },
            ],
            "weekly_treatments": [
                {
                    "step": 1,
                    "action": "Chemical Exfoliant",
                    "ingredient_target": "AHA (Glycolic/Lactic Acid) or BHA (Salicylic Acid)",
                    "notes": "1-2 times per week, skip retinol on exfoliation nights",
                },
            ],
        }
        return json.dumps(fallback)


async def dispatch_tool_call(
    tool_name: str, arguments: dict[str, Any]
) -> str:
    """
    Route a tool call to the correct implementation.
    Returns the tool result as a string.
    """
    if tool_name == "get_weather_advice":
        return await _execute_get_weather_advice(
            latitude=arguments["latitude"],
            longitude=arguments["longitude"],
        )
    elif tool_name == "get_vision_risk_assessment":
        return await _execute_get_vision_risk_assessment(
            image_id=arguments["image_id"],
        )
    elif tool_name == "generate_skincare_routine":
        return await _execute_generate_skincare_routine(
            skin_type=arguments["skin_type"],
            age_range=arguments["age_range"],
            primary_goals=arguments["primary_goals"],
            budget_tier=arguments["budget_tier"],
            climate=arguments["climate"],
        )
    else:
        return f"Unknown tool: {tool_name}"


# =====================================================================
# 5. LLM ORCHESTRATOR
# =====================================================================

SYSTEM_PROMPT = """\
You are **Derm**, a board-certified dermatologist and empathetic skincare coach \
inside the DermAI platform. Your communication style is warm, professional, and \
conversational — like a trusted doctor who genuinely cares about each patient.

─── CORE BEHAVIOR ───

1. **Clarification first.** Never give one-size-fits-all responses. Before advising, \
ensure you understand the user's skin type, age, climate, lifestyle, and goals. Ask \
targeted follow-up questions when any of these are unknown.

2. **Diagnostic quiz.** If a user asks for a skincare routine and their skin profile \
is unknown from conversation history, initiate a brief 5-question diagnostic quiz. \
Ask ONE question at a time, naturally woven into conversation:
   Q1: "What's your skin type? (oily, dry, combination, sensitive, normal)"
   Q2: "What age range are you in? (18-25, 26-35, 36-45, 46-55, 55+)"
   Q3: "What's your primary skincare concern or goal?"
   Q4: "What's your budget preference — drugstore/budget, mid-range, or premium?"
   Q5: "What kind of climate do you live in? (humid/tropical, dry/arid, temperate, cold)"
   After collecting all answers, call the `generate_skincare_routine` tool.

3. **Product recommendations.** ALWAYS qualify recommendations with phrasing like \
"I'd recommend looking for products containing…" — NEVER cite specific brand names \
you cannot verify.

─── SAFETY CONSTRAINTS (NON-NEGOTIABLE) ───

• NEVER diagnose malignancy or cancer. If signs are concerning, say: \
"Based on what you've described, this warrants an in-person evaluation by a \
dermatologist. I can help you understand what to ask your doctor."

• NEVER prescribe or recommend prescription-only medications (tretinoin, \
isotretinoin, antibiotics, oral steroids, biologics). Instead, suggest the user \
discuss these options with their healthcare provider.

• NEVER make confident diagnostic claims about serious conditions. Use hedging \
language: "This could potentially be…", "This is consistent with…"

─── TOOL USAGE ───

• If the user shares their location or you know their coordinates, call \
`get_weather_advice` to factor environmental conditions into your advice.

• If the user references an uploaded image or image analysis, call \
`get_vision_risk_assessment` with the image ID.

• After completing the 5-question diagnostic quiz, call \
`generate_skincare_routine` with the gathered profile data.

─── TONE GUIDELINES ───

• Empathetic, never alarmist. Reassure where appropriate.
• Use plain language. Avoid over-medicalization unless context demands it.
• Use markdown formatting for readability: bold for key terms, bullet points \
for lists, numbered lists for routines.
• Keep responses focused and concise — avoid walls of text.
• End responses with a natural follow-up question or next step when appropriate.

─── DISCLAIMER ───

You are an AI assistant, not a substitute for professional medical care. \
When in doubt, always recommend consulting a board-certified dermatologist.\
"""


async def build_messages(
    user_id: str,
    session_id: str,
    user_message: str,
    location: Optional[LocationPayload],
    image_id: Optional[str],
) -> list[dict[str, Any]]:
    """
    Load history, inject system prompt if needed, append new user message.
    Also injects context hints for location / image_id so the model knows
    these attachments are available for tool calls.
    """
    history = await load_history(user_id, session_id)

    # Ensure system prompt is always first
    if not history or history[0].get("role") != "system":
        history.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    # Build the user message with any context hints
    content_parts: list[str] = [user_message]
    if location:
        content_parts.append(
            f"\n[System context: User's location is lat={location.lat}, lon={location.lon}. "
            f"You may call get_weather_advice to get environmental data.]"
        )
    if image_id:
        content_parts.append(
            f"\n[System context: User has attached image with id='{image_id}'. "
            f"You may call get_vision_risk_assessment to retrieve its risk analysis.]"
        )

    history.append({"role": "user", "content": "\n".join(content_parts)})
    return history


async def generate_suggestion_chips(
    last_user_msg: str, last_assistant_msg: str
) -> list[str]:
    """
    Generate 3 contextually relevant suggestion chips using a lightweight
    secondary LLM call.
    """
    try:
        resp = await openai_client.chat.completions.create(
            model=GPT_MINI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate exactly 3 short follow-up question suggestions "
                        "for a dermatology chatbot. Return ONLY a JSON array of 3 strings. "
                        "Each suggestion should be 4-10 words, naturally conversational, "
                        "and contextually relevant to the last exchange. "
                        "Example: [\"How about sunscreen tips?\", \"What causes my acne?\", \"Tell me about retinol\"]"
                    ),
                },
                {
                    "role": "user",
                    "content": f"User said: {last_user_msg}\nAssistant replied: {last_assistant_msg[:300]}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=150,
        )
        content = resp.choices[0].message.content or "[]"
        parsed = json.loads(content)
        # Handle both {"suggestions": [...]} and [...] formats
        if isinstance(parsed, list):
            chips = parsed[:3]
        elif isinstance(parsed, dict):
            chips = list(parsed.values())[0] if parsed else []
            if isinstance(chips, list):
                chips = chips[:3]
            else:
                chips = []
        else:
            chips = []
        return [str(c) for c in chips]
    except Exception as e:
        logger.warning(f"Suggestion chip generation failed: {e}")
        return [
            "Tell me about my skin type",
            "What skincare routine do you recommend?",
            "How can I protect my skin from the sun?",
        ]


# =====================================================================
# 6. SSE GENERATOR
# =====================================================================


def _sse_event(data: dict[str, Any]) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


async def stream_chat_response(
    user_id: str,
    session_id: str,
    user_message: str,
    location: Optional[LocationPayload],
    image_id: Optional[str],
) -> AsyncGenerator[str, None]:
    """
    Core SSE streaming generator. Handles:
    - OpenAI streaming with tool calls
    - Tool execution with status events
    - Structured routine payloads
    - Suggestion chips generation
    - Full history persistence
    """
    messages = await build_messages(
        user_id, session_id, user_message, location, image_id
    )

    full_assistant_content = ""
    tool_calls_accumulated: dict[int, dict[str, Any]] = {}

    try:
        # --- Main streaming loop (may iterate if tool calls occur) ---
        max_tool_rounds = 5
        for _round in range(max_tool_rounds):
            stream = await openai_client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                stream=True,
                temperature=0.7,
                max_tokens=2000,
            )

            current_content = ""
            tool_calls_in_round: dict[int, dict[str, Any]] = {}
            finish_reason = None

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                # Capture finish reason
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

                # Stream text content
                if delta.content:
                    current_content += delta.content
                    yield _sse_event({"type": "text_delta", "content": delta.content})

                # Accumulate tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_in_round:
                            tool_calls_in_round[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.id:
                            tool_calls_in_round[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_in_round[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_in_round[idx]["arguments"] += tc.function.arguments

            full_assistant_content += current_content

            # If no tool calls, we're done with LLM rounds
            if finish_reason != "tool_calls" or not tool_calls_in_round:
                break

            # --- Process tool calls ---
            # Build the assistant message with tool_calls for history
            assistant_tool_msg: dict[str, Any] = {
                "role": "assistant",
                "content": current_content if current_content else None,
                "tool_calls": [],
            }
            for idx in sorted(tool_calls_in_round.keys()):
                tc_data = tool_calls_in_round[idx]
                assistant_tool_msg["tool_calls"].append(
                    {
                        "id": tc_data["id"],
                        "type": "function",
                        "function": {
                            "name": tc_data["name"],
                            "arguments": tc_data["arguments"],
                        },
                    }
                )
            messages.append(assistant_tool_msg)

            # Execute each tool call
            for idx in sorted(tool_calls_in_round.keys()):
                tc_data = tool_calls_in_round[idx]
                tool_name = tc_data["name"]
                tool_call_id = tc_data["id"]

                # Emit running status
                yield _sse_event(
                    {"type": "tool_call", "tool_name": tool_name, "status": "running"}
                )

                try:
                    args = json.loads(tc_data["arguments"])
                    result = await dispatch_tool_call(tool_name, args)

                    # Check if this is a routine — emit structured event
                    if tool_name == "generate_skincare_routine":
                        try:
                            routine_json = json.loads(result)
                            yield _sse_event(
                                {
                                    "type": "structured_routine",
                                    "payload": routine_json,
                                }
                            )
                        except json.JSONDecodeError:
                            pass

                    yield _sse_event(
                        {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "status": "complete",
                        }
                    )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": result,
                        }
                    )
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    yield _sse_event(
                        {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "status": "failed",
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": (
                                f"Tool '{tool_name}' encountered an error. "
                                "Please provide advice without this tool's data, "
                                "noting that the information is temporarily unavailable."
                            ),
                        }
                    )

        # --- Append final assistant message to history ---
        if full_assistant_content:
            messages.append({"role": "assistant", "content": full_assistant_content})

        # --- Generate suggestion chips ---
        chips = await generate_suggestion_chips(user_message, full_assistant_content)
        yield _sse_event({"type": "suggestion_chips", "chips": chips})

        # --- Persist updated history ---
        await save_history(user_id, session_id, messages)

        # --- Done ---
        yield _sse_event({"type": "done"})

    except Exception as e:
        logger.error(f"Chat stream error: {e}", exc_info=True)
        yield _sse_event(
            {
                "type": "error",
                "message": "Our AI assistant is temporarily unavailable. Please try again shortly.",
            }
        )


# =====================================================================
# 7. FASTAPI ROUTER
# =====================================================================

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message")
async def chat_message(
    body: ChatMessageRequest,
    payload: dict = Depends(verify_token),
) -> StreamingResponse:
    """
    Main chat endpoint — streams SSE events for a conversation turn.

    Requires JWT auth. Rate-limited to 30 requests/minute per user.
    """
    user_id: str = payload["sub"]

    # Rate limit check
    if await check_rate_limit(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before sending more messages.",
            headers={"Retry-After": "60"},
        )

    return StreamingResponse(
        stream_chat_response(
            user_id=user_id,
            session_id=body.session_id,
            user_message=body.message,
            location=body.location,
            image_id=body.image_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    payload: dict = Depends(verify_token),
) -> dict[str, Any]:
    """Returns full message history for a session."""
    user_id: str = payload["sub"]
    history = await load_history(user_id, session_id)

    # Filter out system messages for the client
    client_messages = [
        msg for msg in history if msg.get("role") in ("user", "assistant")
    ]
    return {"session_id": session_id, "messages": client_messages}


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    payload: dict = Depends(verify_token),
) -> dict[str, str]:
    """Clears a Redis/in-memory chat session."""
    user_id: str = payload["sub"]
    deleted = await delete_session(user_id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session cleared successfully"}


@router.get("/sessions")
async def get_sessions(
    payload: dict = Depends(verify_token),
) -> dict[str, Any]:
    """Returns list of session IDs for the authenticated user."""
    user_id: str = payload["sub"]
    session_ids = await list_sessions(user_id)
    return {"user_id": user_id, "sessions": session_ids}
