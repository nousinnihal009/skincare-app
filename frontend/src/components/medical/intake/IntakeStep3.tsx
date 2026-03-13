// REMEDIATION: Fix 2 applied
/**
 * IntakeStep3.tsx — Current treatments multi-select chips
 */

import { useMedicalStore } from '../../../store/medicalStore'
import type { CurrentTreatment } from '../../../types/conditions'

const TREATMENTS: { value: CurrentTreatment; label: string }[] = [
  { value: 'prescription_topical', label: '💊 Rx Topical' },
  { value: 'prescription_oral', label: '💉 Rx Oral' },
  { value: 'otc_topical', label: '🧴 OTC Topical' },
  { value: 'phototherapy', label: '💡 Phototherapy' },
  { value: 'biologics', label: '🧬 Biologics' },
  { value: 'none', label: '❌ None' },
]

export function IntakeStep3() {
  const currentTreatments = useMedicalStore((s) => s.currentTreatments)
  const setCurrentTreatments = useMedicalStore((s) => s.setCurrentTreatments)
  const selectedCondition = useMedicalStore((s) => s.selectedCondition)

  const toggleTreatment = (id: string) => { // Changed 'val' to 'id'
    const v = id as CurrentTreatment // Changed 'val' to 'id'
    setCurrentTreatments(
      currentTreatments.includes(v)
        ? currentTreatments.filter((t) => t !== v)
        : [...currentTreatments, v]
    )
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Current treatments (select all that apply)
        </h3>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {TREATMENTS.map((opt) => {
            const isActive = currentTreatments.includes(opt.value)
            return (
              <button
                key={opt.value}
                onClick={() => toggleTreatment(opt.value)}
                style={{
                  background: isActive ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${isActive ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.1)'}`,
                  color: isActive ? '#a5b4fc' : 'rgba(255,255,255,0.6)',
                  borderRadius: '8px',
                  padding: '0.5rem 0.85rem',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  fontWeight: isActive ? 600 : 400,
                }}
              >
                {opt.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Fix 11: Perioral Dermatitis + Steroid warning */}
      {selectedCondition === 'perioral_dermatitis' && currentTreatments.includes('prescription_topical') && (
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: 'rgba(239,68,68,0.15)',
          border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: '10px',
          color: '#fca5a5',
          fontSize: '0.85rem',
          display: 'flex',
          gap: '0.75rem',
          alignItems: 'flex-start',
        }}>
          <span style={{ fontSize: '1.2rem' }}>⚠️</span>
          <div>
            <strong style={{ display: 'block', color: '#ef4444', marginBottom: '0.25rem' }}>Important: Topical Steroids</strong>
            If your prescription topical is a steroid (like hydrocortisone), be aware that topical steroids can trigger or significantly worsen perioral dermatitis. Discuss non-steroidal alternatives with your doctor.
          </div>
        </div>
      )}
    </div>
  )
}
