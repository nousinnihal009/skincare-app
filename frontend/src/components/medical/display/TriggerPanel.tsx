// REMEDIATION: Fix 3 applied
/**
 * TriggerPanel.tsx — Trigger cards with severity badges
 */

import type { TriggerEntry, KnownTrigger } from '../../../types/conditions'

interface TriggerPanelProps {
  trigger_guidance: TriggerEntry[]
  user_triggers: KnownTrigger[]
}

export function TriggerPanel({ trigger_guidance, user_triggers }: TriggerPanelProps) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '14px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      <h3 style={{ color: '#fff', margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600 }}>
        🎯 Trigger Management
      </h3>
      {trigger_guidance.map((t, i) => {
        const isUserTrigger = user_triggers.some(
          (ut) => t.trigger.toLowerCase().includes(ut.replace(/_/g, ' '))
        )
        return (
          <div key={i} style={{
            display: 'flex', gap: '0.75rem', padding: '0.6rem 0',
            borderBottom: i < trigger_guidance.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
          }}>
            <Badge
              label={t.severity_impact}
              color={t.severity_impact === 'severe' ? '#ef4444' : t.severity_impact === 'moderate' ? '#f59e0b' : '#22c55e'}
            />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: '0.82rem', fontWeight: 600 }}>{t.trigger}</span>
                {isUserTrigger && (
                  <span style={{
                    background: 'rgba(99,102,241,0.2)', color: '#a5b4fc',
                    padding: '0.1rem 0.4rem', borderRadius: '4px',
                    fontSize: '0.6rem', fontWeight: 600,
                  }}>
                    🎯 Your trigger
                  </span>
                )}
              </div>
              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.78rem' }}>{t.management_tip}</div>
            </div>
          </div>
        )
      })}
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
