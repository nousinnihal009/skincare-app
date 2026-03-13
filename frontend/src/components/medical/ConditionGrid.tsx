// REMEDIATION: Fix 5 + Fix 9 + Fix 15 (partial) applied
/**
 * ConditionGrid.tsx — Browsable/searchable grid of 18 supported conditions
 * Includes CategoryDModal intercept and "Not sure what I have" CTA.
 */

import { useState, useMemo } from 'react'
import { useMedicalStore } from '../../store/medicalStore'
import {
  CONDITION_ICONS,
  CONDITION_DESCRIPTORS,
  CATEGORY_LABELS,
  CATEGORY_D_CONDITIONS,
  CONTAGIOUS_CONDITIONS,
} from '../../constants/conditionMeta'
import type { ConditionKey, ConditionCategory } from '../../types/conditions'

const CATEGORY_COLORS: Record<ConditionCategory, string> = {
  inflammatory: '#6366f1',
  infectious: '#f59e0b',
  pigmentation: '#8b5cf6',
  high_risk: '#ef4444',
}

const CATEGORY_BG: Record<ConditionCategory, string> = {
  inflammatory: 'rgba(99,102,241,0.12)',
  infectious: 'rgba(245,158,11,0.12)',
  pigmentation: 'rgba(139,92,246,0.12)',
  high_risk: 'rgba(239,68,68,0.12)',
}

const CATEGORY_ORDER: ConditionCategory[] = ['inflammatory', 'infectious', 'pigmentation', 'high_risk']

const CATEGORY_D: ConditionKey[] = ['actinic_keratosis', 'melanoma_risk']

interface ConditionGridProps {
  onNavigate?: (page: any) => void
}

export function ConditionGrid({ onNavigate }: ConditionGridProps) {
  const conditions = useMedicalStore((s) => s.conditions)
  const conditionsLoading = useMedicalStore((s) => s.conditionsLoading)
  const conditionsError = useMedicalStore((s) => s.conditionsError)
  const selectCondition = useMedicalStore((s) => s.selectCondition)

  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<ConditionCategory | 'all'>('all')

  // Fix 5: Category D modal state
  const [categoryDModalOpen, setCategoryDModalOpen] = useState(false)
  const [pendingCondition, setPendingCondition] = useState<ConditionKey | null>(null)

  const filtered = useMemo(() => {
    let list = conditions
    if (categoryFilter !== 'all') {
      list = list.filter((c) => c.category === categoryFilter)
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter((c) =>
        c.display_name.toLowerCase().includes(q) ||
        (CONDITION_DESCRIPTORS[c.key as ConditionKey] || '').toLowerCase().includes(q)
      )
    }
    return list
  }, [conditions, search, categoryFilter])

  // Fix 5: Modified click handler
  const handleConditionClick = (key: ConditionKey) => {
    if (CATEGORY_D.includes(key)) {
      setPendingCondition(key)
      setCategoryDModalOpen(true)
    } else {
      selectCondition(key)
    }
  }

  const handleCategoryDConfirm = () => {
    if (pendingCondition) {
      selectCondition(pendingCondition)
      setCategoryDModalOpen(false)
      setPendingCondition(null)
    }
  }

  const handleCategoryDCancel = () => {
    setCategoryDModalOpen(false)
    setPendingCondition(null)
  }

  // Fix 9: "Not sure what I have" handler
  const handleUnsureClick = () => {
    if (onNavigate) {
      // NOTE: App doesn't support prefill message natively via navigation,
      // but we send the user to the chat page as requested
      onNavigate('chat')
    }
  }

  if (conditionsLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 1rem', color: 'rgba(255,255,255,0.5)' }}>
        <div style={{
          width: '40px', height: '40px', border: '3px solid rgba(255,255,255,0.15)',
          borderTopColor: '#6366f1', borderRadius: '50%', margin: '0 auto 1rem',
          animation: 'spin 0.8s linear infinite',
        }} />
        <p>Loading conditions…</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      </div>
    )
  }

  if (conditionsError) {
    return (
      <div style={{
        textAlign: 'center', padding: '3rem', color: '#ef4444',
        background: 'rgba(239,68,68,0.08)', borderRadius: '12px', margin: '2rem 0',
      }}>
        <p style={{ fontSize: '1.1rem', fontWeight: 600 }}>Failed to load conditions</p>
        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.85rem' }}>{conditionsError}</p>
      </div>
    )
  }

  return (
    <div>
      {/* Fix 9: Header with "Not sure" CTA */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ color: '#fff', fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>🩺 Medical Skin Conditions</h1>
          <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem', marginTop: '0.35rem', marginBottom: 0 }}>
            Find your condition and get a supportive care protocol built around clinical evidence.
          </p>
        </div>
        <button
          onClick={handleUnsureClick}
          aria-label="I'm not sure what condition I have — get help identifying it"
          style={{
            flexShrink: 0,
            padding: '0.5rem 1rem',
            borderRadius: '12px',
            border: '1px solid rgba(99,102,241,0.4)',
            background: 'none',
            color: '#a5b4fc',
            fontSize: '0.82rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            whiteSpace: 'nowrap',
            marginLeft: '1rem',
          }}
        >
          🤔 Not sure what I have?
        </button>
      </div>

      {/* Search + Filters */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <input
          type="text"
          placeholder="Search conditions…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: '1 1 250px',
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: '10px',
            padding: '0.65rem 1rem',
            color: '#fff',
            fontSize: '0.9rem',
            outline: 'none',
          }}
        />
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <FilterChip
            label="All"
            active={categoryFilter === 'all'}
            color="#6366f1"
            onClick={() => setCategoryFilter('all')}
          />
          {CATEGORY_ORDER.map((cat) => (
            <FilterChip
              key={cat}
              label={CATEGORY_LABELS[cat]}
              active={categoryFilter === cat}
              color={CATEGORY_COLORS[cat]}
              onClick={() => setCategoryFilter(cat)}
            />
          ))}
        </div>
      </div>

      {/* Grid */}
      <div
        role="list"
        aria-label="Available medical skin conditions"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '1rem',
        }}
      >
        {filtered.map((c) => {
          const key = c.key as ConditionKey
          const cat = c.category as ConditionCategory
          const isHighRisk = CATEGORY_D_CONDITIONS.has(key)
          const isContagious = CONTAGIOUS_CONDITIONS.has(key)
          return (
            <button
              key={key}
              role="listitem"
              aria-label={`${c.display_name} — ${CONDITION_DESCRIPTORS[key]}`}
              onClick={() => handleConditionClick(key)}
              style={{
                background: CATEGORY_BG[cat],
                border: `1px solid ${CATEGORY_COLORS[cat]}30`,
                borderRadius: '14px',
                padding: '1.25rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.25s',
                position: 'relative',
                overflow: 'hidden',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.borderColor = `${CATEGORY_COLORS[cat]}60`
                e.currentTarget.style.boxShadow = `0 8px 24px ${CATEGORY_COLORS[cat]}15`
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.borderColor = `${CATEGORY_COLORS[cat]}30`
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              {/* Badges */}
              <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                <span style={{
                  background: `${CATEGORY_COLORS[cat]}25`,
                  color: CATEGORY_COLORS[cat],
                  padding: '0.15rem 0.5rem',
                  borderRadius: '6px',
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}>
                  {CATEGORY_LABELS[cat]}
                </span>
                {isContagious && (
                  <span style={{
                    background: 'rgba(245,158,11,0.2)',
                    color: '#f59e0b',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '6px',
                    fontSize: '0.65rem',
                    fontWeight: 600,
                  }}>⚡ CONTAGIOUS</span>
                )}
                {isHighRisk && (
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                    background: 'rgba(239,68,68,0.2)',
                    color: '#ef4444',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '6px',
                    fontSize: '0.65rem',
                    fontWeight: 600,
                  }}>
                    <span
                      style={{
                        width: '6px', height: '6px', borderRadius: '50%',
                        background: '#ef4444',
                        animation: 'pulse-dot 2s infinite',
                      }}
                      aria-label="High risk condition — immediate medical evaluation recommended"
                      role="img"
                    />
                    HIGH RISK
                  </span>
                )}
              </div>

              {/* Icon + Name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '1.5rem' }}>
                  {CONDITION_ICONS[key] || '🔬'}
                </span>
                <h3 style={{
                  color: '#fff',
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  margin: 0,
                }}>
                  {c.display_name}
                </h3>
              </div>

              {/* Descriptor */}
              <p style={{
                color: 'rgba(255,255,255,0.5)',
                fontSize: '0.78rem',
                margin: '0.25rem 0 0',
                lineHeight: 1.4,
              }}>
                {CONDITION_DESCRIPTORS[key] || ''}
              </p>

              {/* Curable badge */}
              <div style={{ marginTop: '0.75rem' }}>
                <span style={{
                  color: c.is_curable ? '#34d399' : 'rgba(255,255,255,0.4)',
                  fontSize: '0.7rem',
                  fontWeight: 500,
                }}>
                  {c.is_curable ? '✓ Curable' : '◎ Chronic — Manageable'}
                </span>
              </div>
            </button>
          )
        })}
      </div>

      {filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'rgba(255,255,255,0.4)' }}>
          <p style={{ fontSize: '1.1rem' }}>No conditions match your search</p>
        </div>
      )}

      {/* Fix 5: Category D Modal */}
      {categoryDModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="category-d-modal-title"
          style={{
            position: 'fixed', inset: 0, zIndex: 50,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          }}
        >
          <div style={{
            background: '#1A1A2E',
            border: '1px solid rgba(239,68,68,0.5)',
            borderRadius: '16px',
            padding: '2rem',
            boxShadow: '0 25px 50px rgba(0,0,0,0.5)',
            maxWidth: '28rem',
            width: '100%',
            margin: '0 1rem',
          }}>
            <h2 id="category-d-modal-title" style={{ color: '#fff', fontWeight: 700, fontSize: '1.1rem', margin: '0 0 0.75rem' }}>
              ⚠️ Important Notice
            </h2>
            <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.85rem', margin: '0 0 0.5rem' }}>
              This condition may require immediate medical evaluation.
            </p>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.85rem', margin: '0 0 1.5rem' }}>
              The care protocol we provide is supportive information only — it is not a
              substitute for professional dermatological assessment.
              Do you wish to continue?
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button
                onClick={handleCategoryDCancel}
                aria-label="Cancel and return to condition list"
                style={{
                  padding: '0.5rem 1rem', borderRadius: '10px',
                  border: '1px solid rgba(255,255,255,0.2)',
                  background: 'none', color: 'rgba(255,255,255,0.7)',
                  fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.2s',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCategoryDConfirm}
                aria-label="I understand — continue to intake"
                style={{
                  padding: '0.5rem 1rem', borderRadius: '10px',
                  border: 'none',
                  background: '#dc2626', color: '#fff',
                  fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                I Understand — Continue
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  )
}

function FilterChip({ label, active, color, onClick }: {
  label: string; active: boolean; color: string; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? `${color}25` : 'rgba(255,255,255,0.06)',
        color: active ? color : 'rgba(255,255,255,0.5)',
        border: `1px solid ${active ? `${color}50` : 'rgba(255,255,255,0.1)'}`,
        borderRadius: '8px',
        padding: '0.4rem 0.8rem',
        fontSize: '0.78rem',
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      {label}
    </button>
  )
}
