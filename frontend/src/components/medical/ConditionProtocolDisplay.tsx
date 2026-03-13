// REMEDIATION: Fix 3 applied
/**
 * ConditionProtocolDisplay.tsx — Thin layout orchestrator
 * Imports and composes all display sub-components.
 */

import { useMedicalStore } from '../../store/medicalStore'
import { ReferralBanner } from './display/ReferralBanner'
import { EducationCard } from './display/EducationCard'
import { CarePlanSection } from './display/CarePlanSection'
import { IngredientGuide } from './display/IngredientGuide'
import { TriggerPanel } from './display/TriggerPanel'
import { RedFlagsPanel } from './display/RedFlagsPanel'
import { DisclaimerFooter } from './display/DisclaimerFooter'
import { ClimateCard } from './display/ClimateCard'
import type { ConditionKey } from '../../types/conditions'

export function ConditionProtocolDisplay() {
  const protocol = useMedicalStore((s) => s.protocol)
  const knownTriggers = useMedicalStore((s) => s.knownTriggers)
  const resetAll = useMedicalStore((s) => s.resetAll)

  if (!protocol) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem', color: 'rgba(255,255,255,0.5)' }}>
        <p>No protocol generated yet.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Referral Banner */}
      {protocol.referral_recommended && (
        <ReferralBanner
          referral_urgency={protocol.referral_urgency}
          condition={protocol.condition as ConditionKey}
        />
      )}

      {/* Severity Badge + Title */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem',
      }}>
        <div>
          <h2 style={{ color: '#fff', margin: 0, fontSize: '1.3rem', fontWeight: 700 }}>
            {protocol.condition_display_name}
          </h2>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
            <Badge label={`Severity: ${protocol.severity_assessed}`}
              color={protocol.severity_assessed === 'severe' ? '#ef4444' : protocol.severity_assessed === 'moderate' ? '#f59e0b' : '#22c55e'} />
            <Badge label={protocol.category.replace('_', ' ')} color="#6366f1" />
            {protocol.is_contagious && <Badge label="Contagious" color="#f59e0b" />}
            {protocol.llm_enriched && <Badge label="AI-Enhanced" color="#8b5cf6" />}
          </div>
        </div>
      </div>

      {/* Education */}
      <EducationCard
        education={protocol.education}
        referral_recommended={protocol.referral_recommended}
      />

      {/* Care Plan */}
      <CarePlanSection care_plan={protocol.care_plan} />

      {/* Ingredients */}
      <IngredientGuide
        ingredients_to_seek={protocol.ingredients_to_seek}
        ingredients_to_avoid={protocol.ingredients_to_avoid}
      />

      {/* Triggers */}
      <TriggerPanel
        trigger_guidance={protocol.trigger_guidance}
        user_triggers={knownTriggers}
      />

      {/* Red Flags */}
      <RedFlagsPanel
        red_flags={protocol.red_flags}
        when_to_see_doctor={protocol.when_to_see_doctor}
      />

      {/* Weather */}
      {protocol.weather_context && (
        <Card title="🌤️ Weather-Adjusted Advice">
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
            <WeatherStat label="Temp" value={`${protocol.weather_context.temperature_c.toFixed(1)}°C`} />
            <WeatherStat label="Humidity" value={`${protocol.weather_context.humidity_pct.toFixed(0)}%`} />
            <WeatherStat label="UV Index" value={protocol.weather_context.uv_index.toFixed(1)} />
          </div>
          <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.82rem', margin: 0 }}>
            {protocol.weather_context.routine_impact}
          </p>
        </Card>
      )}

      {/* Climate Care Note */}
      {protocol.climate_care_note && (
        <ClimateCard climate_care_note={protocol.climate_care_note} />
      )}

      {/* Prescription Note */}
      {protocol.prescription_interaction_note && (
        <Card title="💊 Prescription Notes">
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.82rem', margin: 0, lineHeight: 1.6 }}>
            {protocol.prescription_interaction_note}
          </p>
        </Card>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '2rem', marginBottom: '4rem' }}>
        <button
          onClick={resetAll}
          style={{
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            border: 'none', color: '#fff', borderRadius: '10px',
            padding: '0.75rem 2rem', fontSize: '0.9rem', fontWeight: 600,
            cursor: 'pointer', transition: 'all 0.2s',
          }}
        >
          ← View Another Condition
        </button>
      </div>

      {/* Disclaimer Footer — sticky */}
      <DisclaimerFooter
        medical_disclaimer={protocol.medical_disclaimer}
        llm_enriched={protocol.llm_enriched}
      />
    </div>
  )
}

// ── Shared helpers kept locally ──────────────────────────

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '14px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      <h3 style={{ color: '#fff', margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600 }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span style={{
      background: `${color}20`, color,
      padding: '0.15rem 0.55rem', borderRadius: '6px',
      fontSize: '0.7rem', fontWeight: 600,
      textTransform: 'capitalize', whiteSpace: 'nowrap',
    }}>
      {label}
    </span>
  )
}

function WeatherStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>
        {label}
      </div>
      <div style={{ color: '#fff', fontSize: '1.1rem', fontWeight: 700 }}>
        {value}
      </div>
    </div>
  )
}
