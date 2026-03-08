"""
recommendations.py — Skincare Routine & Medicine Recommendation API
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from app.services.knowledge_base import (
    get_condition_info,
    generate_skincare_routine,
    check_ingredient_safety,
)

router = APIRouter(prefix="/api", tags=["recommendations"])


class RoutineRequest(BaseModel):
    condition: str
    skin_type: str = "normal"


class IngredientCheckRequest(BaseModel):
    ingredients: List[str]


@router.post("/skincare-routine")
async def get_skincare_routine(payload: RoutineRequest):
    """Generate personalized skincare routine based on condition and skin type."""
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

    # Summary
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
        "disclaimer": "This is an AI-powered analysis. For comprehensive ingredient safety, consult a dermatologist or check resources like INCIDecoder.com."
    }
