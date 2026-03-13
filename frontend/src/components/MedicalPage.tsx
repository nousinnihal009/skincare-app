/**
 * MedicalPage.tsx — Main wrapper page for the Medical Conditions Advisor
 *
 * Uses wizardStep from medicalStore to switch between:
 *   0 → ConditionGrid (browse & select)
 *   1–3 → ConditionIntakeWizard (4-step questionnaire, step 4 generates)
 *   4 → ConditionProtocolDisplay (results)
 */

import { useEffect } from 'react'
import { useMedicalStore } from '../store/medicalStore'
import { ConditionGrid } from './medical/ConditionGrid'
import { ConditionIntakeWizard } from './medical/ConditionIntakeWizard'
import { ConditionProtocolDisplay } from './medical/ConditionProtocolDisplay'
import type { Page } from '../App'

interface MedicalPageProps {
  onNavigate?: (page: Page) => void
}

export default function MedicalPage({ onNavigate }: MedicalPageProps) {
  const wizardStep = useMedicalStore((s) => s.wizardStep)
  const fetchConditions = useMedicalStore((s) => s.fetchConditions)
  const resetAll = useMedicalStore((s) => s.resetAll)

  useEffect(() => {
    fetchConditions()
  }, [fetchConditions])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary, #0a0a12)' }}>
      {/* Header */}
      <div style={{
        padding: '2rem 1.5rem 1rem',
        maxWidth: '1200px',
        margin: '0 auto',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <div>
            <h1 style={{
              fontSize: '1.75rem',
              fontWeight: 700,
              color: '#fff',
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}>
              🩺 Medical Conditions Advisor
            </h1>
            <p style={{
              color: 'rgba(255,255,255,0.5)',
              fontSize: '0.875rem',
              margin: '0.25rem 0 0',
            }}>
              Evidence-based skincare protocols for medical skin conditions
            </p>
          </div>
          {wizardStep > 0 && (
            <button
              onClick={resetAll}
              style={{
                background: 'rgba(255,255,255,0.08)',
                color: 'rgba(255,255,255,0.7)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '8px',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                fontSize: '0.8rem',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.15)' }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)' }}
            >
              ← Start Over
            </button>
          )}
        </div>

        {/* Safety Banner */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(255,179,71,0.1), rgba(255,107,107,0.1))',
          border: '1px solid rgba(255,179,71,0.2)',
          borderRadius: '10px',
          padding: '0.75rem 1rem',
          marginTop: '1rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.5rem',
        }}>
          <span style={{ fontSize: '1.1rem' }}>⚠️</span>
          <p style={{
            color: 'rgba(255,255,255,0.7)',
            fontSize: '0.78rem',
            margin: 0,
            lineHeight: 1.5,
          }}>
            <strong style={{ color: 'rgba(255,179,71,0.9)' }}>Medical Disclaimer:</strong>{' '}
            This tool provides educational skincare guidance only. It does not diagnose, prescribe, or replace professional medical advice.
            Always consult a dermatologist for medical skin conditions.
          </p>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1.5rem 3rem' }}>
        {wizardStep === 0 && <ConditionGrid onNavigate={onNavigate} />}
        {(wizardStep >= 1 && wizardStep <= 3) && <ConditionIntakeWizard />}
        {wizardStep === 4 && <ConditionProtocolDisplay />}
      </div>
    </div>
  )
}
