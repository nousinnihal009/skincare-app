import React, { useState, useEffect } from 'react';
import type { Page } from '../App';

interface Props {
  onNavigate: (page: Page) => void;
}

interface ProgressEntry {
  id: string;
  date: string;
  condition: string;
  confidence: number;
  risk: string;
  notes: string;
  skinType?: string;
}

const ProgressTracker: React.FC<Props> = ({ onNavigate }) => {
  const [entries, setEntries] = useState<ProgressEntry[]>([]);
  const [showAddNote, setShowAddNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState('');
  const [viewMode, setViewMode] = useState<'timeline' | 'chart'>('timeline');

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = () => {
    try {
      const raw = JSON.parse(localStorage.getItem('dermaiProgress') || '[]');
      setEntries(raw);
    } catch {
      // Also try loading from analysis history as seed data
      try {
        const history = JSON.parse(localStorage.getItem('dermaiHistory') || '[]');
        const converted: ProgressEntry[] = history.map((h: any, i: number) => ({
          id: `hist-${i}`,
          date: h.date,
          condition: h.condition,
          confidence: h.confidence,
          risk: h.risk,
          notes: '',
        }));
        setEntries(converted);
        localStorage.setItem('dermaiProgress', JSON.stringify(converted));
      } catch {
        setEntries([]);
      }
    }
  };

  const saveNote = (entryId: string) => {
    const updated = entries.map(e => e.id === entryId ? { ...e, notes: noteText } : e);
    setEntries(updated);
    localStorage.setItem('dermaiProgress', JSON.stringify(updated));
    setShowAddNote(null);
    setNoteText('');
  };

  const deleteEntry = (entryId: string) => {
    const updated = entries.filter(e => e.id !== entryId);
    setEntries(updated);
    localStorage.setItem('dermaiProgress', JSON.stringify(updated));
  };

  const clearAll = () => {
    setEntries([]);
    localStorage.removeItem('dermaiProgress');
  };

  // Compute trend data
  const confidenceTrend = entries.slice().reverse().map(e => e.confidence);
  const maxConfidence = Math.max(...confidenceTrend, 1);
  const riskDistribution = entries.reduce((acc, e) => {
    const key = e.risk.toLowerCase().includes('critical') || e.risk.toLowerCase().includes('high') ? 'High' : e.risk.toLowerCase().includes('moderate') ? 'Moderate' : 'Low';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Unique conditions
  const conditionCounts: Record<string, number> = {};
  entries.forEach(e => { conditionCounts[e.condition] = (conditionCounts[e.condition] || 0) + 1; });
  const topConditions = Object.entries(conditionCounts).sort((a, b) => b[1] - a[1]).slice(0, 5);

  const riskBadge = (risk: string) => {
    const r = risk.toLowerCase();
    if (r.includes('critical') || r.includes('high')) return 'badge-red';
    if (r.includes('moderate')) return 'badge-amber';
    return 'badge-green';
  };

  return (
    <div className="page-container" style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">📈 Skin Progress Tracker</h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          Track your skin health journey over time with visual analytics.
        </p>
      </div>

      {/* View Mode Toggle */}
      <div className="animate-fade-in-up stagger-2" style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '24px' }}>
        <button className={viewMode === 'timeline' ? 'btn-primary' : 'btn-secondary'} onClick={() => setViewMode('timeline')} style={{ padding: '10px 20px', fontSize: '0.9rem' }}>
          📅 Timeline
        </button>
        <button className={viewMode === 'chart' ? 'btn-primary' : 'btn-secondary'} onClick={() => setViewMode('chart')} style={{ padding: '10px 20px', fontSize: '0.9rem' }}>
          📊 Analytics
        </button>
      </div>

      {entries.length === 0 ? (
        <div className="glass-card animate-fade-in-up stagger-3" style={{ textAlign: 'center', padding: '60px 32px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📊</div>
          <h3 style={{ color: 'white', marginBottom: '8px' }}>No Progress Data Yet</h3>
          <p style={{ color: 'var(--dark-200)', marginBottom: '24px' }}>
            Run skin analyses to start tracking your skin health journey over time.
          </p>
          <button className="btn-primary" onClick={() => onNavigate('analysis')}>
            Start First Analysis →
          </button>
        </div>
      ) : viewMode === 'chart' ? (
        <>
          {/* Analytics View */}
          <div className="grid-2 animate-fade-in-up stagger-3" style={{ marginBottom: '24px' }}>
            {/* Confidence Trend Chart */}
            <div className="glass-card">
              <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.05rem' }}>
                📈 Confidence Trend
              </h3>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '140px', padding: '0 4px' }}>
                {confidenceTrend.map((val, i) => (
                  <div key={i} style={{
                    flex: 1,
                    maxWidth: '40px',
                    height: `${(val / maxConfidence) * 100}%`,
                    background: val > 80 ? 'var(--gradient-primary)' : val > 50 ? 'rgba(245,158,11,0.6)' : 'rgba(244,63,94,0.6)',
                    borderRadius: '4px 4px 0 0',
                    minHeight: '4px',
                    transition: 'height 0.6s ease',
                    position: 'relative',
                  }}>
                    <div style={{
                      position: 'absolute', top: '-18px', left: '50%', transform: 'translateX(-50%)',
                      fontSize: '0.65rem', color: 'var(--dark-200)', whiteSpace: 'nowrap'
                    }}>
                      {val}%
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '0.7rem', color: 'var(--dark-300)' }}>
                <span>Oldest</span>
                <span>Latest</span>
              </div>
            </div>

            {/* Risk Distribution */}
            <div className="glass-card">
              <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.05rem' }}>
                ⚖️ Risk Distribution
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {['Low', 'Moderate', 'High'].map(level => {
                  const count = riskDistribution[level] || 0;
                  const pct = entries.length > 0 ? Math.round((count / entries.length) * 100) : 0;
                  return (
                    <div key={level}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span style={{ color: 'var(--dark-100)', fontSize: '0.9rem', fontWeight: 500 }}>{level} Risk</span>
                        <span style={{ color: 'var(--dark-200)', fontSize: '0.85rem' }}>{count} ({pct}%)</span>
                      </div>
                      <div className="progress-bar" style={{ height: '8px' }}>
                        <div className="progress-fill" style={{
                          width: `${pct}%`,
                          background: level === 'High' ? 'rgba(244,63,94,0.8)' : level === 'Moderate' ? 'rgba(245,158,11,0.8)' : 'var(--gradient-primary)',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Top Conditions */}
          <div className="glass-card animate-fade-in-up stagger-4" style={{ marginBottom: '24px' }}>
            <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.05rem' }}>
              🏥 Most Detected Conditions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {topConditions.map(([condition, count], i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  padding: '12px 16px', borderRadius: '10px',
                  border: '1px solid var(--dark-500)',
                  background: i === 0 ? 'rgba(99,102,241,0.08)' : 'transparent',
                }}>
                  <span style={{ color: 'var(--primary-400)', fontWeight: 700, width: '28px' }}>#{i + 1}</span>
                  <span style={{ flex: 1, color: 'white', fontWeight: 500 }}>{condition}</span>
                  <span className="badge badge-blue">{count}×</span>
                </div>
              ))}
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid-4 animate-fade-in-up stagger-5" style={{ marginBottom: '24px' }}>
            {[
              { icon: '🔬', value: entries.length, label: 'Total Scans' },
              { icon: '📈', value: `${Math.round(entries.reduce((s, e) => s + e.confidence, 0) / entries.length)}%`, label: 'Avg Confidence' },
              { icon: '🗓️', value: entries.length > 0 ? Math.ceil((Date.now() - new Date(entries[entries.length - 1].date).getTime()) / (1000 * 60 * 60 * 24)) : 0, label: 'Days Tracking' },
              { icon: '🏥', value: Object.keys(conditionCounts).length, label: 'Unique Conditions' },
            ].map((stat, i) => (
              <div key={i} className="glass-card" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '1.4rem', marginBottom: '6px' }}>{stat.icon}</div>
                <div className="stat-value" style={{ fontSize: '1.4rem' }}>{stat.value}</div>
                <p style={{ color: 'var(--dark-200)', fontSize: '0.75rem', marginTop: '4px' }}>{stat.label}</p>
              </div>
            ))}
          </div>
        </>
      ) : (
        <>
          {/* Timeline View */}
          <div className="animate-fade-in-up stagger-3" style={{ position: 'relative', paddingLeft: '32px' }}>
            {/* Timeline Line */}
            <div style={{
              position: 'absolute', left: '14px', top: '0', bottom: '0', width: '2px',
              background: 'linear-gradient(to bottom, var(--primary-500), var(--accent-cyan), transparent)',
            }} />

            {entries.map((entry, i) => (
              <div key={entry.id} className="glass-card" style={{
                marginBottom: '16px', position: 'relative',
                animationDelay: `${i * 0.08}s`, opacity: 0,
              }} className={`glass-card animate-fade-in-up`}>
                {/* Timeline dot */}
                <div style={{
                  position: 'absolute', left: '-26px', top: '20px',
                  width: '12px', height: '12px', borderRadius: '50%',
                  background: 'var(--gradient-primary)',
                  boxShadow: '0 0 10px rgba(99,102,241,0.4)',
                }} />

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <p style={{ color: 'var(--dark-300)', fontSize: '0.8rem', marginBottom: '4px' }}>
                      {new Date(entry.date).toLocaleDateString('en-US', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
                      {' '}at{' '}
                      {new Date(entry.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    <h4 style={{ color: 'white', fontWeight: 600, fontSize: '1.05rem' }}>{entry.condition}</h4>
                  </div>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <span className={`badge ${riskBadge(entry.risk)}`}>{entry.risk}</span>
                    <button
                      onClick={() => deleteEntry(entry.id)}
                      style={{
                        background: 'transparent', border: 'none', color: 'var(--dark-300)',
                        cursor: 'pointer', fontSize: '0.8rem', padding: '4px'
                      }}
                      title="Delete entry"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <div className="progress-bar" style={{ flex: 1, height: '6px' }}>
                    <div className="progress-fill" style={{ width: `${entry.confidence}%` }} />
                  </div>
                  <span style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 600 }}>
                    {entry.confidence}%
                  </span>
                </div>

                {/* Notes */}
                {entry.notes && (
                  <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem', borderTop: '1px solid var(--dark-600)', paddingTop: '8px', marginTop: '8px', fontStyle: 'italic' }}>
                    📝 {entry.notes}
                  </p>
                )}

                {/* Add note button */}
                {showAddNote === entry.id ? (
                  <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
                    <input
                      className="input-field"
                      placeholder="Add a note about your skin..."
                      value={noteText}
                      onChange={e => setNoteText(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && saveNote(entry.id)}
                      style={{ flex: 1, padding: '8px 12px', fontSize: '0.85rem' }}
                    />
                    <button className="btn-primary" onClick={() => saveNote(entry.id)} style={{ padding: '8px 16px', fontSize: '0.8rem' }}>Save</button>
                    <button className="btn-ghost" onClick={() => { setShowAddNote(null); setNoteText(''); }} style={{ fontSize: '0.8rem' }}>Cancel</button>
                  </div>
                ) : (
                  <button
                    className="btn-ghost"
                    onClick={() => { setShowAddNote(entry.id); setNoteText(entry.notes || ''); }}
                    style={{ fontSize: '0.8rem', marginTop: '4px' }}
                  >
                    {entry.notes ? '✏️ Edit Note' : '📝 Add Note'}
                  </button>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Actions */}
      {entries.length > 0 && (
        <div className="animate-fade-in-up stagger-5" style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '24px' }}>
          <button className="btn-primary" onClick={() => onNavigate('analysis')}>🔬 New Analysis</button>
          <button className="btn-secondary" onClick={clearAll}>🗑️ Clear History</button>
        </div>
      )}
    </div>
  );
};

export default ProgressTracker;
