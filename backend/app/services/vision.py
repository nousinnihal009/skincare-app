"""
vision.py — Vision risk assessment service.
Wraps the existing ML prediction pipeline to provide a simplified risk flag
for the chatbot tool system.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RiskLevel(str, Enum):
    """Tri-level risk classification from the vision model."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


async def get_vision_risk_flag(image_id: str) -> RiskLevel:
    """
    Retrieve a pre-computed risk flag for a previously uploaded skin image.

    In production this queries the analysis history / cache for the given
    image_id and maps the stored risk_level to the RiskLevel enum.

    Args:
        image_id: Unique identifier for a previously uploaded and analyzed image.

    Returns:
        RiskLevel enum value: LOW, MEDIUM, or HIGH.
    """
    import sqlite3
    import os

    db_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "dermai.db")
    )

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT risk_level FROM analysis_history WHERE id = ?",
            (image_id,),
        ).fetchone()
        conn.close()

        if row is None:
            # Default to MEDIUM if image not found (could be an external reference)
            return RiskLevel.MEDIUM

        level_str = row["risk_level"].upper().strip()
        if level_str in ("HIGH", "CRITICAL", "DANGEROUS"):
            return RiskLevel.HIGH
        elif level_str in ("MEDIUM", "MODERATE", "WARNING"):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    except Exception:
        # If DB is unavailable, return MEDIUM as a safe default
        return RiskLevel.MEDIUM
