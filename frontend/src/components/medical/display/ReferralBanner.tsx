// REMEDIATION: Fix 3 + Fix 4 applied
/**
 * ReferralBanner.tsx — Urgency-styled referral banner with CTA
 * Three-urgency behavior: immediate (non-dismissible), soon/routine (minimizable)
 * Category D conditions are always non-dismissible.
 */

import { useState } from 'react'
import type { ReferralUrgency, ConditionKey } from '../../../types/conditions'

interface ReferralBannerProps {
  referral_urgency: ReferralUrgency
  condition: ConditionKey
}

const CATEGORY_D: ConditionKey[] = ['actinic_keratosis', 'melanoma_risk']

export function ReferralBanner({ referral_urgency, condition }: ReferralBannerProps) {
  const isNonDismissible = referral_urgency === 'immediate' || CATEGORY_D.includes(condition)
  const [minimized, setMinimized] = useState(false)

  if (referral_urgency === 'not_required') return null

  const config = {
    immediate: {
      bg: 'rgba(127,29,29,0.8)',
      border: '#ef4444',
      icon: '🚨',
      cta: 'Find a Dermatologist Now',
      ctaHref: 'https://www.google.com/maps/search/dermatologist+near+me',
    },
    soon: {
      bg: 'rgba(124,45,18,0.6)',
      border: '#f97316',
      icon: '⚠️',
      cta: 'Book a Dermatologist Appointment',
      ctaHref: 'https://www.google.com/maps/search/dermatologist+near+me',
    },
    routine: {
      bg: 'rgba(113,63,18,0.5)',
      border: '#ca8a04',
      icon: '📋',
      cta: 'Schedule a Routine Skin Check',
      ctaHref: 'https://www.google.com/maps/search/dermatologist+near+me',
    },
  }[referral_urgency]

  if (!config) return null

  return (
    <div
      role="alert"
      aria-live={referral_urgency === 'immediate' ? 'assertive' : 'polite'}
      style={{
        background: config.bg,
        border: `1px solid ${config.border}`,
        borderRadius: '14px',
        padding: '1rem 1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: '1rem',
      }}
    >
      {minimized ? (
        <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', flex: 1 }}>
          {config.icon} Medical referral recommended
        </span>
      ) : (
        <div style={{ flex: 1 }}>
          <p style={{ color: '#fff', fontWeight: 600, margin: '0 0 0.5rem', fontSize: '0.95rem' }}>
            {config.icon}{' '}
            {referral_urgency === 'immediate'
              ? 'Immediate medical evaluation recommended'
              : referral_urgency === 'soon'
              ? 'Medical evaluation recommended soon'
              : 'Routine dermatologist check recommended'}
          </p>
          <a
            href={config.ctaHref}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`${config.cta} (opens in new tab)`}
            style={{
              display: 'inline-block',
              marginTop: '0.25rem',
              padding: '0.4rem 1rem',
              background: 'rgba(255,255,255,0.1)',
              color: '#fff',
              fontSize: '0.82rem',
              borderRadius: '8px',
              textDecoration: 'none',
              transition: 'background 0.2s',
            }}
          >
            {config.cta} →
          </a>
        </div>
      )}
      {/* Minimize toggle for non-immediate; nothing for immediate/Category D */}
      {!isNonDismissible && (
        <button
          onClick={() => setMinimized((m) => !m)}
          aria-label={minimized ? 'Expand referral notice' : 'Minimize referral notice'}
          style={{
            background: 'none',
            border: 'none',
            color: 'rgba(255,255,255,0.5)',
            cursor: 'pointer',
            fontSize: '0.72rem',
            flexShrink: 0,
            marginTop: '0.15rem',
          }}
        >
          {minimized ? '▼ Show' : '▲ Minimize'}
        </button>
      )}
    </div>
  )
}
