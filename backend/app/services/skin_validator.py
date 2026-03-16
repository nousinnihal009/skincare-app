"""
skin_validator.py — Stage 1: Input Validation

Rejects images that cannot be meaningfully analyzed as skin before any
expensive computation runs.  Equity-safe multi-color-space skin detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import cv2
import numpy as np

# ── Thresholds ───────────────────────────────────────────────
SKIN_RATIO_THRESHOLD = 0.08      # min skin pixels / total pixels
BLUR_THRESHOLD       = 80.0      # Laplacian variance below this → too blurry
BRIGHTNESS_THRESHOLD = 30.0      # mean grey below this → too dark
MIN_DIMENSION        = 150       # minimum width AND height in px


# ── Rejection Taxonomy ───────────────────────────────────────

class RejectionReason(str, Enum):
    NO_SKIN_DETECTED    = "no_skin_detected"
    IMAGE_TOO_BLURRY    = "image_too_blurry"
    IMAGE_TOO_DARK      = "image_too_dark"
    IMAGE_TOO_SMALL     = "image_too_small"
    CORRUPT_OR_INVALID  = "corrupt_or_invalid"
    SCREENSHOT_DETECTED = "screenshot_detected"


# ── Result Container ─────────────────────────────────────────

@dataclass
class ValidationResult:
    is_valid: bool
    rejection_reason: Optional[RejectionReason] = None
    skin_ratio: float = 0.0
    blur_score: float = 0.0
    brightness: float = 0.0
    skin_mask: Optional[np.ndarray] = field(default=None, repr=False)


# ── Private helpers ──────────────────────────────────────────

def _compute_skin_mask(bgr_image: np.ndarray) -> np.ndarray:
    """
    Multi-space skin detection robust across Fitzpatrick Types I-VI.
    Returns binary mask where 1 = skin pixel.
    """
    hsv   = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    ycrcb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2YCrCb)
    lab   = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2Lab)

    # HSV range — broad, covers Types I-VI
    # OpenCV HSV: H 0-179, S 0-255, V 0-255
    hsv_mask = (
        ((hsv[:, :, 0] <= 25) | (hsv[:, :, 0] >= 168)) &
        (hsv[:, :, 1] >= 15) & (hsv[:, :, 1] <= 170) &
        (hsv[:, :, 2] >= 35)
    ).astype(np.uint8)

    # YCrCb range — calibrated for broader skin tone coverage
    ycrcb_mask = (
        (ycrcb[:, :, 1] >= 130) & (ycrcb[:, :, 1] <= 185) &
        (ycrcb[:, :, 2] >= 77)  & (ycrcb[:, :, 2] <= 140)
    ).astype(np.uint8)

    # CIE Lab range — L channel validates luminance presence
    lab_mask = (
        (lab[:, :, 0] >= 20) & (lab[:, :, 0] <= 230)
    ).astype(np.uint8)

    # Ensemble: pixel must pass HSV OR YCrCb, AND pass Lab luminance
    combined = ((hsv_mask | ycrcb_mask) & lab_mask).astype(np.uint8)

    # Morphological cleanup: remove noise and fill small holes
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN,  kernel, iterations=1)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)

    return combined


def _is_screenshot(bgr_image: np.ndarray) -> bool:
    """
    Detects screenshots via UI color saturation analysis.
    Screenshots have abnormally high concentrations of fully-saturated
    or fully-desaturated pixels (UI whites, blacks, greys, and brand colors).
    """
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    h, w = bgr_image.shape[:2]
    total_pixels = h * w

    # High-saturation pixel ratio (UI brand colors, icons)
    high_sat = np.sum(hsv[:, :, 1] > 220) / total_pixels

    # Near-zero saturation ratio (UI whites, greys, blacks)
    near_zero_sat = np.sum(hsv[:, :, 1] < 10) / total_pixels

    # UI-dominant: if >35% of pixels are either fully saturated or near-grey
    return bool((high_sat + near_zero_sat) > 0.35)


def _compute_blur_score(grey_image: np.ndarray) -> float:
    """Laplacian variance — higher = sharper. Threshold: < 80 = too blurry."""
    return float(cv2.Laplacian(grey_image, cv2.CV_64F).var())


def _compute_brightness(grey_image: np.ndarray) -> float:
    """Mean pixel brightness. Threshold: < 30 = too dark to analyze."""
    return float(np.mean(grey_image))


# ── Public Validator Class ───────────────────────────────────

class SkinImageValidator:
    """Stage 1 of the vision pipeline — blocks non-skin, blurry, corrupt images."""

    def validate(self, image_bytes: bytes) -> ValidationResult:
        # Decode
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            return ValidationResult(False, RejectionReason.CORRUPT_OR_INVALID)

        h, w = bgr.shape[:2]
        grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # Size check
        if h < MIN_DIMENSION or w < MIN_DIMENSION:
            return ValidationResult(False, RejectionReason.IMAGE_TOO_SMALL)

        # Darkness
        brightness = _compute_brightness(grey)
        if brightness < BRIGHTNESS_THRESHOLD:
            return ValidationResult(
                False, RejectionReason.IMAGE_TOO_DARK,
                brightness=brightness,
            )

        # Blur
        blur_score = _compute_blur_score(grey)
        if blur_score < BLUR_THRESHOLD:
            return ValidationResult(
                False, RejectionReason.IMAGE_TOO_BLURRY,
                blur_score=blur_score,
            )

        # Screenshot
        if _is_screenshot(bgr):
            return ValidationResult(False, RejectionReason.SCREENSHOT_DETECTED)

        # Skin presence
        skin_mask = _compute_skin_mask(bgr)
        total_px = h * w
        skin_pixels = int(np.sum(skin_mask))
        skin_ratio = skin_pixels / total_px

        if skin_ratio < SKIN_RATIO_THRESHOLD:
            return ValidationResult(
                False, RejectionReason.NO_SKIN_DETECTED,
                skin_ratio=skin_ratio,
            )

        return ValidationResult(
            is_valid=True,
            skin_ratio=skin_ratio,
            blur_score=blur_score,
            brightness=brightness,
            skin_mask=skin_mask,
        )
