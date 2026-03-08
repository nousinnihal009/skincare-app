"""
environment.py — Environmental Skin Risk Alerts API
Uses free weather/UV data APIs.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["environment"])


# UV Index risk levels
UV_RISK_LEVELS = {
    (0, 2): {"level": "Low", "color": "green", "advice": "Minimal protection needed. Wear sunglasses."},
    (3, 5): {"level": "Moderate", "color": "yellow", "advice": "Wear SPF 30+ sunscreen, hat, and sunglasses. Seek shade during midday."},
    (6, 7): {"level": "High", "color": "orange", "advice": "Wear SPF 50+ sunscreen, protective clothing, and wide-brim hat. Avoid midday sun."},
    (8, 10): {"level": "Very High", "color": "red", "advice": "Take ALL precautions. SPF 50+ required. Stay indoors 10am-4pm if possible."},
    (11, 15): {"level": "Extreme", "color": "purple", "advice": "AVOID ALL outdoor exposure during peak hours. Maximum protection essential."},
}


def get_uv_risk(uv_index: float) -> dict:
    for (low, high), info in UV_RISK_LEVELS.items():
        if low <= uv_index <= high:
            return info
    return UV_RISK_LEVELS[(8, 10)]


@router.get("/environment/risks")
async def get_environment_risks(
    uv_index: Optional[float] = 6.0,
    humidity: Optional[float] = 50.0,
    pollution_aqi: Optional[int] = 50,
    temperature: Optional[float] = 25.0,
):
    """Get environmental skin risk alerts based on weather conditions."""

    risks = []

    # UV Risk
    uv_risk = get_uv_risk(uv_index)
    risks.append({
        "type": "UV Radiation",
        "value": uv_index,
        "unit": "UV Index",
        "level": uv_risk["level"],
        "color": uv_risk["color"],
        "advice": uv_risk["advice"],
        "icon": "☀️"
    })

    # Humidity Risk
    if humidity < 30:
        risks.append({
            "type": "Low Humidity",
            "value": humidity,
            "unit": "%",
            "level": "Warning",
            "color": "orange",
            "advice": "Low humidity can dry out skin. Use a heavier moisturizer and consider a humidifier.",
            "icon": "💧"
        })
    elif humidity > 80:
        risks.append({
            "type": "High Humidity",
            "value": humidity,
            "unit": "%",
            "level": "Moderate",
            "color": "yellow",
            "advice": "High humidity may worsen acne and fungal conditions. Use lightweight, oil-free products.",
            "icon": "💧"
        })
    else:
        risks.append({
            "type": "Humidity",
            "value": humidity,
            "unit": "%",
            "level": "Normal",
            "color": "green",
            "advice": "Humidity levels are comfortable for skin health.",
            "icon": "💧"
        })

    # Air Quality
    if pollution_aqi > 150:
        aqi_level = "Unhealthy"
        aqi_color = "red"
        aqi_advice = "High pollution accelerates skin aging and can worsen conditions. Double cleanse in the evening. Use antioxidant serum (Vitamin C)."
    elif pollution_aqi > 100:
        aqi_level = "Moderate-High"
        aqi_color = "orange"
        aqi_advice = "Moderate pollution levels. Use antioxidant protection and cleanse thoroughly at night."
    elif pollution_aqi > 50:
        aqi_level = "Moderate"
        aqi_color = "yellow"
        aqi_advice = "Some pollution present. Standard skincare routine with cleansing is sufficient."
    else:
        aqi_level = "Good"
        aqi_color = "green"
        aqi_advice = "Air quality is good. Standard skincare routine."

    risks.append({
        "type": "Air Quality",
        "value": pollution_aqi,
        "unit": "AQI",
        "level": aqi_level,
        "color": aqi_color,
        "advice": aqi_advice,
        "icon": "🌫️"
    })

    # Temperature
    if temperature > 35:
        risks.append({
            "type": "Heat",
            "value": temperature,
            "unit": "°C",
            "level": "High",
            "color": "red",
            "advice": "Extreme heat increases sweating and sun damage risk. Stay hydrated, use lightweight SPF, and cool showers.",
            "icon": "🌡️"
        })
    elif temperature < 5:
        risks.append({
            "type": "Cold",
            "value": temperature,
            "unit": "°C",
            "level": "Warning",
            "color": "blue",
            "advice": "Cold weather strips moisture from skin. Use heavier moisturizers and protect exposed skin.",
            "icon": "🌡️"
        })

    # Overall recommendation
    high_risks = [r for r in risks if r["color"] in ("red", "purple")]
    if high_risks:
        overall = "⚠️ High environmental skin risk today. Take extra precautions with sun protection and skincare."
    else:
        overall = "✅ Environmental conditions are generally safe for skin health today."

    return {
        "risks": risks,
        "overall": overall,
        "timestamp": "current",
        "disclaimer": "Environmental data shown may be simulated. Check local weather services for accurate readings."
    }
