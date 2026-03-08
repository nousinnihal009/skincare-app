import React, { useState } from 'react';
import { checkIngredients } from '../api';

interface IngredientResult {
  ingredient: string;
  safety: string;
  description: string;
  acne_risk: boolean | null;
  allergen_risk: boolean | null;
}

const IngredientScanner: React.FC = () => {
  const [input, setInput] = useState('');
  const [results, setResults] = useState<IngredientResult[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCheck = async () => {
    if (!input.trim()) return;
    setLoading(true);
    const ingredients = input.split(',').map(i => i.trim()).filter(Boolean);
    try {
      const res = await checkIngredients(ingredients);
      setResults(res.results || []);
      setSummary(res.summary || null);
    } catch { setResults([]); }
    setLoading(false);
  };

  const safetyColor = (safety: string) => {
    if (safety === 'safe') return 'var(--accent-emerald)';
    if (safety === 'caution') return 'var(--accent-amber)';
    if (safety === 'harmful') return 'var(--accent-rose)';
    return 'var(--dark-200)';
  };

  const safetyEmoji = (safety: string) => {
    if (safety === 'safe') return '✅';
    if (safety === 'caution') return '⚠️';
    if (safety === 'harmful') return '🚫';
    return '❓';
  };

  const presets = [
    { label: 'Retinol + Niacinamide', value: 'retinol, niacinamide' },
    { label: 'Common Harmful', value: 'formaldehyde, mercury, lead' },
    { label: 'Acne-safe Check', value: 'salicylic acid, benzoyl peroxide, niacinamide, coconut oil' },
    { label: 'Anti-aging Stack', value: 'retinol, vitamin c, hyaluronic acid, peptides, ceramides' },
  ];

  return (
    <div className="page-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">🧪 Ingredient Safety Scanner</h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          Check if your skincare ingredients are safe, acne-triggering, or allergenic.
        </p>
      </div>

      {/* Input */}
      <div className="glass-card animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
        <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '8px', display: 'block' }}>
          Enter ingredient names (comma separated)
        </label>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input
            className="input-field"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="e.g. retinol, niacinamide, coconut oil"
            onKeyDown={e => e.key === 'Enter' && handleCheck()}
            id="ingredient-input"
          />
          <button className="btn-primary" onClick={handleCheck} disabled={loading || !input.trim()} id="ingredient-check">
            {loading ? '...' : 'Check'}
          </button>
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
          {presets.map((p, i) => (
            <button key={i} onClick={() => setInput(p.value)} style={{
              padding: '6px 14px', borderRadius: '20px', fontSize: '0.8rem',
              background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
              color: 'var(--primary-300)', cursor: 'pointer', fontWeight: 500,
            }}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <div className="glass-card animate-fade-in" style={{ marginBottom: '24px' }}>
          <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px' }}>Summary</h3>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            <div style={{ textAlign: 'center' }}>
              <div className="stat-value" style={{ color: 'var(--accent-emerald)' }}>{summary.safe_count}</div>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem' }}>Safe</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div className="stat-value" style={{ color: 'var(--accent-amber)' }}>{summary.caution_count}</div>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem' }}>Caution</p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div className="stat-value" style={{ color: 'var(--accent-rose)' }}>{summary.harmful_count}</div>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem' }}>Harmful</p>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {results.map((r, i) => (
            <div key={i} className="glass-card animate-fade-in-up" style={{ animationDelay: `${i * 0.08}s`, opacity: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                <h4 style={{ color: 'white', fontWeight: 700, fontSize: '1.05rem' }}>
                  {safetyEmoji(r.safety)} {r.ingredient}
                </h4>
                <span className={`badge ${r.safety === 'safe' ? 'badge-green' : r.safety === 'caution' ? 'badge-amber' : r.safety === 'harmful' ? 'badge-red' : 'badge-purple'}`}>
                  {r.safety}
                </span>
              </div>
              <p style={{ color: 'var(--dark-200)', lineHeight: 1.6, fontSize: '0.9rem', marginBottom: '8px' }}>{r.description}</p>
              <div style={{ display: 'flex', gap: '16px', fontSize: '0.85rem' }}>
                {r.acne_risk !== null && (
                  <span style={{ color: r.acne_risk ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                    {r.acne_risk ? '⚠️ May cause acne' : '✅ Non-comedogenic'}
                  </span>
                )}
                {r.allergen_risk !== null && (
                  <span style={{ color: r.allergen_risk ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                    {r.allergen_risk ? '⚠️ Potential allergen' : '✅ Low allergen risk'}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="disclaimer" style={{ marginTop: '24px' }}>
        <span>⚠️</span>
        <span>AI-powered analysis. For comprehensive ingredient safety, consult a dermatologist or visit INCIDecoder.com.</span>
      </div>
    </div>
  );
};

export default IngredientScanner;
