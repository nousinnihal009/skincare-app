// REMEDIATION: Fix 2 applied
/**
 * IntakeStep1.tsx — Condition confirmation card + severity + skin type selector
 */

import { useMedicalStore } from '../../../store/medicalStore'
import type { Severity, SkinType } from '../../../types/conditions'

const SEVERITY_OPTIONS: { value: Severity; label: string; color: string; desc: string }[] = [
  { value: 'mild', label: 'Mild', color: '#34d399', desc: 'Occasional, minor symptoms' },
  { value: 'moderate', label: 'Moderate', color: '#f59e0b', desc: 'Noticeable, regular symptoms' },
  { value: 'severe', label: 'Severe', color: '#ef4444', desc: 'Significant daily impact' },
]

const SKIN_TYPES: { value: SkinType; label: string }[] = [
  { value: 'oily', label: '🫧 Oily' },
  { value: 'dry', label: '🏜️ Dry' },
  { value: 'combination', label: '⚖️ Combo' },
  { value: 'sensitive', label: '🌸 Sensitive' },
  { value: 'normal', label: '✨ Normal' },
]

export function IntakeStep1() {
  const severity = useMedicalStore((s) => s.severity)
  const setSeverity = useMedicalStore((s) => s.setSeverity)
  const skinType = useMedicalStore((s) => s.skinType)
  const setSkinType = useMedicalStore((s) => s.setSkinType)

  return (
    <div>
      <Section title="How severe are your symptoms?">
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {SEVERITY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSeverity(opt.value)}
              style={{
                flex: '1 1 140px',
                background: severity === opt.value ? `${opt.color}18` : 'rgba(255,255,255,0.04)',
                border: `2px solid ${severity === opt.value ? opt.color : 'rgba(255,255,255,0.1)'}`,
                borderRadius: '12px',
                padding: '1rem',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ color: opt.color, fontWeight: 600, fontSize: '0.95rem' }}>{opt.label}</div>
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.72rem', marginTop: '0.25rem' }}>{opt.desc}</div>
            </button>
          ))}
        </div>
      </Section>

      <Section title="Your skin type">
        <ChipGroup options={SKIN_TYPES} selected={skinType} onSelect={(v) => setSkinType(v as SkinType)} />
      </Section>
    </div>
  )
}

// ── Shared Sub-Components ────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem' }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function ChipGroup({ options, selected, onSelect }: {
  options: { value: string; label: string }[]
  selected: string
  onSelect: (v: string) => void
}) {
  return (
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onSelect(opt.value)}
          style={{
            background: selected === opt.value ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.04)',
            border: `1px solid ${selected === opt.value ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.1)'}`,
            color: selected === opt.value ? '#a5b4fc' : 'rgba(255,255,255,0.6)',
            borderRadius: '8px',
            padding: '0.5rem 0.85rem',
            fontSize: '0.82rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            fontWeight: selected === opt.value ? 600 : 400,
          }}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
