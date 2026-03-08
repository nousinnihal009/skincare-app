import React, { useState, useRef, useCallback } from 'react';
import { analyzeSkin } from '../api';
import type { AnalysisResult } from '../App';

interface Props {
  onAnalysisComplete: (result: AnalysisResult, imageUrl: string) => void;
}

const ANALYSIS_STEPS = [
  { id: 'validate', label: 'Validating image...' },
  { id: 'preprocess', label: 'Preprocessing & normalizing...' },
  { id: 'inference', label: 'Running AI model inference...' },
  { id: 'gradcam', label: 'Generating Grad-CAM heatmap...' },
  { id: 'risk', label: 'Calculating risk assessment...' },
  { id: 'report', label: 'Building analysis report...' },
];

const SkinAnalysis: React.FC<Props> = ({ onAnalysisComplete }) => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, etc.)');
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size: 10MB');
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setError('');
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const handleAnalyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    setError('');

    // Simulate step progression
    for (let i = 0; i < ANALYSIS_STEPS.length; i++) {
      setCurrentStep(i);
      await new Promise(r => setTimeout(r, i === 2 ? 500 : 300));
    }

    try {
      const result = await analyzeSkin(file);
      onAnalysisComplete(result, preview!);
    } catch (err: any) {
      setError(err.message || 'Analysis failed. Please try again.');
      setIsAnalyzing(false);
      setCurrentStep(-1);
    }
  };

  return (
    <div className="page-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">AI Skin Analysis</h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          Upload a clear image of the skin area for AI-powered condition detection and analysis.
        </p>
      </div>

      {/* Upload Area */}
      {!isAnalyzing && (
        <div className="glass-card animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
          <div
            className={`upload-zone ${dragOver ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              style={{ display: 'none' }}
              id="skin-image-upload"
            />

            {preview ? (
              <div>
                <img src={preview} alt="Preview" style={{
                  maxWidth: '300px', maxHeight: '300px', borderRadius: '12px',
                  margin: '0 auto 16px', display: 'block', objectFit: 'cover',
                }} />
                <p style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>{file?.name}</p>
                <p style={{ color: 'var(--dark-300)', fontSize: '0.85rem', marginTop: '4px' }}>
                  Click to change image
                </p>
              </div>
            ) : (
              <div>
                <div style={{
                  width: '64px', height: '64px', borderRadius: '50%',
                  background: 'rgba(99,102,241,0.1)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
                }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary-400)" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <p style={{ color: 'white', fontWeight: 600, fontSize: '1.05rem', marginBottom: '4px' }}>
                  Drag & drop or click to upload
                </p>
                <p style={{ color: 'var(--dark-300)', fontSize: '0.9rem' }}>
                  JPG, PNG, BMP up to 10MB
                </p>
              </div>
            )}
          </div>

          <button
            className="btn-primary"
            onClick={handleAnalyze}
            disabled={!file}
            style={{ width: '100%', marginTop: '20px', padding: '14px' }}
            id="analyze-button"
          >
            🔬 Analyze Skin Image
          </button>

          {error && (
            <div style={{
              marginTop: '16px', padding: '14px 16px', borderRadius: '10px',
              background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)', color: '#fb7185',
            }}>
              {error}
            </div>
          )}
        </div>
      )}

      {/* Analysis Progress */}
      {isAnalyzing && (
        <div className="glass-card animate-fade-in" style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ margin: '0 auto 24px' }} />
          <h3 style={{ color: 'white', fontSize: '1.2rem', marginBottom: '24px' }}>
            Analyzing your skin image...
          </h3>
          <div style={{ textAlign: 'left' }}>
            {ANALYSIS_STEPS.map((step, i) => (
              <div key={step.id} className={`analysis-step ${i < currentStep ? 'done' : i === currentStep ? 'active' : 'waiting'}`}>
                <span style={{ width: '24px', textAlign: 'center' }}>
                  {i < currentStep ? '✅' : i === currentStep ? '⏳' : '○'}
                </span>
                <span>{step.label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="disclaimer" style={{ marginTop: '24px' }}>
        <span>⚠️</span>
        <span>
          This tool provides AI-generated analysis for educational purposes only.
          It is not a medical diagnosis. Always consult a qualified dermatologist for medical advice.
        </span>
      </div>
    </div>
  );
};

export default SkinAnalysis;
