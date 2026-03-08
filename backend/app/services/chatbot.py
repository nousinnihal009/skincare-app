"""
chatbot.py

AI Dermatologist Chatbot — rule-based Q&A system using the dermatology knowledge base.
"""

from app.services.knowledge_base import CONDITION_DATABASE, INGREDIENT_DATABASE, check_ingredient_safety

# ─────────────────────────────────────────────────────────────
# Pre-built Q&A Knowledge
# ─────────────────────────────────────────────────────────────

GENERAL_QA = {
    "melanoma": {
        "keywords": ["melanoma", "melanoma dangerous", "deadliest skin cancer", "most dangerous"],
        "response": (
            "**Melanoma** is the most dangerous form of skin cancer. It develops from melanocytes (pigment cells) and can "
            "metastasize to other organs if not caught early.\n\n"
            "**Key facts:**\n"
            "- 5-year survival rate: **99% if localized** (Stage I), drops to **30% if metastasized**\n"
            "- Use the **ABCDE rule** to check moles: Asymmetry, Border irregularity, Color variation, Diameter >6mm, Evolving\n"
            "- Risk factors: intense UV exposure, fair skin, >50 moles, family history\n\n"
            "⚠️ **If you suspect melanoma, see a dermatologist IMMEDIATELY.** Early detection saves lives."
        )
    },
    "eczema_treatment": {
        "keywords": ["treatment for eczema", "eczema treatment", "treat eczema", "cure eczema", "help eczema"],
        "response": (
            "**Eczema (Atopic Dermatitis) Treatment:**\n\n"
            "**Daily Management:**\n"
            "- Moisturize **immediately after bathing** (within 3 minutes)\n"
            "- Use thick, fragrance-free creams (CeraVe, Vanicream, Eucerin)\n"
            "- Take short lukewarm showers (<10 min)\n"
            "- Use gentle, fragrance-free cleansers\n\n"
            "**Flare Treatments:**\n"
            "- OTC: 1% hydrocortisone cream (max 2 weeks)\n"
            "- Prescription: Topical corticosteroids, tacrolimus, pimecrolimus\n"
            "- Severe cases: Dupilumab (Dupixent) biologic therapy\n\n"
            "**Lifestyle:**\n"
            "- Identify and avoid triggers (stress, allergens, irritants)\n"
            "- Wear soft cotton clothing\n"
            "- Use a humidifier in dry weather\n\n"
            "⚠️ Eczema has no cure, but can be well-managed. See a dermatologist if OTC treatments aren't enough."
        )
    },
    "see_doctor": {
        "keywords": ["should i see a doctor", "when to see doctor", "see a dermatologist", "need doctor", "should i go to doctor"],
        "response": (
            "**When to See a Dermatologist:**\n\n"
            "🔴 **Immediately if:**\n"
            "- A mole is changing (ABCDE criteria)\n"
            "- A sore that won't heal\n"
            "- A rapidly growing lesion\n"
            "- Signs of skin infection (spreading redness, warmth, pus, fever)\n\n"
            "🟡 **Soon if:**\n"
            "- Persistent rash >2 weeks\n"
            "- Severe acne causing scarring\n"
            "- Widespread skin condition\n"
            "- OTC treatments aren't working after 6-8 weeks\n\n"
            "🟢 **Routine (schedule when convenient):**\n"
            "- Annual skin cancer screening (especially if >50 moles or family history)\n"
            "- Mild cosmetic concerns\n"
            "- New skincare routine guidance\n\n"
            "💡 **Tip:** Many dermatologists now offer teledermatology (video consultations) for initial assessments."
        )
    },
    "sunscreen": {
        "keywords": ["sunscreen", "spf", "sun protection", "uv protection", "sunblock"],
        "response": (
            "**Sunscreen Guide:**\n\n"
            "- Use **SPF 30 minimum** (SPF 50 recommended for daily use)\n"
            "- Choose **broad-spectrum** (protects against UVA + UVB)\n"
            "- Apply **1/4 teaspoon for face** (most people under-apply)\n"
            "- Reapply **every 2 hours** outdoors, or after swimming/sweating\n\n"
            "**Types:**\n"
            "- **Mineral** (zinc oxide, titanium dioxide): Best for sensitive/acne-prone skin\n"
            "- **Chemical** (avobenzone, octinoxate): More cosmetically elegant, lighter feel\n\n"
            "**Key facts:**\n"
            "- UV damage is the #1 cause of premature aging\n"
            "- Up to 80% of UV rays penetrate clouds\n"
            "- SPF only measures UVB protection — look for broad-spectrum\n"
            "- Sunscreen is the **single most important anti-aging product**"
        )
    },
    "acne": {
        "keywords": ["acne", "pimple", "breakout", "zits", "acne treatment"],
        "response": (
            "**Acne Treatment Guide:**\n\n"
            "**Mild Acne (blackheads, whiteheads):**\n"
            "- Salicylic acid 2% cleanser\n"
            "- Adapalene 0.1% gel (Differin — now OTC)\n"
            "- Benzoyl peroxide 2.5% spot treatment\n\n"
            "**Moderate Acne (papules, pustules):**\n"
            "- Add benzoyl peroxide wash\n"
            "- Consider prescription retinoid\n"
            "- Topical antibiotics (clindamycin)\n\n"
            "**Severe/Cystic Acne:**\n"
            "- See a dermatologist — may need isotretinoin (Accutane)\n"
            "- Cortisone injections for painful cysts\n"
            "- Hormonal therapy (spironolactone for hormonal acne)\n\n"
            "**Important tips:**\n"
            "- Don't pick or pop — causes scarring\n"
            "- Be patient — most treatments take 6-12 weeks\n"
            "- Always use sunscreen with retinoids"
        )
    },
    "skin_cancer": {
        "keywords": ["skin cancer", "cancer", "cancerous", "malignant", "is it cancer"],
        "response": (
            "**Skin Cancer Overview:**\n\n"
            "**Three main types:**\n"
            "1. **Basal Cell Carcinoma (BCC)** — Most common, slowest growing, rarely spreads\n"
            "2. **Squamous Cell Carcinoma (SCC)** — Can metastasize if neglected\n"
            "3. **Melanoma** — Most dangerous, can be fatal if not caught early\n\n"
            "**Warning signs (ABCDE rule for moles):**\n"
            "- **A**symmetry — one half doesn't match the other\n"
            "- **B**order — irregular, ragged, or blurred edges\n"
            "- **C**olor — uneven color (brown, black, red, white, blue)\n"
            "- **D**iameter — larger than 6mm (pencil eraser)\n"
            "- **E**volving — changing in size, shape, or color\n\n"
            "**Prevention:**\n"
            "- Daily SPF 50+ sunscreen\n"
            "- Avoid tanning beds (increases melanoma risk by 75%)\n"
            "- Wear protective clothing\n"
            "- Monthly self-exams + annual dermatologist screening\n\n"
            "⚠️ **Any suspicious lesion should be evaluated by a dermatologist ASAP.**"
        )
    },
    "retinol": {
        "keywords": ["retinol", "retinoid", "retin-a", "tretinoin", "vitamin a"],
        "response": (
            "**Retinol/Retinoid Guide:**\n\n"
            "Retinoids are Vitamin A derivatives — the **gold standard** for anti-aging and acne.\n\n"
            "**Strength hierarchy (weakest → strongest):**\n"
            "1. Retinyl palmitate (very mild)\n"
            "2. Retinol 0.3-1% (OTC)\n"
            "3. Adapalene 0.1-0.3% (OTC/Rx)\n"
            "4. Tretinoin 0.025-0.1% (prescription)\n"
            "5. Tazarotene (strongest Rx)\n\n"
            "**How to use:**\n"
            "- Start LOW and SLOW (2x/week, increase gradually)\n"
            "- Apply pea-sized amount to DRY skin at night\n"
            "- Always use SPF 50+ during the day\n"
            "- Expect initial 'purging' (weeks 2-6) — this is normal\n"
            "- Results visible after 12-24 weeks\n\n"
            "**Avoid with:** other exfoliants (AHA/BHA), vitamin C (use in AM instead), benzoyl peroxide"
        )
    },
    "dry_skin": {
        "keywords": ["dry skin", "dehydrated skin", "dry face", "flaky skin", "cracked skin"],
        "response": (
            "**Dry Skin Care Guide:**\n\n"
            "**Hydrating routine:**\n"
            "1. Gentle cream cleanser (no foaming/SLS)\n"
            "2. Hyaluronic acid serum on DAMP skin\n"
            "3. Rich moisturizer with ceramides\n"
            "4. Facial oil to seal (squalane, jojoba)\n"
            "5. SPF 30+ (cream-based, not alcohol-based)\n\n"
            "**Key ingredients:**\n"
            "- Hyaluronic acid — draws water to skin\n"
            "- Ceramides — repair skin barrier\n"
            "- Glycerin — humectant\n"
            "- Squalane — lightweight oil\n"
            "- Shea butter — rich emollient\n\n"
            "**Avoid:**\n"
            "- Harsh cleansers (SLS, SLES)\n"
            "- Hot water (use lukewarm)\n"
            "- Over-exfoliating\n"
            "- Alcohol-based toners"
        )
    },
    "greeting": {
        "keywords": ["hello", "hi", "hey", "help", "what can you do"],
        "response": (
            "Hello! 👋 I'm your AI Dermatology Assistant. I can help you with:\n\n"
            "🔬 **Skin conditions** — Information about acne, eczema, psoriasis, skin cancer, and more\n"
            "💊 **Treatments** — Treatment options for various skin conditions\n"
            "🧴 **Skincare routines** — Personalized routine guidance\n"
            "🧪 **Ingredient safety** — Check if skincare ingredients are safe\n"
            "👨‍⚕️ **When to see a doctor** — Guidance on when to seek professional help\n"
            "☀️ **Sun protection** — SPF and UV protection advice\n\n"
            "Just ask me a question! For example:\n"
            "- \"Is melanoma dangerous?\"\n"
            "- \"What treatments exist for eczema?\"\n"
            "- \"Should I see a doctor?\"\n\n"
            "⚠️ *I'm an AI assistant, not a doctor. Always consult a healthcare professional for medical advice.*"
        )
    }
}


def get_chatbot_response(message: str) -> dict:
    """Generate a chatbot response based on the user's message."""
    msg_lower = message.lower().strip()

    # Check general Q&A first
    best_match = None
    best_score = 0
    for qa_id, qa in GENERAL_QA.items():
        for keyword in qa["keywords"]:
            if keyword in msg_lower:
                score = len(keyword)
                if score > best_score:
                    best_score = score
                    best_match = qa

    if best_match:
        return {
            "response": best_match["response"],
            "type": "knowledge",
            "disclaimer": "This information is for educational purposes only and not a substitute for professional medical advice."
        }

    # Check if asking about a specific condition
    for class_name, info in CONDITION_DATABASE.items():
        display_lower = info["display_name"].lower()
        class_lower = class_name.lower()
        if class_lower in msg_lower or display_lower in msg_lower:
            response = (
                f"**{info['display_name']}**\n\n"
                f"{info['description']}\n\n"
                f"**Severity:** {info['severity'].title()}\n"
                f"**Risk Level:** {info['risk_level'].title()}\n\n"
                f"**Common causes:** {', '.join(info['causes'][:3])}\n\n"
                f"**Symptoms:** {', '.join(info['symptoms'][:4])}\n\n"
                f"**When to see a doctor:** {info['when_to_see_doctor']}\n\n"
            )
            if info.get("is_cancerous"):
                response += "⚠️ **This is a form of skin cancer. Please seek immediate medical evaluation.**\n"

            return {
                "response": response,
                "type": "condition_info",
                "condition": class_name,
                "disclaimer": "This information is for educational purposes only and not a substitute for professional medical advice."
            }

    # Check if asking about an ingredient
    ingredient_keywords = ["ingredient", "safe", "harmful", "contain", "chemical"]
    if any(kw in msg_lower for kw in ingredient_keywords):
        # Try to extract ingredient names
        for ing_name in INGREDIENT_DATABASE.keys():
            if ing_name in msg_lower:
                info = check_ingredient_safety(ing_name)
                safety_emoji = "✅" if info["safety"] == "safe" else "⚠️" if info["safety"] == "caution" else "🚫"
                response = (
                    f"{safety_emoji} **{ing_name.title()}** — Safety: **{info['safety'].title()}**\n\n"
                    f"{info['description']}\n\n"
                    f"- Acne risk: {'Yes' if info['acne_risk'] else 'No'}\n"
                    f"- Allergen risk: {'Yes' if info['allergen_risk'] else 'No'}"
                )
                return {
                    "response": response,
                    "type": "ingredient_info",
                    "disclaimer": "Consult INCIDecoder.com or a dermatologist for comprehensive ingredient analysis."
                }

    # Default response
    return {
        "response": (
            "I'm not sure I understand that question. Here are some things I can help with:\n\n"
            "- **Skin conditions**: Ask about acne, eczema, melanoma, psoriasis, etc.\n"
            "- **Treatments**: \"What treatments exist for [condition]?\"\n"
            "- **When to see a doctor**: \"Should I see a doctor?\"\n"
            "- **Ingredients**: \"Is [ingredient name] safe?\"\n"
            "- **Skincare**: \"How do I care for dry/oily skin?\"\n\n"
            "Try rephrasing your question or ask about a specific condition!"
        ),
        "type": "fallback",
        "disclaimer": "I'm an AI assistant. For medical concerns, please consult a healthcare professional."
    }
