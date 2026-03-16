"""
analysis.py — Skin Analysis API route

4-stage pipeline:
  Stage 1: SkinImageValidator       — blocks non-skin / bad images  (HTTP 422)
  Stage 2: SkinFeatureExtractor     — CV skin metrics               (concurrent)
  Stage 3: ResNet50 classify()      — confidence-gated prediction   (concurrent)
  Stage 4: VisionArbiter (GPT-4o)   — cross-validates if uncertain
"""

from __future__ import annotations

import asyncio
import io

from fastapi import APIRouter, File, UploadFile, HTTPException, Request

from app.models.prediction import classify, predict_condition, ClassifierResult
from app.services.skin_validator import (
    SkinImageValidator,
    RejectionReason,
    ValidationResult,
)
from app.services.feature_extractor import (
    SkinFeatureExtractor,
    FeatureExtractionResult,
    SkinMetric,
)
from app.services.vision_arbiter import VisionArbiter, ArbiterResult

router = APIRouter(prefix="/api", tags=["analysis"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# ── Rejection user-facing messages ────────────────────────────

REJECTION_MESSAGES: dict[RejectionReason, str] = {
    RejectionReason.NO_SKIN_DETECTED:    "We couldn't detect skin in this photo. Please upload a clear, close-up photo of the affected skin area.",
    RejectionReason.IMAGE_TOO_BLURRY:    "This photo is too blurry to analyze. Please retake the photo in good lighting and hold your device steady.",
    RejectionReason.IMAGE_TOO_DARK:      "This photo is too dark to analyze. Please retake in better lighting — natural daylight works best.",
    RejectionReason.IMAGE_TOO_SMALL:     "This photo is too small. Please upload an image of at least 150×150 pixels.",
    RejectionReason.CORRUPT_OR_INVALID:  "This file couldn't be read. Please try a different photo in JPG or PNG format.",
    RejectionReason.SCREENSHOT_DETECTED: "This looks like a screenshot rather than a skin photo. Please upload a real photo of your skin.",
}

# ── High-confusion condition pairs ────────────────────────────

HIGH_CONFUSION_PAIRS = {
    frozenset({"Warts Molluscum and other Viral Infections", "acne-pustular"}),
    frozenset({"Warts Molluscum and other Viral Infections", "acne-closed-comedo"}),
    frozenset({"rosacea", "acne-pustular"}),
}


# ── Route handler ─────────────────────────────────────────────

@router.post("/analyze")
async def analyze_skin(file: UploadFile = File(...)):
    """Full skin analysis: 4-stage pipeline → structured results."""

    # ── Pre-checks (unchanged) ─────────────────────────────────
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    image_bytes: bytes = contents

    # ── Stage 1: Validate ──────────────────────────────────────
    validator = SkinImageValidator()
    validation_result = validator.validate(image_bytes)

    if not validation_result.is_valid:
        reason = validation_result.rejection_reason
        raise HTTPException(
            status_code=422,
            detail={
                "rejection_reason": reason.value,
                "user_message": REJECTION_MESSAGES[reason],
                "technical_detail": (
                    f"blur={validation_result.blur_score:.1f} "
                    f"brightness={validation_result.brightness:.1f} "
                    f"skin_ratio={validation_result.skin_ratio:.3f}"
                ),
            },
        )

    # ── Stages 2 + 3: Run concurrently ─────────────────────────
    extractor = SkinFeatureExtractor()

    features_task = asyncio.to_thread(
        extractor.extract, image_bytes, validation_result.skin_mask,
    )
    classifier_task = asyncio.to_thread(classify, image_bytes)

    # Also run legacy predict_condition concurrently for backward compat
    legacy_task = asyncio.to_thread(
        predict_condition, io.BytesIO(image_bytes),
    )

    features, classifier_result, legacy_result = await asyncio.gather(
        features_task, classifier_task, legacy_task,
    )

    # ── Stage 4: Arbitrate if needed ───────────────────────────
    needs_arbitration = (
        not classifier_result.is_confident
        or classifier_result.is_ambiguous
        or frozenset({
            classifier_result.top_prediction,
            classifier_result.second_prediction,
        }) in HIGH_CONFUSION_PAIRS
    )

    arbiter = VisionArbiter()
    if needs_arbitration:
        arbiter_result = await arbiter.arbitrate(
            image_bytes, classifier_result, features,
        )
    else:
        arbiter_result = ArbiterResult(
            validated_condition=classifier_result.top_prediction,
            confidence_adjustment="same",
            visible_features=[],
            assessment_paragraph=(
                f"Analysis indicates characteristics consistent with "
                f"{classifier_result.top_prediction.replace('_', ' ')}. "
                "For any skin concerns, consultation with a dermatologist is recommended."
            ),
            refer_to_dermatologist=False,
            llm_overrode_resnet=False,
            llm_enriched=False,
        )

    # ── Assemble response ──────────────────────────────────────
    def _metric_dict(m: SkinMetric) -> dict:
        return {
            "key": m.key,
            "display_name": m.display_name,
            "percentage": m.percentage,
            "level": m.level,
            "interpretation": m.interpretation,
            "reference_note": m.reference_note,
        }

    # Start from the legacy result (preserves all existing fields)
    result = legacy_result

    # Override condition with arbiter's validated condition
    if arbiter_result.llm_overrode_resnet:
        result["prediction"]["class_name"] = arbiter_result.validated_condition
        result["prediction"]["display_name"] = arbiter_result.validated_condition.replace("_", " ").title()

    # Additive new fields
    result["skin_metrics"] = [
        _metric_dict(features.erythema),
        _metric_dict(features.texture),
        _metric_dict(features.oiliness),
        _metric_dict(features.hydration),
        _metric_dict(features.evenness),
    ]
    result["assessment_paragraph"] = arbiter_result.assessment_paragraph
    result["visible_features"] = arbiter_result.visible_features
    result["refer_to_dermatologist"] = arbiter_result.refer_to_dermatologist
    result["llm_enriched"] = arbiter_result.llm_enriched
    result["llm_overrode_resnet"] = arbiter_result.llm_overrode_resnet
    result["second_prediction"] = classifier_result.second_prediction
    result["second_confidence"] = classifier_result.second_confidence
    result["validation_meta"] = {
        "blur_score": validation_result.blur_score,
        "brightness": validation_result.brightness,
        "skin_ratio": validation_result.skin_ratio,
    }

    result["received_file"] = filename
    return result
