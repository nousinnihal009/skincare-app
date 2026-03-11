// ──────────────────────────────────────────────────────────
// RoutineDisplay.tsx — Extended routine results rendering
// Handles: medical disclaimer, condition overrides, condition_safe
// badges, pollution badge, AM/PM/weekly routine display
// ──────────────────────────────────────────────────────────

import React, { useState } from 'react'
import type { RoutineResponse, RoutineStep } from '../../types/skincare'

interface Props {
  response: RoutineResponse
  pollutionExposure: boolean
}

// ── Category icons ───────────────────────────────────────
const CATEGORY_ICONS: Record<string, string> = {
  cleanser: '🧼',
  'oil-cleanser': '🫧',
  micellar: '💧',
  toner: '🌊',
  serum: '💜',
  moisturizer: '🧴',
  occlusive: '🛡️',
  spf: '☀️',
  exfoliant: '✨',
  mist: '🌬️',
  treatment: '💊',
}

const RoutineDisplay: React.FC<Props> = ({ response, pollutionExposure }) => {
  const [disclaimerDismissed, setDisclaimerDismissed] = useState(false)
  const [overridesExpanded, setOverridesExpanded] = useState(false)

  const {
    profile_summary,
    weather_context,
    am_routine,
    pm_routine,
    weekly_treatments,
    total_time_am,
    total_time_pm,
    medical_disclaimer,
    condition_overrides_applied,
  } = response

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* ── Profile Summary Banner ── */}
      <div
        className="glass-card"
        style={{
          background: 'linear-gradient(135deg, rgba(108,99,255,0.1), rgba(168,156,255,0.05))',
          border: '1px solid rgba(108,99,255,0.2)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '1.3rem' }}>👤</span>
          <span style={{ color: 'white', fontWeight: 600, fontSize: '0.95rem', flex: 1 }}>
            {profile_summary}
          </span>

          {/* Pollution badge */}
          {pollutionExposure && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 12px',
                borderRadius: '20px',
                background: 'rgba(108,99,255,0.15)',
                border: '1px solid rgba(108,99,255,0.3)',
                color: '#A89CFF',
                fontSize: '0.8rem',
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              🌫️ Urban Shield Routine
            </span>
          )}
        </div>

        {/* Weather context */}
        {weather_context && (
          <div
            style={{
              marginTop: '12px',
              display: 'flex',
              gap: '16px',
              flexWrap: 'wrap',
              paddingTop: '12px',
              borderTop: '1px solid rgba(255,255,255,0.05)',
            }}
          >
            <WeatherChip label="Temp" value={`${weather_context.temperature_c.toFixed(0)}°C`} />
            <WeatherChip label="Humidity" value={`${weather_context.humidity_pct.toFixed(0)}%`} />
            <WeatherChip label="UV Index" value={weather_context.uv_index.toFixed(1)} />
            <WeatherChip label="Condition" value={weather_context.condition} />
          </div>
        )}

        {/* Time summary */}
        <div
          style={{
            marginTop: '12px',
            display: 'flex',
            gap: '16px',
            paddingTop: '12px',
            borderTop: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <span style={{ color: 'var(--dark-200)', fontSize: '0.8rem' }}>
            ☀️ AM: ~{total_time_am} min
          </span>
          <span style={{ color: 'var(--dark-200)', fontSize: '0.8rem' }}>
            🌙 PM: ~{total_time_pm} min
          </span>
        </div>
      </div>

      {/* ── Medical Disclaimer Banner ── */}
      {medical_disclaimer && !disclaimerDismissed && (
        <div
          style={{
            padding: '16px',
            borderRadius: '12px',
            background: 'rgba(120,53,15,0.4)',
            border: '1px solid rgba(245,158,11,0.3)',
            color: '#fcd34d',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
          }}
        >
          <span style={{ fontSize: '1.2rem', flexShrink: 0, marginTop: '1px' }}>⚕️</span>
          <p style={{ flex: 1, lineHeight: 1.6, margin: 0 }}>
            {medical_disclaimer}
          </p>
          <button
            onClick={() => setDisclaimerDismissed(true)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'rgba(252,211,77,0.6)',
              cursor: 'pointer',
              fontSize: '1.1rem',
              padding: '0 4px',
              flexShrink: 0,
              lineHeight: 1,
            }}
            aria-label="Dismiss disclaimer"
          >
            ×
          </button>
        </div>
      )}

      {/* ── Condition Overrides Applied (collapsible) ── */}
      {condition_overrides_applied.length > 0 && (
        <div
          style={{
            borderRadius: '12px',
            border: '1px solid var(--dark-500)',
            background: 'var(--dark-700)',
            overflow: 'hidden',
          }}
        >
          <button
            onClick={() => setOverridesExpanded(!overridesExpanded)}
            style={{
              width: '100%',
              padding: '14px 16px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              color: 'white',
              fontWeight: 600,
              fontSize: '0.9rem',
              textAlign: 'left',
            }}
          >
            <span
              style={{
                transition: 'transform 0.2s',
                transform: overridesExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                display: 'inline-block',
              }}
            >
              ▶
            </span>
            Routine adjusted for your skin condition
            <span
              style={{
                marginLeft: 'auto',
                background: 'rgba(108,99,255,0.15)',
                color: '#A89CFF',
                padding: '2px 8px',
                borderRadius: '10px',
                fontSize: '0.75rem',
                fontWeight: 600,
              }}
            >
              {condition_overrides_applied.length} change{condition_overrides_applied.length !== 1 ? 's' : ''}
            </span>
          </button>

          {overridesExpanded && (
            <div
              style={{
                padding: '0 16px 14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {condition_overrides_applied.map((override, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '8px',
                    paddingLeft: '8px',
                  }}
                >
                  <span style={{ color: '#A89CFF', fontSize: '0.85rem', flexShrink: 0 }}>
                    ✓
                  </span>
                  <span style={{ color: 'var(--dark-200)', fontSize: '0.85rem', lineHeight: 1.5 }}>
                    {override}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── AM / PM Routines ── */}
      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        {am_routine.length > 0 && (
          <RoutineColumn
            title="Morning Routine"
            icon="☀️"
            bgColor="rgba(245,158,11,0.15)"
            steps={am_routine}
            totalTime={total_time_am}
          />
        )}
        {pm_routine.length > 0 && (
          <RoutineColumn
            title="Evening Routine"
            icon="🌙"
            bgColor="rgba(99,102,241,0.15)"
            steps={pm_routine}
            totalTime={total_time_pm}
          />
        )}
      </div>

      {/* ── Weekly Treatments ── */}
      {weekly_treatments && weekly_treatments.length > 0 && (
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: 'rgba(16,185,129,0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.3rem',
              }}
            >
              📅
            </div>
            <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem' }}>Weekly Treatments</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {weekly_treatments.map((step) => (
              <StepCard key={step.step} step={step} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// =====================================================================
// RoutineColumn — AM or PM column
// =====================================================================

interface RoutineColumnProps {
  title: string
  icon: string
  bgColor: string
  steps: RoutineStep[]
  totalTime: number
}

const RoutineColumn: React.FC<RoutineColumnProps> = ({ title, icon, bgColor, steps, totalTime }) => (
  <div className="glass-card" style={{ flex: 1, minWidth: '300px' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '12px',
          background: bgColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.3rem',
        }}
      >
        {icon}
      </div>
      <div>
        <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', margin: 0 }}>{title}</h3>
        <span style={{ color: 'var(--dark-300)', fontSize: '0.75rem' }}>~{totalTime} min</span>
      </div>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      {steps.map((step) => (
        <StepCard key={step.step} step={step} />
      ))}
    </div>
  </div>
)

// =====================================================================
// StepCard — Individual routine step
// =====================================================================

interface StepCardProps {
  step: RoutineStep
}

const StepCard: React.FC<StepCardProps> = ({ step }) => {
  const [expanded, setExpanded] = useState(false)
  const icon = CATEGORY_ICONS[step.category] || '🔹'

  return (
    <div
      style={{
        padding: '14px 16px',
        borderRadius: '10px',
        border: '1px solid var(--dark-500)',
        background: 'var(--dark-700)',
        cursor: 'pointer',
        transition: 'all 0.2s',
        // condition_safe: false → amber left border
        borderLeft: !step.condition_safe
          ? '2px solid #f59e0b'
          : '1px solid var(--dark-500)',
      }}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1rem' }}>{icon}</span>
          <span style={{ color: 'var(--primary-300)', fontWeight: 600, fontSize: '0.85rem' }}>
            {step.category.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
          </span>
          {step.is_essential && (
            <span
              style={{
                padding: '1px 6px',
                borderRadius: '6px',
                background: 'rgba(108,99,255,0.15)',
                color: '#A89CFF',
                fontSize: '0.65rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              Essential
            </span>
          )}
          {!step.condition_safe && (
            <span
              style={{
                padding: '1px 6px',
                borderRadius: '6px',
                background: 'rgba(245,158,11,0.15)',
                color: '#f59e0b',
                fontSize: '0.65rem',
                fontWeight: 700,
              }}
            >
              ⚠ Use with caution
            </span>
          )}
          {step.climate_adjusted && (
            <span
              style={{
                padding: '1px 6px',
                borderRadius: '6px',
                background: 'rgba(16,185,129,0.15)',
                color: '#34d399',
                fontSize: '0.65rem',
                fontWeight: 700,
              }}
            >
              🌤 Climate
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--dark-300)', fontSize: '0.75rem' }}>
            {step.time_minutes} min
          </span>
          <span style={{ color: 'var(--dark-400)', fontSize: '0.7rem' }}>
            Step {step.step}
          </span>
        </div>
      </div>

      {/* Ingredient recommendation */}
      <p style={{ color: 'white', fontWeight: 500, fontSize: '0.9rem', marginBottom: '2px', margin: 0 }}>
        {step.ingredient_recommendation}
      </p>

      {/* Expandable why_explanation */}
      {expanded && (
        <p
          style={{
            color: 'var(--dark-200)',
            fontSize: '0.82rem',
            lineHeight: 1.6,
            marginTop: '8px',
            paddingTop: '8px',
            borderTop: '1px solid var(--dark-500)',
            margin: '8px 0 0 0',
          }}
        >
          {step.why_explanation}
        </p>
      )}

      {/* Expand hint */}
      {!expanded && (
        <p style={{ color: 'var(--dark-400)', fontSize: '0.7rem', marginTop: '4px', margin: '4px 0 0 0' }}>
          Tap to learn why →
        </p>
      )}
    </div>
  )
}

// =====================================================================
// WeatherChip — small weather data display
// =====================================================================

interface WeatherChipProps {
  label: string
  value: string
}

const WeatherChip: React.FC<WeatherChipProps> = ({ label, value }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
    <span style={{ color: 'var(--dark-300)', fontSize: '0.75rem' }}>{label}:</span>
    <span style={{ color: 'white', fontSize: '0.8rem', fontWeight: 600 }}>{value}</span>
  </div>
)

export default RoutineDisplay