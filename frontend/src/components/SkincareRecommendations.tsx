import React, { useState, useEffect } from 'react';
import { getSkincareRoutine } from '../api';
import type { AnalysisResult } from '../App';

interface Props {
  result: AnalysisResult | null;
}

interface RoutineStep {
  step: string;
  product: string;
  note: string;
}

const SkincareRecommendations: React.FC<Props> = ({ result }) => {
  const [routine, setRoutine] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [condition, setCondition] = useState(result?.prediction?.class_name || 'acne-pustular');
  const [skinType, setSkinType] = useState('normal');

  const conditions = [
    'acne-closed-comedo', 'acne-cystic', 'acne-pustular', 'acne-scar',
    'Atopic Dermatitis', 'Eczema', 'Melanoma', 'rosacea', 'pigmentation',
    'Psoriasis pictures Lichen Planus and related diseases',
  ];

  const fetchRoutine = async () => {
    setLoading(true);
    try {
      const res = await getSkincareRoutine(condition, skinType);
      setRoutine(res);
    } catch { setRoutine(null); }
    setLoading(false);
  };

  useEffect(() => { fetchRoutine(); }, []);

  const renderRoutineSection = (title: string, icon: string, steps: RoutineStep[], bgColor: string) => (
    <div className="glass-card" style={{ flex: 1, minWidth: '300px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <div style={{
          width: '48px', height: '48px', borderRadius: '12px',
          background: bgColor, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1.3rem'
        }}>{icon}</div>
        <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem' }}>{title}</h3>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {steps.map((s: RoutineStep, i: number) => (
          <div key={i} style={{
            padding: '14px 16px', borderRadius: '10px',
            border: '1px solid var(--dark-500)', background: 'var(--dark-700)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ color: 'var(--primary-300)', fontWeight: 600, fontSize: '0.85rem' }}>{s.step}</span>
              <span style={{ color: 'var(--dark-300)', fontSize: '0.75rem' }}>Step {i + 1}</span>
            </div>
            <p style={{ color: 'white', fontWeight: 500, fontSize: '0.95rem', marginBottom: '4px' }}>{s.product}</p>
            <p style={{ color: 'var(--dark-200)', fontSize: '0.8rem' }}>{s.note}</p>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="page-container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">🧴 Skincare Routine</h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          Personalized skincare routines based on your skin condition and type.
        </p>
      </div>

      {/* Config */}
      <div className="glass-card animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'end' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '6px', display: 'block' }}>Condition</label>
            <select className="select-field" value={condition} onChange={e => setCondition(e.target.value)} id="routine-condition">
              {conditions.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '6px', display: 'block' }}>Skin Type</label>
            <select className="select-field" value={skinType} onChange={e => setSkinType(e.target.value)} id="routine-skin-type">
              <option value="normal">Normal</option>
              <option value="oily">Oily</option>
              <option value="dry">Dry</option>
              <option value="combination">Combination</option>
              <option value="sensitive">Sensitive</option>
            </select>
          </div>
          <button className="btn-primary" onClick={fetchRoutine} style={{ height: '46px' }} id="routine-generate">Generate Routine</button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : routine ? (
        <>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '24px' }}>
            {routine.morning?.length > 0 && renderRoutineSection('Morning Routine', '☀️', routine.morning, 'rgba(245,158,11,0.15)')}
            {routine.evening?.length > 0 && renderRoutineSection('Evening Routine', '🌙', routine.evening, 'rgba(99,102,241,0.15)')}
          </div>

          {routine.weekly?.length > 0 && (
            <div className="glass-card" style={{ marginBottom: '24px' }}>
              <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', marginBottom: '16px' }}>📅 Weekly Care</h3>
              <ul style={{ color: 'var(--dark-200)', paddingLeft: '20px', lineHeight: 2 }}>
                {routine.weekly.map((item: string, i: number) => <li key={i}>{item}</li>)}
              </ul>
            </div>
          )}

          {routine.adjustments?.length > 0 && (
            <div className="glass-card" style={{ marginBottom: '24px' }}>
              <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', marginBottom: '12px' }}>✨ Skin Type Adjustments</h3>
              {routine.adjustments.map((adj: string, i: number) => (
                <p key={i} style={{ color: 'var(--dark-200)', lineHeight: 1.6 }}>{adj}</p>
              ))}
            </div>
          )}
        </>
      ) : null}

      <div className="disclaimer">
        <span>⚠️</span>
        <span>These are AI-generated suggestions, not medical prescriptions. Always consult a dermatologist before starting new products.</span>
      </div>
    </div>
  );
};

export default SkincareRecommendations;
