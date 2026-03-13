// REMEDIATION: Fix 3 applied
/**
 * EducationCard.tsx — Condition education with glassmorphism card
 */

import type { ConditionEducation } from '../../../types/conditions'

interface EducationCardProps {
  education: ConditionEducation
  referral_recommended: boolean
}

export function EducationCard({ education, referral_recommended }: EducationCardProps) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '14px',
      padding: '1.25rem',
      marginBottom: '1rem',
      backdropFilter: 'blur(12px)',
    }}>
      <h3 style={{ color: '#fff', margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600 }}>
        📚 Understanding Your Condition
      </h3>

      <div style={{ marginBottom: '1rem' }}>
        <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', margin: '0 0 0.4rem' }}>
          What is it?
        </h4>
        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.85rem', margin: 0, lineHeight: 1.6 }}>
          {education.what_it_is}
        </p>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', margin: '0 0 0.4rem' }}>
          What causes it?
        </h4>
        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.85rem', margin: 0, lineHeight: 1.6 }}>
          {education.what_causes_it}
        </p>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', margin: '0 0 0.4rem' }}>
          Duration
        </h4>
        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.85rem', margin: 0 }}>
          {education.typical_duration}
        </p>
      </div>

      {/* Badges */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.75rem' }}>
        {education.is_contagious && (
          <span style={{ background: 'rgba(245,158,11,0.2)', color: '#f59e0b', padding: '0.15rem 0.55rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600 }}>
            ⚡ Contagious
          </span>
        )}
        {education.is_curable ? (
          <span style={{ background: 'rgba(34,197,94,0.2)', color: '#22c55e', padding: '0.15rem 0.55rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600 }}>
            ✓ Curable
          </span>
        ) : (
          <span style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.5)', padding: '0.15rem 0.55rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600 }}>
            ◎ Chronic — Manageable
          </span>
        )}
        {referral_recommended && (
          <span style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444', padding: '0.15rem 0.55rem', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 600 }}>
            🩺 Referral Recommended
          </span>
        )}
      </div>

      {education.contagion_guidance && (
        <div style={{
          background: 'rgba(245,158,11,0.1)', borderRadius: '8px', padding: '0.75rem',
          border: '1px solid rgba(245,158,11,0.2)',
        }}>
          <p style={{ color: '#f59e0b', fontSize: '0.82rem', margin: 0, fontWeight: 600 }}>
            ⚡ Contagion Guidance
          </p>
          <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.82rem', margin: '0.25rem 0 0' }}>
            {education.contagion_guidance}
          </p>
        </div>
      )}

      {education.common_misconceptions.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', margin: '0 0 0.5rem' }}>
            Common Myths
          </h4>
          {education.common_misconceptions.map((m, i) => (
            <p key={i} style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.8rem', margin: '0.35rem 0', lineHeight: 1.4 }}>
              {m}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
