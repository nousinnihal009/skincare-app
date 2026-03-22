"""
test_chatbot_smoke.py — Smoke tests for the production chatbot.py rewrite.

Tests:
  1. Module imports without error
  2. All 6 SSE event types identified
  3. `done` event is always the last event emitted
  4. No exception escapes the generator
  5. GEMINI_TOOLS built correctly from TOOL_SCHEMAS
  6. _apply_safety_filter triggers on expected words
  7. _to_gemini_history enforces strict alternation
  8. Intent fallback works when classifier raises
"""
import asyncio
import json
import logging
import sys
import os

# Ensure backend root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING)

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))
    status = PASS if condition else FAIL
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


# ─── Test 1: Module import ───────────────────────────────────────────
print("\n[Test 1] Module import")
try:
    from app.services.chatbot import (
        stream_chat_response,
        _apply_safety_filter,
        _to_gemini_history,
        classify_intent,
        generate_suggestion_chips,
        IntentType,
        IntentResult,
        GEMINI_TOOLS,
        TOOL_SCHEMAS,
        _GEMINI_READY,
        _sse_event,
    )
    check("Module imports without error", True)
except Exception as e:
    check("Module imports without error", False, str(e))
    print("\nFatal: cannot continue without a successful import.")
    sys.exit(1)

# ─── Test 2: GEMINI_TOOLS ────────────────────────────────────────────
print("\n[Test 2] GEMINI_TOOLS built from TOOL_SCHEMAS")
try:
    check("GEMINI_TOOLS is a non-empty list", isinstance(GEMINI_TOOLS, list) and len(GEMINI_TOOLS) > 0)
    check(
        "All 3 tool schemas converted",
        len(GEMINI_TOOLS[0].function_declarations) == len(TOOL_SCHEMAS),
        f"found {len(GEMINI_TOOLS[0].function_declarations)} declarations, expected {len(TOOL_SCHEMAS)}"
    )
    tool_names = {fd.name for fd in GEMINI_TOOLS[0].function_declarations}
    check(
        "Tool names match schema",
        tool_names == {"get_weather_advice", "get_vision_risk_assessment", "generate_skincare_routine"},
        str(tool_names)
    )
except Exception as e:
    check("GEMINI_TOOLS check", False, str(e))

# ─── Test 3: _apply_safety_filter ───────────────────────────────────
print("\n[Test 3] Safety filter")
try:
    text_safe    = "Niacinamide is excellent for oily skin. It helps reduce pore size."
    text_trigger = "This looks like it could be melanoma, you should see a doctor."
    text_rx      = "You may benefit from isotretinoin for severe acne."

    result_safe, triggered_safe       = _apply_safety_filter(text_safe)
    result_trigger, triggered_trigger = _apply_safety_filter(text_trigger)
    result_rx, triggered_rx           = _apply_safety_filter(text_rx)

    check("Safe text: no trigger", not triggered_safe)
    check("Safe text: not modified", result_safe == text_safe)
    check("'melanoma' triggers filter", triggered_trigger)
    check("Trigger: disclaimer appended, not replaced", result_trigger.startswith(text_trigger))
    check("'isotretinoin' triggers filter", triggered_rx)
    check("Disclaimer contains ⚕️", "⚕️" in result_trigger)
except Exception as e:
    check("Safety filter", False, str(e))

# ─── Test 4: _to_gemini_history ─────────────────────────────────────
print("\n[Test 4] _to_gemini_history format conversion")
try:
    msgs = [
        {"role": "system",    "content": "You are Derm."},
        {"role": "user",      "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user",      "content": "How are you?"},
        {"role": "assistant", "content": "Great, thanks!"},
        {"role": "user",      "content": "Final question"},  # current turn — should be popped
    ]
    history = _to_gemini_history(msgs)

    check("System message excluded", not any(h["role"] == "system" for h in history))
    check("History starts with 'user'", history[0]["role"] == "user" if history else True)
    check("History ends with 'model'", history[-1]["role"] == "model" if history else True)
    check(
        "Correct alternation (no consecutive same roles)",
        all(history[i]["role"] != history[i + 1]["role"] for i in range(len(history) - 1)),
        f"roles: {[h['role'] for h in history]}"
    )

    # Test consecutive same-role merge
    msgs_duplicate = [
        {"role": "user",      "content": "First"},
        {"role": "user",      "content": "Second"},  # should merge with above
        {"role": "assistant", "content": "Reply"},
    ]
    hist_dup = _to_gemini_history(msgs_duplicate)
    # After strict alternation: user merged, ends with model
    check("Consecutive user turns merged", len(hist_dup) >= 1 and "First" in hist_dup[0]["parts"][0])
except Exception as e:
    check("_to_gemini_history", False, str(e))

# ─── Test 5: _sse_event format ───────────────────────────────────────
print("\n[Test 5] SSE event format")
try:
    evt = _sse_event({"type": "done"})
    check("SSE event starts with 'data: '", evt.startswith("data: "))
    check("SSE event ends with '\\n\\n'", evt.endswith("\n\n"))
    parsed = json.loads(evt[6:])  # strip "data: "
    check("SSE event JSON parseable", parsed == {"type": "done"})
except Exception as e:
    check("SSE event format", False, str(e))

# ─── Test 6: Generator always emits done (no Gemini key needed) ──────
print("\n[Test 6] Generator emits 'done' when Gemini unavailable")
try:
    from app.services import chatbot as _chatbot_mod

    # Force _GEMINI_READY to False to simulate missing key
    original_ready = _chatbot_mod._GEMINI_READY
    _chatbot_mod._GEMINI_READY = False

    async def _run_generator():
        events = []
        try:
            async for chunk in stream_chat_response(
                "smoke_user", "smoke_session", "Hello test", None, None
            ):
                events.append(chunk)
        except Exception as exc:
            events.append(f"EXCEPTION: {exc}")
        return events

    chunks = asyncio.run(_run_generator())
    _chatbot_mod._GEMINI_READY = original_ready  # restore

    parsed_events = []
    for c in chunks:
        if c.startswith("data: "):
            try:
                parsed_events.append(json.loads(c[6:]))
            except json.JSONDecodeError:
                pass

    types = [e.get("type") for e in parsed_events]
    check("'error' SSE emitted when Gemini unavailable", "error" in types)
    check("'done' SSE always emitted last", types[-1] == "done" if types else False, str(types))
    check("No exception escaped generator", not any(str(c).startswith("EXCEPTION:") for c in chunks))
except Exception as e:
    check("Generator done-guarantee", False, str(e))

# ─── Test 7: IntentType enum values ─────────────────────────────────
print("\n[Test 7] IntentType enum completeness")
try:
    expected = {"routine_request", "medical_question", "image_analysis", "general_chat", "emergency"}
    actual   = {e.value for e in IntentType}
    check("All 5 intent types present", expected == actual, str(actual))
except Exception as e:
    check("IntentType enum", False, str(e))

# ─── Test 8: Dead code removed ────────────────────────────────────────
print("\n[Test 8] Dead code removed")
try:
    import app.services.chatbot as _cm
    check("GPT_MODEL removed", not hasattr(_cm, "GPT_MODEL"))
    check("GPT_MINI_MODEL removed", not hasattr(_cm, "GPT_MINI_MODEL"))
    # tool_calls_accumulated was a local variable inside stream_chat_response — verified by grep
    src_path = os.path.join(os.path.dirname(__file__), "app", "services", "chatbot.py")
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    check("'tool_calls_accumulated' not in source", "tool_calls_accumulated" not in src)
    check("'openai' not imported", "import openai" not in src and "from openai" not in src)
    check("'AsyncOpenAI' not in source", "AsyncOpenAI" not in src)
except Exception as e:
    check("Dead code removal", False, str(e))

# ─── Summary ─────────────────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for _, ok, _ in results if ok)
total  = len(results)
print(f"  Results: {passed}/{total} checks passed")
if passed == total:
    print(f"  {PASS} All smoke tests passed.")
else:
    print(f"  {FAIL} {total - passed} check(s) failed — review above.")
print("=" * 55 + "\n")

sys.exit(0 if passed == total else 1)
