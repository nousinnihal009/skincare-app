// REMEDIATION: Fix 1 + Fix 2 applied
/**
 * ConditionIntakeWizard.tsx — 4-step intake questionnaire (thin orchestrator)
 *
 * Step 1: Severity + Skin Type (IntakeStep1)
 * Step 2: Affected Areas + Duration + Triggers (IntakeStep2)
 * Step 3: Current Treatments (IntakeStep3)
 * Step 4: Age Group + Location Consent → Submit (IntakeStep4)
 */

import { useMedicalStore } from '../../store/medicalStore'
import { IntakeStep1 } from './intake/IntakeStep1'
import { IntakeStep2 } from './intake/IntakeStep2'
import { IntakeStep3 } from './intake/IntakeStep3'
import { IntakeStep4 } from './intake/IntakeStep4'
import {
  CONDITION_ICONS,
  CONDITION_DESCRIPTORS,
} from '../../constants/conditionMeta'
import type { ConditionKey } from '../../types/conditions'

export function ConditionIntakeWizard() {
  const wizardStep = useMedicalStore((s) => s.wizardStep)
  const setWizardStep = useMedicalStore((s) => s.setWizardStep)
  const selectedCondition = useMedicalStore((s) => s.selectedCondition)
  const clearSelection = useMedicalStore((s) => s.clearSelection)

  // Only what the orchestrator needs for validation gates
  const affectedAreas = useMedicalStore((s) => s.affectedAreas)
  const currentTreatments = useMedicalStore((s) => s.currentTreatments)
  const protocolLoading = useMedicalStore((s) => s.protocolLoading)
  const protocolError = useMedicalStore((s) => s.protocolError)
  const generateProtocol = useMedicalStore((s) => s.generateProtocol)

  if (!selectedCondition) return null
  const key = selectedCondition as ConditionKey

  const canProceedStep2 = affectedAreas.length > 0
  const canProceedStep3 = currentTreatments.length > 0

  const STEP_LABELS: Record<number, string> = {
    1: 'Basic Info',
    2: 'Symptoms',
    3: 'Treatments',
    4: 'Profile & Location',
  }

  return (
    <div>
      {/* Progress Bar */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={{
            flex: 1, height: '4px',
            borderRadius: '2px',
            background: wizardStep >= i
              ? 'linear-gradient(90deg, #6366f1, #8b5cf6)'
              : 'rgba(255,255,255,0.1)',
            transition: 'background 0.3s',
          }} />
        ))}
      </div>

      {/* Selected Condition Header */}
      <div style={{
        background: 'rgba(255,255,255,0.04)',
        borderRadius: '12px',
        padding: '1rem 1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.75rem' }}>{CONDITION_ICONS[key]}</span>
          <div>
            <h2 style={{ color: '#fff', margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>
              {CONDITION_DESCRIPTORS[key] ? key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : key}
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.4)', margin: 0, fontSize: '0.78rem' }}>
              Step {wizardStep} of 4 — {STEP_LABELS[wizardStep as number] || ''}
            </p>
          </div>
        </div>
        <button
          onClick={clearSelection}
          style={{
            background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)',
            cursor: 'pointer', fontSize: '0.8rem',
          }}
        >
          ✕ Change
        </button>
      </div>

      {/* Step 1 */}
      {wizardStep === 1 && (
        <div>
          <IntakeStep1 />
          <NavButtons onNext={() => setWizardStep(2)} />
        </div>
      )}

      {/* Step 2 */}
      {wizardStep === 2 && (
        <div>
          <IntakeStep2 />
          <NavButtons
            onBack={() => setWizardStep(1)}
            onNext={() => setWizardStep(3)}
            nextDisabled={!canProceedStep2}
          />
        </div>
      )}

      {/* Step 3 */}
      {wizardStep === 3 && (
        <div>
          <IntakeStep3 />
          <NavButtons
            onBack={() => setWizardStep(2)}
            onNext={() => setWizardStep(4 as any)}
            nextDisabled={!canProceedStep3}
          />
        </div>
      )}

      {/* Step 4 */}
      {wizardStep === 4 && (
        <div>
          <IntakeStep4 />

          {protocolError && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: '10px', padding: '0.75rem 1rem', marginBottom: '1rem',
              color: '#ef4444', fontSize: '0.85rem',
            }}>
              ⚠️ {protocolError}
            </div>
          )}

          <NavButtons
            onBack={() => setWizardStep(3)}
            submitLabel={protocolLoading ? 'Generating Protocol…' : 'Generate My Protocol'}
            onSubmit={generateProtocol}
            submitDisabled={protocolLoading}
          />
        </div>
      )}
    </div>
  )
}

// ── Navigation Buttons (kept in orchestrator) ────────────

function NavButtons({ onBack, onNext, onSubmit, submitLabel, nextDisabled, submitDisabled }: {
  onBack?: () => void
  onNext?: () => void
  onSubmit?: () => void
  submitLabel?: string
  nextDisabled?: boolean
  submitDisabled?: boolean
}) {
  return (
    <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '2rem' }}>
      {onBack && (
        <button onClick={onBack} style={{
          background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
          color: 'rgba(255,255,255,0.7)', borderRadius: '10px', padding: '0.65rem 1.5rem',
          fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.2s',
        }}>
          ← Back
        </button>
      )}
      {onNext && (
        <button
          onClick={onNext}
          disabled={nextDisabled}
          style={{
            background: nextDisabled ? 'rgba(99,102,241,0.2)' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            border: 'none', color: '#fff', borderRadius: '10px',
            padding: '0.65rem 1.5rem', fontSize: '0.85rem', fontWeight: 600,
            cursor: nextDisabled ? 'not-allowed' : 'pointer',
            opacity: nextDisabled ? 0.5 : 1,
            transition: 'all 0.2s',
          }}
        >
          Next →
        </button>
      )}
      {onSubmit && (
        <button
          onClick={onSubmit}
          disabled={submitDisabled}
          style={{
            background: submitDisabled ? 'rgba(34,197,94,0.2)' : 'linear-gradient(135deg, #22c55e, #16a34a)',
            border: 'none', color: '#fff', borderRadius: '10px',
            padding: '0.65rem 1.5rem', fontSize: '0.85rem', fontWeight: 600,
            cursor: submitDisabled ? 'not-allowed' : 'pointer',
            opacity: submitDisabled ? 0.5 : 1,
            transition: 'all 0.2s',
          }}
        >
          {submitLabel || 'Submit'}
        </button>
      )}
    </div>
  )
}
