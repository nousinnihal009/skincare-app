import asyncio
import base64
import json
import logging
import os
from dataclasses import dataclass

import google.generativeai as genai
from PIL import Image
import io

logger = logging.getLogger(__name__)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

ARBITER_TIMEOUT_SECONDS = 12.0

SYSTEM_PROMPT = """You are a clinical dermatology image analysis assistant.
You will be shown a skin image and given the top 2 predictions from a ResNet50 classifier
with their confidence scores. Your role is to:

1. Validate or override the primary prediction based on what you can visually observe
2. Extract specific visible skin features that support your assessment
3. Generate a professional, non-alarmist skin assessment paragraph

STRICT RULES:
- Never diagnose. Use language like "may suggest", "consistent with", "could indicate"
- Always recommend professional evaluation for anything beyond routine skincare concerns
- If the image quality is too poor to assess, say so explicitly
- Do not comment on the person's appearance beyond clinical skin observations
- Keep the assessment between 2-4 sentences

Respond ONLY with valid JSON matching this exact schema:
{
  "validated_condition": string,
  "confidence_adjustment": "higher" | "same" | "lower",
  "visible_features": string[],
  "assessment_paragraph": string,
  "refer_to_dermatologist": boolean,
  "llm_overrode_resnet": boolean
}
No preamble, no markdown, no explanation outside the JSON."""


@dataclass
class ArbiterResult:
    validated_condition:    str
    confidence_adjustment:  str
    visible_features:       list[str]
    assessment_paragraph:   str
    refer_to_dermatologist: bool
    llm_overrode_resnet:    bool
    llm_enriched:           bool


class VisionArbiter:
    async def arbitrate(
        self,
        image_bytes: bytes,
        classifier_result,
        features
    ) -> ArbiterResult:

        fallback = ArbiterResult(
            validated_condition    = classifier_result.top_prediction,
            confidence_adjustment  = "same",
            visible_features       = [],
            assessment_paragraph   = (
                f"Our analysis suggests this may be consistent with "
                f"{classifier_result.top_prediction.replace('_', ' ')}. "
                "For accurate diagnosis and treatment, please consult a dermatologist."
            ),
            refer_to_dermatologist = classifier_result.top_confidence < 0.72,
            llm_overrode_resnet    = False,
            llm_enriched           = False,
        )

        try:
            # Build prompt text
            prompt_text = (
                f"{SYSTEM_PROMPT}\n\n"
                f"ResNet50 primary prediction: {classifier_result.top_prediction} "
                f"(confidence: {classifier_result.top_confidence:.1%})\n"
                f"Runner-up prediction: {classifier_result.second_prediction} "
                f"(confidence: {classifier_result.second_confidence:.1%})\n\n"
                f"CV metrics from this image:\n"
                f"- Redness level: {features.erythema.level} ({features.erythema.percentage}%)\n"
                f"- Texture roughness: {features.texture.level} ({features.texture.percentage}%)\n"
                f"- Oiliness: {features.oiliness.level} ({features.oiliness.percentage}%)\n\n"
                "Please validate or override the primary prediction based on what you observe. "
                "Respond only with the JSON schema specified above."
            )

            # Convert bytes to PIL Image for Gemini
            image = Image.open(io.BytesIO(image_bytes))

            # Run in thread to avoid blocking event loop
            def _call_gemini():
                model    = genai.GenerativeModel("gemini-flash-latest")
                response = model.generate_content([prompt_text, image])
                return response.text

            raw = await asyncio.wait_for(
                asyncio.to_thread(_call_gemini),
                timeout=ARBITER_TIMEOUT_SECONDS
            )

            # Strip markdown fences if present
            clean = raw.strip().replace("```json", "").replace("```", "").strip()
            data  = json.loads(clean)

            logger.info(f"[VisionArbiter] Gemini SUCCESS — validated: {data['validated_condition']}, overrode: {data['llm_overrode_resnet']}")

            return ArbiterResult(
                validated_condition    = data["validated_condition"],
                confidence_adjustment  = data["confidence_adjustment"],
                visible_features       = data.get("visible_features", []),
                assessment_paragraph   = data["assessment_paragraph"],
                refer_to_dermatologist = data["refer_to_dermatologist"],
                llm_overrode_resnet    = data["llm_overrode_resnet"],
                llm_enriched           = True,
            )

        except asyncio.TimeoutError:
            logger.warning(f"[VisionArbiter] Gemini timed out after {ARBITER_TIMEOUT_SECONDS}s — using fallback")
            return fallback
        except json.JSONDecodeError as e:
            logger.error(f"[VisionArbiter] JSON parse failed: {e} — raw response: {raw[:200]}")
            return fallback
        except Exception as e:
            logger.error(f"[VisionArbiter] Gemini call failed: {type(e).__name__}: {e}")
            return fallback
