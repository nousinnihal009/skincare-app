"""
condition_advisor.py — ConditionAdvisorEngine
Orchestrates ConditionKB data, user request, weather context, and optional
LLM enrichment to generate the ConditionResponse payload.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.services.condition_kb import ConditionKnowledgeBase, ConditionKB, KBStep
from app.services.weather import WeatherContext, get_weather_context

load_dotenv()

logger = logging.getLogger("dermai.condition_advisor")

import google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

GPT_MINI_MODEL = "gpt-4o-mini"
LLM_TIMEOUT_SECONDS = 2.0

CATEGORY_D_CONDITIONS = {"actinic_keratosis", "melanoma_risk"}


# =====================================================================
# Pydantic Request / Response Schemas
# =====================================================================


class LocationPayload(BaseModel):
    lat: float
    lon: float


class ConditionRequest(BaseModel):
    condition: str
    severity: Literal["mild", "moderate", "severe"]
    skin_type: Literal["oily", "dry", "combination", "sensitive", "normal"]
    age_group: Literal["teen", "twenties", "thirties", "forties_plus"]
    affected_areas: list[str]
    symptom_duration: Literal[
        "less_than_1_week",
        "1_to_4_weeks",
        "1_to_6_months",
        "more_than_6_months",
        "chronic_recurring",
    ]
    known_triggers: list[str]
    current_treatments: list[str]
    location: LocationPayload | None = None


class RedFlag(BaseModel):
    description: str
    urgency: str
    action: str


class CarePlanStep(BaseModel):
    step: int
    phase: str
    category: str
    recommendation: str
    why_explanation: str
    fallback_why: str
    is_otc_available: bool
    avoid_if: list[str] = Field(default_factory=list)
    condition_safe: bool = True


class IngredientEntry(BaseModel):
    ingredient: str
    reason: str


class TriggerEntry(BaseModel):
    trigger: str
    management_tip: str
    severity_impact: str


class ConditionEducation(BaseModel):
    what_it_is: str
    what_causes_it: str
    is_contagious: bool
    contagion_guidance: str | None
    is_curable: bool
    typical_duration: str
    common_misconceptions: list[str]


class WeatherSummary(BaseModel):
    condition: str
    temperature_c: float
    humidity_pct: float
    uv_index: float
    routine_impact: str


class ConditionResponse(BaseModel):
    condition: str
    condition_display_name: str
    category: str
    severity_assessed: str
    is_contagious: bool
    education: ConditionEducation
    care_plan: list[CarePlanStep]
    ingredients_to_seek: list[IngredientEntry]
    ingredients_to_avoid: list[IngredientEntry]
    trigger_guidance: list[TriggerEntry]
    red_flags: list[RedFlag]
    referral_recommended: bool
    referral_urgency: str
    when_to_see_doctor: str
    weather_context: WeatherSummary | None = None
    climate_care_note: str | None = None
    prescription_interaction_note: str | None = None
    medical_disclaimer: str
    llm_enriched: bool = False
    generated_at: str


# =====================================================================
# Protocol Cache (in-memory, 20 min TTL)
# =====================================================================


class ProtocolCache:
    def __init__(self, ttl_minutes: int = 20):
        self._store: dict[str, tuple[ConditionResponse, datetime]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._lock = asyncio.Lock()

    def _make_key(self, req: ConditionRequest) -> str:
        parts = [
            req.condition, req.severity, req.skin_type, req.age_group,
            ",".join(sorted(req.affected_areas)),
            req.symptom_duration,
            ",".join(sorted(req.known_triggers)),
            ",".join(sorted(req.current_treatments)),
            f"{req.location.lat:.1f},{req.location.lon:.1f}" if req.location else "no_loc",
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    async def get(self, req: ConditionRequest) -> ConditionResponse | None:
        key = self._make_key(req)
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            response, cached_at = entry
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if now - cached_at.replace(tzinfo=None) > self._ttl:
                del self._store[key]
                return None
            return response

    async def set(self, req: ConditionRequest, response: ConditionResponse) -> None:
        key = self._make_key(req)
        async with self._lock:
            self._store[key] = (response, datetime.now(timezone.utc).replace(tzinfo=None))

    async def purge_expired(self) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        async with self._lock:
            expired = [k for k, (_, ts) in self._store.items()
                       if now - ts.replace(tzinfo=None) > self._ttl]
            for k in expired:
                del self._store[k]
            return len(expired)


# Module-level singletons
_protocol_cache = ProtocolCache(ttl_minutes=20)
_kb = ConditionKnowledgeBase()


# =====================================================================
# ConditionAdvisorEngine
# =====================================================================


class ConditionAdvisorEngine:
    """
    Generates a ConditionResponse from:
      1. KB lookup → education, steps, ingredients, triggers, red_flags
      2. Step scoring → mandatory + scored optional steps
      3. Category D safety overrides
      4. Treatment conflict resolution
      5. Weather context injection
      6. LLM enrichment (2s timeout + fallback)
    """

    def __init__(self) -> None:
        self._kb = _kb

    # ── Public ────────────────────────────────────────────

    async def generate_protocol(self, req: ConditionRequest) -> ConditionResponse:
        """Main entry: check cache → build → enrich → cache → return."""

        # Cache check
        cached = await _protocol_cache.get(req)
        if cached is not None:
            logger.info("Protocol cache HIT for %s", req.condition)
            return cached

        # KB lookup
        kb_entry = self._kb.get(req.condition)

        # Category D override: always severe, always immediate referral
        severity = req.severity
        if req.condition in CATEGORY_D_CONDITIONS:
            severity = "severe"

        # Weather context
        weather: WeatherContext | None = None
        if req.location:
            try:
                weather = await get_weather_context(req.location.lat, req.location.lon)
            except Exception as e:
                logger.warning("Weather fetch failed: %s", e)

        # Build care plan
        care_plan = self._build_care_plan(kb_entry, req, severity)

        # Apply treatment conflict resolution
        care_plan, new_avoids = self._resolve_conflicts(care_plan, req)

        # Education block
        education = ConditionEducation(
            what_it_is=kb_entry.what_it_is,
            what_causes_it=kb_entry.what_causes_it,
            is_contagious=kb_entry.is_contagious,
            contagion_guidance=kb_entry.contagion_guidance,
            is_curable=kb_entry.is_curable,
            typical_duration=kb_entry.typical_duration,
            common_misconceptions=kb_entry.common_misconceptions,
        )

        # Ingredients (append any conflicts from care plan step removal)
        seek = [IngredientEntry(ingredient=ing, reason=reason)
                for ing, reason in kb_entry.seek_ingredients]
        avoid = [IngredientEntry(ingredient=ing, reason=reason)
                 for ing, reason in kb_entry.avoid_ingredients]
        avoid.extend(new_avoids)

        # Triggers
        triggers = [TriggerEntry(trigger=t, management_tip=tip, severity_impact=sev)
                    for t, tip, sev in kb_entry.triggers]

        # Red flags
        red_flags = [RedFlag(description=desc, urgency=urg, action=act)
                     for desc, urg, act in kb_entry.red_flags]

        # Weather summary and climate note
        weather_summary, climate_note = self._build_weather_context(kb_entry, weather)

        # Prescription interaction note
        rx_note = self._prescription_interaction_note(req)

        # Referral
        referral_recommended = kb_entry.referral_recommended
        referral_urgency = kb_entry.referral_urgency
        
        # Fix 14: Backend Referral Escalation
        if req.severity == "severe":
            referral_recommended = True
            if referral_urgency in ["not_required", "routine"]:
                referral_urgency = "soon"
                
        if req.symptom_duration in ["more_than_6_months", "chronic_recurring"]:
            referral_recommended = True
            if referral_urgency == "not_required":
                referral_urgency = "routine"

        if req.condition in CATEGORY_D_CONDITIONS:
            referral_recommended = True
            referral_urgency = "immediate"

        # Disclaimer
        disclaimer = kb_entry.base_disclaimer
        if req.condition in CATEGORY_D_CONDITIONS:
            disclaimer = (
                f"⚠️ IMPORTANT: {kb_entry.display_name} requires immediate professional "
                f"medical evaluation. The information provided here is for educational "
                f"purposes only and does NOT replace professional dermatological care. "
                f"{kb_entry.base_disclaimer}"
            )

        # Build response
        response = ConditionResponse(
            condition=req.condition,
            condition_display_name=kb_entry.display_name,
            category=kb_entry.category,
            severity_assessed=severity,
            is_contagious=kb_entry.is_contagious,
            education=education,
            care_plan=care_plan,
            ingredients_to_seek=seek,
            ingredients_to_avoid=avoid,
            trigger_guidance=triggers,
            red_flags=red_flags,
            referral_recommended=referral_recommended,
            referral_urgency=referral_urgency,
            when_to_see_doctor=kb_entry.when_to_see_doctor,
            weather_context=weather_summary,
            climate_care_note=climate_note,
            prescription_interaction_note=rx_note,
            medical_disclaimer=disclaimer,
            llm_enriched=False,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # LLM enrichment (2s timeout, fallback to fallback_why)
        response = await self._enrich_with_llm(response, kb_entry, req)

        # Cache the result
        await _protocol_cache.set(req, response)

        return response

    # ── Care Plan Builder ─────────────────────────────────

    def _build_care_plan(
        self, kb: ConditionKB, req: ConditionRequest, severity: str
    ) -> list[CarePlanStep]:
        """Build ordered care plan from mandatory + scored optional steps."""
        steps: list[CarePlanStep] = []
        step_num = 1

        # Mandatory steps — always included
        for s in kb.mandatory_steps:
            steps.append(CarePlanStep(
                step=step_num,
                phase=s.phase,
                category=s.category,
                recommendation=s.recommendation,
                why_explanation=s.fallback_why,  # LLM will overwrite later
                fallback_why=s.fallback_why,
                is_otc_available=s.is_otc_available,
                avoid_if=s.avoid_if,
                condition_safe=True,
            ))
            step_num += 1

        # Optional steps — include if computed score >= 2
        for s in kb.optional_steps:
            computed = self._score_optional_step(s, req, severity)
            if computed >= 2:
                steps.append(CarePlanStep(
                    step=step_num,
                    phase=s.phase,
                    category=s.category,
                    recommendation=s.recommendation,
                    why_explanation=s.fallback_why,
                    fallback_why=s.fallback_why,
                    is_otc_available=s.is_otc_available,
                    avoid_if=s.avoid_if,
                    condition_safe=True,
                ))
                step_num += 1

        return steps

    def _score_optional_step(
        self, step: KBStep, req: ConditionRequest, severity: str
    ) -> int:
        """
        Compute score for optional step:
          base score + modifier matches from severity, duration, areas.
        """
        score = step.score
        mods = step.score_modifiers

        # Severity match
        if severity in mods:
            score += mods[severity]

        # Duration match
        if req.symptom_duration in mods:
            score += mods[req.symptom_duration]

        # Area match
        for area in req.affected_areas:
            if area in mods:
                score += mods[area]

        # Known triggers match
        for trigger in req.known_triggers:
            if trigger in mods:
                score += mods[trigger]

        return score

    # ── Treatment Conflict Resolution ─────────────────────

    def _resolve_conflicts(
        self, plan: list[CarePlanStep], req: ConditionRequest
    ) -> tuple[list[CarePlanStep], list[IngredientEntry]]:
        """
        Check step.avoid_if against req.current_treatments.
        If there's a match, remove the step from the plan and instead
        return an IngredientEntry for the avoid list.
        Also adds conditional notes for phototherapy, etc.
        """
        resolved: list[CarePlanStep] = []
        new_avoids: list[IngredientEntry] = []

        user_treatments = set(req.current_treatments)

        for step in plan:
            # Check for conflict
            conflict = False
            for avoid_condition in step.avoid_if:
                if avoid_condition in user_treatments:
                    conflict = True
                    break

            if conflict:
                # Remove step, add to avoid list
                new_avoids.append(
                    IngredientEntry(
                        ingredient=step.category,
                        reason=f"Conflicts with your current treatment ({', '.join(user_treatments.intersection(set(step.avoid_if)))}) — DO NOT use."
                    )
                )
                continue

            # Fix 11: perioral_dermatitis steroid warning
            if req.condition == "perioral_dermatitis" and "prescription_topical" in req.current_treatments:
                if step.category == "Treatment":
                    step.recommendation = (
                        f"⚠️ CRITICAL: STOP all topical steroids immediately! Topicals like hydrocortisone "
                        f"can worsen perioral dermatitis. Consult your doctor for non-steroidal alternatives. "
                        f"{step.recommendation}"
                    )

            # If user is on prescription topical AND step recommends OTC of same type,
            # add a note but keep the step
            elif "prescription_topical" in req.current_treatments:
                if step.category == "Treatment" and step.is_otc_available:
                    step.recommendation = (
                        f"{step.recommendation} (Note: You are using a prescription "
                        f"topical — continue your prescribed treatment and consult your "
                        f"dermatologist before adding OTC treatments.)"
                    )

            # Phototherapy patients — extra SPF note
            if "phototherapy" in req.current_treatments:
                if step.category == "Sun Protection":
                    step.recommendation = (
                        f"{step.recommendation} CRITICAL: Patients on phototherapy "
                        f"must be extra vigilant with sun protection on non-treatment days."
                    )

            resolved.append(step)

        return resolved, new_avoids

    # ── Weather Context ───────────────────────────────────

    def _build_weather_context(
        self, kb: ConditionKB, weather: WeatherContext | None
    ) -> tuple[WeatherSummary | None, str | None]:
        """Build weather summary and extract condition-specific climate note."""
        if weather is None:
            return None, None

        summary = WeatherSummary(
            condition=weather.condition,
            temperature_c=weather.temperature_c,
            humidity_pct=weather.humidity_pct,
            uv_index=weather.uv_index,
            routine_impact=self._weather_impact_label(weather),
        )

        # Pick the best matching weather note from KB
        climate_note = None
        notes = kb.weather_notes

        if weather.uv_index >= 6 and "high_uv" in notes:
            climate_note = notes["high_uv"]
        elif weather.humidity_pct > 60 and "humid" in notes:
            climate_note = notes["humid"]
        elif weather.temperature_c < 5 and "cold" in notes:
            climate_note = notes["cold"]
        elif weather.humidity_pct < 30 and "dry_air" in notes:
            climate_note = notes["dry_air"]

        return summary, climate_note

    @staticmethod
    def _weather_impact_label(weather: WeatherContext) -> str:
        if weather.uv_index >= 8:
            return "Very High UV — maximum sun protection required"
        elif weather.uv_index >= 6:
            return "High UV — enhanced sun protection advised"
        elif weather.temperature_c < 5:
            return "Cold conditions — extra barrier protection needed"
        elif weather.humidity_pct > 70:
            return "High humidity — lighter products recommended"
        elif weather.humidity_pct < 30:
            return "Very dry air — extra hydration needed"
        return "Moderate conditions — follow standard routine"

    # ── Prescription Interaction Note ─────────────────────

    @staticmethod
    def _prescription_interaction_note(req: ConditionRequest) -> str | None:
        notes: list[str] = []

        if "prescription_topical" in req.current_treatments:
            notes.append(
                "You indicated you are using a prescription topical treatment. "
                "Continue your prescribed regimen as directed by your dermatologist. "
                "OTC recommendations in this protocol should complement, not replace, "
                "your prescription treatment."
            )

        if "prescription_oral" in req.current_treatments:
            notes.append(
                "You indicated you are taking an oral prescription medication. "
                "Some oral medications (antibiotics, retinoids) increase photosensitivity. "
                "Ensure you apply SPF 50+ daily."
            )

        if "biologics" in req.current_treatments:
            notes.append(
                "You are on biologic therapy. Your immune system may be modulated — "
                "monitor for any signs of infection and report them promptly to your doctor."
            )

        if "phototherapy" in req.current_treatments:
            notes.append(
                "You are undergoing phototherapy. Follow your phototherapy provider's "
                "instructions regarding sun exposure and skincare on treatment days."
            )

        return " ".join(notes) if notes else None

    # ── LLM Enrichment ────────────────────────────────────

    async def _enrich_with_llm(
        self,
        response: ConditionResponse,
        kb: ConditionKB,
        req: ConditionRequest,
    ) -> ConditionResponse:
        """
        Attempt LLM enrichment of why_explanation fields.
        2-second timeout — on failure, fallback_why is already in place.
        """
        if not os.environ.get("GEMINI_API_KEY"):
            logger.info("No Gemini API key — skipping LLM enrichment")
            return response

        try:
            enriched_plan = await asyncio.wait_for(
                self._llm_enrich_care_plan(response, kb, req),
                timeout=LLM_TIMEOUT_SECONDS,
            )
            response.care_plan = enriched_plan
            response.llm_enriched = True
            logger.info("LLM enrichment succeeded for %s", req.condition)
        except asyncio.TimeoutError:
            logger.warning("LLM enrichment timed out (>%.1fs) — using fallback_why", LLM_TIMEOUT_SECONDS)
        except Exception as e:
            logger.warning("LLM enrichment failed: %s — using fallback_why", e)

        return response

    async def _llm_enrich_care_plan(
        self,
        response: ConditionResponse,
        kb: ConditionKB,
        req: ConditionRequest,
    ) -> list[CarePlanStep]:
        """
        Ask Gemini to write personalized why_explanation for each step.
        Single batched prompt for efficiency.
        """
        try:
            steps_payload = [
                {"step": s.step, "recommendation": s.recommendation}
                for s in response.care_plan
            ]
            prompt = (
                f"You are a warm dermatology educator writing care guidance for someone "
                f"with {kb.display_name}. For each care plan step, write a "
                f"why_explanation: 1-2 sentences in second person explaining why this step "
                f"helps their specific condition. Use 'supports', 'manages', 'helps' — "
                f"never 'treats' or 'cures'. "
                f"Return ONLY a JSON array: "
                f'[{{"step": int, "why_explanation": str}}, ...]\n\n'
                f"Steps: {json.dumps(steps_payload)}"
            )

            def _call():
                model    = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                return response.text

            raw   = await asyncio.wait_for(asyncio.to_thread(_call), timeout=2.0)
            clean = raw.strip().replace("```json", "").replace("```", "").strip()
            data  = json.loads(clean)

            enrichment_map = {item["step"]: item["why_explanation"] for item in data}
            for step in response.care_plan:
                if step.step in enrichment_map:
                    step.why_explanation = enrichment_map[step.step]

            response.llm_enriched = True
            return response.care_plan

        except Exception as e:
            logger.warning(f"[ConditionEnrichment] Gemini failed: {e} — using fallback_why")
            response.llm_enriched = False
            return response.care_plan

    # ── Condition Summary Helpers ─────────────────────────

    def get_condition_summary(self, key: str) -> dict:
        """For GET /api/medical/conditions — returns summary dict."""
        kb = self._kb.get(key)
        severity_tier = 3 if key in CATEGORY_D_CONDITIONS else (
            2 if kb.referral_urgency in ("immediate", "soon") else 1
        )
        return {
            "key": kb.key,
            "display_name": kb.display_name,
            "category": kb.category,
            "is_contagious": kb.is_contagious,
            "is_curable": kb.is_curable,
            "severity_tier": severity_tier,
        }

    def get_condition_preview(self, key: str) -> dict:
        """For GET /api/medical/conditions/{key} — returns preview dict."""
        kb = self._kb.get(key)
        return {
            "key": kb.key,
            "display_name": kb.display_name,
            "category": kb.category,
            "is_contagious": kb.is_contagious,
            "contagion_guidance": kb.contagion_guidance,
            "what_it_is": kb.what_it_is,
            "known_triggers": [t[0] for t in kb.triggers],
            "red_flags_preview": [rf[0] for rf in kb.red_flags],
        }

    def list_all_conditions(self) -> list[dict]:
        """For GET /api/medical/conditions — returns list of summaries."""
        return [self.get_condition_summary(k) for k in self._kb.keys()]
