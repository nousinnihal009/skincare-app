import React, { useState } from 'react';
import { generatePDFReport } from '../api';
import type { AnalysisResult, Page } from '../App';
import SkinMetricsPanel from './analyze/SkinMetricsPanel';

interface Props {
  result: AnalysisResult | null;
  uploadedImageUrl: string | null;
  onNavigate: (page: Page) => void;
}

const ResultsPage: React.FC<Props> = ({ result, uploadedImageUrl, onNavigate }) => {
  if (!result) {
    return (
      <div className="page-container" style={{ textAlign: 'center', paddingTop: '80px' }}>
        <h2 style={{ color: 'white', marginBottom: '16px' }}>No Analysis Results</h2>
        <p style={{ color: 'var(--dark-200)', marginBottom: '32px' }}>Upload and analyze a skin image first.</p>
        <button className="btn-primary" onClick={() => onNavigate('analysis')}>
          Go to Analysis →
        </button>
      </div>
    );
  }

  const { prediction, top3, risk_assessment, condition_info, treatments, gradcam_heatmap, confidence_distribution, urgent_warning, disclaimer } = result;

  // New pipeline fields (optional — backward compat)
  const skinMetrics         = result.skin_metrics ?? [];
  const assessmentParagraph = result.assessment_paragraph ?? '';
  const visibleFeatures     = result.visible_features ?? [];
  const referToDerm         = result.refer_to_dermatologist ?? false;
  const llmEnriched         = result.llm_enriched ?? false;
  const llmOverrode         = result.llm_overrode_resnet ?? false;

  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState('');
  const [referralMinimized, setReferralMinimized] = useState(false);

  const handleDownloadPDF = async () => {
    setPdfLoading(true);
    setPdfError('');
    try {
      const blob = await generatePDFReport({
        prediction,
        top3,
        risk_assessment,
        condition_info,
        treatments,
        gradcam_heatmap,
        confidence_distribution,
        urgent_warning,
        disclaimer,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `DermAI_Report_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setPdfError(err.message || 'PDF generation failed');
    }
    setPdfLoading(false);
  };

  const riskBadgeClass = risk_assessment.level === 'critical' || risk_assessment.level === 'high'
    ? 'badge-red' : risk_assessment.level === 'moderate' ? 'badge-amber' : 'badge-green';

  const confidencePercent = Math.round(prediction.confidence * 100);

  // Save to localStorage for dashboard history
  try {
    const history = JSON.parse(localStorage.getItem('dermaiHistory') || '[]');
    history.unshift({
      date: new Date().toISOString(),
      condition: prediction.display_name,
      confidence: confidencePercent,
      risk: risk_assessment.label,
    });
    localStorage.setItem('dermaiHistory', JSON.stringify(history.slice(0, 20)));
  } catch {}

  return (
    <div className="page-container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">Analysis Results</h1>
      </div>

      {/* Urgent Warning */}
      {urgent_warning && (
        <div className={`risk-alert ${risk_assessment.level}`} style={{ marginBottom: '24px' }}>
          <span style={{ fontSize: '1.5rem' }}>🚨</span>
          <div>
            <strong style={{ fontSize: '1.05rem', display: 'block', marginBottom: '4px' }}>
              Urgent Medical Alert
            </strong>
            <p>{urgent_warning}</p>
          </div>
        </div>
      )}

      {/* ── Assessment Paragraph (NEW — above Grad-CAM) ───────── */}
      {assessmentParagraph && (
        <div className="animate-fade-in-up stagger-1" style={{
          background: 'rgba(26,26,46,0.8)',
          border: '1px solid rgba(255,255,255,0.1)',
          backdropFilter: 'blur(12px)',
          borderRadius: '20px',
          padding: '24px',
          marginBottom: '24px',
        }} id="assessment-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', margin: 0 }}>
              🔬 Skin Assessment
            </h3>
            {llmOverrode && (
              <span style={{
                color: 'rgba(108,99,255,0.9)',
                fontSize: '0.7rem',
                fontWeight: 600,
                background: 'rgba(108,99,255,0.1)',
                padding: '2px 8px',
                borderRadius: '8px',
              }}>
                ✨ AI-Enhanced Analysis
              </span>
            )}
          </div>
          <p style={{ color: 'var(--dark-200)', lineHeight: 1.8, fontSize: '0.95rem' }}>
            {assessmentParagraph}
          </p>

          {/* LLM unavailable note */}
          {!llmEnriched && (
            <p className="text-white/40 text-xs mt-3">
              Note: Enhanced analysis unavailable — showing standard assessment.
            </p>
          )}
        </div>
      )}

      {/* Visible Features Chips */}
      {visibleFeatures.length > 0 && (
        <div className="mt-3" style={{ marginBottom: '24px' }}>
          <p className="text-white/50 text-xs mb-2">Observed features:</p>
          <div className="flex flex-wrap gap-2">
            {visibleFeatures.map((feature, i) => (
              <span
                key={i}
                className="bg-muted border border-white/10 text-white/70 text-xs px-3 py-1 rounded-full"
              >
                {feature}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Main Result Card */}
      <div className="glass-card animate-fade-in-up stagger-1" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', alignItems: 'start' }}>
          {/* Left: Prediction */}
          <div>
            <div style={{ marginBottom: '24px' }}>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                Detected Condition
              </p>
              <h2 style={{ color: 'white', fontSize: '1.8rem', fontWeight: 800, marginBottom: '8px' }}>
                {prediction.display_name}
              </h2>
              <span className={`badge ${riskBadgeClass}`}>{risk_assessment.label}</span>
              <span className="badge badge-purple" style={{ marginLeft: '8px' }}>{prediction.category}</span>
            </div>

            {/* Medical disclaimer below condition label */}
            <p className="text-white/50 text-xs mt-2">
              This analysis is for informational purposes only and does not constitute a medical
              diagnosis. Always consult a qualified dermatologist for skin health concerns.
            </p>

            <div style={{ marginBottom: '24px' }}>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '8px', fontWeight: 600 }}>
                Confidence Score
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div className="progress-bar" style={{ flex: 1 }}>
                  <div className="progress-fill" style={{ width: `${confidencePercent}%` }} />
                </div>
                <span style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', minWidth: '45px' }}>
                  {confidencePercent}%
                </span>
              </div>
            </div>

            <div>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '4px', fontWeight: 600 }}>
                Severity
              </p>
              <p style={{ color: 'white', fontWeight: 600, textTransform: 'capitalize' }}>
                {condition_info.severity}
              </p>
            </div>
          </div>

          {/* Right: Grad-CAM */}
          <div>
            {gradcam_heatmap ? (
              <div>
                <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '8px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Grad-CAM Attention Map
                </p>
                <div className="heatmap-container">
                  <img src={`data:image/png;base64,${gradcam_heatmap}`} alt="Grad-CAM heatmap" />
                </div>
                <p style={{ color: 'var(--dark-300)', fontSize: '0.8rem', marginTop: '8px' }}>
                  Highlighted regions show where the AI focused its attention.
                </p>
              </div>
            ) : uploadedImageUrl ? (
              <div>
                <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '8px', fontWeight: 600 }}>
                  Uploaded Image
                </p>
                <div className="heatmap-container">
                  <img src={uploadedImageUrl} alt="Uploaded skin image" />
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* ── Skin Metrics Panel (NEW — below Grad-CAM) ─────────── */}
      {skinMetrics.length > 0 && (
        <div className="animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
          <SkinMetricsPanel metrics={skinMetrics} />
        </div>
      )}

      {/* ── Referral Banner (NEW) ─────────────────────────────── */}
      {referToDerm && (
        <div style={{
          background: 'rgba(120,53,15,0.6)',
          border: '1px solid rgba(245,158,11,0.5)',
          borderRadius: '16px',
          padding: referralMinimized ? '12px 20px' : '20px 24px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          transition: 'padding 0.3s ease',
        }} id="referral-banner">
          {referralMinimized ? (
            <p style={{ color: '#fbbf24', fontSize: '0.85rem', fontWeight: 600, margin: 0 }}>
              ⚠️ Dermatologist consultation recommended
            </p>
          ) : (
            <div style={{ flex: 1 }}>
              <p style={{ color: '#fbbf24', fontSize: '1rem', fontWeight: 700, marginBottom: '4px' }}>
                ⚠️ Professional Evaluation Recommended
              </p>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.88rem', lineHeight: 1.6 }}>
                For accurate evaluation of this condition, we recommend consulting a dermatologist.
              </p>
            </div>
          )}
          <button
            onClick={() => setReferralMinimized(!referralMinimized)}
            style={{
              background: 'transparent',
              border: '1px solid rgba(245,158,11,0.3)',
              color: '#fbbf24',
              borderRadius: '8px',
              padding: '4px 10px',
              fontSize: '0.75rem',
              cursor: 'pointer',
              flexShrink: 0,
            }}
            aria-label={referralMinimized ? 'Expand referral banner' : 'Minimize referral banner'}
          >
            {referralMinimized ? '▼' : '▲'}
          </button>
        </div>
      )}

      {/* Top-3 Predictions */}
      <div className="glass-card animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
        <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.1rem' }}>
          Top-3 Differential Diagnoses
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {top3.map((pred, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: '16px',
              padding: '12px 16px', borderRadius: '10px',
              background: i === 0 ? 'rgba(99,102,241,0.1)' : 'transparent',
              border: i === 0 ? '1px solid rgba(99,102,241,0.2)' : '1px solid var(--dark-600)',
            }}>
              <span style={{ color: i === 0 ? 'var(--primary-400)' : 'var(--dark-300)', fontWeight: 700, width: '28px' }}>
                #{i + 1}
              </span>
              <div style={{ flex: 1 }}>
                <span style={{ color: 'white', fontWeight: 600 }}>{pred.display_name}</span>
                <span className="badge badge-blue" style={{ marginLeft: '8px', fontSize: '0.7rem' }}>{pred.category}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '200px' }}>
                <div className="progress-bar" style={{ flex: 1, height: '6px' }}>
                  <div className="progress-fill" style={{ width: `${Math.round(pred.confidence * 100)}%` }} />
                </div>
                <span style={{ color: 'var(--dark-100)', fontWeight: 600, fontSize: '0.9rem', minWidth: '40px', textAlign: 'right' }}>
                  {Math.round(pred.confidence * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Medical Information */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        <div className="glass-card animate-fade-in-up stagger-3">
          <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.1rem' }}>
            Medical Explanation
          </h3>
          <p style={{ color: 'var(--dark-200)', lineHeight: 1.7, fontSize: '0.95rem' }}>
            {condition_info.medical_explanation}
          </p>
          {condition_info.causes?.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              <p style={{ color: 'var(--dark-100)', fontWeight: 600, marginBottom: '8px' }}>Common Causes:</p>
              <ul style={{ color: 'var(--dark-200)', paddingLeft: '20px', lineHeight: 1.8 }}>
                {condition_info.causes.slice(0, 4).map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
          )}
        </div>

        <div className="glass-card animate-fade-in-up stagger-4">
          <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '16px', fontSize: '1.1rem' }}>
            Recommended Treatments
          </h3>
          {treatments.otc?.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ color: 'var(--accent-emerald)', fontWeight: 600, fontSize: '0.85rem', marginBottom: '6px' }}>
                Over-the-Counter
              </p>
              <ul style={{ color: 'var(--dark-200)', paddingLeft: '20px', lineHeight: 1.8, fontSize: '0.9rem' }}>
                {treatments.otc.slice(0, 3).map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
          {treatments.prescription?.length > 0 && (
            <div>
              <p style={{ color: 'var(--accent-amber)', fontWeight: 600, fontSize: '0.85rem', marginBottom: '6px' }}>
                Prescription (Consult Doctor)
              </p>
              <ul style={{ color: 'var(--dark-200)', paddingLeft: '20px', lineHeight: 1.8, fontSize: '0.9rem' }}>
                {treatments.prescription.slice(0, 3).map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* When to See Doctor */}
      <div className="glass-card animate-fade-in-up stagger-5" style={{ marginBottom: '24px' }}>
        <h3 style={{ color: 'white', fontWeight: 700, marginBottom: '12px', fontSize: '1.1rem' }}>
          👨‍⚕️ When to See a Doctor
        </h3>
        <p style={{ color: 'var(--dark-200)', lineHeight: 1.7 }}>{condition_info.when_to_see_doctor}</p>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <button className="btn-primary" onClick={() => onNavigate('recommendations')}>🧴 Get Skincare Routine</button>
        <button className="btn-primary" onClick={handleDownloadPDF} disabled={pdfLoading} id="export-pdf-btn"
          style={{ background: pdfLoading ? 'var(--dark-500)' : 'linear-gradient(135deg, #10b981, #06b6d4)' }}>
          {pdfLoading ? '⏳ Generating...' : '📄 Export PDF Report'}
        </button>
        <button className="btn-secondary" onClick={() => onNavigate('chat')}>🤖 Ask AI About This</button>
        <button className="btn-secondary" onClick={() => onNavigate('doctors')}>👨‍⚕️ Find a Dermatologist</button>
        <button className="btn-secondary" onClick={() => onNavigate('analysis')}>🔬 Analyze Another Image</button>
      </div>

      {pdfError && (
        <div style={{ marginBottom: '16px', padding: '12px', borderRadius: '10px', background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)', color: '#fb7185', fontSize: '0.9rem' }}>
          ❌ {pdfError}
        </div>
      )}

      {/* Disclaimer */}
      <div className="disclaimer">
        <span>⚠️</span>
        <span>{disclaimer}</span>
      </div>
    </div>
  );
};

export default ResultsPage;
