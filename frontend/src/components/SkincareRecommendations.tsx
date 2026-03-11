// ─────��────────────────────────────────────────────────────
// SkincareRecommendations.tsx — 5-Step Skincare Routine Wizard
// v2 — Extended with Step 5 (Health & Exposure)
// ──────────────────────────────────────────────────────────

import React, { useState } from 'react'
import { useForm, FormProvider, Controller, useFormContext } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import axiosInstance from '../lib/axios'
import { useLocation } from '../hooks/useLocation'
import type { AnalysisResult } from '../App'
import type {
  RoutineRequest,
  RoutineResponse,
  SkinType,
  PrimaryConcern,
  AgeGroup,
  SkinGoal,
  SpecialSituation,
} from '../types/skincare'
import {
  SKIN_TYPE_OPTIONS,
  PRIMARY_CONCERN_OPTIONS,
  AGE_GROUP_OPTIONS,
  SKIN_GOAL_OPTIONS,
  SPECIAL_SITUATION_OPTIONS,
} from '../types/skincare'
import WizardStep5 from './skincare/WizardStep5'
import RoutineDisplay from './skincare/RoutineDisplay'

// ── Constants ────────────────────────────────────────────
const TOTAL_STEPS = 5

const STEP_TITLES = [
  'Your Skin',
  'Your Concerns',
  'Your Goals',
  'Your Environment',
  'Health & Exposure',
]

const API_BASE = 'http://127.0.0.1:8000'

// ── Skin type icons ──────────────────────────────────────
const SKIN_TYPE_ICONS: Record<SkinType, string> = {
  oily: '💧',
  dry: '🏜️',
  combination: '⚖️',
  sensitive: '🌸',
  normal: '✨',
}

const CONCERN_ICONS: Record<PrimaryConcern, string> = {
  acne: '🔴',
  hyperpigmentation: '🟤',
  blackheads: '⚫',
  aging: '⏳',
  dullness: '😶‍🌫️',
  large_pores: '🔍',
  sun_damage: '☀️',
  maintenance: '🛡️',
}

const GOAL_ICONS: Record<SkinGoal, string> = {
  glass_skin: '🪞',
  glowing: '✨',
  brightening: '💡',
  minimalist: '🍃',
  dermatologist: '🩺',
}

// ── Props ───────────────────────────���────────────────────
interface Props {
  result: AnalysisResult | null
}

// =====================================================================
// Main Component
// =====================================================================

const SkincareRecommendations: React.FC<Props> = ({ result }) => {
  const [currentStep, setCurrentStep] = useState(1)
  const [submittedRequest, setSubmittedRequest] = useState<RoutineRequest | null>(null)

  const mutation = useMutation({
    mutationFn: (payload: RoutineRequest) =>
      axiosInstance
        .post<RoutineResponse>('/api/skincare-routine', payload)
        .then((r) => r.data),
    onError: () => {}, // error handled via mutation.isError inline
  })

  const methods = useForm<RoutineRequest>({
    defaultValues: {
      skin_type: 'normal',
      primary_concern: result?.prediction?.class_name?.includes('acne')
        ? 'acne'
        : 'maintenance',
      age_group: 'twenties',
      skin_goals: ['glowing'],
      special_situation: 'none',
      location: null,
      include_weekly: true,
      medical_condition: 'none',
      pollution_exposure: false,
    },
    mode: 'onChange',
  })

  const { handleSubmit, trigger, watch } = methods

  // ── Navigation ──────────────────────────────────────────
  const goNext = async () => {
    const valid = await trigger()
    if (valid && currentStep < TOTAL_STEPS) {
      setCurrentStep((s) => s + 1)
    }
  }

  const goBack = () => {
    if (currentStep > 1) {
      setCurrentStep((s) => s - 1)
    }
  }

  // ── Submit ──────────────────────────────────────────────
  const onSubmit = (data: RoutineRequest) => {
    setSubmittedRequest(data)
    mutation.mutate(data)
  }

  const resetWizard = () => {
    mutation.reset()
    setSubmittedRequest(null)
    setCurrentStep(1)
    methods.reset()
  }

  // ── If routine generated, show results ──────────────────
  if (mutation.isSuccess && mutation.data) {
    return (
      <div className="page-container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
        <div className="page-header">
          <h1 className="page-title animate-fade-in-up">🧴 Your Personalized Routine</h1>
          <p className="page-subtitle animate-fade-in-up stagger-1">
            Tailored to your unique skin profile, goals, and health considerations.
          </p>
        </div>

        <RoutineDisplay
          response={mutation.data}
          pollutionExposure={submittedRequest?.pollution_exposure ?? false}
        />

        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <button
            className="btn-primary"
            onClick={resetWizard}
            style={{ padding: '12px 32px' }}
          >
            ← Generate Another Routine
          </button>
        </div>

        <div className="disclaimer" style={{ marginTop: '24px' }}>
          <span>⚠️</span>
          <span>
            These are AI-generated suggestions, not medical prescriptions. Always
            consult a dermatologist before starting new products.
          </span>
        </div>
      </div>
    )
  }

  // ── Wizard UI ───────────────────────────────────────────
  return (
    <div className="page-container" style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">🧴 Skincare Routine</h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          Answer a few questions to get your personalized routine.
        </p>
      </div>

      {/* ── Progress Bar ── */}
      <div className="glass-card animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ color: 'var(--primary-300)', fontSize: '0.85rem', fontWeight: 600 }}>
            Step {currentStep} of {TOTAL_STEPS}
          </span>
          <span style={{ color: 'var(--dark-300)', fontSize: '0.8rem' }}>
            {STEP_TITLES[currentStep - 1]}
          </span>
        </div>
        <div
          style={{
            width: '100%',
            height: '4px',
            borderRadius: '2px',
            background: 'var(--dark-500)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${(currentStep / TOTAL_STEPS) * 100}%`,
              height: '100%',
              borderRadius: '2px',
              background: 'linear-gradient(90deg, #6C63FF, #A89CFF)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* ── Form Steps ── */}
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="glass-card animate-fade-in-up stagger-3" style={{ minHeight: '300px' }}>
            {/* Step 1 — Your Skin */}
            {currentStep === 1 && (
              <Step1SkinType />
            )}

            {/* Step 2 — Your Concerns */}
            {currentStep === 2 && (
              <Step2Concerns />
            )}

            {/* Step 3 — Your Goals */}
            {currentStep === 3 && (
              <Step3Goals />
            )}

            {/* Step 4 — Your Environment */}
            {currentStep === 4 && (
              <Step4Environment />
            )}

            {/* Step 5 — Health & Exposure */}
            {currentStep === 5 && (
              <WizardStep5 />
            )}
          </div>

          {/* ── Error Display ── */}
          {mutation.isError && (
            <div
              style={{
                marginTop: '16px',
                padding: '12px 16px',
                borderRadius: '10px',
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.3)',
                color: '#fca5a5',
                fontSize: '0.9rem',
              }}
            >
              ⚠️ {(mutation.error as any)?.response?.data?.detail || mutation.error?.message || 'Something went wrong. Please try again.'}
            </div>
          )}

          {/* ── Navigation Buttons ── */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: '20px',
              gap: '12px',
            }}
          >
            <button
              type="button"
              onClick={goBack}
              disabled={currentStep === 1}
              className="btn-secondary"
              style={{
                padding: '12px 24px',
                opacity: currentStep === 1 ? 0.3 : 1,
                cursor: currentStep === 1 ? 'not-allowed' : 'pointer',
              }}
            >
              ← Back
            </button>

            {currentStep < TOTAL_STEPS ? (
              <button
                type="button"
                onClick={goNext}
                className="btn-primary"
                style={{ padding: '12px 32px' }}
              >
                Next →
              </button>
            ) : (
              <button
                type="submit"
                className="btn-primary"
                disabled={mutation.isPending}
                style={{
                  padding: '12px 32px',
                  opacity: mutation.isPending ? 0.7 : 1,
                  cursor: mutation.isPending ? 'wait' : 'pointer',
                }}
              >
                {mutation.isPending ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="spinner" style={{ width: '16px', height: '16px' }} />
                    Generating…
                  </span>
                ) : (
                  '✨ Generate Routine'
                )}
              </button>
            )}
          </div>
        </form>
      </FormProvider>

      <div className="disclaimer" style={{ marginTop: '24px' }}>
        <span>⚠️</span>
        <span>
          These are AI-generated suggestions, not medical prescriptions. Always
          consult a dermatologist before starting new products.
        </span>
      </div>
    </div>
  )
}

// =====================================================================
// Step 1 — Your Skin (skin_type)
// =====================================================================

const Step1SkinType: React.FC = () => {
  const { control } = useForm<RoutineRequest>()
  const { setValue, watch } = useForm<RoutineRequest>()
  const methods = useFormContextSafe()
  const selected = methods.watch('skin_type')

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 style={{ color: 'white', fontWeight: 700, fontSize: '1.3rem', marginBottom: '8px' }}>
          What's your skin type?
        </h2>
        <p style={{ color: 'var(--dark-200)', fontSize: '0.9rem' }}>
          Select the option that best describes your skin.
        </p>
      </div>

      <Controller
        name="skin_type"
        control={methods.control}
        render={({ field }) => (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
            {SKIN_TYPE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => field.onChange(opt.value)}
                style={{
                  padding: '20px 16px',
                  borderRadius: '12px',
                  border: field.value === opt.value
                    ? '2px solid #6C63FF'
                    : '1px solid var(--dark-500)',
                  background: field.value === opt.value
                    ? 'rgba(108,99,255,0.1)'
                    : 'var(--dark-700)',
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>
                  {SKIN_TYPE_ICONS[opt.value]}
                </div>
                <div style={{
                  color: field.value === opt.value ? '#A89CFF' : 'white',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                }}>
                  {opt.label}
                </div>
              </button>
            ))}
          </div>
        )}
      />
    </div>
  )
}

// =====================================================================
// Step 2 — Your Concerns (primary_concern + age_group)
// =====================================================================

const Step2Concerns: React.FC = () => {
  const methods = useFormContextSafe()

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 style={{ color: 'white', fontWeight: 700, fontSize: '1.3rem', marginBottom: '8px' }}>
          What concerns you most?
        </h2>
      </div>

      {/* Primary concern */}
      <div>
        <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '8px', display: 'block' }}>
          Primary Concern
        </label>
        <Controller
          name="primary_concern"
          control={methods.control}
          render={({ field }) => (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
              {PRIMARY_CONCERN_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => field.onChange(opt.value)}
                  style={{
                    padding: '14px 12px',
                    borderRadius: '10px',
                    border: field.value === opt.value
                      ? '2px solid #6C63FF'
                      : '1px solid var(--dark-500)',
                    background: field.value === opt.value
                      ? 'rgba(108,99,255,0.1)'
                      : 'var(--dark-700)',
                    cursor: 'pointer',
                    textAlign: 'center',
                    transition: 'all 0.2s',
                  }}
                >
                  <span style={{ marginRight: '6px' }}>{CONCERN_ICONS[opt.value]}</span>
                  <span style={{
                    color: field.value === opt.value ? '#A89CFF' : 'white',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                  }}>
                    {opt.label}
                  </span>
                </button>
              ))}
            </div>
          )}
        />
      </div>

      {/* Age group */}
      <div>
        <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '8px', display: 'block' }}>
          Age Group
        </label>
        <Controller
          name="age_group"
          control={methods.control}
          render={({ field }) => (
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {AGE_GROUP_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => field.onChange(opt.value)}
                  style={{
                    flex: 1,
                    minWidth: '100px',
                    padding: '12px 16px',
                    borderRadius: '10px',
                    border: field.value === opt.value
                      ? '2px solid #6C63FF'
                      : '1px solid var(--dark-500)',
                    background: field.value === opt.value
                      ? 'rgba(108,99,255,0.1)'
                      : 'var(--dark-700)',
                    cursor: 'pointer',
                    color: field.value === opt.value ? '#A89CFF' : 'white',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    transition: 'all 0.2s',
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        />
      </div>
    </div>
  )
}

// =====================================================================
// Step 3 — Your Goals (skin_goals + special_situation)
// =====================================================================

const Step3Goals: React.FC = () => {
  const methods = useFormContextSafe()
  const selectedGoals = methods.watch('skin_goals') || []

  const toggleGoal = (goal: SkinGoal) => {
    const current = methods.getValues('skin_goals') || []
    if (current.includes(goal)) {
      methods.setValue(
        'skin_goals',
        current.filter((g: SkinGoal) => g !== goal),
        { shouldValidate: true }
      )
    } else {
      methods.setValue('skin_goals', [...current, goal], { shouldValidate: true })
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 style={{ color: 'white', fontWeight: 700, fontSize: '1.3rem', marginBottom: '8px' }}>
          What are your skin goals?
        </h2>
        <p style={{ color: 'var(--dark-200)', fontSize: '0.9rem' }}>
          Select one or more goals.
        </p>
      </div>

      {/* Skin goals (multi-select) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
        {SKIN_GOAL_OPTIONS.map((opt) => {
          const isActive = selectedGoals.includes(opt.value)
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => toggleGoal(opt.value)}
              style={{
                padding: '16px 12px',
                borderRadius: '10px',
                border: isActive
                  ? '2px solid #6C63FF'
                  : '1px solid var(--dark-500)',
                background: isActive
                  ? 'rgba(108,99,255,0.1)'
                  : 'var(--dark-700)',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ fontSize: '1.3rem', marginBottom: '6px' }}>
                {GOAL_ICONS[opt.value]}
              </div>
              <div style={{
                color: isActive ? '#A89CFF' : 'white',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}>
                {opt.label}
              </div>
            </button>
          )
        })}
      </div>

      {/* Special situation */}
      <div>
        <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '8px', display: 'block' }}>
          Special Situation (optional)
        </label>
        <Controller
          name="special_situation"
          control={methods.control}
          render={({ field }) => (
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {SPECIAL_SITUATION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => field.onChange(opt.value)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '20px',
                    border: field.value === opt.value
                      ? '2px solid #6C63FF'
                      : '1px solid var(--dark-500)',
                    background: field.value === opt.value
                      ? 'rgba(108,99,255,0.1)'
                      : 'var(--dark-700)',
                    cursor: 'pointer',
                    color: field.value === opt.value ? '#A89CFF' : 'white',
                    fontSize: '0.8rem',
                    fontWeight: 500,
                    transition: 'all 0.2s',
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        />
      </div>
    </div>
  )
}

// =====================================================================
// Step 4 — Your Environment (location toggle + include_weekly)
// =====================================================================

const Step4Environment: React.FC = () => {
  const methods = useFormContextSafe()
  const includeWeekly = methods.watch('include_weekly') ?? true
  const location = methods.watch('location')
  const { state: locState, coords, request: requestLocation } = useLocation()

  React.useEffect(() => {
    if (locState.status === 'resolved' && coords) {
      methods.setValue('location', coords, { shouldValidate: true })
    }
  }, [locState.status, coords, methods])

  const clearLocation = () => {
    methods.setValue('location', null, { shouldValidate: true })
  }

  const isLoading = locState.status === 'loading'
  const isDenied = locState.status === 'denied'
  const isUnavailable = locState.status === 'unavailable'

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 style={{ color: 'white', fontWeight: 700, fontSize: '1.3rem', marginBottom: '8px' }}>
          Your Environment
        </h2>
        <p style={{ color: 'var(--dark-200)', fontSize: '0.9rem' }}>
          Optional — helps us adjust for your local climate.
        </p>
      </div>

      {/* Location toggle */}
      <div
        style={{
          padding: '16px',
          borderRadius: '12px',
          border: location
            ? '1px solid rgba(108,99,255,0.4)'
            : '1px solid var(--dark-500)',
          background: location
            ? 'rgba(108,99,255,0.05)'
            : 'var(--dark-700)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ color: 'white', fontWeight: 600, fontSize: '0.9rem', marginBottom: '4px' }}>
              📍 Use my location for weather adjustments
            </div>
            <div style={{ color: 'var(--dark-300)', fontSize: '0.8rem' }}>
              {location
                ? `Location: ${location.lat.toFixed(2)}°, ${location.lon.toFixed(2)}°`
                : 'Adjust routine for your local UV, humidity, and temperature'}
            </div>
          </div>
          {location ? (
            <button
              type="button"
              onClick={clearLocation}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                border: '1px solid var(--dark-500)',
                background: 'transparent',
                color: 'var(--dark-200)',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              Clear
            </button>
          ) : (
            <button
              type="button"
              onClick={requestLocation}
              disabled={isLoading}
              className="btn-primary"
              style={{ padding: '8px 16px', fontSize: '0.8rem' }}
            >
              {isLoading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span className="spinner" style={{ width: '12px', height: '12px' }} />
                  Detecting...
                </span>
              ) : (
                'Enable'
              )}
            </button>
          )}
        </div>
        {isDenied && (
          <p style={{ color: '#fca5a5', fontSize: '0.8rem', marginTop: '8px' }}>
            Location access denied. Please enable it in your browser settings.
          </p>
        )}
        {isUnavailable && (
          <p style={{ color: '#fca5a5', fontSize: '0.8rem', marginTop: '8px' }}>
            Geolocation is unavailable. Weather adjustments will be skipped.
          </p>
        )}
      </div>

      {/* Include weekly toggle */}
      <div
        style={{
          padding: '16px',
          borderRadius: '12px',
          border: '1px solid var(--dark-500)',
          background: 'var(--dark-700)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
        }}
        onClick={() =>
          methods.setValue('include_weekly', !includeWeekly, { shouldValidate: true })
        }
      >
        <div>
          <div style={{ color: 'white', fontWeight: 600, fontSize: '0.9rem', marginBottom: '4px' }}>
            📅 Include weekly treatments
          </div>
          <div style={{ color: 'var(--dark-300)', fontSize: '0.8rem' }}>
            Add exfoliation and mask recommendations
          </div>
        </div>
        <div
          style={{
            width: '44px',
            height: '24px',
            borderRadius: '12px',
            background: includeWeekly ? '#6C63FF' : 'var(--dark-500)',
            position: 'relative',
            transition: 'background 0.2s',
            flexShrink: 0,
          }}
        >
          <div
            style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              background: 'white',
              position: 'absolute',
              top: '2px',
              left: includeWeekly ? '22px' : '2px',
              transition: 'left 0.2s',
              boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
            }}
          />
        </div>
      </div>
    </div>
  )
}

// =====================================================================
// Helper: safe useFormContext wrapper
// =====================================================================

function useFormContextSafe() {
  const ctx = useFormContext<RoutineRequest>()
  return ctx
}

export default SkincareRecommendations