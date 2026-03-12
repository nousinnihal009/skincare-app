// ──────────────────────────────────────────────────────────
// conditions.ts — Type contracts for the Medical Conditions Advisor
// ──────────────────────────────────────────────────────────

// ── Condition Keys ──────────────────────────────────────

export type ConditionKey =
  | 'atopic_dermatitis'
  | 'contact_dermatitis'
  | 'rosacea'
  | 'seborrheic_dermatitis'
  | 'psoriasis'
  | 'lichen_planus'
  | 'perioral_dermatitis'
  | 'fungal_acne'
  | 'ringworm'
  | 'warts'
  | 'molluscum_contagiosum'
  | 'impetigo'
  | 'cold_sores'
  | 'vitiligo'
  | 'melasma'
  | 'post_inflammatory_hyperpigmentation'
  | 'actinic_keratosis'
  | 'melanoma_risk'

// ── Enums / Literal Unions ──────────────────────────────

export type ConditionCategory = 'inflammatory' | 'infectious' | 'pigmentation' | 'high_risk'
export type ReferralUrgency = 'immediate' | 'soon' | 'routine' | 'not_required'
export type CarePlanPhase = 'immediate' | 'daily_am' | 'daily_pm' | 'weekly' | 'ongoing_management'
export type Severity = 'mild' | 'moderate' | 'severe'
export type SkinType = 'oily' | 'dry' | 'combination' | 'sensitive' | 'normal'
export type AgeGroup = 'teen' | 'twenties' | 'thirties' | 'forties_plus'
export type SymptomDuration =
  | 'less_than_1_week'
  | '1_to_4_weeks'
  | '1_to_6_months'
  | 'more_than_6_months'
  | 'chronic_recurring'
export type AffectedArea =
  | 'face'
  | 'scalp'
  | 'neck'
  | 'chest'
  | 'back'
  | 'arms'
  | 'legs'
  | 'hands'
  | 'feet'
  | 'genitals'
  | 'widespread'
export type KnownTrigger =
  | 'stress'
  | 'diet'
  | 'heat'
  | 'cold'
  | 'sun_exposure'
  | 'sweat'
  | 'specific_products'
  | 'hormonal'
  | 'unknown'
  | 'none'
export type CurrentTreatment =
  | 'prescription_topical'
  | 'prescription_oral'
  | 'otc_topical'
  | 'phototherapy'
  | 'biologics'
  | 'none'

// ── Response Sub-Models ─────────────────────────────────

export interface RedFlag {
  description: string
  urgency: 'see_doctor_today' | 'within_1_week' | 'within_1_month'
  action: string
}

export interface CarePlanStep {
  step: number
  phase: CarePlanPhase
  category: string
  recommendation: string
  why_explanation: string
  fallback_why: string
  is_otc_available: boolean
  avoid_if: string[]
  condition_safe: boolean
}

export interface IngredientEntry {
  ingredient: string
  reason: string
}

export interface TriggerEntry {
  trigger: string
  management_tip: string
  severity_impact: 'mild' | 'moderate' | 'severe'
}

export interface ConditionEducation {
  what_it_is: string
  what_causes_it: string
  is_contagious: boolean
  contagion_guidance: string | null
  is_curable: boolean
  typical_duration: string
  common_misconceptions: string[]
}

export interface WeatherSummary {
  condition: string
  temperature_c: number
  humidity_pct: number
  uv_index: number
  routine_impact: string
}

// ── Main Response ───────────────────────────────────────

export interface ConditionResponse {
  condition: ConditionKey
  condition_display_name: string
  category: ConditionCategory
  severity_assessed: Severity
  is_contagious: boolean
  education: ConditionEducation
  care_plan: CarePlanStep[]
  ingredients_to_seek: IngredientEntry[]
  ingredients_to_avoid: IngredientEntry[]
  trigger_guidance: TriggerEntry[]
  red_flags: RedFlag[]
  referral_recommended: boolean
  referral_urgency: ReferralUrgency
  when_to_see_doctor: string
  weather_context: WeatherSummary | null
  climate_care_note: string | null
  prescription_interaction_note: string | null
  medical_disclaimer: string
  llm_enriched: boolean
  generated_at: string
}

// ── Request ─────────────────────────────────────────────

export interface ConditionRequest {
  condition: ConditionKey
  severity: Severity
  skin_type: SkinType
  age_group: AgeGroup
  affected_areas: AffectedArea[]
  symptom_duration: SymptomDuration
  known_triggers: KnownTrigger[]
  current_treatments: CurrentTreatment[]
  location?: { lat: number; lon: number } | null
}

// ── Conditions List (GET /api/medical/conditions) ───────

export interface ConditionSummary {
  key: ConditionKey
  display_name: string
  category: ConditionCategory
  is_contagious: boolean
  is_curable: boolean
  severity_tier: 1 | 2 | 3
}

// ── Condition Preview (GET /api/medical/conditions/:key) ─

export interface ConditionPreview {
  key: ConditionKey
  display_name: string
  category: ConditionCategory
  is_contagious: boolean
  contagion_guidance: string | null
  what_it_is: string
  known_triggers: string[]
  red_flags_preview: string[]
}
