// REMEDIATION: Fix 3 applied
/**
 * RedFlagsPanel.tsx — Red flags with urgency-colored rows + when_to_see_doctor
 */

import type { RedFlag } from '../../../types/conditions'

interface RedFlagsPanelProps {
  red_flags: RedFlag[]
  when_to_see_doctor: string
}

export function RedFlagsPanel({ red_flags, when_to_see_doctor }: RedFlagsPanelProps) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderLeft: '4px solid #ef4444',
      borderRadius: '14px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      <h3 style={{ color: '#fff', margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600 }}>
        🚩 Red Flags — When to Seek Help
      </h3>

      {when_to_see_doctor && (
        <div style={{
          background: 'rgba(239,68,68,0.08)',
          borderRadius: '8px',
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
        }}>
          <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.82rem', margin: 0, lineHeight: 1.5 }}>
            {when_to_see_doctor}
          </p>
        </div>
      )}

      {red_flags.map((rf, i) => (
        <div
          key={i}
          role={rf.urgency === 'see_doctor_today' ? 'alert' : undefined}
          aria-live={rf.urgency === 'see_doctor_today' ? 'assertive' : undefined}
          style={{
            background: 'rgba(239,68,68,0.06)',
            border: '1px solid rgba(239,68,68,0.15)',
            borderRadius: '10px',
            padding: '0.75rem 1rem',
            marginBottom: '0.5rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
            <span style={{
              background: 'rgba(239,68,68,0.2)', color: '#ef4444',
              borderRadius: '6px', padding: '0.1rem 0.5rem',
              fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
            }}>
              {rf.urgency.replace(/_/g, ' ')}
            </span>
          </div>
          <div style={{ color: 'rgba(255,255,255,0.85)', fontSize: '0.82rem', fontWeight: 600 }}>
            {rf.description}
          </div>
          <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.78rem', marginTop: '0.2rem' }}>
            {rf.action}
          </div>
        </div>
      ))}

      <a
        href="https://www.google.com/maps/search/dermatologist+near+me"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Find a dermatologist near you (opens in new tab)"
        style={{
          display: 'inline-block', marginTop: '0.5rem',
          padding: '0.5rem 1rem',
          background: 'rgba(239,68,68,0.15)',
          color: '#ef4444', fontSize: '0.82rem', fontWeight: 600,
          borderRadius: '8px', textDecoration: 'none',
          transition: 'background 0.2s',
        }}
      >
        Find a Dermatologist →
      </a>
    </div>
  )
}
