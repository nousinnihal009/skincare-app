"""
knowledge_base.py

Comprehensive dermatology knowledge base covering all 21 skin conditions
from the ISIC 2019 dataset + additional clinical knowledge.
"""

# ─────────────────────────────────────────────────────────────
# Condition Database — maps class names → clinical information
# ─────────────────────────────────────────────────────────────

CONDITION_DATABASE = {
    "acne-closed-comedo": {
        "display_name": "Closed Comedonal Acne",
        "category": "Acne",
        "description": "Closed comedones (whiteheads) occur when a pore is completely blocked by dead skin cells and sebum. They appear as small, flesh-colored bumps under the skin surface.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Excess sebum production", "Dead skin cell buildup", "Hormonal changes", "Comedogenic products"],
        "symptoms": ["Small flesh-colored bumps", "Non-inflamed bumps under skin", "Rough skin texture"],
        "treatments": {
            "otc": ["Salicylic acid 2% cleanser", "Benzoyl peroxide 2.5%", "Adapalene 0.1% gel (Differin)"],
            "prescription": ["Tretinoin cream", "Oral spironolactone (hormonal acne)"],
            "natural": ["Tea tree oil (diluted)", "Green tea extract"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Gentle salicylic acid cleanser (2%)", "note": "Massage for 60 seconds"},
                {"step": "Treatment", "product": "Niacinamide 10% serum", "note": "Helps regulate sebum"},
                {"step": "Moisturizer", "product": "Oil-free gel moisturizer", "note": "Non-comedogenic"},
                {"step": "Sunscreen", "product": "SPF 50 mineral sunscreen", "note": "Essential if using actives"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Oil-based cleanser (double cleanse)", "note": "Removes sunscreen"},
                {"step": "Cleanser", "product": "Gentle foaming cleanser", "note": "Second cleanse"},
                {"step": "Treatment", "product": "Adapalene 0.1% gel", "note": "Apply to dry skin, start 3x/week"},
                {"step": "Moisturizer", "product": "Ceramide-based moisturizer", "note": "Repair barrier"}
            ],
            "weekly": ["Clay mask (1x/week)", "Gentle chemical exfoliant AHA/BHA (1-2x/week)"]
        },
        "when_to_see_doctor": "If OTC treatments don't improve after 8-12 weeks, or if acne is widespread.",
        "medical_explanation": "Comedonal acne is the mildest form, caused by blocked pores. Without treatment, closed comedones can progress to inflammatory acne."
    },
    "acne-cystic": {
        "display_name": "Cystic Acne",
        "category": "Acne",
        "description": "Cystic acne is the most severe form of acne, characterized by large, inflamed, painful cysts deep within the skin. It can lead to permanent scarring.",
        "severity": "severe",
        "risk_level": "moderate",
        "is_cancerous": False,
        "urgency": "soon",
        "causes": ["Hormonal imbalances", "Genetics", "Severe pore blockage", "Bacterial infection (C. acnes)"],
        "symptoms": ["Large painful nodules", "Deep cysts under skin", "Redness and swelling", "Potential scarring"],
        "treatments": {
            "otc": ["Benzoyl peroxide 5% wash", "Ice compress for inflammation"],
            "prescription": ["Isotretinoin (Accutane)", "Oral antibiotics (doxycycline)", "Cortisone injections", "Hormonal therapy (spironolactone)"],
            "natural": ["Zinc supplements", "Anti-inflammatory diet"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Gentle non-foaming cleanser", "note": "Do NOT scrub"},
                {"step": "Treatment", "product": "Azelaic acid 15-20%", "note": "Anti-inflammatory"},
                {"step": "Moisturizer", "product": "Fragrance-free gel moisturizer", "note": "Soothe irritation"},
                {"step": "Sunscreen", "product": "SPF 50 mineral sunscreen", "note": "Critical with medications"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Micellar water", "note": "Gentle first cleanse"},
                {"step": "Treatment", "product": "Prescription retinoid (as directed)", "note": "Follow dermatologist instructions"},
                {"step": "Moisturizer", "product": "Healing ointment on dry patches", "note": "Repair barrier"}
            ],
            "weekly": ["Do NOT pick or squeeze cysts", "Hydrocolloid patches on surfaced lesions"]
        },
        "when_to_see_doctor": "Immediately — cystic acne requires professional treatment to prevent scarring.",
        "medical_explanation": "Cystic acne involves deep infection and inflammation that OTC products cannot adequately treat. Isotretinoin is often the most effective treatment."
    },
    "acne-excoriated": {
        "display_name": "Excoriated Acne",
        "category": "Acne",
        "description": "Excoriated acne results from compulsive picking or scratching at acne lesions, leading to open wounds, scabs, and scarring.",
        "severity": "moderate",
        "risk_level": "moderate",
        "is_cancerous": False,
        "urgency": "soon",
        "causes": ["Compulsive skin picking (dermatillomania)", "Anxiety", "OCD-related behaviors"],
        "symptoms": ["Open sores from picking", "Scabs and crusting", "Scarring", "Skin discoloration"],
        "treatments": {
            "otc": ["Gentle wound care products", "Hydrocolloid bandages", "Centella asiatica cream"],
            "prescription": ["Cognitive behavioral therapy (CBT)", "SSRIs for underlying anxiety", "Topical antibiotics for wounds"],
            "natural": ["Stress management techniques", "Keep hands busy"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Ultra-gentle cream cleanser", "note": "No scrubbing"},
                {"step": "Treatment", "product": "Centella asiatica serum", "note": "Wound healing"},
                {"step": "Moisturizer", "product": "Rich barrier-repair cream", "note": "Protect healing skin"},
                {"step": "Sunscreen", "product": "SPF 50 mineral sunscreen", "note": "Prevent scarring darkening"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Micellar water on cotton pad", "note": "Minimal rubbing"},
                {"step": "Treatment", "product": "Niacinamide 5%", "note": "Help with discoloration"},
                {"step": "Moisturizer", "product": "Petrolatum-based healing ointment", "note": "On open areas"}
            ],
            "weekly": ["Cover tempting lesions with hydrocolloid patches"]
        },
        "when_to_see_doctor": "If you cannot stop picking — a therapist specializing in skin-picking disorders can help significantly.",
        "medical_explanation": "The primary issue is behavioral, not dermatological. Treating the underlying compulsive behavior is more important than treating the acne itself."
    },
    "acne-infantile": {
        "display_name": "Infantile Acne",
        "category": "Acne",
        "description": "Acne occurring in infants (typically 3-16 months), caused by maternal hormones. Usually resolves on its own but may need treatment if severe.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Maternal hormones (androgens)", "Developing sebaceous glands", "Genetic predisposition"],
        "symptoms": ["Small red bumps on baby's face", "Whiteheads", "Usually on cheeks and forehead"],
        "treatments": {
            "otc": ["Gentle baby cleanser", "No treatment needed in mild cases"],
            "prescription": ["Topical erythromycin (if severe)", "Low-strength benzoyl peroxide (if prescribed)"],
            "natural": ["Breast milk application", "Keep area clean and dry"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Lukewarm water only", "note": "Gentle pat dry"},
                {"step": "Moisturizer", "product": "Fragrance-free baby lotion", "note": "If skin is dry"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Gentle baby wash", "note": "2-3 times per week"},
                {"step": "Moisturizer", "product": "Fragrance-free baby cream", "note": "If needed"}
            ],
            "weekly": ["Monitor for changes", "Do not apply adult acne products"]
        },
        "when_to_see_doctor": "If acne is severe, persistent beyond 6 months, or accompanied by other symptoms.",
        "medical_explanation": "Usually harmless and self-limiting. Parental reassurance is often the main treatment needed."
    },
    "acne-open-comedo": {
        "display_name": "Open Comedonal Acne (Blackheads)",
        "category": "Acne",
        "description": "Open comedones (blackheads) occur when pores are partially blocked. The dark appearance is from oxidized melanin, not dirt.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Excess sebum production", "Dead skin cells", "Hormonal fluctuations", "Certain cosmetics"],
        "symptoms": ["Small dark spots on skin surface", "Slightly raised bumps", "Commonly on nose, chin, forehead"],
        "treatments": {
            "otc": ["Salicylic acid 2%", "Benzoyl peroxide wash", "Retinol products", "BHA exfoliants"],
            "prescription": ["Tretinoin (Retin-A)", "Adapalene"],
            "natural": ["Clay masks", "Gentle extraction (professional only)"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Salicylic acid cleanser 2%", "note": "Focus on T-zone"},
                {"step": "Treatment", "product": "BHA toner", "note": "Helps unclog pores"},
                {"step": "Moisturizer", "product": "Lightweight gel moisturizer", "note": "Non-comedogenic"},
                {"step": "Sunscreen", "product": "SPF 30+ lightweight sunscreen", "note": "Daily"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Oil cleanser (double cleanse)", "note": "Dissolves sebum plugs"},
                {"step": "Cleanser", "product": "Gentle foaming cleanser", "note": "Second cleanse"},
                {"step": "Treatment", "product": "Retinol serum 0.3-0.5%", "note": "Start slowly"},
                {"step": "Moisturizer", "product": "Niacinamide moisturizer", "note": "Pore-minimizing"}
            ],
            "weekly": ["Clay mask (1-2x/week)", "Professional facial extraction (monthly)"]
        },
        "when_to_see_doctor": "If blackheads are widespread or not improving with OTC treatments after 3 months.",
        "medical_explanation": "The black color is not dirt — it's oxidized melanin and sebum. Regular chemical exfoliation is the most effective approach."
    },
    "acne-pustular": {
        "display_name": "Pustular Acne",
        "category": "Acne",
        "description": "Inflammatory acne characterized by pus-filled lesions (pustules) surrounded by red, inflamed skin. More severe than comedonal acne.",
        "severity": "moderate",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Bacterial infection (C. acnes)", "Inflammation", "Hormonal changes", "Stress"],
        "symptoms": ["White/yellow pus-filled bumps", "Red inflamed base", "Tenderness", "Can leave marks"],
        "treatments": {
            "otc": ["Benzoyl peroxide 2.5-5%", "Salicylic acid", "Sulfur-based treatments"],
            "prescription": ["Topical antibiotics (clindamycin)", "Topical retinoids", "Oral antibiotics for widespread cases"],
            "natural": ["Tea tree oil (diluted)", "Zinc supplements"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Gentle foaming cleanser", "note": "Don't over-cleanse"},
                {"step": "Treatment", "product": "Benzoyl peroxide 2.5% (spot treatment)", "note": "On active pustules"},
                {"step": "Moisturizer", "product": "Oil-free moisturizer", "note": "Non-comedogenic"},
                {"step": "Sunscreen", "product": "SPF 50 mineral sunscreen", "note": "Essential"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Gentle cleanser", "note": "Lukewarm water"},
                {"step": "Treatment", "product": "Adapalene or prescription retinoid", "note": "Apply to entire face"},
                {"step": "Moisturizer", "product": "Ceramide moisturizer", "note": "Barrier repair"}
            ],
            "weekly": ["Don't pop pustules", "Change pillowcases frequently"]
        },
        "when_to_see_doctor": "If pustular acne covers large areas or doesn't respond to OTC treatment within 6-8 weeks.",
        "medical_explanation": "Pustules are a sign of active bacterial infection and immune response. Topical treatments targeting bacteria and inflammation are key."
    },
    "acne-scar": {
        "display_name": "Acne Scarring",
        "category": "Acne",
        "description": "Permanent textural changes in skin resulting from severe acne or picking. Types include ice pick, boxcar, and rolling scars.",
        "severity": "moderate",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Deep inflammatory acne", "Picking/squeezing", "Delayed acne treatment", "Genetic predisposition to scarring"],
        "symptoms": ["Depressed (atrophic) scars", "Raised (hypertrophic) scars", "Dark spots (PIH)", "Red marks (PIE)"],
        "treatments": {
            "otc": ["Retinol products", "Vitamin C serum", "AHA exfoliants", "Silicone scar sheets"],
            "prescription": ["Chemical peels", "Microneedling", "Laser resurfacing", "Dermal fillers for deep scars"],
            "natural": ["Rosehip oil", "Patience — PIH fades over 6-12 months"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Gentle cream cleanser", "note": "Don't irritate"},
                {"step": "Treatment", "product": "Vitamin C serum 15-20%", "note": "Brightening + collagen"},
                {"step": "Moisturizer", "product": "Hyaluronic acid moisturizer", "note": "Plumping effect"},
                {"step": "Sunscreen", "product": "SPF 50 sunscreen", "note": "Prevents darkening of scars"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Gentle cleanser", "note": "Standard"},
                {"step": "Treatment", "product": "Retinol 0.5-1%", "note": "Promotes cell turnover"},
                {"step": "Moisturizer", "product": "Peptide-rich night cream", "note": "Supports collagen"}
            ],
            "weekly": ["AHA peel 10-15% (1x/week)", "Consult dermatologist for in-office treatments"]
        },
        "when_to_see_doctor": "If you want significant improvement — professional treatments (laser, microneedling) are the most effective options.",
        "medical_explanation": "Most OTC products can help with discoloration but cannot remove textural scars. Professional procedures like fractional laser or TCA CROSS are needed for deep scars."
    },
    "Atopic Dermatitis": {
        "display_name": "Atopic Dermatitis (Eczema)",
        "category": "Inflammatory",
        "description": "A chronic inflammatory skin condition causing dry, itchy, red patches. Often associated with allergies and asthma ('atopic triad').",
        "severity": "moderate",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Genetic (filaggrin gene mutation)", "Immune dysfunction", "Environmental triggers", "Stress"],
        "symptoms": ["Intense itching", "Dry, cracked skin", "Red or dark patches", "Thickened skin (lichenification)"],
        "treatments": {
            "otc": ["Ceramide moisturizers (CeraVe, Vanicream)", "Colloidal oatmeal baths", "1% hydrocortisone (short-term)"],
            "prescription": ["Topical corticosteroids", "Tacrolimus/pimecrolimus", "Dupilumab (Dupixent) for severe cases"],
            "natural": ["Oatmeal baths", "Coconut oil (gentle)", "Wet wrap therapy"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Fragrance-free cream cleanser (or water only)", "note": "Never use soap"},
                {"step": "Treatment", "product": "Prescription topical (if prescribed)", "note": "Apply to affected areas"},
                {"step": "Moisturizer", "product": "Thick ceramide cream", "note": "Apply within 3 min of washing"},
                {"step": "Sunscreen", "product": "Mineral SPF 30+ for sensitive skin", "note": "Avoid chemical filters"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Lukewarm water or gentle wash", "note": "Short showers (<10 min)"},
                {"step": "Treatment", "product": "Prescription topical steroid (if flaring)", "note": "As directed"},
                {"step": "Moisturizer", "product": "Healing ointment or thick cream", "note": "Seal in moisture"}
            ],
            "weekly": ["Colloidal oatmeal bath (2x/week when flaring)", "Wash bedding in fragrance-free detergent"]
        },
        "when_to_see_doctor": "If itching disrupts sleep, if skin becomes infected (oozing, crusting), or if OTC moisturizers aren't enough.",
        "medical_explanation": "Atopic dermatitis involves a defective skin barrier and overactive immune response. Maintaining the moisture barrier is the cornerstone of management."
    },
    "Basal Cell Carcinoma (BCC)": {
        "display_name": "Basal Cell Carcinoma",
        "category": "Skin Cancer",
        "description": "The most common type of skin cancer. It grows slowly and rarely metastasizes, but can cause significant local tissue destruction if untreated.",
        "severity": "severe",
        "risk_level": "high",
        "is_cancerous": True,
        "urgency": "urgent",
        "causes": ["Chronic UV exposure", "Fair skin", "History of sunburns", "Age >50", "Immunosuppression"],
        "symptoms": ["Pearly or waxy bump", "Flat flesh-colored lesion", "Bleeding or scabbing sore that heals and returns", "Rolled borders"],
        "treatments": {
            "otc": ["No OTC treatment — requires medical intervention"],
            "prescription": ["Mohs micrographic surgery", "Excisional surgery", "Cryotherapy", "Topical imiquimod (superficial BCC)", "Radiation therapy"],
            "natural": ["No natural treatments — surgery is required"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Sunscreen", "product": "SPF 50+ broad-spectrum", "note": "CRITICAL — reapply every 2 hours"},
                {"step": "Protection", "product": "Wide-brim hat + UV-protective clothing", "note": "Physical sun protection"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Gentle cleanser", "note": "Be gentle around surgical sites"},
                {"step": "Moisturizer", "product": "Healing moisturizer", "note": "Post-treatment skin repair"}
            ],
            "weekly": ["Monthly full-body skin self-exam", "Annual dermatologist skin check"]
        },
        "when_to_see_doctor": "IMMEDIATELY — any suspicious lesion should be evaluated promptly. Early detection = better outcomes.",
        "medical_explanation": "BCC arises from basal cells in the epidermis. While it rarely metastasizes, it can invade locally and destroy surrounding tissue, including cartilage and bone. Surgery is curative in >95% of cases."
    },
    "Benign Keratosis-like Lesions (BKL)": {
        "display_name": "Benign Keratosis",
        "category": "Benign Growth",
        "description": "Non-cancerous growths including solar lentigines (sun spots), seborrheic keratoses, and lichen planus-like keratoses. Common with aging.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Sun exposure (solar lentigines)", "Aging", "Genetics", "Skin friction"],
        "symptoms": ["Brown/tan patches", "Waxy, stuck-on appearance", "Well-defined borders", "Can be rough or smooth"],
        "treatments": {
            "otc": ["Typically no treatment needed", "Sunscreen to prevent new spots", "Alpha hydroxy acids for mild spots"],
            "prescription": ["Cryotherapy (freezing)", "Laser treatment", "Curettage (scraping)"],
            "natural": ["Vitamin C serum", "Licorice root extract"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Gentle cleanser", "note": "Standard"},
                {"step": "Treatment", "product": "Vitamin C serum", "note": "Brightening"},
                {"step": "Moisturizer", "product": "Regular moisturizer", "note": "As needed"},
                {"step": "Sunscreen", "product": "SPF 50 broad-spectrum", "note": "Prevent new spots"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Gentle cleanser", "note": "Standard"},
                {"step": "Treatment", "product": "Glycolic acid toner", "note": "Gradual fade"},
                {"step": "Moisturizer", "product": "Night cream", "note": "Standard"}
            ],
            "weekly": ["Monitor any changes in size, shape, or color"]
        },
        "when_to_see_doctor": "If a lesion changes rapidly, bleeds, or has irregular borders — rule out melanoma.",
        "medical_explanation": "BKL are benign and generally harmless. The main concern is distinguishing them from melanoma, which can sometimes look similar."
    },
    "Eczema": {
        "display_name": "Eczema (Dermatitis)",
        "category": "Inflammatory",
        "description": "General term for inflammatory skin conditions causing itchy, red, dry, cracked skin. Includes contact dermatitis and nummular eczema.",
        "severity": "moderate",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Irritants (soaps, detergents)", "Allergens", "Dry climate", "Stress", "Genetic factors"],
        "symptoms": ["Itchy dry patches", "Redness", "Cracking and flaking", "Weeping or crusting when severe"],
        "treatments": {
            "otc": ["Fragrance-free moisturizers", "1% hydrocortisone cream", "Colloidal oatmeal products"],
            "prescription": ["Topical corticosteroids", "Calcineurin inhibitors", "Phototherapy"],
            "natural": ["Oatmeal baths", "Aloe vera", "Evening primrose oil"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Water or fragrance-free wash", "note": "Minimal cleansing"},
                {"step": "Moisturizer", "product": "Thick cream or ointment", "note": "Apply liberally"},
                {"step": "Sunscreen", "product": "Mineral SPF 30+ for sensitive skin", "note": "Avoid fragrances"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Lukewarm shower with gentle wash", "note": "< 10 minutes"},
                {"step": "Treatment", "product": "Topical steroid if flaring", "note": "As prescribed"},
                {"step": "Moisturizer", "product": "Petroleum jelly or healing ointment", "note": "Immediately after bathing"}
            ],
            "weekly": ["Identify and avoid triggers", "Use humidifier in dry weather"]
        },
        "when_to_see_doctor": "If eczema is not controlled with OTC moisturizers, if skin becomes infected, or if it significantly affects quality of life.",
        "medical_explanation": "Eczema is driven by a combination of genetic barrier defects and immune dysregulation. The itch-scratch cycle worsens the condition."
    },
    "hidradenitis-suppurativa": {
        "display_name": "Hidradenitis Suppurativa",
        "category": "Inflammatory",
        "description": "A chronic, painful skin condition causing lumps, abscesses, and tunnels under the skin, typically in areas where skin rubs together.",
        "severity": "severe",
        "risk_level": "moderate",
        "is_cancerous": False,
        "urgency": "soon",
        "causes": ["Blocked hair follicles", "Immune system dysfunction", "Genetics", "Hormonal factors", "Smoking"],
        "symptoms": ["Painful lumps in armpits/groin/buttocks", "Tunnels under skin", "Scarring", "Drainage of pus"],
        "treatments": {
            "otc": ["Antibacterial washes (benzoyl peroxide, chlorhexidine)", "Warm compresses"],
            "prescription": ["Adalimumab (Humira)", "Antibiotics (doxycycline, clindamycin)", "Surgical drainage/excision"],
            "natural": ["Zinc supplements", "Anti-inflammatory diet", "Smoking cessation"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Benzoyl peroxide wash 5%", "note": "On affected areas"},
                {"step": "Treatment", "product": "Prescription topical (if prescribed)", "note": "As directed"},
                {"step": "Protection", "product": "Loose-fitting breathable clothing", "note": "Reduce friction"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Chlorhexidine wash", "note": "Antibacterial"},
                {"step": "Treatment", "product": "Warm compress (15 min)", "note": "On painful lumps"},
                {"step": "Moisturizer", "product": "Zinc-based cream", "note": "Anti-inflammatory"}
            ],
            "weekly": ["Do NOT squeeze or lance abscesses at home"]
        },
        "when_to_see_doctor": "At the first sign of recurring lumps — early treatment prevents progression and tunneling.",
        "medical_explanation": "HS is a chronic, relapsing condition that requires long-term management. It is underdiagnosed and undertreated, with many patients waiting years for correct diagnosis."
    },
    "Melanocytic Nevi (NV)": {
        "display_name": "Melanocytic Nevi (Moles)",
        "category": "Benign Growth",
        "description": "Common benign growths of pigment-producing cells (melanocytes). Most moles are harmless but should be monitored for changes.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Genetic predisposition", "Sun exposure", "Fair skin & many nevi = higher melanoma risk"],
        "symptoms": ["Round/oval shaped", "Uniform color (brown/tan)", "Well-defined borders", "Usually <6mm"],
        "treatments": {
            "otc": ["No treatment needed", "Sunscreen to protect"],
            "prescription": ["Excision (if cosmetically unwanted)", "Biopsy if suspicious changes"],
            "natural": ["Sun protection"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Regular gentle cleanser", "note": "Standard"},
                {"step": "Moisturizer", "product": "Regular moisturizer", "note": "Standard"},
                {"step": "Sunscreen", "product": "SPF 30-50", "note": "Protect moles from UV damage"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Regular cleanser", "note": "Standard"},
                {"step": "Moisturizer", "product": "Night moisturizer", "note": "Standard"}
            ],
            "weekly": ["Monthly ABCDE self-check", "Annual dermatologist skin exam"]
        },
        "when_to_see_doctor": "If any mole changes per ABCDE criteria: Asymmetry, Border irregularity, Color changes, Diameter >6mm, Evolving.",
        "medical_explanation": "Most melanocytic nevi are benign. However, having >50 moles increases melanoma risk. Regular monitoring with the ABCDE criteria is essential."
    },
    "Melanoma": {
        "display_name": "Melanoma",
        "category": "Skin Cancer",
        "description": "The most dangerous form of skin cancer, arising from melanocytes. Melanoma can metastasize rapidly and be life-threatening if not caught early.",
        "severity": "critical",
        "risk_level": "critical",
        "is_cancerous": True,
        "urgency": "emergency",
        "causes": ["Intense UV exposure/sunburns", "Fair skin, light eyes", "Family history", "Many moles (>50)", "Immunosuppression"],
        "symptoms": ["Asymmetric mole", "Irregular borders", "Multiple colors (brown, black, red, white, blue)", "Growing or changing lesion", "Diameter >6mm"],
        "treatments": {
            "otc": ["No OTC treatment — requires immediate medical intervention"],
            "prescription": ["Wide local excision surgery", "Sentinel lymph node biopsy", "Immunotherapy (pembrolizumab, nivolumab)", "Targeted therapy (BRAF inhibitors)"],
            "natural": ["No natural treatments — surgery and medical treatment are essential"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Sunscreen", "product": "SPF 50+ broad-spectrum (CRITICAL)", "note": "Reapply every 2 hours"},
                {"step": "Protection", "product": "UV-protective clothing, hat, sunglasses", "note": "Physical barriers essential"}
            ],
            "evening": [
                {"step": "Monitoring", "product": "Full-body skin self-exam monthly", "note": "Use ABCDE criteria"},
                {"step": "Moisturizer", "product": "Gentle moisturizer", "note": "Post-surgical skin care"}
            ],
            "weekly": ["Avoid tanning beds (NEVER)", "Seek shade during peak UV hours (10am-4pm)"]
        },
        "when_to_see_doctor": "IMMEDIATELY — melanoma is a medical emergency. Any suspicious lesion needs urgent biopsy. Early melanoma (Stage I) has >95% survival rate; late-stage is much lower.",
        "medical_explanation": "Melanoma is the deadliest skin cancer because it can metastasize to lymph nodes, lungs, brain, and other organs. The key to survival is EARLY DETECTION. The 5-year survival rate drops from 99% (localized) to 30% (distant metastasis)."
    },
    "perioral-dermatitis": {
        "display_name": "Perioral Dermatitis",
        "category": "Inflammatory",
        "description": "An inflammatory rash around the mouth, nose, and sometimes eyes. Often mistaken for acne or eczema. Commonly triggered by topical steroids.",
        "severity": "moderate",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Topical corticosteroid overuse", "Fluorinated toothpaste", "Heavy skincare products", "Hormonal changes"],
        "symptoms": ["Red bumps around mouth and nose", "Scaling", "Burning/stinging sensation", "Clear zone around lip border"],
        "treatments": {
            "otc": ["Stop ALL topical steroids", "Switch to SLS-free toothpaste", "Minimal skincare"],
            "prescription": ["Topical metronidazole", "Oral doxycycline", "Topical erythromycin"],
            "natural": ["Zinc-based moisturizer", "Simplify skincare routine drastically"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Water only or ultra-gentle cleanser", "note": "Zero actives"},
                {"step": "Treatment", "product": "Prescription metronidazole (if prescribed)", "note": "As directed"},
                {"step": "Moisturizer", "product": "Simple zinc-based moisturizer", "note": "Minimal ingredients"},
                {"step": "Sunscreen", "product": "Mineral sunscreen only", "note": "Avoid chemical filters"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Gentle micellar water", "note": "No rubbing"},
                {"step": "Treatment", "product": "Prescription topical", "note": "As directed"},
                {"step": "Moisturizer", "product": "Minimal moisturizer", "note": "Only if needed"}
            ],
            "weekly": ["Avoid: steroids, retinoids, AHAs, BHAs", "Use fluoride-free toothpaste"]
        },
        "when_to_see_doctor": "If the rash persists after stopping steroids and simplifying skincare. A course of oral antibiotics often resolves it.",
        "medical_explanation": "Perioral dermatitis paradoxically worsens with topical steroids, creating a dependency cycle. The first and most important step is stopping all steroids."
    },
    "pigmentation": {
        "display_name": "Hyperpigmentation / Melasma",
        "category": "Pigmentary Disorder",
        "description": "Excess melanin production causing dark patches on the skin. Includes melasma, post-inflammatory hyperpigmentation (PIH), and sun spots.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Sun exposure", "Hormonal changes (pregnancy, birth control)", "Post-inflammatory (after acne, injury)", "Medications"],
        "symptoms": ["Dark patches or spots", "Uneven skin tone", "Commonly on face, hands", "Worsens with sun exposure"],
        "treatments": {
            "otc": ["Vitamin C serum", "Niacinamide 10%", "Alpha arbutin", "Azelaic acid 10%", "Tranexamic acid"],
            "prescription": ["Hydroquinone 4%", "Tretinoin", "Chemical peels", "Laser therapy"],
            "natural": ["Licorice root extract", "Kojic acid"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Gentle cleanser", "note": "Standard"},
                {"step": "Treatment", "product": "Vitamin C serum 15-20%", "note": "Antioxidant + brightening"},
                {"step": "Treatment", "product": "Niacinamide serum 10%", "note": "Melanin transfer inhibitor"},
                {"step": "Moisturizer", "product": "Hydrating moisturizer", "note": "Standard"},
                {"step": "Sunscreen", "product": "SPF 50 tinted mineral sunscreen", "note": "THE MOST IMPORTANT STEP"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Double cleanse", "note": "Remove sunscreen thoroughly"},
                {"step": "Treatment", "product": "Azelaic acid 15-20% or tretinoin", "note": "Alternate nights"},
                {"step": "Treatment", "product": "Alpha arbutin serum", "note": "Tyrosinase inhibitor"},
                {"step": "Moisturizer", "product": "Barrier-repair cream", "note": "Essential when using actives"}
            ],
            "weekly": ["Reapply sunscreen every 2 hours when outdoors", "Be patient — results take 3-6 months"]
        },
        "when_to_see_doctor": "If pigmentation is worsening despite sun protection, or if you want faster results with prescription treatments.",
        "medical_explanation": "Sun protection is the single most important factor. Without SPF 50+, no treatment will be effective — UV exposure constantly triggers new melanin production."
    },
    "Psoriasis pictures Lichen Planus and related diseases": {
        "display_name": "Psoriasis / Lichen Planus",
        "category": "Autoimmune",
        "description": "Chronic autoimmune conditions. Psoriasis causes thick, scaly plaques. Lichen planus causes flat-topped purple patches. Both involve immune system overactivity.",
        "severity": "moderate",
        "risk_level": "moderate",
        "is_cancerous": False,
        "urgency": "soon",
        "causes": ["Autoimmune dysfunction", "Genetics", "Stress", "Infections", "Certain medications"],
        "symptoms": ["Thick silvery scales (psoriasis)", "Purple flat-topped lesions (lichen planus)", "Itching", "Joint pain (psoriatic arthritis)"],
        "treatments": {
            "otc": ["Coal tar shampoo/cream", "Salicylic acid (scale removal)", "Moisturizers"],
            "prescription": ["Topical corticosteroids", "Calcipotriol (vitamin D analog)", "Methotrexate", "Biologics (adalimumab, secukinumab)"],
            "natural": ["Dead Sea salt baths", "Aloe vera", "Turmeric supplements"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Gentle fragrance-free cleanser", "note": "Don't scrub plaques"},
                {"step": "Treatment", "product": "Topical corticosteroid (prescribed)", "note": "On active plaques"},
                {"step": "Moisturizer", "product": "Thick emollient cream", "note": "Apply generously"},
                {"step": "Sunscreen", "product": "SPF 30+ (controlled sun helps some psoriasis)", "note": "Discuss phototherapy with doctor"}
            ],
            "evening": [
                {"step": "Bath", "product": "Lukewarm bath with colloidal oatmeal", "note": "Soak 15 min"},
                {"step": "Treatment", "product": "Coal tar preparation or calcipotriol", "note": "As prescribed"},
                {"step": "Moisturizer", "product": "Petroleum jelly or thick ointment", "note": "Seal in moisture"}
            ],
            "weekly": ["Gentle scale removal (don't pick)", "Stress management (yoga, meditation)"]
        },
        "when_to_see_doctor": "If psoriasis covers >3% of body, if joints are painful/swollen (psoriatic arthritis), or if current treatment isn't working.",
        "medical_explanation": "Psoriasis involves accelerated skin cell turnover (3-4 days vs normal 28-30 days). It's a systemic disease with increased cardiovascular risk. Modern biologics can achieve near-complete clearance."
    },
    "rosacea": {
        "display_name": "Rosacea",
        "category": "Inflammatory",
        "description": "A chronic inflammatory condition causing facial redness, visible blood vessels, and sometimes acne-like bumps. Common in fair-skinned adults.",
        "severity": "moderate",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Vascular instability", "Demodex mites", "Genetic predisposition", "Triggers: alcohol, spicy food, heat, stress"],
        "symptoms": ["Persistent facial redness", "Visible blood vessels (telangiectasia)", "Papules and pustules", "Burning/stinging", "Eye irritation (ocular rosacea)"],
        "treatments": {
            "otc": ["Azelaic acid gel 15%", "Gentle zinc-based products", "Green-tinted primer (cosmetic)"],
            "prescription": ["Topical metronidazole", "Topical ivermectin (Soolantra)", "Oral doxycycline (low-dose)", "IPL/laser for blood vessels"],
            "natural": ["Green tea compresses", "Niacinamide", "Trigger avoidance"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Ultra-gentle cream cleanser", "note": "Cool water, pat dry"},
                {"step": "Treatment", "product": "Azelaic acid 15%", "note": "Anti-inflammatory + anti-redness"},
                {"step": "Moisturizer", "product": "Fragrance-free, minimal-ingredient cream", "note": "Soothing"},
                {"step": "Sunscreen", "product": "Mineral SPF 50 (zinc oxide)", "note": "CRUCIAL — UV is a major trigger"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Micellar water", "note": "No rubbing"},
                {"step": "Treatment", "product": "Prescription ivermectin or metronidazole", "note": "As directed"},
                {"step": "Moisturizer", "product": "Ceramide barrier cream", "note": "Repair damaged barrier"}
            ],
            "weekly": ["Track triggers in a diary", "Avoid: hot drinks, alcohol, spicy food, extreme temps"]
        },
        "when_to_see_doctor": "If redness is persistent, if eyes are affected (ocular rosacea can damage vision), or if nose is thickening (rhinophyma).",
        "medical_explanation": "Rosacea has no cure, but can be well-controlled with the right treatment. The key is identifying and avoiding personal triggers while using consistent anti-inflammatory treatment."
    },
    "Seborrheic Keratoses and other Benign Tumors": {
        "display_name": "Seborrheic Keratosis",
        "category": "Benign Growth",
        "description": "Very common benign skin growths that appear as waxy, stuck-on, brown/tan raised lesions. Completely harmless but can be cosmetically bothersome.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Aging", "Genetics", "Sun exposure", "Skin friction"],
        "symptoms": ["Waxy, stuck-on appearance", "Brown/tan/black color", "Raised", "Can be itchy if irritated"],
        "treatments": {
            "otc": ["No treatment needed", "Can be left alone safely"],
            "prescription": ["Cryotherapy", "Curettage", "Electrodesiccation", "Laser removal"],
            "natural": ["None needed — cosmetic removal only"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Regular cleanser", "note": "Standard"},
                {"step": "Moisturizer", "product": "Regular moisturizer", "note": "Standard"},
                {"step": "Sunscreen", "product": "SPF 30+", "note": "General skin health"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Regular cleanser", "note": "Standard"},
                {"step": "Moisturizer", "product": "Regular moisturizer", "note": "Standard"}
            ],
            "weekly": ["Monitor for changes", "Don't pick at growths"]
        },
        "when_to_see_doctor": "If a growth changes rapidly, if you want cosmetic removal, or if it becomes irritated from clothing/jewelry friction.",
        "medical_explanation": "Seborrheic keratoses are the most common benign skin tumors. They have zero malignant potential. The main clinical importance is distinguishing them from melanoma."
    },
    "Tinea Ringworm Candidiasis and other Fungal Infections": {
        "display_name": "Fungal Skin Infection",
        "category": "Infection",
        "description": "Fungal infections of the skin including ringworm (tinea), candidiasis (yeast), and athlete's foot. Caused by dermatophytes or Candida species.",
        "severity": "moderate",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["Warm/moist environments", "Direct contact with infected person/animal", "Compromised immunity", "Tight clothing"],
        "symptoms": ["Ring-shaped rash (tinea)", "Red, itchy patches", "Scaling at borders", "White patches in skin folds (candidiasis)"],
        "treatments": {
            "otc": ["Clotrimazole 1% cream", "Terbinafine cream (Lamisil)", "Miconazole", "Antifungal powder"],
            "prescription": ["Oral terbinafine (widespread/resistant)", "Oral fluconazole (candidiasis)", "Griseofulvin (scalp ringworm)"],
            "natural": ["Tea tree oil (diluted)", "Keep area clean and dry"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Antifungal wash", "note": "On affected areas"},
                {"step": "Treatment", "product": "Antifungal cream (clotrimazole/terbinafine)", "note": "Apply beyond borders of rash"},
                {"step": "Protection", "product": "Antifungal powder on prone areas", "note": "Keep dry"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Gentle cleanser", "note": "Clean affected area"},
                {"step": "Treatment", "product": "Antifungal cream", "note": "Continue 1-2 weeks after rash clears"},
                {"step": "Protection", "product": "Breathable cotton clothing", "note": "Reduce moisture"}
            ],
            "weekly": ["Wash towels/bedding in hot water", "Don't share personal items", "Treat pets if they're the source"]
        },
        "when_to_see_doctor": "If infection doesn't improve after 2 weeks of OTC antifungal, if it involves the scalp or nails, or if you're immunocompromised.",
        "medical_explanation": "Fungal infections thrive in warm, moist environments. The most important aspects of treatment are completing the full course of antifungal medication and keeping the area dry."
    },
    "Warts Molluscum and other Viral Infections": {
        "display_name": "Viral Skin Infection (Warts/Molluscum)",
        "category": "Infection",
        "description": "Viral skin infections including warts (HPV), molluscum contagiosum (poxvirus). Warts appear as rough bumps; molluscum as pearly dome-shaped papules.",
        "severity": "mild",
        "risk_level": "low",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": ["HPV (warts)", "Poxvirus (molluscum)", "Direct contact", "Compromised skin barrier", "Immunosuppression"],
        "symptoms": ["Rough, cauliflower-like bumps (warts)", "Pearly dome papules with central dimple (molluscum)", "Can spread to other body areas"],
        "treatments": {
            "otc": ["Salicylic acid 17% (warts)", "Cryotherapy kits (OTC freeze)", "Duct tape occlusion"],
            "prescription": ["Professional cryotherapy", "Cantharidin (blistering agent)", "Imiquimod cream", "Curettage"],
            "natural": ["Immune support", "Time (many resolve spontaneously in 1-2 years)"]
        },
        "skincare_routine": {
            "morning": [
                {"step": "Cleanser", "product": "Regular cleanser", "note": "Wash hands after touching lesions"},
                {"step": "Treatment", "product": "Salicylic acid on warts (if using)", "note": "Protect surrounding skin"},
                {"step": "Protection", "product": "Cover lesions to prevent spread", "note": "Bandage or tape"}
            ],
            "evening": [
                {"step": "Cleanser", "product": "Regular cleanser", "note": "Standard"},
                {"step": "Treatment", "product": "Salicylic acid treatment", "note": "Apply, let dry, cover"},
                {"step": "Protection", "product": "Don't share towels/razors", "note": "Prevent spread"}
            ],
            "weekly": ["File down dead skin on warts with emery board", "Discard used files/pumice"]
        },
        "when_to_see_doctor": "If lesions are on the face or genitals, if spreading rapidly, if OTC treatment fails after 3 months, or if immunocompromised.",
        "medical_explanation": "Both warts and molluscum are self-limiting in immunocompetent individuals, but treatment can speed resolution and prevent spread. HPV vaccination can prevent some types of warts."
    }
}

# ─────────────────────────────────────────────────────────────
# Risk Level Mapping
# ─────────────────────────────────────────────────────────────

RISK_LEVELS = {
    "low": {"label": "Low Risk", "color": "green", "action": "Monitor with routine skincare and follow-up"},
    "moderate": {"label": "Moderate Risk", "color": "amber", "action": "Consider scheduling a dermatologist appointment"},
    "high": {"label": "High Risk", "color": "red", "action": "Consult a dermatologist as soon as possible"},
    "critical": {"label": "Critical Risk", "color": "red", "action": "Seek immediate medical evaluation — this could be life-threatening"}
}


# ─────────────────────────────────────────────────────────────
# Ingredient Safety Database
# ─────────────────────────────────────────────────────────────

INGREDIENT_DATABASE = {
    "hydroquinone": {"safety": "caution", "description": "Effective skin lightener but can cause ochronosis with prolonged use. Use only under dermatologist supervision.", "acne_risk": False, "allergen_risk": False},
    "retinol": {"safety": "safe", "description": "Vitamin A derivative that promotes cell turnover. Effective for anti-aging and acne. Start slowly to avoid irritation.", "acne_risk": False, "allergen_risk": False},
    "tretinoin": {"safety": "safe", "description": "Prescription-strength retinoid. Gold standard for acne and anti-aging. Causes initial purging.", "acne_risk": False, "allergen_risk": False},
    "benzoyl peroxide": {"safety": "safe", "description": "Antibacterial that kills C. acnes. Available 2.5-10%. Lower concentrations equally effective with less irritation.", "acne_risk": False, "allergen_risk": True},
    "salicylic acid": {"safety": "safe", "description": "BHA that penetrates pores to dissolve sebum. Excellent for blackheads and oily skin.", "acne_risk": False, "allergen_risk": False},
    "niacinamide": {"safety": "safe", "description": "Vitamin B3 — anti-inflammatory, brightening, sebum-regulating. Well-tolerated by most skin types.", "acne_risk": False, "allergen_risk": False},
    "hyaluronic acid": {"safety": "safe", "description": "Humectant that draws moisture to skin. Safe for all skin types. Use on damp skin.", "acne_risk": False, "allergen_risk": False},
    "vitamin c": {"safety": "safe", "description": "Antioxidant that brightens and stimulates collagen. L-ascorbic acid is most potent but least stable.", "acne_risk": False, "allergen_risk": False},
    "glycolic acid": {"safety": "safe", "description": "AHA exfoliant that improves texture and tone. Start with low concentrations (5-8%).", "acne_risk": False, "allergen_risk": False},
    "lactic acid": {"safety": "safe", "description": "Gentle AHA suitable for sensitive skin. Exfoliates and hydrates simultaneously.", "acne_risk": False, "allergen_risk": False},
    "zinc oxide": {"safety": "safe", "description": "Mineral sunscreen ingredient. Also anti-inflammatory. Safe for sensitive and acne-prone skin.", "acne_risk": False, "allergen_risk": False},
    "titanium dioxide": {"safety": "safe", "description": "Mineral sunscreen ingredient. May leave white cast on darker skin tones.", "acne_risk": False, "allergen_risk": False},
    "coconut oil": {"safety": "caution", "description": "Highly comedogenic (pore-clogging). Good for body moisturizing but avoid on face if acne-prone.", "acne_risk": True, "allergen_risk": False},
    "isopropyl myristate": {"safety": "caution", "description": "Emollient that is highly comedogenic. Found in many cosmetics. Avoid if acne-prone.", "acne_risk": True, "allergen_risk": False},
    "sodium lauryl sulfate": {"safety": "caution", "description": "Harsh surfactant that strips natural oils and can damage skin barrier. Switch to gentler alternatives.", "acne_risk": False, "allergen_risk": True},
    "fragrance": {"safety": "caution", "description": "Leading cause of contact dermatitis. 'Parfum' can contain hundreds of undisclosed chemicals.", "acne_risk": False, "allergen_risk": True},
    "alcohol denat": {"safety": "caution", "description": "Drying alcohol that damages skin barrier. Small amounts in formulations are usually fine, but avoid in high concentrations.", "acne_risk": False, "allergen_risk": False},
    "parabens": {"safety": "caution", "description": "Preservatives with weak estrogenic activity. Generally recognized as safe at cosmetic concentrations, but alternatives exist.", "acne_risk": False, "allergen_risk": True},
    "formaldehyde": {"safety": "harmful", "description": "Known carcinogen and strong sensitizer. Banned in many countries. Also released by formaldehyde-releasing preservatives.", "acne_risk": False, "allergen_risk": True},
    "mercury": {"safety": "harmful", "description": "Toxic heavy metal sometimes found in illegal skin-lightening products. Can cause kidney damage and neurological effects.", "acne_risk": False, "allergen_risk": False},
    "lead": {"safety": "harmful", "description": "Toxic heavy metal that can be found as a contaminant in some cosmetics. No safe level of lead exposure.", "acne_risk": False, "allergen_risk": False},
    "mineral oil": {"safety": "safe", "description": "Non-comedogenic occlusive moisturizer. Cosmetic-grade mineral oil is highly purified and safe.", "acne_risk": False, "allergen_risk": False},
    "ceramides": {"safety": "safe", "description": "Natural skin lipids essential for barrier function. Excellent for all skin types, especially eczema and dry skin.", "acne_risk": False, "allergen_risk": False},
    "peptides": {"safety": "safe", "description": "Signal molecules that stimulate collagen production. Well-tolerated and effective for anti-aging.", "acne_risk": False, "allergen_risk": False},
    "azelaic acid": {"safety": "safe", "description": "Multi-purpose acid: anti-acne, anti-rosacea, brightening. Safe during pregnancy. Excellent for sensitive skin.", "acne_risk": False, "allergen_risk": False},
    "tea tree oil": {"safety": "caution", "description": "Natural antibacterial/antifungal. Must be diluted (5% max). Can cause contact dermatitis in some people.", "acne_risk": False, "allergen_risk": True},
    "sulfur": {"safety": "safe", "description": "Antibacterial and keratolytic. Good for acne and fungal conditions. Has a distinctive smell.", "acne_risk": False, "allergen_risk": False},
    "centella asiatica": {"safety": "safe", "description": "Soothing plant extract (aka cica). Excellent for wound healing, anti-inflammation, and barrier repair.", "acne_risk": False, "allergen_risk": False},
    "oxybenzone": {"safety": "harmful", "description": "Chemical sunscreen filter. Known endocrine disruptor and linked to coral reef bleaching. Found in many older sunscreens.", "acne_risk": False, "allergen_risk": True},
    "octinoxate": {"safety": "caution", "description": "Chemical sunscreen filter. Some evidence of endocrine disruption and environmental harm. Often used with oxybenzone.", "acne_risk": False, "allergen_risk": True},
    "dimethicone": {"safety": "safe", "description": "Non-comedogenic silicone that forms a breathable barrier on skin. Prevents transepidermal water loss. Excellent for dry skin.", "acne_risk": False, "allergen_risk": False},
    "phenoxyethanol": {"safety": "safe", "description": "Common, effective preservative used as an alternative to parabens. Safe at cosmetic concentrations (up to 1%).", "acne_risk": False, "allergen_risk": False},
    "bht": {"safety": "caution", "description": "Butylated hydroxytoluene. Synthetic antioxidant preservative. Controversial due to potential endocrine disruption at high doses, but generally recognized as safe in trace cosmetic amounts.", "acne_risk": False, "allergen_risk": False},
    "polyethylene glycol": {"safety": "caution", "description": "PEGs are thickeners and solvents. Generally safe, but can be contaminated with 1,4-dioxane (a carcinogen) depending on manufacturing quality.", "acne_risk": False, "allergen_risk": False},
    "retinyl palmitate": {"safety": "safe", "description": "Weakest OTC retinoid (vitamin A ester). Very gentle, but also least effective for anti-aging. Some controversy regarding sun exposure, best used at night.", "acne_risk": False, "allergen_risk": False},
    "panthenol": {"safety": "safe", "description": "Vitamin B5. Excellent humectant, soothing agent, and barrier repair ingredient.", "acne_risk": False, "allergen_risk": False},
    "squalane": {"safety": "safe", "description": "Highly stable, non-comedogenic oil derived from olives or sugarcane. Biocompatible with skin sebum.", "acne_risk": False, "allergen_risk": False},
    "jojoba oil": {"safety": "safe", "description": "Liquid wax ester that closely mimics human sebum. Non-comedogenic and good for balancing oil production.", "acne_risk": False, "allergen_risk": False},
    "shea butter": {"safety": "safe", "description": "Rich emollient high in fatty acids. Excellent for dry skin, but can be heavy/comedogenic for very oily skin.", "acne_risk": False, "allergen_risk": False},
    "witch hazel": {"safety": "caution", "description": "Natural astringent. Can be soothing for acne, but commercial extracts often contain high levels of drying alcohol. Avoid if daily.", "acne_risk": False, "allergen_risk": False},
    "rosehip oil": {"safety": "safe", "description": "Plant oil rich in linoleic acid and provitamin A. Excellent for acne-prone skin and fading hyperpigmentation.", "acne_risk": False, "allergen_risk": False},
    "glycerin": {"safety": "safe", "description": "One of the most effective, well-tolerated, and inexpensive humectants. Found in almost all moisturizers.", "acne_risk": False, "allergen_risk": False},
    "bakuchiol": {"safety": "safe", "description": "Plant-derived alternative to retinol. Offers similar anti-aging benefits without the irritation or sun sensitivity. Safe during pregnancy.", "acne_risk": False, "allergen_risk": False},
    "triclosan": {"safety": "harmful", "description": "Antibacterial agent banned in OTC consumer washes by FDA due to endocrine disruption and bacterial resistance concerns.", "acne_risk": False, "allergen_risk": False},
    "phthalates": {"safety": "harmful", "description": "Used as plasticizers and in synthetic fragrances. Known endocrine disruptors linked to reproductive issues.", "acne_risk": False, "allergen_risk": False},
    "alpha arbutin": {"safety": "safe", "description": "Effective skin-brightening derivative of hydroquinone. Much safer alternative for treating hyperpigmentation.", "acne_risk": False, "allergen_risk": False},
    "allantoin": {"safety": "safe", "description": "Highly effective soothing and skin-conditioning agent extracted from the comfrey plant.", "acne_risk": False, "allergen_risk": False},
}


def get_condition_info(class_name: str) -> dict:
    """Get detailed information about a skin condition."""
    info = CONDITION_DATABASE.get(class_name)
    if info:
        return info
    for key, val in CONDITION_DATABASE.items():
        if key.lower() == class_name.lower():
            return val
    return {
        "display_name": class_name,
        "category": "Unknown",
        "description": "Information not available for this condition.",
        "severity": "unknown",
        "risk_level": "moderate",
        "is_cancerous": False,
        "urgency": "routine",
        "causes": [],
        "symptoms": [],
        "treatments": {"otc": [], "prescription": [], "natural": []},
        "skincare_routine": {"morning": [], "evening": [], "weekly": []},
        "when_to_see_doctor": "Consult a dermatologist for any persistent skin concern.",
        "medical_explanation": "Please consult a healthcare professional for more information."
    }


def check_ingredient_safety(ingredient_name: str) -> dict:
    """Check the safety of a skincare ingredient."""
    name_lower = ingredient_name.lower().strip()
    if name_lower in INGREDIENT_DATABASE:
        return {"ingredient": ingredient_name, **INGREDIENT_DATABASE[name_lower]}
    for key, val in INGREDIENT_DATABASE.items():
        if key in name_lower or name_lower in key:
            return {"ingredient": ingredient_name, **val}
    return {
        "ingredient": ingredient_name,
        "safety": "unknown",
        "description": f"'{ingredient_name}' is not in our database. Consult a dermatologist or check resources like INCIDecoder.com for detailed information.",
        "acne_risk": None,
        "allergen_risk": None
    }


def generate_skincare_routine(condition: str, skin_type: str = "normal") -> dict:
    """Generate a personalized skincare routine based on condition and skin type."""
    info = get_condition_info(condition)
    routine = info.get("skincare_routine", {})

    adjustments = []
    if skin_type == "oily":
        adjustments.append("Use gel-based and oil-free products. Consider double-cleansing in the evening.")
    elif skin_type == "dry":
        adjustments.append("Use cream-based products. Apply moisturizer on damp skin. Consider adding facial oil at night.")
    elif skin_type == "sensitive":
        adjustments.append("Patch test all new products. Introduce one product at a time. Avoid fragrances and essential oils.")
    elif skin_type == "combination":
        adjustments.append("Use lighter products on T-zone and richer products on cheeks. Multi-masking can help.")

    return {
        "condition": info.get("display_name", condition),
        "skin_type": skin_type,
        "morning": routine.get("morning", []),
        "evening": routine.get("evening", []),
        "weekly": routine.get("weekly", []),
        "adjustments": adjustments,
        "disclaimer": "This routine is AI-generated and not a substitute for professional dermatological advice. Consult a dermatologist before starting any new treatment."
    }
