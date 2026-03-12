"""
condition_kb.py — Clinical Knowledge Base for 18 Supported Skin Conditions
All data is hardcoded. The LLM never modifies this data — it only enriches language.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class KBStep:
    phase: Literal["immediate", "daily_am", "daily_pm", "weekly", "ongoing_management"]
    category: str
    recommendation: str
    fallback_why: str
    is_otc_available: bool
    avoid_if: list[str] = field(default_factory=list)
    score: int = 0  # 0 = mandatory, >0 = optional (included if score >= 2)
    score_modifiers: dict = field(default_factory=dict)


@dataclass
class ConditionKB:
    key: str
    display_name: str
    category: Literal["inflammatory", "infectious", "pigmentation", "high_risk"]
    is_contagious: bool
    is_curable: bool
    contagion_guidance: str | None

    # Education
    what_it_is: str
    what_causes_it: str
    typical_duration: str
    common_misconceptions: list[str]

    # Care plan building blocks
    mandatory_steps: list[KBStep]
    optional_steps: list[KBStep]

    # Ingredient guidance
    seek_ingredients: list[tuple[str, str]]
    avoid_ingredients: list[tuple[str, str]]

    # Trigger management
    triggers: list[tuple[str, str, str]]

    # Safety
    red_flags: list[tuple[str, str, str]]
    referral_recommended: bool
    referral_urgency: Literal["immediate", "soon", "routine", "not_required"]
    when_to_see_doctor: str
    base_disclaimer: str

    # Weather sensitivity
    weather_notes: dict[str, str] = field(default_factory=dict)


class ConditionKnowledgeBase:
    """Lookup service for condition KB entries."""

    def __init__(self) -> None:
        self._db: dict[str, ConditionKB] = _build_kb()

    def get(self, key: str) -> ConditionKB:
        if key not in self._db:
            raise KeyError(f"Unknown condition key: {key}")
        return self._db[key]

    def list_all(self) -> list[ConditionKB]:
        return list(self._db.values())

    def keys(self) -> list[str]:
        return list(self._db.keys())


def _build_kb() -> dict[str, ConditionKB]:
    kb: dict[str, ConditionKB] = {}

    # ── Category A — Inflammatory ────────────────────────

    kb["atopic_dermatitis"] = ConditionKB(
        key="atopic_dermatitis",
        display_name="Atopic Dermatitis (Eczema)",
        category="inflammatory",
        is_contagious=False,
        is_curable=False,
        contagion_guidance=None,
        what_it_is="Atopic dermatitis is a chronic inflammatory skin condition that causes dry, itchy, and inflamed patches of skin. It tends to flare periodically and is closely linked to a weakened skin barrier and immune system overactivity.",
        what_causes_it="It is caused by a combination of genetic factors (filaggrin gene mutations affecting the skin barrier), immune system dysfunction, and environmental triggers.",
        typical_duration="Chronic — managed, not cured. Many children outgrow it, but it can persist into adulthood.",
        common_misconceptions=[
            "Myth: Eczema is contagious — Fact: It is not contagious at all; it is an immune-mediated condition.",
            "Myth: Eczema is caused by poor hygiene — Fact: Over-washing actually worsens eczema by stripping the skin barrier.",
            "Myth: Steroids are the only treatment — Fact: Moisturizers, barrier repair, and trigger avoidance are the foundation of management.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Gentle Cleanser", recommendation="Use a fragrance-free cream cleanser with pH 5.5–6.0. Avoid foaming cleansers entirely.", fallback_why="A low-pH, fragrance-free cleanser protects your weakened skin barrier instead of stripping it further.", is_otc_available=True),
            KBStep(phase="daily_am", category="Ceramide Moisturizer", recommendation="Apply a ceramide-rich moisturizer (containing ceramides NP, AP, or EOP) immediately after cleansing while skin is still slightly damp.", fallback_why="Ceramides restore the lipid barrier that is deficient in eczema-prone skin, locking in moisture.", is_otc_available=True),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply SPF 30+ mineral sunscreen (zinc oxide or titanium dioxide), fragrance-free. Chemical sunscreens may irritate eczema-prone skin.", fallback_why="Mineral SPF protects without the chemical irritants that can trigger eczema flares.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Cleanser", recommendation="Use the same gentle cream cleanser as morning. Double cleansing is unnecessary and may irritate.", fallback_why="Consistent gentle cleansing prevents barrier disruption while removing daily buildup.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Treatment", recommendation="Apply prescription topical (tacrolimus or corticosteroid) if prescribed, OR OTC hydrocortisone 1% cream to active flare areas only.", fallback_why="Targeted anti-inflammatory treatment calms active flares while the barrier-repair routine works.", is_otc_available=True, avoid_if=["long_term_steroid_use"]),
            KBStep(phase="daily_pm", category="Occlusive Emollient", recommendation="Seal everything with a thick emollient — petrolatum (Vaseline) or shea butter as the final occlusive layer.", fallback_why="An occlusive final layer prevents transepidermal water loss, which is elevated in eczema skin.", is_otc_available=True),
        ],
        optional_steps=[
            KBStep(phase="weekly", category="Wet Wrap Therapy", recommendation="For severe flares: apply moisturizer, cover with damp cotton wraps, then dry wraps on top. Leave for 2–4 hours or overnight.", fallback_why="Wet wraps dramatically increase moisturizer absorption and calm severe inflammation.", is_otc_available=True, score=1, score_modifiers={"severe": 3, "chronic_recurring": 1}),
            KBStep(phase="weekly", category="Colloidal Oatmeal Soak", recommendation="Soak in lukewarm bath with colloidal oatmeal for 15–20 minutes. Pat dry gently, moisturize immediately.", fallback_why="Colloidal oatmeal has natural anti-inflammatory and skin-soothing properties.", is_otc_available=True, score=1, score_modifiers={"chronic_recurring": 2, "moderate": 1}),
        ],
        seek_ingredients=[
            ("Ceramides (NP/AP/EOP complex)", "Restore the deficient lipid barrier in eczema skin"),
            ("Colloidal oatmeal", "Natural anti-inflammatory that soothes itching and redness"),
            ("Panthenol (Pro-Vitamin B5)", "Supports skin barrier repair and hydration"),
            ("Squalane", "Lightweight emollient that mimics natural skin oils without clogging pores"),
            ("Glycerin (≥5%)", "Humectant that draws and retains moisture in the skin"),
            ("Niacinamide (≤4%)", "Strengthens the skin barrier and reduces inflammation at low concentrations"),
        ],
        avoid_ingredients=[
            ("Fragrances (synthetic and natural)", "Top allergen and irritant for eczema-prone skin"),
            ("SLS/SLES (sodium lauryl/laureth sulfate)", "Harsh surfactants that strip the skin barrier"),
            ("Alcohol denat. (denatured alcohol)", "Dries and irritates compromised skin"),
            ("AHAs (glycolic acid, lactic acid)", "Chemical exfoliants are too harsh for eczema-compromised skin"),
            ("BHAs (salicylic acid)", "Can cause stinging and further barrier damage on eczema skin"),
            ("Retinoids (retinol, tretinoin)", "Too irritating for eczema skin — causes peeling and inflammation"),
            ("Essential oils (tea tree, lavender, etc.)", "Common sensitizers that trigger eczema flares"),
            ("Methylisothiazolinone (MI)", "Preservative and potent contact allergen"),
        ],
        triggers=[
            ("Soap and detergents", "Use fragrance-free, sulfate-free cleansers. Wear gloves for dishwashing.", "severe"),
            ("Stress", "Practice stress management — stress hormones directly trigger immune flares.", "moderate"),
            ("Heat and sweat", "Keep cool, wear breathable fabrics, shower after sweating.", "moderate"),
            ("Dust mites", "Use allergen-proof bedding covers, wash bedding weekly in hot water.", "moderate"),
            ("Pet dander", "Keep pets out of the bedroom, wash hands after contact.", "mild"),
        ],
        red_flags=[
            ("Oozing or crusting with yellow discharge", "see_doctor_today", "Possible secondary bacterial infection requiring antibiotics — see a doctor today."),
            ("Spreading redness with warmth and swelling", "see_doctor_today", "Possible cellulitis — seek medical attention immediately."),
            ("No improvement after 2 weeks of consistent care", "within_1_week", "Schedule a dermatologist appointment to discuss prescription options."),
        ],
        referral_recommended=True,
        referral_urgency="soon",
        when_to_see_doctor="See a dermatologist if your eczema does not improve with OTC moisturizers and hydrocortisone within 2 weeks, if flares are frequent or severe, or if you notice signs of skin infection. Prescription options such as tacrolimus, pimecrolimus, and dupilumab can provide significant relief.",
        base_disclaimer="Prescription topicals such as tacrolimus (Protopic) and pimecrolimus (Elidel) are available for eczema management. Discuss these options with your dermatologist.",
        weather_notes={
            "cold": "Cold, dry air worsens eczema. Apply extra emollient before going outdoors and use a humidifier indoors.",
            "dry_air": "Low humidity increases transepidermal water loss. Layer moisturizer + occlusive and consider a bedroom humidifier.",
            "humid": "Humidity can help eczema, but sweat can trigger flares. Stay cool and rinse sweat promptly.",
            "high_uv": "Use mineral SPF only — chemical sunscreens contain irritants for eczema skin.",
        },
    )

    kb["contact_dermatitis"] = ConditionKB(
        key="contact_dermatitis",
        display_name="Contact Dermatitis",
        category="inflammatory",
        is_contagious=False,
        is_curable=True,
        contagion_guidance=None,
        what_it_is="Contact dermatitis is an inflammatory skin reaction that occurs when the skin comes into direct contact with an irritant or allergen. It presents as a red, itchy, and sometimes blistering rash localized to the area of contact.",
        what_causes_it="It is caused either by direct chemical irritation (irritant contact dermatitis) or by an allergic immune reaction to a specific substance (allergic contact dermatitis).",
        typical_duration="Acute — resolves within 2–4 weeks once the trigger is identified and removed.",
        common_misconceptions=[
            "Myth: Contact dermatitis means you have sensitive skin — Fact: Anyone can develop it from exposure to the right irritant or allergen.",
            "Myth: It only happens with harsh chemicals — Fact: Common culprits include nickel jewelry, fragrances, preservatives, and even plants like poison ivy.",
            "Myth: If a product didn't bother you before, it can't cause contact dermatitis — Fact: Allergic sensitization can develop after months or years of prior uneventful use.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Trigger Removal", recommendation="Identify and completely remove the triggering substance before starting any skincare. Wash the area with cool water to remove residue.", fallback_why="Removing the trigger is the single most important step — no treatment works if exposure continues.", is_otc_available=True),
            KBStep(phase="daily_am", category="Gentle Rinse", recommendation="Rinse affected area with cool water only. Avoid cleansers on active rash areas.", fallback_why="Cool water soothes inflamed skin without adding potentially irritating chemicals.", is_otc_available=True),
            KBStep(phase="daily_am", category="Barrier Cream", recommendation="Apply a fragrance-free barrier cream or ointment to protect healing skin.", fallback_why="A barrier cream shields the damaged skin from further exposure to environmental irritants.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Rinse", recommendation="Rinse affected area gently with cool water.", fallback_why="Gentle rinsing removes accumulated irritants from the day without disrupting healing.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Treatment", recommendation="Apply OTC hydrocortisone 1% cream or prescribed topical steroid to inflamed areas. Follow with a thin layer of petrolatum.", fallback_why="Hydrocortisone reduces the inflammatory reaction while petrolatum locks in moisture.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Occlusive", recommendation="Seal with plain petrolatum as the final step.", fallback_why="Petrolatum creates a protective seal that supports skin healing overnight.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Zinc oxide", "Soothing, protective barrier ingredient"),
            ("Colloidal oatmeal", "Anti-inflammatory and anti-itch properties"),
            ("Aloe vera (pure)", "Cooling and soothing for irritated skin"),
            ("Centella asiatica", "Promotes wound healing and reduces inflammation"),
            ("Panthenol", "Supports skin repair and hydration"),
        ],
        avoid_ingredients=[
            ("Fragrances (all types)", "Top allergen causing contact dermatitis recurrence"),
            ("Preservatives (parabens, MI)", "Common contact allergens"),
            ("Nickel-containing products", "One of the most common contact allergens worldwide"),
            ("Latex", "Common allergen in sensitive individuals"),
            ("The specific identified allergen", "Once identified via patch testing, avoid completely and permanently"),
        ],
        triggers=[
            ("Specific products (cosmetics, detergents)", "Identify through patch testing and eliminate. Read ingredient labels carefully.", "severe"),
            ("Specific metals (nickel, cobalt)", "Wear hypoallergenic jewelry. Choose titanium or surgical steel.", "moderate"),
            ("Plants (poison ivy, poison oak)", "Learn to identify and avoid. Wash exposed skin within 30 minutes.", "moderate"),
        ],
        red_flags=[
            ("Blistering or vesicles forming", "within_1_week", "See a dermatologist for potential prescription-strength steroid."),
            ("Widespread rash beyond contact area", "see_doctor_today", "May indicate systemic allergic reaction — seek medical attention."),
            ("Difficulty breathing or throat tightness", "see_doctor_today", "Anaphylaxis — call emergency services immediately (911/112)."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a dermatologist for patch testing to identify the specific allergen causing your reaction. This is especially important for recurrent episodes. Patch testing is the gold standard for identifying contact allergens.",
        base_disclaimer="Patch testing by a dermatologist is recommended to identify specific allergens. Avoid suspected triggers until professional evaluation.",
        weather_notes={
            "humid": "Sweat can carry allergens to new skin areas. Rinse skin after sweating.",
            "cold": "Dry, cracked skin is more vulnerable to irritant penetration. Moisturize well.",
            "dry_air": "Low humidity weakens the skin barrier, making irritant reactions more likely.",
        },
    )

    kb["rosacea"] = ConditionKB(
        key="rosacea",
        display_name="Rosacea",
        category="inflammatory",
        is_contagious=False,
        is_curable=False,
        contagion_guidance=None,
        what_it_is="Rosacea is a chronic inflammatory skin condition primarily affecting the central face, causing persistent redness, visible blood vessels, and sometimes papules and pustules. It tends to flare with specific triggers.",
        what_causes_it="The exact cause is not fully understood but involves neurovascular dysregulation, immune system overactivity, and Demodex mite overgrowth. Genetics play a significant role.",
        typical_duration="Chronic — managed, not cured. Flares are episodic and can be minimized with trigger avoidance and treatment.",
        common_misconceptions=[
            "Myth: Rosacea is caused by alcohol abuse — Fact: While alcohol can trigger flares, rosacea is a neurovascular condition unrelated to alcohol consumption habits.",
            "Myth: Rosacea is just blushing — Fact: It is a progressive medical condition that can worsen without treatment.",
            "Myth: You should exfoliate to reduce rosacea redness — Fact: Physical and chemical exfoliation worsens rosacea significantly.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Gentle Cleanser", recommendation="Use a gentle, low-pH (5.0–5.5) fragrance-free cleanser. Rinse with lukewarm (never hot) water. Pat dry — never rub.", fallback_why="Low-pH cleansing avoids disrupting the acid mantle, which is critical for rosacea-prone skin.", is_otc_available=True),
            KBStep(phase="daily_am", category="Treatment Serum", recommendation="Apply azelaic acid 10–15% serum (Tier 1 rosacea treatment) OR niacinamide serum ≤5%. Azelaic acid is preferred if tolerated.", fallback_why="Azelaic acid is clinically proven to reduce rosacea redness, papules, and pustules.", is_otc_available=True),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply fragrance-free mineral SPF 50+ (zinc oxide/titanium dioxide). Chemical sunscreens contain irritants. Reapply every 2 hours outdoors.", fallback_why="UV exposure is one of the top rosacea triggers. Mineral SPF provides broad protection without chemical irritation.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Cleanser", recommendation="Same gentle cleanser as morning. Lukewarm water only.", fallback_why="Consistent gentle cleansing removes the day's buildup without triggering a flare.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Treatment", recommendation="Apply azelaic acid serum or prescribed metronidazole gel/cream. Allow to absorb fully.", fallback_why="Evening treatment allows active ingredients to work overnight when the skin barrier is most permeable.", is_otc_available=False),
            KBStep(phase="daily_pm", category="Moisturizer", recommendation="Apply a fragrance-free, lightweight moisturizer. Avoid heavy occlusives which can trap heat.", fallback_why="Light moisture without heavy occlusion supports the skin barrier without causing flushing.", is_otc_available=True),
        ],
        optional_steps=[
            KBStep(phase="daily_am", category="Green Tea Serum", recommendation="Apply a green tea extract (EGCG) serum before SPF for added anti-inflammatory protection.", fallback_why="Green tea EGCG has potent anti-inflammatory and anti-redness properties beneficial for rosacea.", is_otc_available=True, score=1, score_modifiers={"face": 2}),
            KBStep(phase="ongoing_management", category="Thermal Water Mist", recommendation="Carry a thermal spring water mist to cool skin during flushing episodes. Store in refrigerator for extra cooling.", fallback_why="Thermal water mist provides instant cooling to interrupt flushing episodes.", is_otc_available=True, score=1, score_modifiers={"heat": 2}),
            KBStep(phase="ongoing_management", category="LED Therapy Note", recommendation="Consider at-home LED red light therapy (630nm wavelength) for 10 minutes, 3x/week. Reduces inflammation and promotes healing.", fallback_why="Red LED light therapy has clinical evidence for reducing rosacea inflammation.", is_otc_available=True, score=1, score_modifiers={"chronic_recurring": 2}),
        ],
        seek_ingredients=[
            ("Azelaic acid (10–15%)", "First-line rosacea treatment — reduces redness, papules, and pustules"),
            ("Niacinamide (≤5%)", "Anti-inflammatory that strengthens the skin barrier"),
            ("Centella asiatica / madecassoside", "Calms inflammation and supports skin repair"),
            ("Green tea EGCG", "Potent antioxidant and anti-inflammatory for redness"),
            ("Zinc oxide (in SPF)", "Gentle mineral sun protection with soothing properties"),
            ("Madecassoside", "Centella-derived compound that calms rosacea redness"),
        ],
        avoid_ingredients=[
            ("Retinoids (all forms — retinol, tretinoin, adapalene)", "Cause peeling, irritation, and worsening of rosacea"),
            ("AHAs (glycolic acid, lactic acid)", "Too irritating for rosacea-compromised skin"),
            ("BHAs (salicylic acid)", "Can trigger stinging and flushing"),
            ("Alcohol-based toners", "Dry and irritate rosacea skin, triggering flares"),
            ("Physical scrubs", "Mechanical irritation worsens rosacea dramatically"),
            ("Fragrance (any type)", "Triggers flushing and irritation"),
            ("Menthol and peppermint", "Vasodilators that trigger flushing"),
            ("Spicy skincare ingredients (capsaicin)", "Triggers intense flushing"),
            ("High-heat tools (steamers, hot towels)", "Heat is a primary rosacea trigger"),
        ],
        triggers=[
            ("Heat and hot environments", "Stay cool, use fans, avoid hot showers. Carry cooling mist.", "severe"),
            ("Sun exposure", "Wear SPF 50+ daily, seek shade, wear wide-brim hat.", "severe"),
            ("Spicy food", "Reduce or eliminate spicy foods if they trigger flushing.", "moderate"),
            ("Alcohol consumption", "Red wine is the most common trigger. Consider reducing intake.", "moderate"),
            ("Stress", "Practice stress management techniques to reduce flare frequency.", "moderate"),
            ("Wind exposure", "Protect face with a scarf in windy conditions.", "mild"),
        ],
        red_flags=[
            ("Eye involvement (redness, dryness, gritty feeling)", "see_doctor_today", "Possible ocular rosacea — requires ophthalmological evaluation."),
            ("Thickening skin on nose", "within_1_month", "Possible rhinophyma — early treatment can prevent progression."),
            ("No improvement on azelaic acid after 8 weeks", "within_1_month", "See a dermatologist for prescription alternatives."),
        ],
        referral_recommended=True,
        referral_urgency="soon",
        when_to_see_doctor="See a dermatologist if OTC azelaic acid and trigger avoidance do not control your symptoms within 8 weeks. Prescription options including ivermectin cream (Soolantra), brimonidine gel (Mirvaso), and oral low-dose doxycycline are highly effective.",
        base_disclaimer="Prescription treatments including ivermectin cream and brimonidine gel are available for rosacea. Never use retinoids, physical exfoliants, or any product with 'acid' in the name except azelaic acid.",
        weather_notes={
            "high_uv": "UV is a major rosacea trigger — reapply SPF every 2 hours and wear a wide-brim hat.",
            "humid": "Humidity can trigger flushing — carry a thermal water mist to cool skin.",
            "cold": "Cold wind can trigger rosacea flares — protect face with a soft scarf.",
        },
    )

    kb["seborrheic_dermatitis"] = ConditionKB(
        key="seborrheic_dermatitis",
        display_name="Seborrheic Dermatitis",
        category="inflammatory",
        is_contagious=False,
        is_curable=False,
        contagion_guidance=None,
        what_it_is="Seborrheic dermatitis is a chronic inflammatory condition that causes flaky, greasy scales and redness in areas rich in oil glands, particularly the scalp, face (eyebrows, nasolabial folds), and chest.",
        what_causes_it="It is caused by an inflammatory reaction to Malassezia yeast that naturally lives on oily skin. Factors include excess sebum production, immune response, and stress.",
        typical_duration="Chronic — managed, not cured. Flares are common during stress or seasonal changes.",
        common_misconceptions=[
            "Myth: Dandruff is just dry scalp — Fact: Seborrheic dermatitis is a yeast-driven inflammatory condition, not simple dryness.",
            "Myth: Washing your hair more often causes it — Fact: Regular washing with antifungal shampoo actually helps control it.",
            "Myth: It's caused by poor hygiene — Fact: It's caused by Malassezia yeast and individual immune response.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Antifungal Cleanser", recommendation="Use a zinc pyrithione 1% or ketoconazole 2% cleanser. Leave on skin/scalp for 2 minutes before rinsing.", fallback_why="Antifungal cleansers target the Malassezia yeast that drives seborrheic dermatitis.", is_otc_available=True),
            KBStep(phase="daily_am", category="Light Moisturizer", recommendation="Apply a light, non-comedogenic, oil-free moisturizer. Avoid heavy creams that feed Malassezia.", fallback_why="Light moisture prevents dryness without providing the oils that Malassezia yeast feeds on.", is_otc_available=True),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply SPF if seborrheic dermatitis is on the face. Use a non-comedogenic, oil-free formula.", fallback_why="Sun protection prevents post-inflammatory discoloration from healed flare sites.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Antifungal Cleanser", recommendation="Same antifungal cleanser as morning. For scalp: alternate with selenium sulfide 2.5% or ciclopirox as prescribed.", fallback_why="Evening antifungal cleansing reduces overnight Malassezia proliferation.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Treatment", recommendation="Apply selenium sulfide 2.5% lotion or ciclopirox cream (if prescribed) to affected areas. For scalp, use coal tar or ketoconazole shampoo.", fallback_why="Targeted antifungal treatment addresses the underlying cause of flaking and redness.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Lightweight Moisturizer", recommendation="Apply a lightweight, oil-free moisturizer to treated areas.", fallback_why="Light moisturizing prevents the over-drying that antifungal treatments can cause.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Zinc pyrithione", "Antifungal and antibacterial that targets Malassezia"),
            ("Ketoconazole", "Potent antifungal effective against Malassezia yeast"),
            ("Selenium sulfide", "Antifungal that reduces scalp flaking"),
            ("Salicylic acid (≤2%)", "Helps remove scales and flakes"),
            ("Coal tar", "Anti-inflammatory and antifungal for scalp involvement"),
            ("Tea tree oil (≤5%, diluted)", "Natural antifungal with mild anti-inflammatory properties"),
        ],
        avoid_ingredients=[
            ("Heavy occlusive oils (coconut, olive)", "Feed Malassezia yeast and worsen the condition"),
            ("Heavy pomades and hair oils", "Create an environment that promotes Malassezia growth"),
            ("Sugary or yeast-heavy diet (note)", "May contribute to yeast overgrowth systemically"),
        ],
        triggers=[
            ("Stress", "Practice stress management — cortisol increases sebum production and yeast growth.", "severe"),
            ("Oily scalp and skin", "Wash regularly with antifungal cleanser. Avoid skipping washes.", "moderate"),
            ("Hormonal changes", "Flares may worsen during hormonal shifts. Maintain antifungal routine.", "moderate"),
            ("Diet high in sugar/yeast", "Consider reducing sugar and yeast-heavy foods during flares.", "mild"),
        ],
        red_flags=[
            ("Spreading beyond typical areas (scalp, face, chest)", "within_1_week", "See a dermatologist to confirm diagnosis and rule out other conditions."),
            ("Hair loss in affected areas", "within_1_week", "Hair loss may indicate inflammation is affecting follicles — needs evaluation."),
            ("No response to zinc pyrithione after 4 weeks", "within_1_week", "Schedule a dermatologist visit for prescription antifungal options."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a dermatologist if OTC antifungal shampoos and cleansers do not control your symptoms within 4 weeks, or if seborrheic dermatitis spreads to new areas.",
        base_disclaimer="Seborrheic dermatitis is a chronic condition that requires ongoing management. Over-the-counter antifungal treatments are effective for most cases.",
        weather_notes={
            "cold": "Cold, dry weather can worsen flaking. Maintain antifungal routine and use light moisturizer.",
            "humid": "High humidity increases oil production which feeds Malassezia. Cleanse more frequently.",
            "dry_air": "Dry air can cause excess flaking. Use a humidifier and light moisturizer.",
        },
    )

    # Continued in _build_kb_part2
    _build_kb_part2(kb)
    _build_kb_part3(kb)
    _build_kb_part4(kb)
    return kb


def _build_kb_part2(kb: dict[str, ConditionKB]) -> None:
    """Conditions: psoriasis, lichen_planus, perioral_dermatitis, fungal_acne"""

    kb["psoriasis"] = ConditionKB(
        key="psoriasis",
        display_name="Psoriasis",
        category="inflammatory",
        is_contagious=False,
        is_curable=False,
        contagion_guidance=None,
        what_it_is="Psoriasis is a chronic autoimmune condition that causes rapid skin cell turnover, resulting in thick, scaly plaques with silvery-white buildup. It most commonly appears on the elbows, knees, scalp, and lower back.",
        what_causes_it="It is caused by an overactive immune system that accelerates skin cell production. Genetic predisposition, immune triggers, and environmental factors all contribute.",
        typical_duration="Chronic — managed, not cured. Flares and remissions are common throughout life.",
        common_misconceptions=[
            "Myth: Psoriasis is contagious — Fact: It is an autoimmune condition and cannot be transmitted through touch or contact.",
            "Myth: Psoriasis is just dry skin — Fact: It is a systemic autoimmune disease that can also affect joints.",
            "Myth: Psoriasis is caused by poor hygiene — Fact: It is driven by genetics and immune dysfunction, not cleanliness.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Plaque Protection", recommendation="Do not pick, scratch, or remove plaques — this triggers the Koebner phenomenon, causing new plaques to form at injury sites.", fallback_why="Trauma to psoriatic skin triggers new plaque formation (Koebner phenomenon), making the condition worse.", is_otc_available=True),
            KBStep(phase="daily_am", category="Gentle Cleanser", recommendation="Use a gentle, sulfate-free cleanser. Avoid scrubbing plaques.", fallback_why="Sulfate-free cleansing avoids irritating plaques while keeping skin clean.", is_otc_available=True),
            KBStep(phase="daily_am", category="Scale Treatment", recommendation="Apply salicylic acid 2% treatment to scaly areas for scale removal. This is an OTC keratolytic.", fallback_why="Salicylic acid softens and removes scales so that treatments beneath can penetrate effectively.", is_otc_available=True),
            KBStep(phase="daily_am", category="Ceramide Cream", recommendation="Apply a thick ceramide cream to all affected and surrounding areas.", fallback_why="Ceramides support the compromised skin barrier in psoriasis, reducing transepidermal water loss.", is_otc_available=True),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply SPF 50+ — psoriasis skin is photosensitive on some medications. Use mineral SPF on plaques.", fallback_why="Sun protection is critical as many psoriasis treatments increase photosensitivity.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Cleanser", recommendation="Same gentle sulfate-free cleanser. Be especially gentle around plaques.", fallback_why="Evening cleansing removes the day's buildup without disrupting healing plaques.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Treatment", recommendation="Apply coal tar 5% ointment (OTC) OR prescribed topical (corticosteroid, calcipotriol, or combination). Follow label directions.", fallback_why="Coal tar slows skin cell production and reduces inflammation, scaling, and itching.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Urea Cream", recommendation="Apply urea 10–20% cream to thick plaques. This softens and thins them over time.", fallback_why="Urea is a powerful keratolytic that penetrates and softens thick psoriatic plaques.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Occlusive Emollient", recommendation="Seal with a thick emollient (shea butter, petrolatum) as the final layer.", fallback_why="A thick occlusive layer locks in moisture and treatment actives overnight.", is_otc_available=True),
            KBStep(phase="weekly", category="Dead Sea Salt Bath", recommendation="Soak in a lukewarm bath with Dead Sea salt for 15 minutes. Pat dry and moisturize immediately.", fallback_why="Dead Sea minerals have anti-inflammatory properties that reduce psoriasis plaques.", is_otc_available=True),
        ],
        optional_steps=[
            KBStep(phase="ongoing_management", category="Phototherapy Reference", recommendation="Ask your dermatologist about narrowband UVB phototherapy — it is one of the most effective treatments for moderate-to-severe psoriasis.", fallback_why="Narrowband UVB phototherapy is clinically proven to clear psoriasis plaques effectively.", is_otc_available=False, score=1, score_modifiers={"severe": 3}),
        ],
        seek_ingredients=[
            ("Salicylic acid (≤2%)", "Keratolytic that removes psoriatic scales"),
            ("Coal tar", "Slows skin cell turnover and reduces inflammation"),
            ("Urea (10–20%)", "Softens and thins thick plaques"),
            ("Ceramides", "Restore impaired skin barrier"),
            ("Aloe vera", "Soothing and anti-inflammatory for plaques"),
            ("Shea butter", "Natural emollient that softens plaques"),
            ("Dead Sea minerals", "Anti-inflammatory properties for psoriasis"),
        ],
        avoid_ingredients=[
            ("AHAs at >5% concentration", "Too irritating for psoriatic skin"),
            ("Harsh physical scrubs", "Cause Koebner phenomenon — new plaques at injury sites"),
            ("Hot water", "Triggers psoriasis flares and increases itching"),
            ("Fragrances", "Irritate compromised psoriatic skin"),
            ("Alcohol-based products", "Dry and irritate plaques"),
            ("Topical NSAIDs", "Can paradoxically worsen psoriasis"),
        ],
        triggers=[
            ("Stress", "Practice stress management — stress is the most common psoriasis trigger.", "severe"),
            ("Streptococcal infection", "Get throat infections treated promptly — strep triggers guttate psoriasis.", "severe"),
            ("Skin injury (cuts, scrapes, sunburn)", "Protect skin from trauma — Koebner phenomenon causes plaques at injury sites.", "moderate"),
            ("Alcohol consumption", "Alcohol worsens psoriasis and interferes with treatments. Reduce intake.", "moderate"),
            ("Certain medications (lithium, beta blockers)", "Discuss with your doctor — some medications can trigger or worsen psoriasis.", "moderate"),
        ],
        red_flags=[
            ("Full-body redness and skin shedding", "see_doctor_today", "Possible erythrodermic psoriasis — this is a medical emergency. Seek immediate care."),
            ("Pus-filled blisters on skin", "see_doctor_today", "Possible pustular psoriasis — requires urgent medical evaluation."),
            ("Joint pain, stiffness, or swelling starting", "within_1_week", "Possible psoriatic arthritis — early treatment prevents joint damage."),
        ],
        referral_recommended=True,
        referral_urgency="soon",
        when_to_see_doctor="See a dermatologist if psoriasis covers more than 5% of your body, if OTC treatments do not provide relief within 4 weeks, or if you develop joint symptoms. Biologics and systemic treatments can provide dramatic improvement.",
        base_disclaimer="Psoriasis is a systemic autoimmune condition. Biologics, systemic medications, and phototherapy are available for moderate-to-severe cases.",
        weather_notes={
            "cold": "Cold weather typically worsens psoriasis. Keep skin well-moisturized and use a humidifier.",
            "dry_air": "Dry air increases plaque thickness and itching. Apply extra emollient.",
            "high_uv": "Moderate sun exposure can help psoriasis, but sunburn triggers flares. Use SPF on unaffected skin.",
            "humid": "Humidity generally helps psoriasis by keeping skin moist. Maintain routine.",
        },
    )

    kb["lichen_planus"] = ConditionKB(
        key="lichen_planus",
        display_name="Lichen Planus",
        category="inflammatory",
        is_contagious=False,
        is_curable=True,
        contagion_guidance=None,
        what_it_is="Lichen planus is an inflammatory condition that produces purple, flat-topped, itchy bumps on the skin. It can also affect the mouth, nails, and scalp. The exact cause is unknown but involves an autoimmune reaction.",
        what_causes_it="The immune system mistakenly attacks skin and mucous membrane cells. Triggers can include hepatitis C, certain medications, and dental materials, though often no cause is identified.",
        typical_duration="Usually self-resolves in 1–2 years, but oral and nail forms may persist longer. Recurrence is possible.",
        common_misconceptions=[
            "Myth: Lichen planus is contagious — Fact: It is an immune-mediated condition and cannot spread to others.",
            "Myth: OTC creams can cure lichen planus — Fact: Most cases require prescription corticosteroids for effective management.",
            "Myth: It only affects the skin — Fact: It can also involve the mouth, genitals, nails, and scalp.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Dermatologist Visit", recommendation="See a dermatologist — most OTC treatments are ineffective for lichen planus. Prescription management is the standard of care.", fallback_why="Lichen planus requires prescription corticosteroids or immunomodulators that OTC products cannot replace.", is_otc_available=False),
            KBStep(phase="daily_am", category="Gentle Cleanser", recommendation="Use a fragrance-free gentle cleanser. Avoid any physical or chemical exfoliation.", fallback_why="Gentle cleansing avoids irritating the inflammatory lesions.", is_otc_available=True),
            KBStep(phase="daily_am", category="Soothing Moisturizer", recommendation="Apply a minimal soothing moisturizer with ceramides or squalane. Less is more — avoid layering actives.", fallback_why="Light, barrier-supportive moisturizing calms irritation without interfering with prescription treatments.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Cleanser", recommendation="Same gentle fragrance-free cleanser.", fallback_why="Consistent gentle cleansing prevents additional irritation.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Treatment", recommendation="Apply prescribed topical corticosteroid (if available) OR calamine lotion for itch relief.", fallback_why="Topical corticosteroids suppress the immune reaction driving lichen planus.", is_otc_available=False),
            KBStep(phase="daily_pm", category="Barrier Cream", recommendation="Apply a thick barrier cream (ceramide or squalane-based) as the final step.", fallback_why="A barrier cream protects healing skin and locks in prescribed treatments.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Ceramides", "Support skin barrier repair"),
            ("Squalane", "Gentle, non-irritating emollient"),
            ("Panthenol", "Soothes and supports skin healing"),
            ("Zinc oxide", "Calming and protective"),
            ("Calamine", "Relieves itching associated with lichen planus"),
            ("Oat extract", "Natural anti-itch and anti-inflammatory"),
        ],
        avoid_ingredients=[
            ("All exfoliating actives (AHAs/BHAs/PHAs/retinoids)", "Exfoliation worsens the inflammatory process"),
            ("L-ascorbic acid >5%", "Can irritate active lesions"),
            ("Fragrances", "Irritate already inflamed skin"),
            ("Mechanical irritation (scrubbing, rubbing)", "Triggers Koebner phenomenon in lichen planus"),
        ],
        triggers=[
            ("Stress", "Stress management helps reduce flare frequency and severity.", "moderate"),
            ("Certain medications", "Some medications trigger lichen planus — discuss all medications with your dermatologist.", "moderate"),
            ("Dental materials (amalgam)", "If oral lichen planus is present, discuss dental material testing.", "mild"),
        ],
        red_flags=[
            ("Oral involvement (white patches, sores in mouth)", "within_1_week", "Oral lichen planus requires separate evaluation and treatment."),
            ("Genital involvement", "see_doctor_today", "Genital lichen planus needs urgent dermatological assessment."),
            ("No improvement after 4 weeks of treatment", "within_1_week", "Follow up with your dermatologist for treatment adjustment."),
        ],
        referral_recommended=True,
        referral_urgency="immediate",
        when_to_see_doctor="See a dermatologist as soon as possible. Lichen planus requires prescription management — no OTC treatment is adequate. Prescription corticosteroids, calcineurin inhibitors, or systemic immunosuppressants may be needed.",
        base_disclaimer="OTC management for lichen planus is supportive only. This condition requires professional dermatological evaluation and prescription treatment.",
        weather_notes={
            "high_uv": "Protect affected areas from sun exposure to prevent post-inflammatory discoloration.",
            "dry_air": "Keep skin well-moisturized to reduce irritation and itching.",
        },
    )

    kb["perioral_dermatitis"] = ConditionKB(
        key="perioral_dermatitis",
        display_name="Perioral Dermatitis",
        category="inflammatory",
        is_contagious=False,
        is_curable=True,
        contagion_guidance=None,
        what_it_is="Perioral dermatitis is a facial rash of small red bumps and mild peeling around the mouth, nose, and sometimes eyes. It is often mistakenly treated with topical steroids, which dramatically worsen the condition.",
        what_causes_it="The most common cause is topical steroid use on the face. Other causes include heavy moisturizers, fluorinated toothpaste, inhaled steroids, and hormonal factors.",
        typical_duration="Resolves in 6–12 weeks with correct treatment (stopping steroids + oral antibiotics). May temporarily worsen for 2–4 weeks when steroids are withdrawn.",
        common_misconceptions=[
            "Myth: Moisturizing more will help perioral dermatitis — Fact: Heavy moisturizers and occlusives WORSEN perioral dermatitis.",
            "Myth: Topical steroids treat perioral dermatitis — Fact: Topical steroids are the most common CAUSE and dramatically worsen it.",
            "Myth: It's caused by poor hygiene — Fact: Over-treating and over-moisturizing the skin are the main culprits.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="STOP Topical Steroids", recommendation="STOP using ALL topical steroids immediately if currently using any. This is the single most important action. Expect temporary worsening for 2–4 weeks — this is normal steroid withdrawal.", fallback_why="Topical steroids are the primary driver of perioral dermatitis. Stopping them is essential for healing, even though a temporary flare occurs.", is_otc_available=True),
            KBStep(phase="immediate", category="Stop Occlusives", recommendation="Stop all heavy moisturizers and occlusive products around the mouth area. Zero occlusion is the goal.", fallback_why="Occlusive products trap irritation and create the environment that drives perioral dermatitis.", is_otc_available=True),
            KBStep(phase="daily_am", category="Water Rinse Only", recommendation="Rinse face with plain water only — no cleanser for the first 2 weeks. After 2 weeks, a very gentle fragrance-free cleanser may be reintroduced.", fallback_why="Eliminating all products allows the skin to recover from product overload.", is_otc_available=True),
            KBStep(phase="daily_am", category="Minimal Treatment", recommendation="Apply a thin layer of azelaic acid 10% or niacinamide serum only. No moisturizer.", fallback_why="Azelaic acid has anti-inflammatory and antimicrobial properties that help perioral dermatitis without occluding the skin.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Water Rinse Only", recommendation="Same water-only rinse as morning.", fallback_why="Minimal intervention allows the damaged skin around the mouth to heal.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Minimal Treatment", recommendation="Apply a thin layer of niacinamide or azelaic acid. No moisturizer — zero occlusion around the mouth.", fallback_why="Evening treatment supports healing while maintaining the zero-occlusion approach.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Azelaic acid (10–15%)", "Anti-inflammatory and antimicrobial without occluding skin"),
            ("Niacinamide (≤5%)", "Calms inflammation without heavy texture"),
            ("Zinc oxide (physical SPF only)", "Non-irritating sun protection"),
            ("Sulfur-based treatments (if prescribed)", "Antimicrobial that helps perioral dermatitis"),
        ],
        avoid_ingredients=[
            ("ALL topical steroids (hydrocortisone, betamethasone, etc.)", "The most common cause of perioral dermatitis — NEVER use on face for this condition"),
            ("Heavy creams and moisturizers", "Occlusion worsens perioral dermatitis"),
            ("Occlusive moisturizers (petrolatum, lanolin near mouth)", "Trap the irritation that drives the condition"),
            ("Fluorinated toothpaste", "Fluoride can trigger and maintain perioral dermatitis"),
            ("Fragrance (near mouth area)", "Irritates the sensitive perioral skin"),
            ("Chemical SPF filters near mouth", "Can irritate perioral dermatitis — use zinc oxide only"),
        ],
        triggers=[
            ("Topical steroids", "STOP immediately — this is the most common cause and the most critical trigger.", "severe"),
            ("Heavy moisturizers and occlusives", "Eliminate all heavy products around the mouth.", "severe"),
            ("Hormonal changes", "Flares may occur with hormonal shifts. Maintain minimal routine.", "moderate"),
            ("Inhaled steroids (asthma inhalers)", "Discuss with your prescriber — use a spacer and rinse mouth after use.", "moderate"),
        ],
        red_flags=[
            ("Spreading above lip line to nose and cheeks", "within_1_week", "Expanding perioral dermatitis may need prescription oral antibiotics."),
            ("No improvement 4 weeks after stopping steroids", "within_1_week", "See a dermatologist for oral tetracycline-class antibiotic prescription."),
        ],
        referral_recommended=True,
        referral_urgency="soon",
        when_to_see_doctor="See a dermatologist if your perioral dermatitis does not improve within 4 weeks of stopping topical steroids. Oral tetracycline-class antibiotics (doxycycline, minocycline) are highly effective and may be necessary.",
        base_disclaimer="The most important step is stopping all topical steroids. Oral antibiotics from a dermatologist are the gold standard treatment for persistent perioral dermatitis.",
        weather_notes={
            "cold": "Cold wind can irritate perioral skin. Protect with a soft scarf but avoid heavy balms.",
            "dry_air": "Resist the urge to moisturize heavily — use minimal niacinamide-based hydration only.",
        },
    )

    kb["fungal_acne"] = ConditionKB(
        key="fungal_acne",
        display_name="Fungal Acne (Malassezia Folliculitis)",
        category="infectious",
        is_contagious=False,
        is_curable=True,
        contagion_guidance=None,
        what_it_is="Fungal acne is not actually acne — it is a yeast infection of the hair follicles caused by Malassezia yeast overgrowth. It presents as uniform, itchy bumps usually on the chest, back, and forehead.",
        what_causes_it="Caused by overgrowth of Malassezia yeast in hair follicles, triggered by excess sweat, humidity, occlusive products, and use of products containing ingredients that feed the yeast.",
        typical_duration="Responds to antifungal treatment within 2–4 weeks. Can recur if triggers are not managed.",
        common_misconceptions=[
            "Myth: Fungal acne is the same as regular acne — Fact: It is a completely different condition caused by yeast, not bacteria. Standard acne treatments don't work.",
            "Myth: Benzoyl peroxide treats fungal acne — Fact: Benzoyl peroxide targets bacteria, not Malassezia yeast.",
            "Myth: Coconut oil is good for fungal acne — Fact: Coconut oil fatty acids FEED Malassezia yeast and worsen it.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Antifungal Cleanser", recommendation="Use zinc pyrithione or selenium sulfide 2.5% body wash as a face/body cleanser on affected areas. Leave on for 2–3 minutes, then rinse.", fallback_why="Antifungal cleansers directly kill the Malassezia yeast driving the infection.", is_otc_available=True),
            KBStep(phase="daily_am", category="Lightweight Moisturizer", recommendation="Apply a lightweight, non-comedogenic, oil-free moisturizer. Check that it contains NO fatty acids or esters.", fallback_why="Oil-free moisture prevents dryness without feeding the Malassezia yeast.", is_otc_available=True),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Use an oil-free, Malassezia-safe SPF. Avoid sunscreens with fatty acid esters.", fallback_why="Sun protection prevents post-inflammatory marks without contributing to yeast overgrowth.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Antifungal Cleanser", recommendation="Same antifungal cleanser as morning.", fallback_why="Twice-daily antifungal cleansing maximizes yeast reduction.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Antifungal Treatment", recommendation="Apply ketoconazole 2% cream (if prescribed) or use dandruff shampoo as a face/body mask — leave on for 5 minutes, then rinse.", fallback_why="Leave-on antifungal treatment provides prolonged contact time to kill Malassezia.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Oil-Free Moisturizer", recommendation="Apply an oil-free gel moisturizer. Glycerin and hyaluronic acid are safe — avoid fatty acids.", fallback_why="Gel-based moisturizers hydrate without the fatty acids that Malassezia feeds on.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Zinc pyrithione", "Antifungal that targets Malassezia yeast"),
            ("Ketoconazole", "Potent antifungal for Malassezia"),
            ("Selenium sulfide", "Antifungal effective against fungal acne"),
            ("Capryloyl glycine", "Antimicrobial safe for Malassezia-prone skin"),
            ("Glycerin", "Humectant that does not feed Malassezia"),
            ("Hyaluronic acid", "Hydrator that is Malassezia-safe (no fatty acids)"),
        ],
        avoid_ingredients=[
            ("Fatty acid-rich oils (coconut, olive, sunflower, flaxseed)", "These are the primary food source for Malassezia yeast"),
            ("Esters (isopropyl myristate, isopropyl palmitate)", "Feed Malassezia and worsen fungal acne"),
            ("Fermented ingredients (galactomyces, saccharomyces)", "May promote yeast overgrowth"),
            ("Polysorbates (polysorbate 20, 60, 80)", "Esters that feed Malassezia"),
            ("Certain algae extracts", "Some algae contain fatty acids that feed Malassezia"),
        ],
        triggers=[
            ("Sweat", "Shower immediately after exercise. Don't sit in sweaty clothes.", "severe"),
            ("Humidity", "Use antifungal body wash preventively in humid conditions.", "severe"),
            ("Oil-based skincare products", "Switch to entirely oil-free, Malassezia-safe routine.", "severe"),
            ("Occlusive sunscreens", "Use oil-free, non-comedogenic SPF only.", "moderate"),
        ],
        red_flags=[
            ("Spreading to new body areas", "within_1_week", "See a dermatologist for prescription-strength antifungal."),
            ("No improvement with antifungal treatment after 4 weeks", "within_1_week", "Schedule a dermatologist visit — oral antifungals may be needed."),
            ("Fever with skin involvement", "see_doctor_today", "Seek medical attention — fever with skin infection needs evaluation."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a dermatologist if OTC antifungal treatments do not clear your fungal acne within 4 weeks. Prescription oral antifungals (fluconazole, itraconazole) can resolve severe cases quickly.",
        base_disclaimer="Fungal acne is DIFFERENT from bacterial acne. Standard acne treatments like benzoyl peroxide do not treat fungal acne. Antifungal treatment is required.",
        weather_notes={
            "humid": "High humidity promotes Malassezia growth. Cleanse with antifungal wash twice daily and change sweaty clothing.",
            "high_uv": "Use Malassezia-safe, oil-free SPF.",
        },
    )


def _build_kb_part3(kb: dict[str, ConditionKB]) -> None:
    """Conditions: ringworm, warts, molluscum, impetigo, cold_sores"""

    kb["ringworm"] = ConditionKB(
        key="ringworm",
        display_name="Ringworm (Tinea Corporis)",
        category="infectious",
        is_contagious=True,
        is_curable=True,
        contagion_guidance="Avoid skin-to-skin contact with the affected area. Wash clothing and bedding in hot water. Keep the area dry and covered. Do not share towels, clothing, or personal items.",
        what_it_is="Ringworm is a common fungal infection of the skin (not caused by a worm). It produces circular, red, scaly patches with a raised border that expand outward as the center clears.",
        what_causes_it="Caused by dermatophyte fungi (Trichophyton, Microsporum). Spread through direct skin contact, contaminated surfaces, or contact with infected animals.",
        typical_duration="Clears within 2–4 weeks with consistent antifungal treatment.",
        common_misconceptions=[
            "Myth: Ringworm is caused by a worm — Fact: It is a fungal infection, not a parasitic one.",
            "Myth: Only dirty people get ringworm — Fact: Anyone can get it through contact with infected people, animals, or surfaces.",
            "Myth: Cortisone cream treats ringworm — Fact: Cortisone suppresses symptoms but does NOT treat the infection, and can make it worse.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Hygiene Protocol", recommendation="Wash hands before and after touching the affected area. Do not share towels, clothing, or bedding. Launder contaminated items in hot water.", fallback_why="Strict hygiene prevents spreading ringworm to other body areas and to other people.", is_otc_available=True),
            KBStep(phase="daily_am", category="Antifungal Treatment", recommendation="Apply clotrimazole 1% or terbinafine 1% cream to the affected area and 2cm beyond the visible edge. Continue for 1 week after the rash clears.", fallback_why="OTC antifungal cream kills the dermatophyte fungus. Treating beyond the visible edge catches spreading spores.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Cleansing", recommendation="Gently wash the affected area with mild soap before applying antifungal treatment. Pat dry thoroughly.", fallback_why="Clean, dry skin allows antifungal medication to penetrate effectively.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Antifungal Treatment", recommendation="Apply the same antifungal cream (clotrimazole or terbinafine) as the morning application.", fallback_why="Twice-daily application maintains consistent antifungal coverage.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Clotrimazole 1%", "Broad-spectrum OTC antifungal effective against dermatophytes"),
            ("Terbinafine 1%", "Potent OTC antifungal — often clears ringworm faster than clotrimazole"),
            ("Miconazole 2%", "Alternative OTC antifungal option"),
            ("Benzoyl peroxide (for surrounding skin)", "Helps prevent secondary bacterial infection"),
        ],
        avoid_ingredients=[
            ("Cortisone/hydrocortisone cream alone", "Suppresses symptoms but does NOT treat the fungal infection — can worsen it"),
            ("Occlusive dressings over the infection", "Trap moisture and promote fungal growth"),
            ("Sharing personal items", "Spreads the infection to others"),
        ],
        triggers=[
            ("Close skin-to-skin contact", "Avoid contact sports until cleared. Cover affected area.", "severe"),
            ("Shared equipment and towels", "Use personal towels and disinfect shared equipment.", "severe"),
            ("Warm, moist environments", "Keep affected area cool and dry. Change sweaty clothing promptly.", "moderate"),
            ("Weakened immune system", "Maintain overall health. See a doctor if infections are recurrent.", "moderate"),
        ],
        red_flags=[
            ("Spreading despite 2 weeks of OTC treatment", "within_1_week", "See a dermatologist — prescription oral antifungal may be needed."),
            ("Scalp involvement in children", "see_doctor_today", "Tinea capitis (scalp ringworm) requires oral antifungals — topical treatments cannot penetrate hair follicles."),
            ("Deep, boggy, pus-filled area (kerion)", "see_doctor_today", "A kerion is a severe inflammatory reaction to ringworm requiring urgent medical treatment."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a doctor if ringworm does not clear within 4 weeks of OTC antifungal treatment, if it involves the scalp or beard area, or if a deep inflammatory reaction (kerion) develops.",
        base_disclaimer="Ringworm is contagious. Maintain strict hygiene and avoid sharing personal items until the infection has fully cleared.",
        weather_notes={
            "humid": "Humidity promotes fungal growth. Keep affected area dry and apply antifungal consistently.",
            "high_uv": "Sun exposure does not treat ringworm. Protect healing skin from sun damage.",
        },
    )

    kb["warts"] = ConditionKB(
        key="warts",
        display_name="Common Warts (Verruca Vulgaris)",
        category="infectious",
        is_contagious=True,
        is_curable=True,
        contagion_guidance="Avoid direct contact with warts. Do not share shoes in public areas. Keep warts covered with a bandage. Do not bite nails if you have periungual warts.",
        what_it_is="Common warts are rough, raised bumps on the skin caused by human papillomavirus (HPV) infection of the top layer of skin. They are harmless but can be cosmetically bothersome and spread.",
        what_causes_it="Caused by HPV (human papillomavirus) entering through tiny cuts or breaks in the skin. The virus stimulates rapid growth of cells on the outer layer of skin.",
        typical_duration="Most warts resolve spontaneously in 1–2 years. Treatment speeds resolution to weeks or months.",
        common_misconceptions=[
            "Myth: Toads cause warts — Fact: Warts are caused by HPV, not by touching animals.",
            "Myth: Warts have roots — Fact: Warts only grow in the top layer of skin (epidermis) and do not have roots.",
            "Myth: Cutting off a wart removes it permanently — Fact: Cutting can spread the virus and cause new warts.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Wart Treatment", recommendation="Soak the wart in warm water for 5 minutes. Gently file dead skin with a disposable emery board. Apply salicylic acid 17–26% solution or patch to the wart only — protect surrounding skin with petroleum jelly.", fallback_why="Soaking softens the wart tissue, filing removes dead layers, and salicylic acid chemically dissolves the wart layer by layer.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Wart Treatment", recommendation="Repeat: soak → file → salicylic acid application. Cover with a waterproof bandage overnight.", fallback_why="Twice-daily treatment with overnight occlusion accelerates wart clearance.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Salicylic acid 17–26%", "Gold standard OTC wart treatment — dissolves wart tissue"),
            ("Cryotherapy (clinic-applied)", "Liquid nitrogen freezing — effective for resistant warts"),
            ("Duct tape occlusion", "Low-evidence but low-risk complementary approach"),
        ],
        avoid_ingredients=[
            ("Cutting or shaving warts", "Spreads the virus to new areas"),
            ("Biting or picking nails with periungual warts", "Spreads warts to lips and other fingers"),
        ],
        triggers=[
            ("Skin breaks and cuts", "Keep skin intact. Avoid biting nails.", "moderate"),
            ("Walking barefoot in public areas", "Wear shoes in locker rooms, pools, and showers.", "moderate"),
            ("Weakened immune system", "Warts are more common and persistent with immune suppression.", "moderate"),
        ],
        red_flags=[
            ("Wart on the face", "within_1_month", "Salicylic acid risks scarring on facial skin — see a dermatologist for safer removal options."),
            ("Genital warts", "see_doctor_today", "Genital warts are caused by different HPV strains and require different treatment — see a doctor."),
            ("Rapidly spreading despite treatment", "within_1_week", "See a dermatologist for cryotherapy or immunotherapy."),
            ("Painful or bleeding wart without picking", "within_1_week", "Spontaneous bleeding or pain may warrant evaluation."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a dermatologist if OTC salicylic acid treatment does not clear warts within 12 weeks, if warts are on the face or genitals, or if they are spreading rapidly. Professional cryotherapy and immunotherapy options are available.",
        base_disclaimer="Most common warts are harmless and will eventually resolve on their own. Treatment speeds this process.",
        weather_notes={
            "humid": "Moisture can soften wart-affected skin. Keep warts dry and covered.",
        },
    )

    kb["molluscum_contagiosum"] = ConditionKB(
        key="molluscum_contagiosum",
        display_name="Molluscum Contagiosum",
        category="infectious",
        is_contagious=True,
        is_curable=True,
        contagion_guidance="Cover lesions during sports or close contact. Avoid shared baths with siblings. Do not scratch or pick lesions — this spreads them. Do not share towels or clothing.",
        what_it_is="Molluscum contagiosum is a viral skin infection that causes small, firm, dome-shaped bumps with a characteristic central dimple. It is caused by a poxvirus and spreads through direct contact.",
        what_causes_it="Caused by the molluscum contagiosum virus (a poxvirus). Spreads through direct skin contact, contaminated objects, and sexual contact in adults.",
        typical_duration="Self-resolves in 6–18 months in most cases. Treatment can speed clearance.",
        common_misconceptions=[
            "Myth: Molluscum only affects children — Fact: Adults can get it too, especially through sexual contact or in immunocompromised states.",
            "Myth: Squeezing the bumps will clear them — Fact: Squeezing spreads the virus to new areas.",
            "Myth: Once you have it, you're immune — Fact: Reinfection is possible.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Gentle Cleansing", recommendation="Use a gentle fragrance-free cleanser. Do NOT pick, squeeze, or scratch any lesions — this spreads the virus to new areas.", fallback_why="Gentle cleansing without trauma prevents spreading the virus to unaffected skin.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Cleansing", recommendation="Same gentle cleanser. For children under 10: often best to leave alone and let resolve naturally (6–18 months). For adults or immunocompromised: seek prescription treatment.", fallback_why="The treatment approach differs by age — children often self-resolve while adults benefit from active treatment.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Prescription Treatment", recommendation="If prescribed: apply cantharidin (clinic-only application) or tretinoin 0.05–0.1% or imiquimod 5% cream to individual lesions.", fallback_why="Prescription treatments speed viral clearance significantly compared to waiting for self-resolution.", is_otc_available=False),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Gentle fragrance-free cleanser", "Minimizes irritation and prevents spreading"),
            ("Tretinoin (prescription)", "Speeds clearance by increasing skin cell turnover"),
            ("Imiquimod 5% cream (prescription)", "Stimulates the immune system to fight the virus"),
        ],
        avoid_ingredients=[
            ("Picking or squeezing lesions", "Spreads the virus to new body areas"),
            ("Sharing towels or clothing", "Spreads the virus to other people"),
            ("Scratching affected areas", "Creates new infection sites"),
        ],
        triggers=[
            ("Direct skin contact", "Cover lesions during activities involving skin contact.", "severe"),
            ("Sharing personal items", "Use separate towels, razors, and clothing.", "moderate"),
            ("Scratching", "Resist scratching — cover lesions with bandages if needed.", "severe"),
        ],
        red_flags=[
            ("Genital involvement in adults", "see_doctor_today", "Rule out STI — genital molluscum in adults requires medical evaluation."),
            ("Spreading despite 6 months of observation", "within_1_month", "Consider active treatment — see a dermatologist."),
            ("Secondary bacterial infection of lesions (redness, pus, warmth)", "see_doctor_today", "Infected molluscum needs antibiotics — see a doctor promptly."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a dermatologist if molluscum lesions are not resolving after 6 months, if they are spreading rapidly, or if you are an adult with genital involvement. Prescription treatments can accelerate clearance.",
        base_disclaimer="Molluscum contagiosum is generally harmless and self-limiting. Treatment is optional but can speed resolution.",
        weather_notes={
            "humid": "Sweating can increase spread via autoinoculation. Keep lesions dry and covered.",
        },
    )

    kb["impetigo"] = ConditionKB(
        key="impetigo",
        display_name="Impetigo",
        category="infectious",
        is_contagious=True,
        is_curable=True,
        contagion_guidance="Stay home from school/work until 24 hours after starting antibiotics. Wash all bedding and clothing in hot water. Do not touch affected areas and then touch other people. Wash hands with antibacterial soap frequently.",
        what_it_is="Impetigo is a highly contagious bacterial skin infection that causes honey-colored crusted sores, most commonly around the nose and mouth. It primarily affects children but can occur in adults.",
        what_causes_it="Caused by Staphylococcus aureus or Streptococcus pyogenes bacteria entering through broken skin. It spreads rapidly through direct contact.",
        typical_duration="Resolves within 7–10 days with antibiotic treatment. Without treatment, it can spread and cause complications.",
        common_misconceptions=[
            "Myth: Impetigo is caused by being dirty — Fact: It is caused by bacteria that can infect anyone through skin breaks.",
            "Myth: OTC antibiotic ointment is enough — Fact: Most impetigo requires prescription-strength mupirocin or oral antibiotics.",
            "Myth: It will go away on its own — Fact: Without antibiotics, impetigo can spread and cause kidney complications.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Seek Medical Care", recommendation="This is a bacterial infection requiring antibiotic treatment. See a doctor TODAY or within 24 hours for an antibiotic prescription (topical mupirocin or oral flucloxacillin/cephalexin).", fallback_why="Impetigo requires prescription antibiotics — OTC treatment is not adequate and delays risk spread and complications.", is_otc_available=False),
            KBStep(phase="daily_am", category="Crust Removal", recommendation="Gently soak crusts with warm water and a clean cloth to soften and remove. Pat dry with disposable paper towel.", fallback_why="Removing crusts allows prescribed antibiotic ointment to reach the infected skin beneath.", is_otc_available=True),
            KBStep(phase="daily_am", category="Antibiotic Application", recommendation="Apply prescribed mupirocin 2% ointment to affected areas. Cover with a non-stick dressing.", fallback_why="Mupirocin is the gold standard topical antibiotic for impetigo, targeting both staph and strep.", is_otc_available=False),
            KBStep(phase="daily_pm", category="Crust Removal", recommendation="Same gentle soaking and crust removal as morning. Use a fresh cloth each time.", fallback_why="Twice-daily crust removal and antibiotic application speeds healing.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Antibiotic Application", recommendation="Apply mupirocin ointment and fresh non-stick dressing. Wash hands thoroughly with antibacterial soap before and after.", fallback_why="Consistent antibiotic application and strict hand hygiene prevent spreading the infection.", is_otc_available=False),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Mupirocin 2% ointment (prescription)", "First-line topical antibiotic for impetigo"),
            ("Fusidic acid (prescription)", "Alternative topical antibiotic"),
            ("Gentle saline soaks", "Softens crusts for removal"),
        ],
        avoid_ingredients=[
            ("Sharing towels, clothing, or bedding", "Highly contagious — separate all personal items"),
            ("Touching face then touching others", "Bacteria spread through direct contact"),
            ("Stopping antibiotics early", "Incomplete treatment risks treatment failure and resistance"),
        ],
        triggers=[
            ("Skin breaks (cuts, scrapes, insect bites)", "Keep wounds clean and covered to prevent bacterial entry.", "severe"),
            ("Close contact with infected person", "Avoid contact until 24 hours after starting antibiotics.", "severe"),
            ("Poor hand hygiene", "Wash hands frequently with antibacterial soap.", "severe"),
            ("Crowded living conditions", "Maintain personal hygiene and separate personal items.", "moderate"),
        ],
        red_flags=[
            ("Fever developing", "see_doctor_today", "Fever with impetigo may indicate the infection is spreading systemically."),
            ("Spreading despite 48 hours of antibiotics", "see_doctor_today", "May need a different antibiotic — see your doctor for reassessment."),
            ("Deep, ulcerated lesions", "see_doctor_today", "Possible ecthyma — a deeper form of infection requiring stronger treatment."),
            ("Dark urine or swelling after infection", "see_doctor_today", "Possible post-streptococcal glomerulonephritis — kidney complication requiring urgent evaluation."),
        ],
        referral_recommended=True,
        referral_urgency="immediate",
        when_to_see_doctor="See a doctor TODAY. Impetigo requires prescription antibiotics — OTC treatment is not adequate. Topical mupirocin for mild cases or oral antibiotics for extensive involvement.",
        base_disclaimer="Impetigo is highly contagious and requires prescription antibiotic treatment. Do not rely on OTC products alone.",
        weather_notes={
            "humid": "Warm, humid weather promotes bacterial growth. Maintain strict hygiene and keep wounds covered.",
        },
    )

    kb["cold_sores"] = ConditionKB(
        key="cold_sores",
        display_name="Cold Sores (Herpes Labialis)",
        category="infectious",
        is_contagious=True,
        is_curable=False,
        contagion_guidance="The herpes simplex virus is contagious during outbreaks AND between outbreaks (asymptomatic shedding). Do not kiss during an outbreak. Do not share utensils, lip products, or razors. Use SPF lip balm year-round as UV triggers outbreaks.",
        what_it_is="Cold sores are painful, fluid-filled blisters that appear on or near the lips, caused by herpes simplex virus type 1 (HSV-1). The virus remains dormant in nerve cells and reactivates periodically.",
        what_causes_it="Caused by herpes simplex virus type 1 (HSV-1). After initial infection, the virus stays dormant in nerve ganglia and reactivates due to triggers like stress, sun exposure, and illness.",
        typical_duration="Individual outbreaks last 7–10 days without treatment, 4–6 days with antiviral treatment started at the first sign.",
        common_misconceptions=[
            "Myth: Cold sores only spread when visible — Fact: The virus can spread through asymptomatic shedding even without visible sores.",
            "Myth: Cold sores mean you have an STI — Fact: HSV-1 is extremely common (50–80% of adults carry it) and is usually acquired in childhood through non-sexual contact.",
            "Myth: Cold sores can be cured — Fact: The virus remains dormant for life, but outbreaks can be managed and reduced.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Antiviral Cream", recommendation="Apply antiviral cream (aciclovir 5% or penciclovir 1%) at the FIRST sign — tingling or itching BEFORE the blister appears. Starting early dramatically reduces outbreak duration.", fallback_why="Antivirals are most effective in the first 72 hours. Applying at the tingling stage can prevent full blister formation.", is_otc_available=True),
            KBStep(phase="daily_am", category="Antiviral Application", recommendation="Apply OTC antiviral cream (aciclovir 5%) every 4 hours while awake. Keep the area moisturized with petroleum jelly between applications.", fallback_why="Frequent antiviral application maintains consistent drug levels to suppress viral replication.", is_otc_available=True),
            KBStep(phase="daily_am", category="SPF Lip Protection", recommendation="Apply SPF lip balm over the antiviral cream. UV exposure is a major outbreak trigger and worsens healing.", fallback_why="UV radiation triggers HSV-1 reactivation. SPF lip balm both treats the current outbreak environment and prevents future ones.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Antiviral Application", recommendation="Apply final antiviral cream application of the day. Seal with petroleum jelly. Avoid kissing or sharing utensils during the outbreak.", fallback_why="Evening antiviral application continues suppressing the virus overnight.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Aciclovir 5% cream", "OTC antiviral — most widely available cold sore treatment"),
            ("Penciclovir 1% cream", "Alternative OTC antiviral for cold sores"),
            ("Petroleum jelly", "Protects healing skin and prevents cracking"),
            ("SPF lip balm", "UV protection prevents outbreak triggers — use daily as prevention"),
        ],
        avoid_ingredients=[
            ("Touching the blister then touching eyes", "Risk of ocular herpes — a serious eye infection"),
            ("Sharing utensils, lip products, or razors", "Spreads the virus to others"),
            ("Oral contact during outbreak", "High risk of transmission during active sores"),
            ("Squeezing or picking blisters", "Delays healing and increases transmission risk"),
        ],
        triggers=[
            ("Sun exposure", "Use SPF lip balm daily as prevention — UV is the #1 trigger. This is preventive, not just during outbreaks.", "severe"),
            ("Stress", "Chronic stress weakens immune surveillance of dormant HSV-1. Practice stress management.", "severe"),
            ("Illness and fever", "The immune system is suppressed during illness, allowing viral reactivation.", "moderate"),
            ("Hormonal changes", "Menstrual cycle fluctuations can trigger outbreaks in some people.", "moderate"),
        ],
        red_flags=[
            ("Eye area involvement (pain, redness, blurred vision near eye)", "see_doctor_today", "Possible ocular herpes — this can cause vision loss. Seek immediate ophthalmological evaluation."),
            ("Immunocompromised patient with severe widespread outbreak", "see_doctor_today", "Severe HSV in immunocompromised patients requires urgent systemic antiviral treatment."),
            ("Rapid spreading of blisters, especially with eczema", "see_doctor_today", "Possible eczema herpeticum — a medical emergency requiring IV antivirals."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a doctor if you experience more than 6 outbreaks per year — prescription oral antivirals (valaciclovir) for suppressive therapy can dramatically reduce frequency. Also seek care for any eye involvement.",
        base_disclaimer="Cold sores are caused by HSV-1, which is extremely common. Oral antiviral medications are available by prescription for frequent outbreaks.",
        weather_notes={
            "high_uv": "UV is the #1 cold sore trigger. Apply SPF lip balm every 2 hours outdoors, even when you don't have an outbreak.",
            "cold": "Cold wind can dry and crack lips, creating vulnerable areas. Use SPF lip balm and petroleum jelly.",
        },
    )


def _build_kb_part4(kb: dict[str, ConditionKB]) -> None:
    """Conditions: vitiligo, melasma, PIH, actinic_keratosis, melanoma_risk"""

    kb["vitiligo"] = ConditionKB(
        key="vitiligo",
        display_name="Vitiligo",
        category="pigmentation",
        is_contagious=False,
        is_curable=False,
        contagion_guidance=None,
        what_it_is="Vitiligo is an autoimmune condition in which the immune system destroys melanocytes (pigment-producing cells), resulting in white patches of skin. It can affect any area of the body and is highly variable in progression.",
        what_causes_it="The immune system mistakenly attacks and destroys melanocytes. Genetic predisposition combined with environmental triggers (stress, sunburn, skin trauma) contribute to onset.",
        typical_duration="Chronic — variable progression. Some cases stabilize, others slowly progress. New treatments can restore significant pigmentation.",
        common_misconceptions=[
            "Myth: Vitiligo is caused by poor hygiene — Fact: It is an autoimmune condition unrelated to cleanliness.",
            "Myth: Vitiligo is contagious — Fact: It cannot spread to others through any form of contact.",
            "Myth: Nothing can be done for vitiligo — Fact: New treatments like topical ruxolitinib can significantly restore pigmentation.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply broad-spectrum SPF 50+ mineral sunscreen (zinc oxide/titanium dioxide) to ALL depigmented patches. These areas have no melanin and burn extremely easily. Consider a vitamin D supplement due to sun avoidance.", fallback_why="Depigmented skin has zero melanin protection and burns in minutes. SPF 50+ mineral is essential daily.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Treatment", recommendation="Apply topical calcineurin inhibitor (tacrolimus 0.1% or pimecrolimus — prescription) OR topical corticosteroid pulse therapy (1 week on, 1 week off — prescription). Moisturize affected areas well.", fallback_why="Calcineurin inhibitors and pulsed corticosteroids can halt progression and stimulate repigmentation.", is_otc_available=False),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Zinc oxide / titanium dioxide SPF 50+", "Essential mineral sun protection for depigmented skin"),
            ("Calcineurin inhibitors (tacrolimus, pimecrolimus — prescription)", "Stimulate repigmentation and halt progression"),
            ("Antioxidant serum (vitamin C + E)", "Supports melanocyte health and protects from oxidative stress"),
            ("Afamelanotide analogue (clinical)", "Investigational treatment to stimulate melanin production"),
        ],
        avoid_ingredients=[
            ("Kojic acid", "Counterproductive — depigments surrounding skin, worsening contrast"),
            ("Hydroquinone on affected areas", "Further depigments already affected areas"),
            ("Tanning (sun or artificial)", "Increases the visible contrast between normal and depigmented skin"),
            ("Self-tanners on patches only", "Cosmetic cover is fine, but tanning products don't treat vitiligo"),
        ],
        triggers=[
            ("Stress", "Stress can trigger new patches and accelerate progression. Practice stress management.", "moderate"),
            ("Skin trauma (cuts, scrapes, friction)", "Koebner effect — vitiligo can appear at sites of skin injury. Protect skin.", "moderate"),
            ("Sunburn on depigmented patches", "Severe sunburn can extend patches. Use SPF 50+ on all exposed depigmented areas.", "severe"),
        ],
        red_flags=[
            ("Rapid spreading of depigmented patches", "within_1_week", "See a dermatologist urgently — aggressive treatment may halt rapid progression."),
            ("Mucosal involvement (mouth, nose, eyes)", "within_1_month", "Mucosal vitiligo may indicate more extensive autoimmune involvement."),
            ("Associated thyroid symptoms (fatigue, weight changes, temperature sensitivity)", "within_1_month", "Vitiligo is linked to autoimmune thyroid disease — request thyroid function tests."),
        ],
        referral_recommended=True,
        referral_urgency="soon",
        when_to_see_doctor="See a dermatologist as soon as possible. New FDA-approved topical ruxolitinib 1.5% (Opzelura) has shown significant repigmentation results. Phototherapy (narrowband UVB) is also highly effective. Early treatment yields better outcomes.",
        base_disclaimer="Vitiligo is a cosmetic and autoimmune condition — it is not a hygiene issue and is not contagious. Treatment options have improved dramatically in recent years.",
        weather_notes={
            "high_uv": "Depigmented skin burns extremely quickly. Apply SPF 50+ every 90 minutes outdoors. Wear protective clothing.",
            "cold": "Cold weather is generally less problematic for vitiligo. Continue SPF on exposed depigmented areas.",
        },
    )

    kb["melasma"] = ConditionKB(
        key="melasma",
        display_name="Melasma",
        category="pigmentation",
        is_contagious=False,
        is_curable=False,
        contagion_guidance=None,
        what_it_is="Melasma is a common pigmentation disorder that causes dark, symmetrical patches on sun-exposed areas of the face, particularly the cheeks, forehead, upper lip, and chin. It is strongly influenced by UV exposure and hormones.",
        what_causes_it="Caused by overactive melanocytes stimulated by UV radiation, hormonal factors (pregnancy, oral contraceptives), and heat. Genetic predisposition and darker skin tones are risk factors.",
        typical_duration="Chronic — managed, not cured. Melasma can fade with consistent treatment but recurs with sun exposure or hormonal changes.",
        common_misconceptions=[
            "Myth: Melasma only affects pregnant women — Fact: It can affect anyone, including men, though it is more common in women.",
            "Myth: Once treated, melasma stays away — Fact: A single sun exposure can re-pigment treated areas. Lifelong SPF is essential.",
            "Myth: Stronger is better for melasma treatment — Fact: Aggressive treatments can worsen melasma through post-inflammatory hyperpigmentation.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Vitamin C Serum", recommendation="Apply L-ascorbic acid 10–15% or ascorbyl glucoside serum. This brightens and provides antioxidant protection.", fallback_why="Vitamin C inhibits tyrosinase (the enzyme that produces melanin) and provides antioxidant UV defense.", is_otc_available=True),
            KBStep(phase="daily_am", category="Niacinamide", recommendation="Apply niacinamide 5% serum after vitamin C.", fallback_why="Niacinamide prevents melanin transfer from melanocytes to keratinocytes, reducing visible pigmentation.", is_otc_available=True),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply broad-spectrum SPF 50+ PA++++ mineral sunscreen. This is CRITICAL — UV worsens melasma severely and re-pigments treated areas. Reapply every 2 hours outdoors.", fallback_why="UV exposure is the #1 melasma trigger. Without daily SPF 50+, all other treatments are futile.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Cleanser", recommendation="Use a gentle, fragrance-free cleanser.", fallback_why="Gentle cleansing avoids irritation that can worsen pigmentation.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Tranexamic Acid", recommendation="Apply tranexamic acid serum to pigmented areas.", fallback_why="Tranexamic acid interferes with the UV-melanin pathway and is one of the most effective melasma treatments.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Azelaic Acid", recommendation="Apply azelaic acid 10–20% over tranexamic acid.", fallback_why="Azelaic acid inhibits abnormal melanocytes and is safe for all skin tones.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Light Moisturizer", recommendation="Apply a lightweight, fragrance-free moisturizer as the final step.", fallback_why="Light moisture supports treatment tolerance without clogging pores.", is_otc_available=True),
            KBStep(phase="weekly", category="Gentle AHA", recommendation="Use mandelic acid ≤5% as a weekly gentle exfoliant. Mandelic acid is gentler and suitable for all skin tones.", fallback_why="Gentle exfoliation accelerates the turnover of pigmented skin cells.", is_otc_available=True),
        ],
        optional_steps=[
            KBStep(phase="daily_pm", category="Alpha Arbutin Spot Treatment", recommendation="Apply alpha arbutin 2% as a spot treatment to the most pigmented areas, weekly.", fallback_why="Alpha arbutin is a naturally derived tyrosinase inhibitor that lightens hyperpigmented spots.", is_otc_available=True, score=1, score_modifiers={"moderate": 1, "severe": 2}),
        ],
        seek_ingredients=[
            ("Tranexamic acid", "One of the most effective melasma treatments — inhibits UV-melanin pathway"),
            ("Azelaic acid (10–20%)", "Inhibits abnormal melanocytes, safe for all skin tones"),
            ("Kojic acid", "Natural tyrosinase inhibitor for brightening"),
            ("Niacinamide (5%)", "Prevents melanin transfer and strengthens skin barrier"),
            ("Alpha arbutin", "Naturally derived tyrosinase inhibitor"),
            ("Mandelic acid", "Gentle AHA suitable for melasma-prone skin"),
            ("Vitamin C (L-ascorbic acid)", "Antioxidant and tyrosinase inhibitor"),
            ("Broad-spectrum mineral SPF 50+", "The single most important melasma management tool"),
        ],
        avoid_ingredients=[
            ("Any UV exposure without SPF", "A single sun exposure undoes weeks of treatment"),
            ("Hormonal triggers (discuss contraceptive options with GP if pill-related)", "Estrogen-containing contraceptives are a common melasma trigger"),
            ("Heat (infrared)", "Heat also worsens melasma — avoid saunas, hot yoga, cooking over stove"),
            ("Hydroquinone long-term (>3 months without break)", "Risk of ochronosis (paradoxical darkening) with prolonged use"),
        ],
        triggers=[
            ("Sun exposure", "The most important trigger. SPF 50+ daily, reapply every 2 hours. Sunglasses and hat.", "severe"),
            ("Hormonal changes (pregnancy, OCP)", "Discuss with GP. Progesterone-only or non-hormonal contraception may help.", "severe"),
            ("Heat (including infrared)", "Avoid saunas, hot yoga, and prolonged stove cooking. Heat worsens melasma independently of UV.", "moderate"),
            ("Stress", "Stress can worsen hormonal fluctuations that trigger melasma.", "mild"),
        ],
        red_flags=[
            ("Sudden rapid darkening", "within_1_week", "Rule out hormonal cause — check thyroid function and discuss contraception with GP."),
            ("Not responding after 6 months of SPF + actives", "within_1_month", "See a dermatologist for prescription triple combination cream (hydroquinone + tretinoin + steroid)."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a dermatologist if your melasma does not respond to OTC tranexamic acid + azelaic acid + SPF within 6 months. Prescription options include hydroquinone 4%, tretinoin, and combination creams.",
        base_disclaimer="Melasma requires lifelong sun protection. Even one day of unprotected sun exposure can undo months of treatment progress.",
        weather_notes={
            "high_uv": "UV is the #1 melasma trigger. Double down on SPF — reapply every 90 minutes, wear a hat, seek shade.",
            "humid": "Humidity does not directly worsen melasma, but heat does. Stay cool and maintain SPF.",
        },
    )

    kb["post_inflammatory_hyperpigmentation"] = ConditionKB(
        key="post_inflammatory_hyperpigmentation",
        display_name="Post-Inflammatory Hyperpigmentation",
        category="pigmentation",
        is_contagious=False,
        is_curable=True,
        contagion_guidance=None,
        what_it_is="Post-inflammatory hyperpigmentation (PIH) is the dark marks left behind after skin inflammation or injury. It occurs when excess melanin is deposited in response to inflammation from acne, eczema flares, cuts, or any skin trauma.",
        what_causes_it="Caused by excess melanin production triggered by skin inflammation. Any inflammatory event (acne, eczema, injury, even aggressive skin treatments) can leave PIH behind.",
        typical_duration="Most PIH fades within 3–12 months with consistent SPF and brightening actives. Deeper PIH may take longer.",
        common_misconceptions=[
            "Myth: PIH is permanent scarring — Fact: PIH is pigment in the skin, not scar tissue, and fades with time and treatment.",
            "Myth: Scrubbing dark spots will remove them — Fact: Scrubbing causes more inflammation and makes PIH worse.",
            "Myth: PIH only happens with dark skin — Fact: It can happen to anyone, though it is more common and visible in darker skin tones.",
        ],
        mandatory_steps=[
            KBStep(phase="daily_am", category="Niacinamide", recommendation="Apply niacinamide 10% serum to PIH areas and surrounding skin.", fallback_why="Niacinamide at 10% effectively prevents melanin transfer to the skin surface, fading dark marks.", is_otc_available=True),
            KBStep(phase="daily_am", category="Vitamin C", recommendation="Apply vitamin C 10–15% serum over niacinamide.", fallback_why="Vitamin C inhibits melanin production and provides antioxidant protection against further pigmentation.", is_otc_available=True),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply SPF 50+ — critical. UV exposure intensifies PIH dramatically. Any sun exposure without SPF undoes weeks of progress.", fallback_why="UV radiation stimulates melanocytes to produce even more melanin at PIH sites, making dark marks darker.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Gentle Cleanser", recommendation="Use a gentle, fragrance-free cleanser.", fallback_why="Gentle cleansing avoids additional inflammation that could create new PIH.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Brightening Serum", recommendation="Apply alpha arbutin 2% OR tranexamic acid serum to PIH areas.", fallback_why="These tyrosinase inhibitors reduce melanin production at the cellular level.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Retinol", recommendation="Apply retinol 0.025–0.05% every other night. Start low, increase frequency slowly over 4–6 weeks. Use only at night.", fallback_why="Retinol accelerates skin cell turnover, bringing pigmented cells to the surface faster for shedding.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Lightweight Moisturizer", recommendation="Apply a lightweight moisturizer as the final step.", fallback_why="Moisturizer supports skin barrier function during active treatment with retinol and brightening agents.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Niacinamide (10%)", "Prevents melanin transfer — most effective single PIH ingredient"),
            ("Vitamin C (10–15%)", "Tyrosinase inhibitor and antioxidant"),
            ("Alpha arbutin (2%)", "Naturally derived brightening agent"),
            ("Tranexamic acid", "Inhibits melanin production pathway"),
            ("Kojic acid", "Additional tyrosinase inhibitor"),
            ("Mandelic acid", "Gentle AHA for accelerating turnover"),
            ("Azelaic acid", "Inhibits abnormal melanocytes, great for darker skin tones"),
            ("Retinol (PM only)", "Accelerates turnover of pigmented cells"),
        ],
        avoid_ingredients=[
            ("Picking or squeezing ANY skin lesion", "PIH is caused by inflammation — picking causes more"),
            ("Sun exposure without SPF", "UV intensifies PIH and undoes treatment progress"),
            ("Hydroquinone as sole agent", "Use only in combination, not alone long-term"),
            ("High-concentration AHAs without acclimatization", "Can cause irritation leading to more PIH"),
        ],
        triggers=[
            ("Sun exposure", "SPF 50+ daily is non-negotiable. UV makes PIH worse and prevents fading.", "severe"),
            ("Picking or squeezing skin", "Stop picking — this is the most common cause of new PIH.", "severe"),
            ("Any new inflammatory lesion", "Treat acne and inflammation promptly to prevent new PIH.", "moderate"),
        ],
        red_flags=[
            ("PIH not fading after 12 months of consistent treatment", "within_1_month", "See a dermatologist for professional chemical peels or laser treatment options."),
        ],
        referral_recommended=True,
        referral_urgency="routine",
        when_to_see_doctor="See a dermatologist if PIH has not faded significantly after 12 months of consistent SPF + niacinamide + retinol. Professional options include chemical peels, microneedling, and laser treatments.",
        base_disclaimer="Most PIH resolves with consistent SPF + niacinamide within 3–12 months. Patience and sun protection are the foundation of treatment.",
        weather_notes={
            "high_uv": "UV is the #1 enemy of PIH fading. Reapply SPF every 2 hours outdoors.",
            "humid": "Humidity supports skin hydration, which is helpful during active treatment.",
        },
    )

    # ── Category D — High Risk / Oncology-Adjacent ───────
    # REFERRAL = IMMEDIATE. Severity = ALWAYS SEVERE. No exceptions.

    kb["actinic_keratosis"] = ConditionKB(
        key="actinic_keratosis",
        display_name="Actinic Keratosis (Pre-cancerous)",
        category="high_risk",
        is_contagious=False,
        is_curable=True,
        contagion_guidance=None,
        what_it_is="Actinic keratosis (AK) is a rough, scaly patch on the skin caused by years of cumulative sun damage. It is a pre-cancerous lesion — if left untreated, a small percentage can progress to squamous cell carcinoma (a type of skin cancer).",
        what_causes_it="Caused by cumulative UV damage to skin cells over years. Fair skin, history of sunburns, frequent sun exposure, and immunosuppression increase risk significantly.",
        typical_duration="Persistent — will not resolve on its own. Requires professional treatment (cryotherapy, topical prescription, or photodynamic therapy).",
        common_misconceptions=[
            "Myth: Actinic keratosis is just a rough patch that doesn't matter — Fact: It is a pre-cancerous lesion that can progress to squamous cell carcinoma.",
            "Myth: Only old people get AK — Fact: Anyone with significant cumulative sun exposure can develop it, including younger adults.",
            "Myth: Sunscreen is enough to treat AK — Fact: Existing AK requires medical treatment. Sunscreen prevents new ones.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Dermatologist Evaluation", recommendation="Seek evaluation by a dermatologist as soon as possible. Actinic keratosis is a pre-cancerous lesion that can progress to squamous cell carcinoma. OTC skincare is supportive ONLY.", fallback_why="Actinic keratosis requires professional evaluation and treatment to prevent progression to skin cancer.", is_otc_available=False),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply broad-spectrum SPF 50+ mineral sunscreen to ALL exposed areas, every single day. Reapply every 2 hours when outdoors. Wear protective clothing and a hat.", fallback_why="UV exposure caused the AK and continues to promote progression. Sun protection is the most important ongoing measure.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Prescribed Treatment", recommendation="Apply prescribed treatment as directed — 5-fluorouracil (Efudex) cream, imiquimod (Aldara), or diclofenac gel (Solaraze). These are prescription-only.", fallback_why="Prescription topicals destroy pre-cancerous cells. Only a dermatologist can determine the appropriate treatment.", is_otc_available=False),
            KBStep(phase="daily_pm", category="Gentle Moisturizer", recommendation="Apply a gentle, non-irritating ceramide moisturizer to areas not under active prescription treatment.", fallback_why="Gentle moisturizing supports skin health in surrounding areas without interfering with prescription treatment.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("Broad-spectrum SPF 50+ mineral (zinc oxide)", "Essential daily sun protection to prevent new AK"),
            ("Antioxidant serum (vitamin C + ferulic acid)", "Additional UV defense and free radical protection"),
            ("Gentle ceramide moisturizer", "Supports skin barrier without irritating treated areas"),
        ],
        avoid_ingredients=[
            ("Sun exposure without SPF at ALL costs", "UV continues to promote AK progression and new lesion formation"),
            ("Tanning beds", "Absolute contraindication — carcinogenic UV exposure"),
            ("Irritating actives on affected areas (AHAs, retinoids, strong vitamin C)", "May irritate during prescription treatment"),
        ],
        triggers=[
            ("Sun exposure", "The cause of AK. SPF 50+ every day, protective clothing, wide-brim hat.", "severe"),
            ("Immunosuppression", "Immunosuppressed patients develop AK at much higher rates.", "severe"),
            ("History of sunburns", "Cumulative UV damage cannot be reversed but new exposure must be prevented.", "moderate"),
        ],
        red_flags=[
            ("Lesion is bleeding or ulcerating", "see_doctor_today", "Possible progression to squamous cell carcinoma — seek immediate dermatological evaluation."),
            ("New rapidly growing lesion", "see_doctor_today", "Rapid growth may indicate malignant transformation — urgent evaluation required."),
            ("Not responding to prescribed treatment after 8 weeks", "within_1_week", "Follow up with your dermatologist for treatment reassessment — may need cryotherapy or biopsy."),
        ],
        referral_recommended=True,
        referral_urgency="immediate",
        when_to_see_doctor="See a dermatologist IMMEDIATELY. Actinic keratosis is a pre-cancerous lesion that requires professional evaluation, monitoring, and treatment. Do not delay.",
        base_disclaimer="Actinic keratosis requires professional medical evaluation and treatment. This protocol provides supportive skin protection information only and does NOT replace professional dermatological care.",
        weather_notes={
            "high_uv": "CRITICAL: High UV accelerates AK progression. Stay indoors during peak UV (10am–4pm), use SPF 50+ constantly, wear UPF clothing.",
            "cold": "UV exposure occurs even in cold weather. Continue daily SPF on all exposed skin.",
        },
    )

    kb["melanoma_risk"] = ConditionKB(
        key="melanoma_risk",
        display_name="Elevated Melanoma Risk / Atypical Moles",
        category="high_risk",
        is_contagious=False,
        is_curable=False,
        contagion_guidance=None,
        what_it_is="Elevated melanoma risk refers to having atypical moles (dysplastic nevi), a family history of melanoma, extensive sun damage, or other risk factors for developing melanoma — the most dangerous form of skin cancer. Early detection saves lives.",
        what_causes_it="Risk factors include UV exposure, family history of melanoma, having many moles (>50), atypical moles, fair skin, history of blistering sunburns, and immunosuppression.",
        typical_duration="Lifelong surveillance. Melanoma risk does not go away — it requires annual full-body skin examinations and ongoing vigilance.",
        common_misconceptions=[
            "Myth: Melanoma only appears as a new mole — Fact: About 70% of melanomas arise from existing moles. Monitor ALL moles for changes.",
            "Myth: Young people don't get melanoma — Fact: Melanoma is one of the most common cancers in young adults (20–39).",
            "Myth: Dark-skinned people can't get melanoma — Fact: While less common, melanoma in darker skin tones is often diagnosed later and has worse outcomes.",
        ],
        mandatory_steps=[
            KBStep(phase="immediate", category="Full-Body Skin Exam", recommendation="Undergo a full-body skin examination by a dermatologist as soon as possible. Use the ABCDE rule to monitor moles: Asymmetry, Border irregularity, Color variation, Diameter >6mm, Evolution (any change).", fallback_why="Professional skin examination with dermoscopy catches melanoma at its earliest, most treatable stage.", is_otc_available=False),
            KBStep(phase="daily_am", category="Sun Protection", recommendation="Apply broad-spectrum SPF 50+ PA++++ mineral sunscreen (zinc oxide/titanium dioxide). Apply 20 minutes before sun exposure. Reapply every 90 minutes outdoors. This is non-negotiable.", fallback_why="UV radiation is the primary modifiable risk factor for melanoma. Rigorous sun protection reduces risk significantly.", is_otc_available=True),
            KBStep(phase="daily_pm", category="Antioxidant Serum", recommendation="Apply vitamin C + ferulic acid + vitamin E antioxidant serum. This provides additional photoprotection and DNA repair support.", fallback_why="Antioxidant serums neutralize free radicals caused by UV exposure and support DNA repair mechanisms.", is_otc_available=True),
            KBStep(phase="daily_pm", category="DNA Repair Product", recommendation="Apply a product containing DNA repair enzymes (photolyase) — available OTC. Follow with a gentle ceramide moisturizer.", fallback_why="Photolyase enzymes help repair UV-induced DNA damage in skin cells, reducing mutagenic risk.", is_otc_available=True),
        ],
        optional_steps=[],
        seek_ingredients=[
            ("SPF 50+ mineral (zinc oxide / titanium dioxide)", "Gold standard sun protection — physical blockers"),
            ("Vitamin C + ferulic acid", "Antioxidant combo that boosts sunscreen effectiveness by 4x"),
            ("Vitamin E (tocopherol)", "Lipid-soluble antioxidant that supports DNA repair"),
            ("DNA repair enzymes (photolyase, endonuclease V)", "Help repair UV-induced DNA damage"),
            ("Niacinamide", "Reduces melanoma risk markers and supports DNA repair"),
        ],
        avoid_ingredients=[
            ("Tanning beds", "ABSOLUTE CONTRAINDICATION — classified as carcinogenic by WHO. Any use dramatically increases melanoma risk"),
            ("Self-tanning without SPF on top", "Self-tanners provide ZERO UV protection — always layer SPF"),
            ("Any AM active that increases photosensitivity without SPF (retinol, AHAs)", "Do not use photosensitizing actives in the morning without immediately applying SPF"),
        ],
        triggers=[
            ("UV exposure (sun and tanning beds)", "The primary modifiable risk factor. SPF 50+ daily, protective clothing, avoid peak UV hours.", "severe"),
            ("Sunburns (especially blistering)", "Even one blistering sunburn significantly increases lifetime melanoma risk.", "severe"),
            ("Family history of melanoma", "Increases risk 2–8x. Requires more frequent surveillance (every 6 months).", "severe"),
            ("Large number of moles (>50)", "More moles = more cells to monitor. Annual full-body exams are essential.", "moderate"),
        ],
        red_flags=[
            ("Any mole changing in color, shape, or size", "see_doctor_today", "ABCDE changes in a mole may indicate malignant transformation — seek urgent dermatological evaluation."),
            ("Any new dark spot appearing rapidly", "see_doctor_today", "Rapidly appearing pigmented lesions need immediate evaluation."),
            ("Lesion that bleeds or itches persistently without trauma", "see_doctor_today", "Persistent symptoms in a mole warrant urgent evaluation."),
            ("Family history of melanoma", "within_1_week", "Discuss surveillance protocol with a dermatologist — you may need 6-month dermoscopy monitoring."),
        ],
        referral_recommended=True,
        referral_urgency="immediate",
        when_to_see_doctor="See a dermatologist IMMEDIATELY for a full-body skin examination with dermoscopy. If you have atypical moles or a family history of melanoma, you need annual (or bi-annual) surveillance. Any mole changes require URGENT evaluation.",
        base_disclaimer="Elevated melanoma risk requires annual full-body skin examinations and may require dermoscopy surveillance. Skincare recommendations here relate to photoprotection ONLY. This is not a diagnostic tool — professional evaluation is essential.",
        weather_notes={
            "high_uv": "CRITICAL: High UV days dramatically increase melanoma risk. Stay indoors during 10am–4pm, apply SPF 50+ every 90 minutes, wear UPF 50+ clothing and a wide-brim hat.",
            "cold": "UV exposure occurs year-round. Continue daily SPF on all exposed skin even in winter.",
        },
    )
