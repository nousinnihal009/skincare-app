// ──────────────────────────────────────────────────────────
// WizardStep5.tsx — "Health & Exposure" (Step 5 of 5)
// Medical condition selector + pollution exposure toggle
// ──────────────────────────────────────────────────────────

import React from 'react'
import { useFormContext, Controller } from 'react-hook-form'
import type { RoutineRequest, MedicalCondition } from '../../types/skincare'
import { MEDICAL_CONDITION_OPTIONS } from '../../types/skincare'

// ── Condition card icons (emoji-based, matching Step 1 pattern) ──
const CONDITION_ICONS: Record<MedicalCondition, string> = {
  none: '✅',
  eczema: '🩹',
  rosacea: '🌹',
  psoriasis: '🔬',
  lichen_planus: '💜',
  atopic_dermatitis: '🛡️',
  melanoma_risk: '☀️',
}

const WizardStep5: React.FC = () => {
  const { control, watch, setValue } = useFormContext<RoutineRequest>()
  const selectedCondition = watch('medical_condition') ?? 'none'
  const pollutionExposure = watch('pollution_exposure') ?? false

  return (
    <div className="space-y-8">
      {/* ── Step Header ── */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">
          Health &amp; Exposure
        </h2>
        <p className="text-white/50 text-sm">
          Optional — skip if not applicable to you.
        </p>
      </div>

      {/* ── Medical Condition Selector ── */}
      <div className="space-y-4">
        <label className="block text-sm font-medium text-white/70">
          Do you have a diagnosed skin condition?
        </label>

        <Controller
          name="medical_condition"
          control={control}
          defaultValue="none"
          render={({ field }) => (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {MEDICAL_CONDITION_OPTIONS.map((option) => {
                const isSelected = field.value === option.value
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => field.onChange(option.value)}
                    className={`
                      relative flex flex-col items-start p-4 rounded-xl border transition-all duration-200
                      text-left cursor-pointer
                      ${
                        isSelected
                          ? 'border-brand bg-brand/10 ring-1 ring-brand shadow-lg shadow-brand/10'
                          : 'border-white/10 bg-card hover:border-white/20 hover:bg-muted/50'
                      }
                    `}
                  >
                    {/* Icon + Label row */}
                    <div className="flex items-center gap-3 mb-1.5">
                      <span className="text-xl" role="img" aria-label={option.label}>
                        {CONDITION_ICONS[option.value]}
                      </span>
                      <span
                        className={`font-semibold text-sm ${
                          isSelected ? 'text-brand-light' : 'text-white'
                        }`}
                      >
                        {option.label}
                      </span>
                    </div>

                    {/* Descriptor */}
                    <p className="text-xs text-white/50 pl-9 leading-relaxed">
                      {option.descriptor}
                    </p>

                    {/* Selection indicator */}
                    {isSelected && (
                      <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-brand flex items-center justify-center">
                        <svg
                          className="w-3 h-3 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={3}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          )}
        />

        {/* Informational notice */}
        <div className="bg-muted/50 border border-white/10 text-sm text-white/60 rounded-lg p-3 flex items-start gap-2.5">
          <span className="text-base leading-none mt-0.5">ℹ️</span>
          <p className="leading-relaxed">
            Selecting a condition adjusts your routine to avoid known irritants and
            prioritize safe, barrier-supporting ingredients. This is not medical
            advice.
          </p>
        </div>
      </div>

      {/* ── Divider ── */}
      <div className="border-t border-white/5" />

      {/* ── Pollution Exposure Toggle ── */}
      <div className="space-y-2">
        <div
          className={`
            flex items-center justify-between p-4 rounded-xl border transition-all duration-200 cursor-pointer
            ${
              pollutionExposure
                ? 'border-brand/40 bg-brand/5'
                : 'border-white/10 bg-card hover:border-white/20'
            }
          `}
          onClick={() => setValue('pollution_exposure', !pollutionExposure, { shouldValidate: true })}
          role="switch"
          aria-checked={pollutionExposure}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              setValue('pollution_exposure', !pollutionExposure, { shouldValidate: true })
            }
          }}
        >
          <div className="flex-1 mr-4">
            <div className="flex items-center gap-2.5 mb-1">
              <span className="text-lg" role="img" aria-label="pollution">
                🌫️
              </span>
              <span className="font-semibold text-sm text-white">
                I live or work in a high-pollution urban environment
              </span>
            </div>
            <p className="text-xs text-white/40 pl-8">
              Adds antioxidant protection and double-cleansing steps to your
              routine
            </p>
          </div>

          {/* Toggle switch */}
          <div
            className={`
              relative flex-shrink-0 w-11 h-6 rounded-full transition-colors duration-200
              ${pollutionExposure ? 'bg-brand' : 'bg-white/10'}
            `}
          >
            <div
              className={`
                absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-md
                transition-transform duration-200
                ${pollutionExposure ? 'translate-x-5' : 'translate-x-0'}
              `}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default WizardStep5