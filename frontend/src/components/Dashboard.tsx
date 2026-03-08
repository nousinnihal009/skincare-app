import React, { useState, useEffect } from 'react';
import { getEnvironmentRisks } from '../api';
import type { Page } from '../App';

interface Props {
  onNavigate: (page: Page) => void;
}

interface HistoryEntry {
  date: string;
  condition: string;
  confidence: number;
  risk: string;
}

const Dashboard: React.FC<Props> = ({ onNavigate }) => {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [envRisks, setEnvRisks] = useState<any>(null);

  useEffect(() => {
    // Load history from localStorage
    try {
      const h = JSON.parse(localStorage.getItem('dermaiHistory') || '[]');
      setHistory(h);
    } catch { setHistory([]); }

    // Fetch environment risks
    getEnvironmentRisks({ uv_index: 7, humidity: 45, pollution_aqi: 65, temperature: 28 })
      .then(setEnvRisks)
      .catch(() => {});
  }, []);

  const totalScans = history.length;
  const avgConfidence = totalScans > 0 ? Math.round(history.reduce((s, h) => s + h.confidence, 0) / totalScans) : 0;
  const highRiskCount = history.filter(h => h.risk.toLowerCase().includes('high') || h.risk.toLowerCase().includes('critical')).length;

  // Condition frequency
  const conditionCounts: Record<string, number> = {};
  history.forEach(h => { conditionCounts[h.condition] = (conditionCounts[h.condition] || 0) + 1; });
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
        <h1 className="page-title animate-fade-in-up">📊 Dashboard</h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          Track your skin health journey and environmental risk factors.
        </p>
      </div>

      {/* Stats */}
      <div className="grid-4 animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
        {[
          { value: totalScans, label: 'Total Scans', icon: '🔬' },
          { value: `${avgConfidence}%`, label: 'Avg Confidence', icon: '📈' },
          { value: highRiskCount, label: 'High Risk Alerts', icon: '🚨' },
          { value: topConditions[0]?.[0] || 'N/A', label: 'Most Detected', icon: '🏥' },
        ].map((stat, i) => (
          <div key={i} className="glass-card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>{stat.icon}</div>
            <div className="stat-value" style={{ fontSize: typeof stat.value === 'string' && stat.value.length > 5 ? '1rem' : '1.5rem' }}>
              {stat.value}
            </div>
            <p style={{ color: 'var(--dark-200)', fontSize: '0.8rem', marginTop: '4px' }}>{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '24px' }}>
        {/* Environment Risks */}
        <div className="glass-card animate-fade-in-up stagger-3">
          <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.1rem' }}>
            🌍 Environmental Skin Risks
          </h3>
          {envRisks?.risks ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {envRisks.risks.map((risk: any, i: number) => (
                <div key={i} style={{
                  padding: '12px', borderRadius: '10px', border: '1px solid var(--dark-500)',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.2rem' }}>{risk.icon}</span>
                    <div>
                      <p style={{ color: 'white', fontWeight: 600, fontSize: '0.9rem' }}>{risk.type}</p>
                      <p style={{ color: 'var(--dark-300)', fontSize: '0.8rem' }}>{risk.value} {risk.unit}</p>
                    </div>
                  </div>
                  <span className={`badge ${risk.color === 'green' ? 'badge-green' : risk.color === 'red' || risk.color === 'purple' ? 'badge-red' : risk.color === 'orange' ? 'badge-amber' : 'badge-blue'}`}>
                    {risk.level}
                  </span>
                </div>
              ))}
              <p style={{ color: 'var(--dark-300)', fontSize: '0.8rem', marginTop: '4px' }}>{envRisks.overall}</p>
            </div>
          ) : (
            <p style={{ color: 'var(--dark-300)' }}>Loading environment data...</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="glass-card animate-fade-in-up stagger-4">
          <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.1rem' }}>
            ⚡ Quick Actions
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { icon: '🔬', label: 'New Skin Analysis', page: 'analysis' as Page },
              { icon: '🤖', label: 'Ask AI Dermatologist', page: 'chat' as Page },
              { icon: '👨‍⚕️', label: 'Find a Dermatologist', page: 'doctors' as Page },
              { icon: '🧴', label: 'Skincare Routine', page: 'recommendations' as Page },
              { icon: '🧪', label: 'Ingredient Scanner', page: 'ingredients' as Page },
            ].map((action, i) => (
              <button key={i} onClick={() => onNavigate(action.page)} style={{
                display: 'flex', alignItems: 'center', gap: '12px',
                padding: '12px 16px', borderRadius: '10px',
                border: '1px solid var(--dark-500)', background: 'transparent',
                color: 'var(--dark-100)', cursor: 'pointer', width: '100%', textAlign: 'left',
                transition: 'all 0.2s', fontSize: '0.95rem',
              }}
              onMouseOver={e => { e.currentTarget.style.background = 'rgba(99,102,241,0.1)'; e.currentTarget.style.borderColor = 'rgba(99,102,241,0.3)'; }}
              onMouseOut={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'var(--dark-500)'; }}
              >
                <span style={{ fontSize: '1.2rem' }}>{action.icon}</span>
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Recent History */}
      <div className="glass-card animate-fade-in-up stagger-5" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem' }}>📋 Recent Analyses</h3>
          {history.length > 0 && (
            <button className="btn-ghost" onClick={() => { localStorage.removeItem('dermaiHistory'); setHistory([]); }} style={{ fontSize: '0.8rem' }}>
              Clear History
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <p style={{ color: 'var(--dark-300)', marginBottom: '16px' }}>No analyses yet. Start by uploading a skin image.</p>
            <button className="btn-primary" onClick={() => onNavigate('analysis')}>Start Analysis →</button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--dark-500)' }}>
                  {['Date', 'Condition', 'Confidence', 'Risk Level'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '10px 12px', color: 'var(--dark-200)', fontWeight: 600, fontSize: '0.85rem' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 10).map((entry, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--dark-600)' }}>
                    <td style={{ padding: '10px 12px', color: 'var(--dark-100)', fontSize: '0.9rem' }}>
                      {new Date(entry.date).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '10px 12px', color: 'white', fontWeight: 500, fontSize: '0.9rem' }}>
                      {entry.condition}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="progress-bar" style={{ width: '80px', height: '5px' }}>
                          <div className="progress-fill" style={{ width: `${entry.confidence}%` }} />
                        </div>
                        <span style={{ color: 'var(--dark-100)', fontSize: '0.85rem' }}>{entry.confidence}%</span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className={`badge ${riskBadge(entry.risk)}`}>{entry.risk}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
