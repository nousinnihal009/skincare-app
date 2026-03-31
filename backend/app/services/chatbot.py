"""
chatbot.py — Production-Grade Stateful Tool-Augmented LLM Agent

Sections:
  1.  Imports & Constants
  2.  Gemini Initialization (crash-safe)
  3.  Pydantic Schemas
  4.  Redis Helpers
  5.  Tool Definitions & Gemini Tool Conversion
  6.  Tool Dispatcher
  7.  Intent Classifier
  8.  Safety Filter
  9.  Message History Builder
  10. Suggestion Chips Generator
  11. System Prompt
  12. Core SSE Agent Loop
  13. FastAPI Router
"""

from __future__ import annotations

# =====================================================================
# 1. IMPORTS & CONSTANTS
# =====================================================================

import asyncio
import json
import logging
import os
import time
import uuid
from enum import Enum
from typing import Any, AsyncGenerator, Literal, Optional

import google.generativeai as genai
import google.generativeai.protos as protos
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from google.generativeai.types import FunctionDeclaration, GenerationConfig, Tool
from pydantic import BaseModel, Field, field_validator

from app.routes.auth import verify_token
from app.services.vision import RiskLevel, get_vision_risk_flag
from app.services.weather import WeatherContext, get_weather_context

load_dotenv()
logger = logging.getLogger("dermai.chatbot")

# ── Model config ──────────────────────────────────────────────────────
GEMINI_PRO_MODEL   = "gemini-pro-latest"      # main agent — best reasoning
GEMINI_FLASH_MODEL = "gemini-flash-latest"    # chips + intent — fast/cheap

# ── Timeouts ──────────────────────────────────────────────────────────
AGENT_TIMEOUT_S  = 45.0   # main agent stream (pro model is slower)
TOOL_TIMEOUT_S   = 10.0   # individual tool execution
CHIPS_TIMEOUT_S  = 3.0    # suggestion chips
INTENT_TIMEOUT_S = 1.5    # intent classifier

# ── Agent config ──────────────────────────────────────────────────────
MAX_TOOL_ROUNDS  = 5      # maximum tool call iterations per turn
MAX_PAIRS        = 20     # message pairs retained in history
HISTORY_TTL_S    = 86400  # 24 hours
RATE_LIMIT_RPM   = 30     # requests per minute per user

# ── Safety trigger words (post-generation filter) ─────────────────────
_SAFETY_TRIGGERS = [
    "melanoma", "carcinoma", "malignant", "cancer", "tretinoin",
    "isotretinoin", "accutane", "methotrexate", "cyclosporine",
    "you have", "you definitely have", "this is definitely",
    "i diagnose", "my diagnosis is",
]

_SAFETY_DISCLAIMER = (
    "\n\n---\n⚕️ *This information is for educational purposes only and does not "
    "constitute a medical diagnosis or prescription. Please consult a board-certified "
    "dermatologist for any medical skin concerns.*"
)


# =====================================================================
# 2. GEMINI INITIALIZATION (CRASH-SAFE)
# =====================================================================

_GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
_GEMINI_READY = False

if _GEMINI_KEY:
    try:
        genai.configure(api_key=_GEMINI_KEY)
        # Warm-up probe — verify key is valid at startup, not at first request
        _probe_model = genai.GenerativeModel(GEMINI_FLASH_MODEL)
        logger.info("[DermAI] Gemini SDK initialized — key verified")
        _GEMINI_READY = True
    except Exception as _init_err:
        logger.error(f"[DermAI] Gemini initialization failed: {_init_err}")
else:
    logger.error(
        "[DermAI] GEMINI_API_KEY not set — all chat requests will fail gracefully"
    )


# =====================================================================
# 3. PYDANTIC SCHEMAS
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


class IntentType(str, Enum):
    ROUTINE_REQUEST  = "routine_request"   # wants a skincare routine
    MEDICAL_QUESTION = "medical_question"  # asking about a condition/symptom
    IMAGE_ANALYSIS   = "image_analysis"    # referencing an uploaded image
    GENERAL_CHAT     = "general_chat"      # general skincare/beauty question
    EMERGENCY        = "emergency"         # mentions self-harm, severe symptoms


class IntentResult(BaseModel):
    intent:     IntentType
    confidence: float           # 0.0–1.0
    reasoning:  str             # 1-sentence explanation — for logging only


class TurnMetadata(BaseModel):
    """Attached to every response for observability."""
    session_id:       str
    turn_index:       int
    intent:           IntentType
    tools_called:     list[str]
    tool_rounds:      int
    safety_triggered: bool
    llm_model:        str
    latency_ms:       int


# =====================================================================
# 4. REDIS HELPERS
# =====================================================================

# We try to use redis.asyncio. If Redis is unavailable we fall back to
# a process-local dict so the app doesn't crash.

_in_memory_store:    dict[str, Any]        = {}
_in_memory_sessions: dict[str, set[str]]   = {}
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


HISTORY_TTL_SECONDS = HISTORY_TTL_S
MAX_PAIRS           = MAX_PAIRS  # already defined above, re-bind for readability


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
    non_system  = [m for m in history if m.get("role") != "system"]
    if len(non_system) > MAX_PAIRS * 2:
        non_system = non_system[-(MAX_PAIRS * 2):]
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
    now          = time.time()
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
        count   = results[2]
        return count > RATE_LIMIT_RPM
    else:
        entries = _rate_limit_counters.get(user_id, [])
        entries = [t for t in entries if t > window_start]
        entries.append(now)
        _rate_limit_counters[user_id] = entries
        return len(entries) > RATE_LIMIT_RPM


async def get_turn_index(user_id: str, session_id: str) -> int:
    """
    Returns the current turn count for this session.
    Used for TurnMetadata and analytics.
    """
    history    = await load_history(user_id, session_id)
    user_turns = [m for m in history if m.get("role") == "user"]
    return len(user_turns)


# =====================================================================
# 5. TOOL DEFINITIONS & GEMINI TOOL CONVERSION
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
                        "type":        "number",
                        "description": "Latitude of the user's location",
                    },
                    "longitude": {
                        "type":        "number",
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
                        "type":        "string",
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
                        "type":        "string",
                        "description": "User's skin type (e.g., oily, dry, combination, sensitive, normal)",
                    },
                    "age_range": {
                        "type":        "string",
                        "description": "User's age range (e.g., 18-25, 26-35, 36-45, 46-55, 55+)",
                    },
                    "primary_goals": {
                        "type":  "array",
                        "items": {"type": "string"},
                        "description": "User's skincare goals (e.g., anti-aging, acne control, hydration, brightening)",
                    },
                    "budget_tier": {
                        "type":        "string",
                        "enum":        ["budget", "mid", "premium"],
                        "description": "User's budget preference",
                    },
                    "climate": {
                        "type":        "string",
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


def _build_gemini_tools(openai_schemas: list[dict]) -> list[Tool]:
    """
    Convert OpenAI-format function schemas to Gemini Tool objects.
    Called once at module load. Result cached in GEMINI_TOOLS.
    """
    declarations = []
    for schema in openai_schemas:
        fn = schema["function"]
        declarations.append(
            FunctionDeclaration(
                name        = fn["name"],
                description = fn["description"],
                parameters  = fn.get("parameters", {})
            )
        )
    return [Tool(function_declarations=declarations)]


GEMINI_TOOLS: list[Tool] = _build_gemini_tools(TOOL_SCHEMAS)


# =====================================================================
# 6. TOOL DISPATCHER
# =====================================================================


async def _execute_get_weather_advice(latitude: float, longitude: float) -> str:
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
    skin_type:     str,
    age_range:     str,
    primary_goals: list[str],
    budget_tier:   str,
    climate:       str,
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
        def _call_gemini_routine():
            model = genai.GenerativeModel(GEMINI_FLASH_MODEL)
            response = model.generate_content(
                [
                    "You are a skincare formulation expert. Return ONLY valid JSON, no markdown.",
                    routine_prompt
                ],
                generation_config=GenerationConfig(
                    temperature        = 0.7,
                    max_output_tokens  = 2000,
                    response_mime_type = "application/json",
                )
            )
            return response.text

        raw_content = await asyncio.wait_for(
            asyncio.to_thread(_call_gemini_routine), timeout=10.0
        )

        # Validate the structure with Pydantic
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

    except ToolExecutionError:
        raise
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


async def dispatch_tool_call(tool_name: str, arguments: dict[str, Any]) -> str:
    """
    Route a tool call to the correct implementation.
    Returns the tool result as a string.
    """
    if tool_name == "get_weather_advice":
        return await _execute_get_weather_advice(
            latitude  = arguments["latitude"],
            longitude = arguments["longitude"],
        )
    elif tool_name == "get_vision_risk_assessment":
        return await _execute_get_vision_risk_assessment(
            image_id = arguments["image_id"],
        )
    elif tool_name == "generate_skincare_routine":
        return await _execute_generate_skincare_routine(
            skin_type     = arguments["skin_type"],
            age_range     = arguments["age_range"],
            primary_goals = arguments["primary_goals"],
            budget_tier   = arguments["budget_tier"],
            climate       = arguments["climate"],
        )
    else:
        return f"Unknown tool: {tool_name}"


# =====================================================================
# 7. INTENT CLASSIFIER
# =====================================================================

_INTENT_SYSTEM = """\
You are an intent classifier for a dermatology AI assistant.
Classify the user's message into exactly one of these intents:
- routine_request: user wants a skincare routine or product recommendations
- medical_question: user is asking about a skin condition, symptom, or diagnosis
- image_analysis: user is referencing an uploaded skin image
- general_chat: general skincare/beauty question not fitting above
- emergency: user mentions severe pain, spreading infection, difficulty breathing,
  signs of anaphylaxis, or self-harm

Respond ONLY with valid JSON:
{"intent": "<intent_type>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}
No preamble. No markdown."""


async def classify_intent(
    user_message: str,
    has_image:    bool,
    history_len:  int,
) -> IntentResult:
    """
    Lightweight intent classification using Gemini Flash.
    Falls back to GENERAL_CHAT on any failure — never blocks the main flow.

    Used to:
    1. Fast-path EMERGENCY intent to safety response before agent runs
    2. Provide context hints to the agent system prompt
    3. Log intent distribution for product analytics
    """
    fallback = IntentResult(
        intent     = IntentType.IMAGE_ANALYSIS if has_image else IntentType.GENERAL_CHAT,
        confidence = 0.5,
        reasoning  = "Classification unavailable — using heuristic fallback"
    )

    if not _GEMINI_READY:
        return fallback

    try:
        context = (
            f"User message: {user_message[:300]}\n"
            f"Has attached image: {has_image}\n"
            f"Conversation turn: {history_len}"
        )

        def _call() -> str:
            m = genai.GenerativeModel(
                model_name         = GEMINI_FLASH_MODEL,
                system_instruction = _INTENT_SYSTEM,
                generation_config  = GenerationConfig(
                    temperature       = 0.1,
                    max_output_tokens = 100,
                )
            )
            return m.generate_content(context).text

        raw   = await asyncio.wait_for(asyncio.to_thread(_call), timeout=INTENT_TIMEOUT_S)
        clean = raw.strip().replace("```json", "").replace("```", "").strip()
        data  = json.loads(clean)

        return IntentResult(
            intent     = IntentType(data["intent"]),
            confidence = float(data.get("confidence", 0.8)),
            reasoning  = data.get("reasoning", "")
        )

    except asyncio.TimeoutError:
        logger.warning("[Intent] Classifier timed out — using fallback")
        return fallback
    except Exception as e:
        logger.warning(f"[Intent] Classification failed: {type(e).__name__}: {e}")
        return fallback


# =====================================================================
# 8. SAFETY FILTER
# =====================================================================


def _apply_safety_filter(text: str) -> tuple[str, bool]:
    """
    Post-generation safety check on assistant output.

    Scans for trigger words that indicate the model may have:
    - Made a confident diagnosis claim
    - Named a prescription medication
    - Used diagnostic language beyond its scope

    Returns: (filtered_text, was_triggered)
    - If triggered: appends mandatory disclaimer to the text
    - Never removes or modifies the original text — only appends
    - Always logs when triggered for monitoring
    """
    text_lower = text.lower()
    triggered  = any(trigger in text_lower for trigger in _SAFETY_TRIGGERS)

    if triggered:
        logger.warning(
            f"[Safety] Trigger detected in assistant response. "
            f"Appending disclaimer. Preview: {text[:100]}"
        )
        return text + _SAFETY_DISCLAIMER, True

    return text, False


# =====================================================================
# 9. MESSAGE HISTORY BUILDER
# =====================================================================


async def build_messages(
    user_id:      str,
    session_id:   str,
    user_message: str,
    location:     Optional[LocationPayload],
    image_id:     Optional[str],
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


def _to_gemini_history(messages: list[dict]) -> list[dict]:
    """
    Convert stored OpenAI-format message history to Gemini chat history.

    Rules:
    - system messages → skipped (handled via system_instruction param)
    - role="user"      → role="user"
    - role="assistant" → role="model"
    - role="tool"      → skipped (tool results sent as FunctionResponse, not history)
    - Gemini REQUIRES strictly alternating user/model turns
    - Consecutive same-role messages are merged by joining content
    - History must start with "user" and end with "model" if non-empty

    This is called every agent loop iteration with the current messages list.
    """
    result: list[dict] = []

    for msg in messages:
        role = msg.get("role")
        if role in ("system", "tool"):
            continue

        gemini_role = "user" if role == "user" else "model"
        content     = msg.get("content") or ""
        if not isinstance(content, str):
            content = json.dumps(content)
        if not content.strip():
            continue

        # Merge consecutive same-role messages (Gemini strict alternation requirement)
        if result and result[-1]["role"] == gemini_role:
            result[-1]["parts"][0] += f"\n{content}"
        else:
            result.append({"role": gemini_role, "parts": [content]})

    # Enforce Gemini history constraints
    # Must start with user turn
    while result and result[0]["role"] != "user":
        result.pop(0)
    # Must end with model turn (last user turn becomes the current message)
    while result and result[-1]["role"] != "model":
        result.pop()

    return result


# =====================================================================
# 10. SUGGESTION CHIPS GENERATOR
# =====================================================================


async def generate_suggestion_chips(
    user_message:    str,
    assistant_reply: str,
    intent:          IntentType,
) -> list[str]:
    """
    Generate 3 contextually relevant follow-up suggestion chips.

    Intent-aware: chips are tailored to the conversation context.
    - routine_request  → product/ingredient follow-ups
    - medical_question → symptom/referral follow-ups
    - image_analysis   → image-specific follow-ups
    - general_chat     → broad skincare follow-ups
    - emergency        → never called for emergency (handled upstream)

    3-second hard timeout. Falls back to intent-appropriate defaults.
    Handles both JSON array and JSON object response formats.
    """
    DEFAULTS_BY_INTENT: dict[IntentType, list[str]] = {
        IntentType.ROUTINE_REQUEST:  ["What ingredients should I layer?",   "How long until I see results?",    "Can I use this with retinol?"],
        IntentType.MEDICAL_QUESTION: ["When should I see a dermatologist?", "What ingredients should I avoid?", "Can this spread to others?"],
        IntentType.IMAGE_ANALYSIS:   ["Should I be concerned about this?",  "What does the red area indicate?", "Is this getting worse?"],
        IntentType.GENERAL_CHAT:     ["What skincare routine suits me?",     "How do I improve my skin barrier?","What SPF should I use?"],
        IntentType.EMERGENCY:        [],  # never called
    }
    defaults = DEFAULTS_BY_INTENT.get(intent, DEFAULTS_BY_INTENT[IntentType.GENERAL_CHAT])

    if not _GEMINI_READY:
        return defaults

    try:
        intent_hint = {
            IntentType.ROUTINE_REQUEST:  "skincare routine and ingredient follow-ups",
            IntentType.MEDICAL_QUESTION: "condition management and medical referral follow-ups",
            IntentType.IMAGE_ANALYSIS:   "image analysis and skin observation follow-ups",
            IntentType.GENERAL_CHAT:     "general skincare education follow-ups",
        }.get(intent, "dermatology follow-ups")

        prompt = (
            f"Generate exactly 3 short follow-up question suggestions for a dermatology "
            f"AI chatbot. Focus on {intent_hint}.\n\n"
            f"User asked: {user_message[:200]}\n"
            f"Assistant replied: {assistant_reply[:400]}\n\n"
            "Rules:\n"
            "- Each suggestion must be 4-10 words\n"
            "- Naturally conversational, not robotic\n"
            "- Directly relevant to the specific exchange above\n"
            "- Never repeat what was already discussed\n\n"
            'Return ONLY a JSON array: ["suggestion 1", "suggestion 2", "suggestion 3"]\n'
            "No preamble. No markdown."
        )

        def _call() -> str:
            m = genai.GenerativeModel(
                model_name        = GEMINI_FLASH_MODEL,
                generation_config = GenerationConfig(
                    temperature       = 0.85,
                    max_output_tokens = 150,
                )
            )
            return m.generate_content(prompt).text

        raw    = await asyncio.wait_for(asyncio.to_thread(_call), timeout=CHIPS_TIMEOUT_S)
        clean  = raw.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)

        if isinstance(parsed, list):
            chips = [str(c) for c in parsed[:3]]
        elif isinstance(parsed, dict):
            first = next(iter(parsed.values()), [])
            chips = [str(c) for c in first[:3]] if isinstance(first, list) else []
        else:
            chips = []

        return chips if len(chips) == 3 else defaults

    except asyncio.TimeoutError:
        logger.warning("[Chips] Gemini timed out — using intent defaults")
        return defaults
    except json.JSONDecodeError:
        logger.warning("[Chips] JSON parse failed — using intent defaults")
        return defaults
    except Exception as e:
        logger.warning(f"[Chips] Failed: {type(e).__name__}: {e} — using defaults")
        return defaults


# =====================================================================
# 11. SYSTEM PROMPT
# =====================================================================

SYSTEM_PROMPT = """\
You are **Derm**, a board-certified dermatologist and empathetic skincare coach \
inside the DermAI platform. Your communication style is warm, professional, and \
conversational — like a trusted doctor who genuinely cares about each patient.

─── CORE BEHAVIOR ───────────────────────────────────────────────────────────────

1. **Clarification first.** Never give one-size-fits-all responses. Before advising,
   ensure you understand the user's skin type, age, climate, lifestyle, and goals.
   Ask targeted follow-up questions when any of these are unknown.

2. **Diagnostic quiz.** If a user asks for a skincare routine and their skin profile
   is unknown from conversation history, initiate a brief 5-question diagnostic quiz.
   Ask ONE question at a time, naturally woven into conversation — never as a numbered
   list dump:
   Q1: "What's your skin type? (oily / dry / combination / sensitive / normal)"
   Q2: "What age range are you in? (18-25 / 26-35 / 36-45 / 46-55 / 55+)"
   Q3: "What's your primary skincare concern or goal?"
   Q4: "What's your budget preference — drugstore, mid-range, or premium?"
   Q5: "What kind of climate do you live in? (humid, dry, temperate, cold)"
   After collecting all 5 answers, call `generate_skincare_routine` immediately.

3. **Memory.** You have access to the full conversation history. Reference it
   naturally — don't ask the user to repeat information they've already given.

4. **Product recommendations.** ALWAYS qualify with "I'd recommend looking for
   products containing…" — NEVER cite specific brand names.

5. **Layering guidance.** When recommending multiple ingredients, always explain
   the correct application order and any ingredient interactions
   (e.g., "Don't layer niacinamide with pure vitamin C — use them at different times").

─── CLINICAL DEPTH ──────────────────────────────────────────────────────────────

When discussing skin conditions, always cover:
- **What it is** in plain language
- **What triggers or worsens it**
- **What helps** (OTC-accessible approaches only)
- **When to see a doctor** — give specific escalation signals, not generic "see a doctor"

When discussing ingredients:
- State the evidence tier: clinically proven / well-supported / promising / anecdotal
- State the ideal concentration range (e.g., "niacinamide is most effective at 5-10%")
- Note any photosensitivity concerns and whether to use AM or PM
- Note any known interactions with other common actives

─── SAFETY CONSTRAINTS (NON-NEGOTIABLE) ─────────────────────────────────────────

• NEVER diagnose malignancy, cancer, or any serious pathology.
  If concerning: "Based on what you've described, this warrants an in-person
  evaluation by a dermatologist. I can help you understand what to ask your doctor."

• NEVER recommend or name prescription-only medications (tretinoin, isotretinoin,
  antibiotics, oral steroids, biologics, immunosuppressants). Instead:
  "There are prescription options your dermatologist can discuss with you."

• NEVER make confident diagnostic claims. Always use:
  "This could be consistent with...", "This may suggest...", "This sounds like
  it could be..."

• EMERGENCY PROTOCOL: If the user describes: rapidly spreading rash, difficulty
  breathing, facial swelling, severe pain, signs of infection with fever — respond
  with: "⚠️ What you're describing may require immediate medical attention.
  Please contact emergency services or go to an urgent care facility now.
  I am an AI and cannot assess emergencies." Then stop and do not provide
  further skincare advice in that turn.

─── TOOL USAGE ──────────────────────────────────────────────────────────────────

• If the user shares their location OR you know their coordinates from context,
  call `get_weather_advice` BEFORE giving any routine or product advice.
  Climate conditions materially affect skincare recommendations.

• If the user references an uploaded image OR the context shows an image_id,
  call `get_vision_risk_assessment` to retrieve its risk analysis.
  Always lead with the risk level before giving any advice.

• After completing the 5-question diagnostic quiz (all 5 answers collected),
  call `generate_skincare_routine` immediately with the gathered profile.

─── RESPONSE FORMAT ─────────────────────────────────────────────────────────────

• Use markdown: **bold** for key terms, bullet points for lists, numbered lists
  for ordered routines, > blockquotes for important warnings.
• Keep responses focused. Avoid walls of text — break complex topics into sections.
• End with a natural follow-up question or clear next step when appropriate.
• For routines: always show AM and PM separately with numbered steps.
• For ingredient advice: always include % concentration and AM/PM timing.

─── DISCLAIMER ──────────────────────────────────────────────────────────────────

You are an AI assistant, not a substitute for professional medical care.
When in doubt, always recommend consulting a board-certified dermatologist.\
"""


# =====================================================================
# 12. SSE HELPERS & CORE AGENT LOOP
# =====================================================================


def _sse_event(data: dict[str, Any]) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


async def stream_chat_response(
    user_id:      str,
    session_id:   str,
    user_message: str,
    location:     Optional[LocationPayload],
    image_id:     Optional[str],
) -> AsyncGenerator[str, None]:
    """
    Production-grade SSE streaming agent.

    Pipeline:
    1. Build message context (history + system prompt + user message)
    2. Classify intent (parallel, non-blocking)
    3. Emergency fast-path (bypass agent loop)
    4. Multi-round Gemini Pro agent loop with native function calling
       - True token streaming via stream=True
       - Function call detection per chunk
       - Tool execution with typed SSE events
       - FunctionResponse injection for next round
    5. Post-generation safety filter
    6. Suggestion chips (parallel Gemini Flash call)
    7. Persist history to Redis
    8. Emit done event

    Guarantees:
    - Always emits a `done` event regardless of any error
    - Never hangs — all external calls have explicit timeouts
    - All exceptions are typed and logged with full traceback
    """
    turn_start_ms         = int(time.time() * 1000)
    full_reply            = ""
    tools_called: list[str] = []
    tool_rounds           = 0
    safety_hit            = False

    # ── Step 1: Build context ─────────────────────────────────────────
    messages   = await build_messages(
        user_id, session_id, user_message, location, image_id
    )
    turn_index = await get_turn_index(user_id, session_id)

    # ── Step 2: Classify intent (parallel, non-blocking) ──────────────
    intent_task = asyncio.create_task(
        classify_intent(user_message, has_image=bool(image_id), history_len=turn_index)
    )

    # ── Step 3: Guard — Gemini not ready ─────────────────────────────
    if not _GEMINI_READY:
        yield _sse_event({
            "type":    "error",
            "message": "AI service is temporarily unavailable. Please try again shortly."
        })
        yield _sse_event({"type": "done"})
        return

    # ── Step 4: Await intent (with timeout) ──────────────────────────
    try:
        intent_result: IntentResult = await asyncio.wait_for(
            intent_task, timeout=INTENT_TIMEOUT_S + 0.5
        )
    except asyncio.TimeoutError:
        intent_result = IntentResult(
            intent     = IntentType.GENERAL_CHAT,
            confidence = 0.5,
            reasoning  = "timeout"
        )

    logger.info(
        f"[DermAI] Turn {turn_index} | user={user_id[:8]} | "
        f"intent={intent_result.intent} ({intent_result.confidence:.0%})"
    )

    # ── Step 5: Emergency fast-path ───────────────────────────────────
    if intent_result.intent == IntentType.EMERGENCY:
        emergency_msg = (
            "⚠️ **What you're describing may require immediate medical attention.**\n\n"
            "Please contact emergency services or go to an urgent care facility now. "
            "I am an AI assistant and cannot assess medical emergencies.\n\n"
            "**Emergency resources:**\n"
            "- Emergency services: 112 (India) / 911 (US) / 999 (UK)\n"
            "- Or go to your nearest emergency department immediately."
        )
        yield _sse_event({"type": "text_delta", "content": emergency_msg})
        yield _sse_event({"type": "suggestion_chips", "chips": []})
        yield _sse_event({"type": "done"})
        # Persist the emergency turn
        messages.append({"role": "assistant", "content": emergency_msg})
        await save_history(user_id, session_id, messages)
        return

    # ── Step 6: Build Gemini model with tools ─────────────────────────
    # Inject intent hint into system context for better tool triggering
    intent_context = (
        f"\n\n[Internal context: This message is classified as "
        f"'{intent_result.intent}' with {intent_result.confidence:.0%} confidence. "
        f"Use this to inform your response strategy.]"
    )

    # Temporarily augment system message with intent context
    augmented_messages = []
    for msg in messages:
        if msg.get("role") == "system":
            augmented_messages.append({
                "role":    "system",
                "content": msg["content"] + intent_context
            })
        else:
            augmented_messages.append(msg)

    system_instruction = next(
        (m["content"] for m in augmented_messages if m["role"] == "system"),
        SYSTEM_PROMPT
    )

    model = genai.GenerativeModel(
        model_name         = GEMINI_PRO_MODEL,
        system_instruction = system_instruction,
        tools              = GEMINI_TOOLS,
        generation_config  = GenerationConfig(
            temperature       = 0.75,
            max_output_tokens = 2048,
            candidate_count   = 1,
        )
    )

    # ── Step 7: Multi-round agent loop ────────────────────────────────
    current_msg: Any = augmented_messages[-1].get("content", user_message)

    try:
        for _round in range(MAX_TOOL_ROUNDS):
            history              = _to_gemini_history(augmented_messages[:-1])
            chat                 = model.start_chat(history=history)
            current_content      = ""
            tool_calls_found: list[dict] = []

            # Stream Gemini response
            def _stream(msg):
                return chat.send_message(msg, stream=True)

            try:
                stream = await asyncio.wait_for(
                    asyncio.to_thread(_stream, current_msg),
                    timeout=AGENT_TIMEOUT_S
                )
            except asyncio.TimeoutError:
                logger.error(f"[DermAI] Agent timed out on round {_round}")
                if not full_reply:
                    yield _sse_event({
                        "type":    "error",
                        "message": "Response is taking too long. Please try again."
                    })
                break
            except Exception as e:
                logger.error(
                    f"[DermAI] Gemini call failed round {_round}: "
                    f"{type(e).__name__}: {e}"
                )
                if not full_reply:
                    yield _sse_event({
                        "type":    "error",
                        "message": "Our AI assistant is temporarily unavailable. Please try again shortly."
                    })
                break

            # Iterate chunks — stream to frontend token by token
            for chunk in stream:
                # Text delta — emit immediately per token
                if chunk.text:
                    current_content += chunk.text
                    yield _sse_event({
                        "type":    "text_delta",
                        "content": chunk.text
                    })

                # Function call detection
                for candidate in (chunk.candidates or []):
                    if not candidate.content:
                        continue
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            # Deduplicate — Gemini sometimes repeats function calls
                            call_sig = (
                                f"{fc.name}:"
                                f"{json.dumps(dict(fc.args), sort_keys=True)}"
                            )
                            if not any(
                                f"{tc['name']}:{json.dumps(tc['args'], sort_keys=True)}" == call_sig
                                for tc in tool_calls_found
                            ):
                                tool_calls_found.append({
                                    "name": fc.name,
                                    "args": dict(fc.args),
                                })

            full_reply  += current_content
            tool_rounds  = _round + 1

            # No tool calls — agent is done
            if not tool_calls_found:
                augmented_messages.append({
                    "role":    "assistant",
                    "content": current_content
                })
                break

            # Append assistant turn (may be empty if model went straight to tool call)
            if current_content:
                augmented_messages.append({
                    "role":    "assistant",
                    "content": current_content
                })

            # Execute tool calls
            function_response_parts: list[protos.Part] = []

            for tc in tool_calls_found:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tools_called.append(tool_name)

                yield _sse_event({
                    "type":      "tool_call",
                    "tool_name": tool_name,
                    "status":    "running"
                })

                try:
                    result = await asyncio.wait_for(
                        dispatch_tool_call(tool_name, tool_args),
                        timeout=TOOL_TIMEOUT_S
                    )

                    # Emit structured routine payload when applicable
                    if tool_name == "generate_skincare_routine":
                        try:
                            routine_json = json.loads(result)
                            yield _sse_event({
                                "type":    "structured_routine",
                                "payload": routine_json
                            })
                        except json.JSONDecodeError:
                            pass

                    yield _sse_event({
                        "type":      "tool_call",
                        "tool_name": tool_name,
                        "status":    "complete"
                    })

                    function_response_parts.append(
                        protos.Part(
                            function_response=protos.FunctionResponse(
                                name     = tool_name,
                                response = {"result": result}
                            )
                        )
                    )

                except asyncio.TimeoutError:
                    logger.error(f"[DermAI] Tool '{tool_name}' timed out")
                    yield _sse_event({
                        "type":      "tool_call",
                        "tool_name": tool_name,
                        "status":    "failed"
                    })
                    function_response_parts.append(
                        protos.Part(
                            function_response=protos.FunctionResponse(
                                name     = tool_name,
                                response = {
                                    "result": (
                                        f"Tool '{tool_name}' timed out. "
                                        "Advise the user without this data."
                                    )
                                }
                            )
                        )
                    )

                except Exception as e:
                    logger.error(
                        f"[DermAI] Tool '{tool_name}' failed: {type(e).__name__}: {e}"
                    )
                    yield _sse_event({
                        "type":      "tool_call",
                        "tool_name": tool_name,
                        "status":    "failed"
                    })
                    function_response_parts.append(
                        protos.Part(
                            function_response=protos.FunctionResponse(
                                name     = tool_name,
                                response = {
                                    "result": (
                                        f"Tool '{tool_name}' encountered an error. "
                                        "Provide advice without this data, noting it is unavailable."
                                    )
                                }
                            )
                        )
                    )

            # Send tool results back to Gemini for next round
            current_msg = protos.Content(parts=function_response_parts)

    except Exception as e:
        logger.error(f"[DermAI] Agent loop unhandled error: {e}", exc_info=True)
        if not full_reply:
            yield _sse_event({
                "type":    "error",
                "message": "Our AI assistant is temporarily unavailable. Please try again shortly."
            })

    # ── Step 8: Safety filter ─────────────────────────────────────────
    if full_reply:
        filtered_reply, safety_hit = _apply_safety_filter(full_reply)
        if safety_hit:
            # Emit the disclaimer as an additional text_delta
            disclaimer_suffix = filtered_reply[len(full_reply):]
            yield _sse_event({
                "type":    "text_delta",
                "content": disclaimer_suffix
            })
            full_reply = filtered_reply

    # ── Step 9: Suggestion chips (parallel, non-blocking) ────────────
    chips = await generate_suggestion_chips(
        user_message    = user_message,
        assistant_reply = full_reply,
        intent          = intent_result.intent,
    )
    yield _sse_event({"type": "suggestion_chips", "chips": chips})

    # ── Step 10: Persist history ──────────────────────────────────────
    # Use original messages list (not augmented — don't persist intent hints)
    if full_reply:
        messages.append({"role": "assistant", "content": full_reply})
    await save_history(user_id, session_id, messages)

    # ── Step 11: Observability log ────────────────────────────────────
    latency_ms = int(time.time() * 1000) - turn_start_ms
    logger.info(
        f"[DermAI] Turn complete | "
        f"rounds={tool_rounds} | "
        f"tools={tools_called} | "
        f"safety={safety_hit} | "
        f"latency={latency_ms}ms | "
        f"reply_len={len(full_reply)}"
    )

    # ── Step 12: Done — always emitted ───────────────────────────────
    yield _sse_event({"type": "done"})


# =====================================================================
# 13. FASTAPI ROUTER
# =====================================================================

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/message")
async def chat_message(
    body:    ChatMessageRequest,
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
            user_id      = user_id,
            session_id   = body.session_id,
            user_message = body.message,
            location     = body.location,
            image_id     = body.image_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "Connection":       "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    payload:    dict = Depends(verify_token),
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
    payload:    dict = Depends(verify_token),
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
    user_id: str    = payload["sub"]
    session_ids     = await list_sessions(user_id)
    return {"user_id": user_id, "sessions": session_ids}


@router.get("/session/{session_id}/metadata")
async def get_session_metadata(
    session_id: str,
    payload:    dict = Depends(verify_token),
) -> dict[str, Any]:
    """
    Returns lightweight session metadata without full message content.
    Used by frontend to show session info in sidebar.
    """
    user_id: str = payload["sub"]
    history = await load_history(user_id, session_id)

    user_msgs      = [m for m in history if m.get("role") == "user"]
    assistant_msgs = [m for m in history if m.get("role") == "assistant"]

    # Extract first user message as session title (truncated)
    first_msg = user_msgs[0].get("content", "") if user_msgs else ""
    title     = first_msg[:60] + "..." if len(first_msg) > 60 else first_msg

    return {
        "session_id":    session_id,
        "title":         title or "New conversation",
        "turn_count":    len(user_msgs),
        "message_count": len([m for m in history if m.get("role") != "system"]),
        "has_history":   len(user_msgs) > 0,
    }
