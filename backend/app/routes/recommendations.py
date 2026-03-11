"""
recommendations.py — Skincare Routine & Medicine Recommendation API
v2 — Medical Dermatology Conditions & Environmental Exposure Extension
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from typing import Any, Literal, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Depends
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, model_validator

from app.services.knowledge_base import (
    check_ingredient_safety,
    generate_skincare_routine,
    get_condition_info,
)
from app.services.weather import WeatherContext, get_weather_context

load_dotenv()

logger = logging.getLogger("dermai.recommendations")

router = APIRouter(prefix="/api", tags=["recommendations"])

# ─── OpenAI client (shared) ──────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
GPT_MINI_MODEL = "gpt-4o-mini"
LLM_TIMEOUT_SECONDS = 2.0

import asyncio
from app.utils.rate_limit import create_rate_limiter

rate_limit_dependency = create_rate_limiter(limit=20, window_seconds=60)


# =====================================================================
# Pydantic Schemas
# =====================================================================


class Location(BaseModel):
    lat: float
    lon: float


class RoutineRequest(BaseModel):
    """Extended request payload for skincare routine generation."""

    # --- Existing fields ---
    skin_type: Literal["oily", "dry", "combination", "sensitive", "normal"]
    primary_concern: Literal[
        "acne",
        "hyperpigmentation",
        "blackheads",
        "aging",
        "dullness",
        "large_pores",
        "sun_damage",
        "maintenance",
    ]
    age_group: Literal["teen", "twenties", "thirties", "forties_plus"]
    skin_goals: list[
        Literal["glass_skin", "glowing", "brightening", "minimalist", "dermatologist"]
    ]
    special_situation: Literal[
        "pre_makeup", "post_sun", "travel", "post_workout", "post_acne", "none"
    ] = "none"
    location: Location | None = None
    include_weekly: bool = True

    # --- New fields (v2 extension) ---
    medical_condition: Literal[
        "eczema",
        "rosacea",
        "psoriasis",
        "lichen_planus",
        "atopic_dermatitis",
        "melanoma_risk",
        "none",
    ] = "none"
    pollution_exposure: bool = False

    @model_validator(mode="after")
    def validate_medical_interactions(self) -> "RoutineRequest":
        # Eczema / atopic_dermatitis + brightening → remove brightening, add dermatologist
        if self.medical_condition in ("eczema", "atopic_dermatitis"):
            if "brightening" in self.skin_goals:
                self.skin_goals = [g for g in self.skin_goals if g != "brightening"]
                if "dermatologist" not in self.skin_goals:
                    self.skin_goals.append("dermatologist")
                logger.warning(
                    "RoutineRequest validator: removed 'brightening' goal — "
                    f"contraindicated for {self.medical_condition}. Added 'dermatologist'."
                )

        # Melanoma risk + post_sun → reset situation, override primary concern
        if (
            self.medical_condition == "melanoma_risk"
            and self.special_situation == "post_sun"
        ):
            self.special_situation = "none"
            self.primary_concern = "sun_damage"
            logger.warning(
                "RoutineRequest validator: melanoma_risk + post_sun detected — "
                "overriding primary_concern to 'sun_damage', clearing special_situation."
            )

        return self


class WeatherSummary(BaseModel):
    temperature_c: float
    humidity_pct: float
    uv_index: float
    condition: str
    is_humid: bool
    is_cold: bool


class RoutineStep(BaseModel):
    """A single step in the AM/PM/weekly routine."""

    step: int
    time_minutes: int
    category: str
    ingredient_recommendation: str
    why_explanation: str
    is_essential: bool
    climate_adjusted: bool
    condition_safe: bool = True


class RoutineResponse(BaseModel):
    """Extended response payload for skincare routine generation."""

    profile_summary: str
    weather_context: WeatherSummary | None
    am_routine: list[RoutineStep]
    pm_routine: list[RoutineStep]
    weekly_treatments: list[RoutineStep] | None
    total_time_am: int
    total_time_pm: int
    generated_at: datetime
    medical_disclaimer: str | None = None
    condition_overrides_applied: list[str] = Field(default_factory=list)


# =====================================================================
# Ingredient Candidate Model
# =====================================================================


class IngredientCandidate(BaseModel):
    """Internal model representing a scored ingredient candidate."""

    name: str
    category: str  # e.g. "cleanser", "serum", "moisturizer", "spf", "exfoliant", ...
    ingredient_detail: str
    base_priority: int = 0
    tags: list[str] = Field(default_factory=list)
    time_minutes: int = 1
    is_essential: bool = False
    routine_slot: Literal["am", "pm", "both", "weekly"] = "both"
    score: int = 0


# =====================================================================
# Master Ingredient Pool
# =====================================================================

_INGREDIENT_POOL: list[dict[str, Any]] = [
    # ── Cleansers ──
    {
        "name": "Gentle Cream Cleanser",
        "category": "cleanser",
        "ingredient_detail": "Syndet bar or cream cleanser, pH 5.5–6.0, fragrance-free",
        "base_priority": 10,
        "tags": ["gentle", "fragrance-free", "barrier-safe"],
        "time_minutes": 2,
        "is_essential": True,
        "routine_slot": "both",
    },
    {
        "name": "Foaming Gel Cleanser",
        "category": "cleanser",
        "ingredient_detail": "Salicylic acid 0.5% gel cleanser, sulfate-free",
        "base_priority": 8,
        "tags": ["bha", "salicylic-acid", "foaming"],
        "time_minutes": 2,
        "is_essential": True,
        "routine_slot": "both",
    },
    {
        "name": "Oil Cleanser",
        "category": "oil-cleanser",
        "ingredient_detail": "Cleansing oil or micellar water to remove particulate matter and pollutants",
        "base_priority": 6,
        "tags": ["oil-cleanser", "double-cleanse"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "pm",
    },
    {
        "name": "Micellar Water Cleanser",
        "category": "micellar",
        "ingredient_detail": "Micellar water on cotton pad (no rubbing)",
        "base_priority": 5,
        "tags": ["micellar", "gentle", "fragrance-free"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    # ── Toners ──
    {
        "name": "Hydrating Toner",
        "category": "toner",
        "ingredient_detail": "Hyaluronic acid + beta-glucan hydrating toner, alcohol-free",
        "base_priority": 5,
        "tags": ["hydrating", "alcohol-free", "hyaluronic-acid", "beta-glucan"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    {
        "name": "Alcohol-Based Toner",
        "category": "toner",
        "ingredient_detail": "Witch hazel toner with alcohol denat.",
        "base_priority": 3,
        "tags": ["alcohol", "astringent", "fragrance"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    # ── Serums / Treatments ──
    {
        "name": "Vitamin C Serum",
        "category": "serum",
        "ingredient_detail": "15-20% L-ascorbic acid + vitamin E + ferulic acid",
        "base_priority": 8,
        "tags": ["antioxidant", "vitamin-c", "l-ascorbic-acid", "ferulic-acid", "brightening"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "am",
    },
    {
        "name": "Niacinamide Serum",
        "category": "serum",
        "ingredient_detail": "Niacinamide 5% + zinc PCA serum",
        "base_priority": 7,
        "tags": ["antioxidant", "niacinamide", "anti-inflammatory", "brightening"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    {
        "name": "Azelaic Acid Serum",
        "category": "serum",
        "ingredient_detail": "Azelaic acid 10–15% gel or cream",
        "base_priority": 7,
        "tags": ["azelaic-acid", "anti-inflammatory", "anti-redness", "gentle-acid"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    {
        "name": "Retinol Serum",
        "category": "serum",
        "ingredient_detail": "Retinol 0.3–0.5% in squalane base",
        "base_priority": 9,
        "tags": ["retinoid", "retinol", "anti-aging", "photosensitizing"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    {
        "name": "Low-Dose Retinol",
        "category": "serum",
        "ingredient_detail": "Retinol 0.025–0.05% in ceramide base (low concentration for sensitive conditions)",
        "base_priority": 5,
        "tags": ["retinoid", "retinol", "low-dose", "anti-aging"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    {
        "name": "Centella Asiatica Serum",
        "category": "serum",
        "ingredient_detail": "Centella asiatica extract + madecassoside calming serum",
        "base_priority": 6,
        "tags": ["centella", "madecassoside", "calming", "anti-inflammatory"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    {
        "name": "Green Tea Extract Serum",
        "category": "serum",
        "ingredient_detail": "Green tea EGCG antioxidant serum",
        "base_priority": 5,
        "tags": ["antioxidant", "green-tea", "egcg", "calming"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "am",
    },
    {
        "name": "Hyaluronic Acid Serum",
        "category": "serum",
        "ingredient_detail": "Multi-weight hyaluronic acid serum (low + high molecular weight)",
        "base_priority": 7,
        "tags": ["hydrating", "hyaluronic-acid", "barrier-safe"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    {
        "name": "Resveratrol Serum",
        "category": "serum",
        "ingredient_detail": "Resveratrol 1% + ferulic acid antioxidant serum",
        "base_priority": 4,
        "tags": ["antioxidant", "resveratrol", "ferulic-acid"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    {
        "name": "Panthenol Serum",
        "category": "serum",
        "ingredient_detail": "Panthenol (provitamin B5) 5% + squalane repair serum",
        "base_priority": 6,
        "tags": ["panthenol", "barrier-repair", "soothing"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    {
        "name": "Thermal Spring Water Mist",
        "category": "mist",
        "ingredient_detail": "Thermal spring water calming facial mist",
        "base_priority": 3,
        "tags": ["calming", "thermal-water", "mist"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "am",
    },
    {
        "name": "Antioxidant Mist",
        "category": "mist",
        "ingredient_detail": "Green tea or centella antioxidant mist spray",
        "base_priority": 3,
        "tags": ["antioxidant", "mist", "green-tea", "centella"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "am",
    },
    {
        "name": "Aloe Vera Gel",
        "category": "treatment",
        "ingredient_detail": "Pure aloe vera gel, fragrance-free",
        "base_priority": 4,
        "tags": ["aloe-vera", "soothing", "fragrance-free"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    # ── Moisturizers ──
    {
        "name": "Lightweight Gel Moisturizer",
        "category": "moisturizer",
        "ingredient_detail": "Oil-free gel moisturizer with hyaluronic acid",
        "base_priority": 8,
        "tags": ["lightweight", "oil-free", "hyaluronic-acid"],
        "time_minutes": 1,
        "is_essential": True,
        "routine_slot": "am",
    },
    {
        "name": "Ceramide Moisturizer",
        "category": "moisturizer",
        "ingredient_detail": "Ceramide NP/AP/EOP complex + cholesterol moisturizer, fragrance-free",
        "base_priority": 9,
        "tags": ["ceramide", "barrier-repair", "fragrance-free"],
        "time_minutes": 1,
        "is_essential": True,
        "routine_slot": "both",
    },
    {
        "name": "Colloidal Oatmeal Moisturizer",
        "category": "moisturizer",
        "ingredient_detail": "Colloidal oatmeal soothing cream, fragrance-free",
        "base_priority": 7,
        "tags": ["colloidal-oatmeal", "soothing", "barrier-safe", "fragrance-free"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "both",
    },
    {
        "name": "Squalane Oil",
        "category": "moisturizer",
        "ingredient_detail": "100% plant-derived squalane facial oil",
        "base_priority": 5,
        "tags": ["squalane", "emollient", "barrier-repair"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    {
        "name": "Shea Butter Balm",
        "category": "moisturizer",
        "ingredient_detail": "Shea butter + glycerin 5% rich balm, PM use",
        "base_priority": 5,
        "tags": ["shea-butter", "glycerin", "heavy-occlusive", "pm-only"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    {
        "name": "Thick Emollient Moisturizer",
        "category": "moisturizer",
        "ingredient_detail": "Urea 5–10% cream or ceramide-rich balm",
        "base_priority": 7,
        "tags": ["urea", "ceramide", "emollient", "scale-reduction"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    {
        "name": "Petrolatum Occlusive",
        "category": "occlusive",
        "ingredient_detail": "Vaseline/petrolatum occlusive layer (final PM step)",
        "base_priority": 4,
        "tags": ["petrolatum", "occlusive", "heavy-occlusive", "pm-only"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "pm",
    },
    # ── SPF ──
    {
        "name": "Mineral Sunscreen SPF 50+",
        "category": "spf",
        "ingredient_detail": "Broad-spectrum SPF 50+, PA++++, mineral (zinc oxide/titanium dioxide) preferred",
        "base_priority": 10,
        "tags": ["spf", "mineral", "broad-spectrum"],
        "time_minutes": 2,
        "is_essential": True,
        "routine_slot": "am",
    },
    {
        "name": "Chemical Sunscreen SPF 30",
        "category": "spf",
        "ingredient_detail": "Broad-spectrum SPF 30, lightweight chemical formula",
        "base_priority": 8,
        "tags": ["spf", "chemical", "lightweight"],
        "time_minutes": 2,
        "is_essential": True,
        "routine_slot": "am",
    },
    # ── Exfoliants ──
    {
        "name": "Glycolic Acid Exfoliant",
        "category": "exfoliant",
        "ingredient_detail": "Glycolic acid 7% toning solution",
        "base_priority": 6,
        "tags": ["aha", "glycolic-acid", "exfoliant", "photosensitizing"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "weekly",
    },
    {
        "name": "Lactic Acid Exfoliant",
        "category": "exfoliant",
        "ingredient_detail": "Lactic acid 5% gentle exfoliant",
        "base_priority": 5,
        "tags": ["aha", "lactic-acid", "exfoliant"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "weekly",
    },
    {
        "name": "Salicylic Acid Treatment",
        "category": "exfoliant",
        "ingredient_detail": "Salicylic acid 2% BHA liquid exfoliant",
        "base_priority": 7,
        "tags": ["bha", "salicylic-acid", "exfoliant"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "weekly",
    },
    {
        "name": "Low-Dose Salicylic Acid",
        "category": "exfoliant",
        "ingredient_detail": "Salicylic acid ≤2% for gentle scale reduction",
        "base_priority": 5,
        "tags": ["bha", "salicylic-acid", "low-dose", "scale-reduction"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "weekly",
    },
    {
        "name": "Gentle Enzyme Exfoliant",
        "category": "exfoliant",
        "ingredient_detail": "Papaya/pineapple enzyme exfoliant, no AHA/BHA",
        "base_priority": 5,
        "tags": ["enzyme", "gentle", "exfoliant"],
        "time_minutes": 3,
        "is_essential": False,
        "routine_slot": "weekly",
    },
    {
        "name": "Physical Scrub",
        "category": "exfoliant",
        "ingredient_detail": "Microcrystalline physical exfoliant scrub",
        "base_priority": 3,
        "tags": ["physical-scrub", "exfoliant"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "weekly",
    },
    {
        "name": "Coal Tar Extract Treatment",
        "category": "treatment",
        "ingredient_detail": "Coal tar extract 1–2% treatment (PM only)",
        "base_priority": 4,
        "tags": ["coal-tar", "psoriasis-treatment", "pm-only"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "pm",
    },
    # ── Self-tanning ──
    {
        "name": "Self-Tanning Drops",
        "category": "treatment",
        "ingredient_detail": "DHA-based self-tanning facial drops",
        "base_priority": 2,
        "tags": ["dha", "self-tanning"],
        "time_minutes": 2,
        "is_essential": False,
        "routine_slot": "pm",
    },
    # ── Fragrance-containing ──
    {
        "name": "Fragrance Face Mist",
        "category": "mist",
        "ingredient_detail": "Rose water + essential oil facial mist",
        "base_priority": 2,
        "tags": ["fragrance", "essential-oils", "mist"],
        "time_minutes": 1,
        "is_essential": False,
        "routine_slot": "am",
    },
]


# =====================================================================
# Score Modifier Tables
# =====================================================================

_AGE_MODIFIERS: dict[str, dict[str, int]] = {
    "teen": {"cleanser": 2, "spf": 1, "exfoliant": -1, "serum": -1},
    "twenties": {"serum": 1, "spf": 1, "exfoliant": 1},
    "thirties": {"serum": 2, "moisturizer": 1, "spf": 2, "exfoliant": 1},
    "forties_plus": {"serum": 3, "moisturizer": 2, "spf": 3, "occlusive": 1},
}

_GOAL_MODIFIERS: dict[str, dict[str, int]] = {
    "glass_skin": {"hyaluronic-acid": 3, "niacinamide": 2, "ceramide": 2},
    "glowing": {"vitamin-c": 3, "antioxidant": 2, "aha": 1},
    "brightening": {"vitamin-c": 4, "niacinamide": 2, "aha": 2, "azelaic-acid": 2},
    "minimalist": {},  # no boosts; step cap applies
    "dermatologist": {"retinoid": 2, "ceramide": 2, "azelaic-acid": 2, "spf": 2},
}

_SITUATION_MODIFIERS: dict[str, dict[str, int]] = {
    "pre_makeup": {"lightweight": 2, "spf": 1},
    "post_sun": {"aloe-vera": 3, "hydrating": 2, "soothing": 2},
    "travel": {"mist": 2, "lightweight": 1},
    "post_workout": {"cleanser": 2, "gentle": 1},
    "post_acne": {"niacinamide": 3, "azelaic-acid": 2, "barrier-repair": 2},
    "none": {},
}

_WEATHER_MODIFIERS: dict[str, int] = {
    "humid_oil_free": 2,
    "cold_ceramide": 3,
    "high_uv_spf": 4,
}

_POLLUTION_MODIFIERS: dict[str, int] = {
    "antioxidant": 3,
    "double-cleanse": 4,
    "oil-cleanser": 3,
    "micellar": 3,
    "heavy-occlusive-solo-penalty": -2,
    "antioxidant-mist": 2,
}

_STEP_CAPS: dict[str, tuple[int, int, int]] = {
    # (max_am, max_pm, max_weekly)
    "minimalist": (3, 3, 1),
    "default": (5, 6, 3),
    "rosacea": (4, 4, 2),
    "eczema": (3, 3, 0),
    "atopic_dermatitis": (3, 3, 0),
    "lichen_planus": (3, 3, 0),
}

# ── Tags that trigger removal per condition ──
_ROSACEA_REMOVE_TAGS = {
    "retinoid", "retinol", "aha", "glycolic-acid", "lactic-acid",
    "physical-scrub", "alcohol", "astringent", "fragrance", "essential-oils",
}
_ROSACEA_REMOVE_CATEGORIES = {"exfoliant"}  # Only high-conc BHA removed via tags

_ECZEMA_REMOVE_TAGS = {
    "aha", "glycolic-acid", "lactic-acid", "bha", "salicylic-acid",
    "retinoid", "retinol", "physical-scrub", "fragrance", "essential-oils",
    "alcohol", "astringent",
}

_PSORIASIS_REMOVE_TAGS = {
    "physical-scrub",
}

_LICHEN_PLANUS_REMOVE_TAGS = {
    "aha", "glycolic-acid", "lactic-acid", "bha", "salicylic-acid",
    "retinoid", "retinol", "physical-scrub", "exfoliant",
}

_MELANOMA_REMOVE_TAGS = {
    "dha", "self-tanning",
}

# ── Tags that trigger boosts per condition ──
_ROSACEA_BOOST_TAGS = {
    "azelaic-acid", "niacinamide", "centella", "madecassoside",
    "green-tea", "thermal-water", "calming",
}
_ECZEMA_BOOST_TAGS = {
    "ceramide", "colloidal-oatmeal", "panthenol", "squalane",
    "glycerin", "shea-butter", "petrolatum", "barrier-repair",
    "barrier-safe", "fragrance-free",
}
_PSORIASIS_BOOST_TAGS = {
    "low-dose", "scale-reduction", "coal-tar", "urea", "ceramide",
    "colloidal-oatmeal", "aloe-vera", "emollient",
}
_LICHEN_PLANUS_BOOST_TAGS = {
    "ceramide", "squalane", "panthenol", "hyaluronic-acid",
    "beta-glucan", "barrier-repair", "barrier-safe",
}
_MELANOMA_BOOST_TAGS = {
    "spf", "antioxidant", "vitamin-c", "ferulic-acid", "niacinamide",
}


# =====================================================================
# Medical Disclaimers
# =====================================================================

_MEDICAL_DISCLAIMERS: dict[str, str] = {
    "eczema": (
        "This routine is formulated to support eczema-prone skin by prioritizing "
        "barrier repair and avoiding known irritants. It is not a substitute for "
        "prescribed treatments. Consult your dermatologist if symptoms worsen or "
        "during active flares."
    ),
    "atopic_dermatitis": (
        "This routine is formulated to support eczema-prone skin by prioritizing "
        "barrier repair and avoiding known irritants. It is not a substitute for "
        "prescribed treatments. Consult your dermatologist if symptoms worsen or "
        "during active flares."
    ),
    "rosacea": (
        "This routine avoids known rosacea triggers and emphasizes calming, "
        "anti-inflammatory ingredients. Individual triggers vary — patch test new "
        "products and consult your dermatologist if flushing or papules persist."
    ),
    "psoriasis": (
        "This routine supports psoriasis-prone skin with gentle actives and "
        "emollients. Prescription treatments (topical corticosteroids, biologics) "
        "are outside the scope of a skincare routine — please maintain your "
        "prescribed regimen alongside this routine."
    ),
    "lichen_planus": (
        "Lichen planus is a chronic inflammatory condition. This routine provides "
        "supportive skincare only. Active flares require evaluation and prescription "
        "treatment by a dermatologist."
    ),
    "melanoma_risk": (
        "This routine prioritizes maximum photoprotection. It is not a substitute "
        "for regular dermatologist-supervised skin checks. Individuals with elevated "
        "melanoma risk should have a full-body skin examination at least annually."
    ),
}


class RoutineCache:
    def __init__(self, ttl_minutes: int = 30):
        self._store: dict[str, tuple[RoutineResponse, datetime]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._lock = asyncio.Lock()

    def _make_key(self, request: RoutineRequest, weather: WeatherContext | None) -> str:
        parts = [
            request.skin_type,
            request.primary_concern,
            request.age_group,
            ",".join(sorted(request.skin_goals)),
            request.special_situation,
            request.medical_condition,
            str(request.pollution_exposure),
            str(request.include_weekly),
            str(round(weather.temperature_c / 5) * 5) if weather else "no_weather",
            str(round(weather.uv_index)) if weather else "no_uv",
        ]
        return hashlib.sha256("|".join(parts).encode()).hexdigest()

    async def get(self, request: RoutineRequest, weather: WeatherContext | None) -> RoutineResponse | None:
        key = self._make_key(request, weather)
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            response, cached_at = entry
            if datetime.now(timezone.utc).replace(tzinfo=None) - cached_at.replace(tzinfo=None) > self._ttl:
                del self._store[key]
                return None
            return response

    async def set(self, request: RoutineRequest, weather: WeatherContext | None, response: RoutineResponse) -> None:
        key = self._make_key(request, weather)
        async with self._lock:
            self._store[key] = (response, datetime.now(timezone.utc).replace(tzinfo=None))

    async def purge_expired(self) -> int:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        async with self._lock:
            expired = [k for k, (_, ts) in self._store.items() if now - ts.replace(tzinfo=None) > self._ttl]
            for k in expired:
                del self._store[k]
            return len(expired)

# Module-level singleton
_routine_cache = RoutineCache(ttl_minutes=30)

# =====================================================================
# RoutineRuleEngine
# =====================================================================


class RoutineRuleEngine:
    """
    Two-phase rule engine:
      Phase 1 — Medical safety overrides (pre-scoring gate)
      Phase 2 — Weighted scoring matrix
    """

    def __init__(self, request: RoutineRequest, weather: WeatherContext | None = None):
        self._req = request
        self._weather = weather
        self._overrides: list[str] = []
        self._include_weekly = request.include_weekly

    # ─────────────────────────────────────────────────────────────
    # Phase 1: Medical Safety Overrides
    # ─────────────────────────────────────────────────────────────

    def apply_medical_overrides(
        self,
        candidates: list[IngredientCandidate],
        condition: str,
    ) -> tuple[list[IngredientCandidate], list[str]]:
        """
        Pre-scoring gate: filter and boost candidates based on medical condition.
        Returns (filtered_candidates, override_descriptions).
        """
        if condition == "none":
            return candidates, []

        overrides: list[str] = []

        if condition == "rosacea":
            candidates, overrides = self._apply_rosacea(candidates)
        elif condition in ("eczema", "atopic_dermatitis"):
            candidates, overrides = self._apply_eczema(candidates, condition)
        elif condition == "psoriasis":
            candidates, overrides = self._apply_psoriasis(candidates)
        elif condition == "lichen_planus":
            candidates, overrides = self._apply_lichen_planus(candidates)
        elif condition == "melanoma_risk":
            candidates, overrides = self._apply_melanoma_risk(candidates)

        return candidates, overrides

    def _apply_rosacea(
        self, candidates: list[IngredientCandidate]
    ) -> tuple[list[IngredientCandidate], list[str]]:
        overrides: list[str] = []
        filtered: list[IngredientCandidate] = []

        for c in candidates:
            tag_set = set(c.tags)
            if tag_set & _ROSACEA_REMOVE_TAGS:
                if "retinoid" in tag_set or "retinol" in tag_set:
                    overrides.append(
                        "Retinol removed — retinoids are known rosacea triggers"
                    )
                elif tag_set & {"aha", "glycolic-acid", "lactic-acid"}:
                    overrides.append(
                        "AHA replaced with azelaic acid — gentler acid that reduces redness without flushing"
                    )
                elif "physical-scrub" in tag_set:
                    overrides.append(
                        "Physical scrub removed — mechanical exfoliation aggravates rosacea"
                    )
                elif tag_set & {"alcohol", "astringent"}:
                    overrides.append(
                        "Alcohol-based toner removed — alcohol is a common rosacea trigger"
                    )
                elif tag_set & {"fragrance", "essential-oils"}:
                    overrides.append(
                        "Fragrance-containing product removed — fragrances can trigger rosacea flares"
                    )
                continue  # remove candidate

            # BHA: remove salicylic acid >1% (keep only if explicitly low-dose tagged)
            if "salicylic-acid" in tag_set and "low-dose" not in tag_set:
                overrides.append(
                    "Salicylic acid >1% removed — high-concentration BHA irritates rosacea"
                )
                continue

            # Boost calming ingredients
            if tag_set & _ROSACEA_BOOST_TAGS:
                c.score += 4

            filtered.append(c)

        return filtered, list(dict.fromkeys(overrides))  # deduplicate preserving order

    def _apply_eczema(
        self, candidates: list[IngredientCandidate], condition: str
    ) -> tuple[list[IngredientCandidate], list[str]]:
        overrides: list[str] = []
        filtered: list[IngredientCandidate] = []
        condition_label = "eczema" if condition == "eczema" else "atopic dermatitis"

        for c in candidates:
            tag_set = set(c.tags)
            if tag_set & _ECZEMA_REMOVE_TAGS:
                if "retinoid" in tag_set or "retinol" in tag_set:
                    overrides.append(
                        f"Retinol removed — retinoids are too harsh for {condition_label}-prone skin"
                    )
                elif tag_set & {"aha", "glycolic-acid", "lactic-acid"}:
                    overrides.append(
                        f"AHA exfoliant removed — acid exfoliation contraindicated for {condition_label}"
                    )
                elif tag_set & {"bha", "salicylic-acid"}:
                    overrides.append(
                        f"BHA removed — salicylic acid contraindicated for {condition_label}"
                    )
                elif "physical-scrub" in tag_set:
                    overrides.append(
                        f"Physical scrub removed — mechanical exfoliation damages {condition_label} barrier"
                    )
                elif tag_set & {"fragrance", "essential-oils"}:
                    overrides.append(
                        f"Fragrance-containing product removed — fragrances are common {condition_label} triggers"
                    )
                elif tag_set & {"alcohol", "astringent"}:
                    overrides.append(
                        f"Alcohol-based product removed — alcohol disrupts barrier in {condition_label}"
                    )
                continue

            # Boost eczema-safe ingredients
            if tag_set & _ECZEMA_BOOST_TAGS:
                c.score += 5

            filtered.append(c)

        # Disable weekly treatments
        self._include_weekly = False
        overrides.append(
            f"Weekly exfoliation disabled — contraindicated for {condition_label}"
        )

        return filtered, list(dict.fromkeys(overrides))

    def _apply_psoriasis(
        self, candidates: list[IngredientCandidate]
    ) -> tuple[list[IngredientCandidate], list[str]]:
        overrides: list[str] = []
        filtered: list[IngredientCandidate] = []
        req = self._req
        retain_low_retinol = req.age_group in ("thirties", "forties_plus") and req.primary_concern == "aging"

        for c in candidates:
            tag_set = set(c.tags)
            # Remove physical scrubs
            if "physical-scrub" in tag_set:
                overrides.append("Physical scrub removed — too harsh for psoriasis-prone skin")
                continue
            # Remove high-concentration AHAs (keep enzyme exfoliants)
            if tag_set & {"aha", "glycolic-acid", "lactic-acid"} and "enzyme" not in tag_set:
                overrides.append(
                    "AHA exfoliant replaced with enzyme exfoliant — safe for psoriasis-prone skin"
                )
                continue
            # Remove harsh sulfate cleansers (marked with "astringent" or "alcohol")
            if tag_set & {"alcohol", "astringent"}:
                overrides.append("Harsh cleanser/toner removed — sulfates and alcohol irritate psoriasis")
                continue
            # Retinoids: conditionally retain at low dose
            if ("retinoid" in tag_set or "retinol" in tag_set) and "low-dose" not in tag_set:
                if retain_low_retinol:
                    # Replace with low-dose variant — mark as not condition_safe
                    overrides.append(
                        "Retinol replaced with low-dose 0.025–0.05% — use with caution for psoriasis"
                    )
                    continue  # remove full-strength; low-dose variant remains in pool
                else:
                    overrides.append("Retinol removed — retinoids can irritate psoriasis plaques")
                    continue

            # Boost psoriasis-friendly ingredients
            if tag_set & _PSORIASIS_BOOST_TAGS:
                c.score += 4

            filtered.append(c)

        return filtered, list(dict.fromkeys(overrides))

    def _apply_lichen_planus(
        self, candidates: list[IngredientCandidate]
    ) -> tuple[list[IngredientCandidate], list[str]]:
        overrides: list[str] = []
        filtered: list[IngredientCandidate] = []

        for c in candidates:
            tag_set = set(c.tags)
            if tag_set & _LICHEN_PLANUS_REMOVE_TAGS:
                if "retinoid" in tag_set or "retinol" in tag_set:
                    overrides.append("Retinol removed — all retinoids contraindicated for lichen planus")
                elif tag_set & {"aha", "glycolic-acid", "lactic-acid", "bha", "salicylic-acid"}:
                    overrides.append("Chemical exfoliant removed — acids irritate lichen planus lesions")
                elif "physical-scrub" in tag_set:
                    overrides.append("Physical exfoliant removed — abrasion worsens lichen planus")
                continue

            # Remove high-conc vitamin C (>10% L-ascorbic acid only)
            if "l-ascorbic-acid" in tag_set:
                overrides.append(
                    "High-concentration L-ascorbic acid removed — oxidative forms acceptable, "
                    "but >10% L-ascorbic acid is too irritating for lichen planus"
                )
                continue

            if tag_set & _LICHEN_PLANUS_BOOST_TAGS:
                c.score += 4

            filtered.append(c)

        # Disable weekly treatments
        self._include_weekly = False
        overrides.append("Weekly treatments disabled — lichen planus skin must not be exfoliated")

        return filtered, list(dict.fromkeys(overrides))

    def _apply_melanoma_risk(
        self, candidates: list[IngredientCandidate]
    ) -> tuple[list[IngredientCandidate], list[str]]:
        overrides: list[str] = []
        filtered: list[IngredientCandidate] = []

        for c in candidates:
            tag_set = set(c.tags)
            # Remove self-tanning / DHA
            if tag_set & _MELANOMA_REMOVE_TAGS:
                overrides.append("Self-tanning product removed — DHA not recommended for melanoma-risk skin")
                continue

            # Boost SPF significantly
            if "spf" in tag_set:
                c.score += 6
                c.is_essential = True

            # Boost antioxidants
            if tag_set & _MELANOMA_BOOST_TAGS and "spf" not in tag_set:
                c.score += 3

            filtered.append(c)

        # Ensure AM retinol is not standalone without SPF pairing
        # (handled at routine assembly level)

        return filtered, list(dict.fromkeys(overrides))

    # ─────────────────────────────────────────────────────────────
    # Phase 2: Weighted Scoring Matrix
    # ─────────────────────────────────────────────────────────────

    def _build_candidates(self) -> list[IngredientCandidate]:
        """Build the initial candidate pool from the master ingredient list."""
        candidates: list[IngredientCandidate] = []
        for item in _INGREDIENT_POOL:
            candidates.append(
                IngredientCandidate(
                    name=item["name"],
                    category=item["category"],
                    ingredient_detail=item["ingredient_detail"],
                    base_priority=item["base_priority"],
                    tags=list(item["tags"]),
                    time_minutes=item["time_minutes"],
                    is_essential=item["is_essential"],
                    routine_slot=item["routine_slot"],
                    score=item["base_priority"],
                )
            )
        return candidates

    def _apply_scoring(self, candidates: list[IngredientCandidate]) -> list[IngredientCandidate]:
        """Apply age, goal, weather, situation, and pollution modifiers."""
        req = self._req

        # Age modifiers
        age_mods = _AGE_MODIFIERS.get(req.age_group, {})
        for c in candidates:
            c.score += age_mods.get(c.category, 0)

        # Goal modifiers
        for goal in req.skin_goals:
            goal_mods = _GOAL_MODIFIERS.get(goal, {})
            for c in candidates:
                for tag_key, bonus in goal_mods.items():
                    if tag_key in c.tags or tag_key == c.category:
                        c.score += bonus

        # Situation modifiers
        sit_mods = _SITUATION_MODIFIERS.get(req.special_situation, {})
        for c in candidates:
            for tag_key, bonus in sit_mods.items():
                if tag_key in c.tags or tag_key == c.category:
                    c.score += bonus

        # Weather modifiers
        if self._weather:
            for c in candidates:
                tag_set = set(c.tags)
                if self._weather.is_humid and "oil-free" in tag_set:
                    c.score += _WEATHER_MODIFIERS["humid_oil_free"]
                if self._weather.is_cold and "ceramide" in tag_set:
                    c.score += _WEATHER_MODIFIERS["cold_ceramide"]
                if self._weather.uv_index >= 6 and "spf" in tag_set:
                    c.score += _WEATHER_MODIFIERS["high_uv_spf"]

        # Pollution modifiers
        if req.pollution_exposure:
            for c in candidates:
                tag_set = set(c.tags)
                if "antioxidant" in tag_set:
                    c.score += _POLLUTION_MODIFIERS["antioxidant"]
                if "double-cleanse" in tag_set or "oil-cleanser" in tag_set:
                    c.score += _POLLUTION_MODIFIERS["double-cleanse"]
                if "micellar" in tag_set:
                    c.score += _POLLUTION_MODIFIERS["micellar"]
                if "mist" in tag_set and "antioxidant" in tag_set:
                    c.score += _POLLUTION_MODIFIERS["antioxidant-mist"]
                # Penalty: heavy occlusive without antioxidant pairing
                if "heavy-occlusive" in tag_set and "antioxidant" not in tag_set:
                    c.score += _POLLUTION_MODIFIERS["heavy-occlusive-solo-penalty"]

        return candidates

    # ─────────────────────────────────────────────────────────────
    # Routine Assembly
    # ─────────────────────────────────────────────────────────────

    def _select_top(
        self,
        candidates: list[IngredientCandidate],
        slot: str,
        max_steps: int,
    ) -> list[IngredientCandidate]:
        """Select top candidates for a routine slot, respecting step caps."""
        eligible = [
            c
            for c in candidates
            if c.routine_slot in (slot, "both")
        ]
        # Sort by score descending, then by base_priority descending
        eligible.sort(key=lambda c: (c.score, c.base_priority), reverse=True)

        selected: list[IngredientCandidate] = []
        seen_categories: set[str] = set()
        for c in eligible:
            if len(selected) >= max_steps:
                break
            # Allow one per category (except serums which can have multiple)
            cat_key = c.category if c.category != "serum" else f"serum-{c.name}"
            if cat_key in seen_categories:
                continue
            seen_categories.add(cat_key)
            selected.append(c)

        return selected

    def generate(self) -> tuple[RoutineResponse, list[str]]:
        """Execute the full engine pipeline and return the response + overrides."""
        req = self._req
        condition = req.medical_condition

        # Step 1: Build candidate pool
        candidates = self._build_candidates()

        # Step 2: Medical overrides (pre-scoring gate)
        candidates, overrides = self.apply_medical_overrides(candidates, condition)
        self._overrides = overrides

        # Step 3: Scoring
        candidates = self._apply_scoring(candidates)

        # Step 4: Determine step caps
        if condition in _STEP_CAPS:
            max_am, max_pm, max_weekly = _STEP_CAPS[condition]
        elif "minimalist" in req.skin_goals:
            max_am, max_pm, max_weekly = _STEP_CAPS["minimalist"]
            # Override minimalist cap for pollution antioxidant
            if req.pollution_exposure:
                max_am += 1
        else:
            max_am, max_pm, max_weekly = _STEP_CAPS["default"]

        # Step 5: Select top candidates per slot
        am_candidates = self._select_top(candidates, "am", max_am)
        pm_candidates = self._select_top(candidates, "pm", max_pm)
        weekly_candidates = (
            self._select_top(candidates, "weekly", max_weekly)
            if self._include_weekly
            else []
        )

        # Step 6: Medical mandatory injections
        am_candidates, pm_candidates, weekly_candidates = self._apply_mandatory_injections(
            am_candidates, pm_candidates, weekly_candidates, condition
        )

        # Step 7: Pollution mandatory injections
        if req.pollution_exposure:
            am_candidates, pm_candidates = self._apply_pollution_injections(
                am_candidates, pm_candidates, condition
            )

        # Step 8: Melanoma SPF reordering — ensure SPF follows any photosensitizer in AM
        if condition == "melanoma_risk":
            am_candidates = self._ensure_spf_last_am(am_candidates)

        # Step 9: Build RoutineStep objects
        climate_adjusted = self._weather is not None
        am_steps = self._to_steps(am_candidates, climate_adjusted, condition)
        pm_steps = self._to_steps(pm_candidates, climate_adjusted, condition)
        weekly_steps = self._to_steps(weekly_candidates, climate_adjusted, condition) if weekly_candidates else None

        # Melanoma AM Step Reordering
        if condition == "melanoma_risk":
            am_steps = self._enforce_melanoma_spf_ordering(am_steps)

        # Step 10: Profile summary
        profile = self._build_profile_summary()

        # Step 11: Weather summary
        weather_summary = None
        if self._weather:
            weather_summary = WeatherSummary(
                temperature_c=self._weather.temperature_c,
                humidity_pct=self._weather.humidity_pct,
                uv_index=self._weather.uv_index,
                condition=self._weather.condition,
                is_humid=self._weather.is_humid,
                is_cold=self._weather.temperature_c < 15,
            )

        # Step 12: Medical disclaimer
        disclaimer = _MEDICAL_DISCLAIMERS.get(condition)

        # Step 13: Assemble response
        response = RoutineResponse(
            profile_summary=profile,
            weather_context=weather_summary,
            am_routine=am_steps,
            pm_routine=pm_steps,
            weekly_treatments=weekly_steps,
            total_time_am=sum(s.time_minutes for s in am_steps),
            total_time_pm=sum(s.time_minutes for s in pm_steps),
            generated_at=datetime.now(timezone.utc),
            medical_disclaimer=disclaimer,
            condition_overrides_applied=overrides,
        )

        return response, overrides

    def _apply_mandatory_injections(
        self,
        am: list[IngredientCandidate],
        pm: list[IngredientCandidate],
        weekly: list[IngredientCandidate],
        condition: str,
    ) -> tuple[list[IngredientCandidate], list[IngredientCandidate], list[IngredientCandidate]]:
        """Inject mandatory steps for specific medical conditions."""

        if condition in ("eczema", "atopic_dermatitis"):
            # Mandatory AM step 1: gentle cream cleanser
            gentle_cleanser = IngredientCandidate(
                name="Gentle Cream Cleanser",
                category="cleanser",
                ingredient_detail="Syndet bar or cream cleanser, pH 5.5–6.0, fragrance-free",
                base_priority=15,
                tags=["gentle", "fragrance-free", "barrier-safe"],
                time_minutes=2,
                is_essential=True,
                routine_slot="am",
                score=20,
            )
            # Remove any existing cleansers from AM, replace with gentle
            am = [c for c in am if c.category != "cleanser"]
            am.insert(0, gentle_cleanser)

            # Ensure petrolatum occlusive as final PM step
            has_occlusive = any(c.category == "occlusive" for c in pm)
            if not has_occlusive:
                pm.append(
                    IngredientCandidate(
                        name="Petrolatum Occlusive",
                        category="occlusive",
                        ingredient_detail="Vaseline/petrolatum occlusive layer (final PM step)",
                        base_priority=10,
                        tags=["petrolatum", "occlusive", "heavy-occlusive", "pm-only"],
                        time_minutes=1,
                        is_essential=True,
                        routine_slot="pm",
                        score=15,
                    )
                )

        elif condition == "psoriasis":
            # Mandatory PM final step: thick emollient
            has_emollient = any("urea" in c.tags or "emollient" in c.tags for c in pm)
            if not has_emollient:
                pm.append(
                    IngredientCandidate(
                        name="Thick Emollient Moisturizer",
                        category="moisturizer",
                        ingredient_detail="Urea 5–10% cream or ceramide-rich balm",
                        base_priority=12,
                        tags=["urea", "ceramide", "emollient", "scale-reduction"],
                        time_minutes=1,
                        is_essential=True,
                        routine_slot="pm",
                        score=18,
                    )
                )

            # Replace standard exfoliants with enzyme exfoliant in weekly
            weekly = [w for w in weekly if "enzyme" in w.tags or w.category != "exfoliant"]
            has_enzyme = any("enzyme" in w.tags for w in weekly)
            if not has_enzyme and self._include_weekly:
                weekly.append(
                    IngredientCandidate(
                        name="Gentle Enzyme Exfoliant",
                        category="exfoliant",
                        ingredient_detail="Papaya/pineapple enzyme exfoliant, no AHA/BHA",
                        base_priority=8,
                        tags=["enzyme", "gentle", "exfoliant"],
                        time_minutes=3,
                        is_essential=False,
                        routine_slot="weekly",
                        score=12,
                    )
                )

            # If retaining low-dose retinol for aging + thirties/forties
            if (
                self._req.age_group in ("thirties", "forties_plus")
                and self._req.primary_concern == "aging"
            ):
                has_low_retinol = any("low-dose" in c.tags and "retinol" in c.tags for c in pm)
                if not has_low_retinol:
                    pm.append(
                        IngredientCandidate(
                            name="Low-Dose Retinol",
                            category="serum",
                            ingredient_detail="Retinol 0.025–0.05% in ceramide base (low concentration for sensitive conditions)",
                            base_priority=5,
                            tags=["retinoid", "retinol", "low-dose", "anti-aging"],
                            time_minutes=1,
                            is_essential=False,
                            routine_slot="pm",
                            score=8,
                        )
                    )

        elif condition == "melanoma_risk":
            # Ensure SPF is present and boosted
            has_spf = any("spf" in c.tags for c in am)
            if not has_spf:
                am.append(
                    IngredientCandidate(
                        name="Mineral Sunscreen SPF 50+",
                        category="spf",
                        ingredient_detail="Broad-spectrum SPF 50+, PA++++, mineral (zinc oxide/titanium dioxide) preferred",
                        base_priority=15,
                        tags=["spf", "mineral", "broad-spectrum"],
                        time_minutes=2,
                        is_essential=True,
                        routine_slot="am",
                        score=25,
                    )
                )

        return am, pm, weekly

    def _apply_pollution_injections(
        self,
        am: list[IngredientCandidate],
        pm: list[IngredientCandidate],
        condition: str,
    ) -> tuple[list[IngredientCandidate], list[IngredientCandidate]]:
        """Inject pollution-related mandatory steps."""

        # AM: ensure antioxidant step
        has_antioxidant = any("antioxidant" in c.tags for c in am)
        if not has_antioxidant:
            am.insert(
                max(0, len(am) - 1),  # before SPF
                IngredientCandidate(
                    name="Vitamin C Serum",
                    category="serum",
                    ingredient_detail="15-20% L-ascorbic acid + vitamin E + ferulic acid",
                    base_priority=12,
                    tags=["antioxidant", "vitamin-c", "l-ascorbic-acid", "ferulic-acid"],
                    time_minutes=1,
                    is_essential=True,
                    routine_slot="am",
                    score=18,
                ),
            )
            # If lichen_planus removed l-ascorbic-acid, use niacinamide instead
            if condition == "lichen_planus":
                am[-2] = IngredientCandidate(
                    name="Niacinamide Serum",
                    category="serum",
                    ingredient_detail="Niacinamide 5% + zinc PCA serum",
                    base_priority=12,
                    tags=["antioxidant", "niacinamide", "anti-inflammatory"],
                    time_minutes=1,
                    is_essential=True,
                    routine_slot="am",
                    score=18,
                )

        # PM: double cleanse injection
        # Remove existing PM cleansers first to replace with double cleanse
        existing_pm_non_cleansers = [c for c in pm if c.category not in ("cleanser", "oil-cleanser", "micellar")]

        # Choose step 1 based on eczema/atopic interaction
        if condition in ("eczema", "atopic_dermatitis"):
            step1 = IngredientCandidate(
                name="Double Cleanse — Step 1",
                category="micellar",
                ingredient_detail="Micellar water on cotton pad (no rubbing)",
                base_priority=14,
                tags=["micellar", "gentle", "double-cleanse", "fragrance-free"],
                time_minutes=2,
                is_essential=True,
                routine_slot="pm",
                score=20,
            )
            self._overrides.append(
                "Double cleanse adapted — oil cleanser replaced with micellar water for eczema-safe pollutant removal"
            )
        else:
            step1 = IngredientCandidate(
                name="Double Cleanse — Step 1",
                category="oil-cleanser",
                ingredient_detail="Cleansing oil or micellar water to remove particulate matter and pollutants",
                base_priority=14,
                tags=["oil-cleanser", "double-cleanse"],
                time_minutes=2,
                is_essential=True,
                routine_slot="pm",
                score=20,
            )

        step2 = IngredientCandidate(
            name="Double Cleanse — Step 2",
            category="cleanser",
            ingredient_detail="Gentle water-based cleanser, pH-balanced",
            base_priority=13,
            tags=["gentle", "cleanser", "double-cleanse"],
            time_minutes=2,
            is_essential=True,
            routine_slot="pm",
            score=19,
        )

        pm = [step1, step2] + existing_pm_non_cleansers
        self._overrides.append(
            "Double cleansing added — essential for removing airborne pollutants and heavy metals from urban environments"
        )

        return am, pm

    def _enforce_melanoma_spf_ordering(self, am_steps: list[RoutineStep]) -> list[RoutineStep]:
        """
        Ensures SPF always appears immediately after any photosensitizing ingredient in AM.
        Photosensitizers: retinol, AHA, BHA, vitamin C (L-ascorbic acid).
        If SPF is not immediately after a photosensitizer, move it to follow the last one.
        """
        photosensitizer_indices = [
            i for i, s in enumerate(am_steps)
            if any(tag in s.ingredient_recommendation.lower()
                   for tag in ['retinol', 'glycolic', 'lactic', 'salicylic', 'l-ascorbic'])
        ]
        if not photosensitizer_indices:
            return am_steps

        spf_index = next(
            (i for i, s in enumerate(am_steps) if 'spf' in s.category.lower()), None
        )
        if spf_index is None:
            return am_steps

        last_photosensitizer = max(photosensitizer_indices)
        if spf_index <= last_photosensitizer:
            spf_step = am_steps.pop(spf_index)
            am_steps.insert(last_photosensitizer + 1, spf_step)
            # Renumber steps
            for i, step in enumerate(am_steps):
                step.step = i + 1

        return am_steps

    def _ensure_spf_last_am(
        self, am: list[IngredientCandidate]
    ) -> list[IngredientCandidate]:
        """For melanoma_risk: ensure SPF is the last AM step (after any photosensitizers)."""
        spf_items = [c for c in am if "spf" in c.tags]
        non_spf = [c for c in am if "spf" not in c.tags]
        return non_spf + spf_items

    def _to_steps(
        self,
        candidates: list[IngredientCandidate],
        climate_adjusted: bool,
        condition: str,
    ) -> list[RoutineStep]:
        """Convert sorted candidates into RoutineStep objects."""
        steps: list[RoutineStep] = []
        for i, c in enumerate(candidates, start=1):
            # Determine condition_safe
            safe = True
            if condition == "psoriasis" and "low-dose" in c.tags and "retinol" in c.tags:
                safe = False  # borderline ingredient kept with caution

            why = self._build_fallback_why(c, condition)

            # Melanoma SPF reapplication note
            if condition == "melanoma_risk" and "spf" in c.tags:
                why += (
                    " With your elevated sun sensitivity, reapply every 90 minutes "
                    "during outdoor exposure — not just in the morning."
                )

            steps.append(
                RoutineStep(
                    step=i,
                    time_minutes=c.time_minutes,
                    category=c.category,
                    ingredient_recommendation=c.ingredient_detail,
                    why_explanation=why,
                    is_essential=c.is_essential,
                    climate_adjusted=climate_adjusted,
                    condition_safe=safe,
                )
            )
        return steps

    def _build_fallback_why(self, candidate: IngredientCandidate, condition: str) -> str:
        """Generate a deterministic fallback explanation for a routine step."""
        parts: list[str] = []

        cat_descriptions = {
            "cleanser": "Cleansing is the foundation of any routine — it removes impurities without stripping your skin.",
            "oil-cleanser": "Oil cleansing dissolves makeup, sunscreen, and environmental debris gently.",
            "micellar": "Micellar water lifts away impurities with minimal friction on your skin.",
            "toner": "This toner prepares your skin to absorb subsequent products more effectively.",
            "serum": f"{candidate.name} delivers concentrated actives where your skin needs them most.",
            "moisturizer": "Locking in moisture strengthens your skin barrier and prevents transepidermal water loss.",
            "occlusive": "An occlusive layer seals in all previous hydration and treatment layers overnight.",
            "spf": "Daily sun protection is the single most effective anti-aging and cancer-prevention step.",
            "exfoliant": "Gentle exfoliation promotes cell turnover and keeps pores clear.",
            "mist": "A quick mist refreshes and delivers actives throughout the day.",
            "treatment": f"{candidate.name} provides targeted support for your skin concerns.",
        }
        parts.append(cat_descriptions.get(candidate.category, f"{candidate.name} supports your skin health."))

        if condition != "none":
            condition_label = condition.replace("_", " ")
            parts.append(f"Selected as safe for {condition_label}-prone skin.")

        return " ".join(parts)

    def _build_profile_summary(self) -> str:
        """Build a human-readable profile summary string."""
        req = self._req
        parts = [
            f"{req.skin_type.capitalize()} skin",
            f"{req.age_group.replace('_', ' ')} age group",
            f"primary concern: {req.primary_concern.replace('_', ' ')}",
        ]
        if req.skin_goals:
            goals_str = ", ".join(g.replace("_", " ") for g in req.skin_goals)
            parts.append(f"goals: {goals_str}")
        if req.special_situation != "none":
            parts.append(f"situation: {req.special_situation.replace('_', ' ')}")
        if req.medical_condition != "none":
            parts.append(f"condition: {req.medical_condition.replace('_', ' ')}")
        if req.pollution_exposure:
            parts.append("high-pollution environment")

        return " | ".join(parts)


# =====================================================================
# LLM Enrichment Layer
# =====================================================================


def _build_llm_system_prompt(condition: str, pollution: bool) -> str:
    """Build the LLM enrichment system prompt, extended for medical/pollution context."""
    base = (
        "You are a skincare expert writing short, friendly explanations for each step "
        "in a personalized skincare routine. For each step, explain WHY this ingredient "
        "is recommended in 1-2 sentences. Be specific to the user's skin profile. "
        "Return a JSON array of strings, one per step, in the same order as the input steps."
    )

    extensions: list[str] = []

    if condition != "none":
        extensions.append(
            "\n\nWhen medical_condition is present:\n"
            "- Incorporate the condition naturally into each explanation without alarming the user.\n"
            "- For every step, briefly acknowledge why the ingredient is safe for their condition "
            '(e.g., "Azelaic acid is ideal for your rosacea — it reduces redness and kills '
            'acne-causing bacteria without triggering flushing the way retinoids can.").\n'
            '- End the final step\'s explanation with: "For persistent symptoms or flare-ups, '
            "please consult a board-certified dermatologist — this routine is supportive care, "
            'not a medical treatment."\n'
            "- Never suggest that this routine treats, cures, or manages the medical condition. "
            'Use language like "supports your skin barrier" or "minimizes irritation triggers" '
            'rather than "treats eczema" or "controls psoriasis".'
        )

    if pollution:
        extensions.append(
            "\n\nWhen pollution_exposure is True:\n"
            "- Reference the pollution context in antioxidant and cleansing step explanations "
            '(e.g., "Urban pollution deposits free radicals on your skin throughout the day — '
            'Vitamin C neutralizes these before they cause oxidative damage.").\n'
            "- For the double cleanse steps, explain the two-phase mechanism plainly."
        )

    return base + "".join(extensions)


async def _enrich_with_llm(
    steps: list[RoutineStep],
    profile_summary: str,
    condition: str,
    pollution: bool,
) -> list[RoutineStep]:
    """
    Attempt LLM enrichment of why_explanation fields.
    Falls back to existing fallback_why on timeout or failure.
    """
    if not _openai_client:
        return steps

    system_prompt = _build_llm_system_prompt(condition, pollution)

    user_content = json.dumps(
        {
            "profile": profile_summary,
            "medical_condition": condition,
            "pollution_exposure": pollution,
            "steps": [
                {
                    "step": s.step,
                    "category": s.category,
                    "ingredient": s.ingredient_recommendation,
                }
                for s in steps
            ],
        }
    )

    try:
        response = await _openai_client.chat.completions.create(
            model=GPT_MINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
            max_tokens=1000,
            timeout=LLM_TIMEOUT_SECONDS,
        )

        raw = response.choices[0].message.content or ""
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        enriched: list[str] = json.loads(raw)

        if isinstance(enriched, list) and len(enriched) == len(steps):
            for i, explanation in enumerate(enriched):
                if isinstance(explanation, str) and explanation.strip():
                    steps[i].why_explanation = explanation.strip()

    except Exception as e:
        logger.warning("LLM enrichment failed (using fallback): %s", e)

    return steps


# =====================================================================
# Cache Key
# =====================================================================


def _cache_key(req: RoutineRequest, weather: WeatherContext | None) -> str:
    """Generate a deterministic cache key including medical + pollution fields."""
    key_data = req.model_dump(mode="json")
    if weather:
        key_data["_weather"] = weather.model_dump(mode="json")
    raw = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


# =====================================================================
# API Endpoints
# =====================================================================


@router.post("/skincare-routine", response_model=RoutineResponse)
async def get_skincare_routine_v2(
    payload: RoutineRequest,
    req: Request,
    _: None = Depends(rate_limit_dependency),
):
    """
    Generate a personalized, multi-step skincare routine.
    Extended with medical condition safety overrides and pollution exposure modifiers.
    """
    # Fetch weather context if location provided
    weather: WeatherContext | None = None
    if payload.location:
        try:
            weather = await get_weather_context(
                payload.location.lat, payload.location.lon
            )
        except Exception as e:
            logger.warning("Weather fetch failed: %s", e)

    # Check cache
    cached = await _routine_cache.get(payload, weather)
    if cached is not None:
        logger.info("Cache hit for routine request")
        return cached

    # Run rule engine
    try:
        engine = RoutineRuleEngine(payload, weather)
        response, overrides = engine.generate()
    except Exception as e:
        logger.error("Rule engine failure: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail="Routine generation engine failed")

    # LLM enrichment for AM + PM + weekly
    all_steps = list(response.am_routine) + list(response.pm_routine)
    if response.weekly_treatments:
        all_steps += list(response.weekly_treatments)

    enriched = await _enrich_with_llm(
        all_steps,
        response.profile_summary,
        payload.medical_condition,
        payload.pollution_exposure,
    )

    # Redistribute enriched steps back
    am_count = len(response.am_routine)
    pm_count = len(response.pm_routine)
    response.am_routine = enriched[:am_count]
    response.pm_routine = enriched[am_count : am_count + pm_count]
    if response.weekly_treatments:
        response.weekly_treatments = enriched[am_count + pm_count :]

    # Cache result
    await _routine_cache.set(payload, weather, response)

    return response


# ── Legacy endpoints (unchanged) ──────────────────────────────────


class LegacyRoutineRequest(BaseModel):
    condition: str
    skin_type: str = "normal"


class IngredientCheckRequest(BaseModel):
    ingredients: list[str]


@router.post("/skincare-routine-legacy")
async def get_skincare_routine_legacy(payload: LegacyRoutineRequest):
    """Legacy endpoint: Generate skincare routine based on condition lookup."""
    routine = generate_skincare_routine(payload.condition, payload.skin_type)
    return routine


@router.get("/medicines/{condition}")
async def get_medicines(condition: str):
    """Get medicine recommendations for a condition."""
    info = get_condition_info(condition)
    return {
        "condition": info["display_name"],
        "treatments": info.get("treatments", {}),
        "when_to_see_doctor": info.get("when_to_see_doctor", ""),
        "disclaimer": (
            "⚠️ These are informational suggestions only. "
            "Never self-medicate. Always consult a healthcare professional before "
            "starting any medication or treatment."
        ),
    }


@router.post("/ingredient-check")
async def check_ingredients(payload: IngredientCheckRequest):
    """Check safety of skincare ingredients."""
    results = []
    for ingredient in payload.ingredients:
        result = check_ingredient_safety(ingredient)
        results.append(result)

    harmful = [r for r in results if r["safety"] == "harmful"]
    caution = [r for r in results if r["safety"] == "caution"]
    safe = [r for r in results if r["safety"] == "safe"]

    return {
        "results": results,
        "summary": {
            "total_checked": len(results),
            "safe_count": len(safe),
            "caution_count": len(caution),
            "harmful_count": len(harmful),
        },
        "disclaimer": (
            "This is an AI-powered analysis. For comprehensive ingredient safety, "
            "consult a dermatologist or check resources like INCIDecoder.com."
        ),
    }