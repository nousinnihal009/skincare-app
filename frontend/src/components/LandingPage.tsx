import React from 'react';
import type { Page } from '../App';

interface Props {
  onNavigate: (page: Page) => void;
}

const LandingPage: React.FC<Props> = ({ onNavigate }) => {
  const features = [
    { icon: '🔬', title: 'AI Skin Analysis', desc: 'Upload a skin image and receive instant AI-powered analysis with Grad-CAM heatmap visualization.' },
    { icon: '🧬', title: 'Explainable AI', desc: 'Understand model decisions with attention maps, confidence distributions, and top-3 differential diagnoses.' },
    { icon: '💊', title: 'Treatment Insights', desc: 'Get condition-specific treatment recommendations including OTC, prescription, and natural options.' },
    { icon: '🤖', title: 'AI Dermatologist', desc: 'Chat with our AI assistant trained on dermatology knowledge for instant answers to skin questions.' },
    { icon: '👨‍⚕️', title: 'Find Specialists', desc: 'Locate board-certified dermatologists near you with ratings, telemedicine, and appointment booking.' },
    { icon: '🧴', title: 'Smart Skincare', desc: 'Personalized morning & evening routines based on your detected condition and skin type.' },
  ];

  const stats = [
    { value: '21+', label: 'Skin Conditions' },
    { value: '95%', label: 'Accuracy Rate' },
    { value: '10K+', label: 'Images Trained' },
    { value: '24/7', label: 'AI Available' },
  ];

  const steps = [
    { num: '01', title: 'Upload', desc: 'Capture or upload a clear image of the skin area you want analyzed.' },
    { num: '02', title: 'AI Analysis', desc: 'Our ResNet50 model processes the image through validated preprocessing and inference.' },
    { num: '03', title: 'Results', desc: 'View predicted condition, confidence score, risk level, and Grad-CAM heatmap.' },
    { num: '04', title: 'Action Plan', desc: 'Get personalized skincare routines, treatment options, and doctor referrals.' },
  ];

  return (
    <div>
      {/* Hero Section */}
      <section style={{
        background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 40%, #12121a 100%)',
        padding: '100px 24px 80px',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Background glow effects */}
        <div style={{
          position: 'absolute', width: '500px', height: '500px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(79,70,229,0.15) 0%, transparent 70%)',
          top: '-100px', right: '-100px', pointerEvents: 'none'
        }} />
        <div style={{
          position: 'absolute', width: '400px', height: '400px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 70%)',
          bottom: '-50px', left: '-50px', pointerEvents: 'none'
        }} />

        <div style={{ maxWidth: '1100px', margin: '0 auto', textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <div className="animate-fade-in-up" style={{ marginBottom: '20px' }}>
            <span className="badge badge-purple" style={{ fontSize: '0.8rem', padding: '6px 16px' }}>
              🔬 Powered by Deep Learning
            </span>
          </div>

          <h1 className="animate-fade-in-up stagger-1" style={{
            fontSize: 'clamp(2.5rem, 5vw, 4rem)', fontWeight: 900, color: 'white',
            lineHeight: 1.1, marginBottom: '24px', letterSpacing: '-0.03em',
          }}>
            AI-Powered<br />
            <span style={{
              background: 'linear-gradient(135deg, #818cf8, #06b6d4)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>
              Skin Analysis
            </span>
            <br />& Dermatology Assistant
          </h1>

          <p className="animate-fade-in-up stagger-2" style={{
            fontSize: '1.15rem', color: '#b4b4cc', maxWidth: '650px', margin: '0 auto 40px',
            lineHeight: 1.7
          }}>
            Advanced skin lesion detection using deep learning. Get instant AI analysis,
            explainable insights with Grad-CAM, personalized skincare routines, and
            connect with dermatology specialists.
          </p>

          <div className="animate-fade-in-up stagger-3" style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn-primary" style={{ padding: '14px 32px', fontSize: '1rem' }}
              onClick={() => onNavigate('analysis')}>
              Start Skin Analysis →
            </button>
            <button className="btn-secondary" style={{ padding: '14px 32px', fontSize: '1rem' }}
              onClick={() => onNavigate('chat')}>
              Ask AI Dermatologist
            </button>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section style={{
        background: 'var(--dark-800)',
        borderBottom: '1px solid var(--glass-border)',
        padding: '32px 24px',
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '24px' }}>
          {stats.map((s, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div className="stat-value">{s.value}</div>
              <div style={{ color: 'var(--dark-200)', fontSize: '0.85rem', fontWeight: 500 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section style={{ background: 'var(--dark-900)', padding: '80px 24px' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '56px' }}>
            <h2 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'white', marginBottom: '12px' }}>How It Works</h2>
            <p style={{ color: 'var(--dark-200)', fontSize: '1.05rem' }}>From upload to action plan in seconds</p>
          </div>

          <div className="grid-4" style={{ gap: '20px' }}>
            {steps.map((step, i) => (
              <div key={i} className="glass-card animate-fade-in-up" style={{ animationDelay: `${i * 0.1}s`, opacity: 0, textAlign: 'center' }}>
                <div style={{
                  fontSize: '2rem', fontWeight: 900, marginBottom: '16px',
                  background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                }}>{step.num}</div>
                <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', marginBottom: '8px' }}>{step.title}</h3>
                <p style={{ color: 'var(--dark-200)', fontSize: '0.9rem', lineHeight: 1.5 }}>{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section style={{ background: 'var(--dark-800)', padding: '80px 24px' }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '56px' }}>
            <h2 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'white', marginBottom: '12px' }}>Platform Features</h2>
            <p style={{ color: 'var(--dark-200)', fontSize: '1.05rem' }}>Everything you need for intelligent skin health management</p>
          </div>

          <div className="grid-3">
            {features.map((f, i) => (
              <div key={i} className="glass-card animate-fade-in-up" style={{ animationDelay: `${i * 0.08}s`, opacity: 0, cursor: 'pointer' }}>
                <div style={{ fontSize: '2rem', marginBottom: '16px' }}>{f.icon}</div>
                <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', marginBottom: '8px' }}>{f.title}</h3>
                <p style={{ color: 'var(--dark-200)', fontSize: '0.9rem', lineHeight: 1.5 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{
        background: 'linear-gradient(135deg, var(--dark-800), var(--dark-900))',
        padding: '80px 24px', textAlign: 'center',
        borderTop: '1px solid var(--glass-border)',
      }}>
        <div style={{ maxWidth: '700px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'white', marginBottom: '16px' }}>
            Ready to Analyze Your Skin?
          </h2>
          <p style={{ color: 'var(--dark-200)', marginBottom: '32px', fontSize: '1.05rem' }}>
            Get instant AI-powered analysis, personalized recommendations, and connect with certified dermatologists.
          </p>
          <button className="btn-primary" style={{ padding: '16px 40px', fontSize: '1.05rem' }}
            onClick={() => onNavigate('analysis')}>
            Start Free Analysis →
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        background: 'var(--dark-900)', padding: '32px 24px',
        borderTop: '1px solid var(--glass-border)', textAlign: 'center',
      }}>
        <p style={{ color: 'var(--dark-300)', fontSize: '0.85rem' }}>
          ⚠️ DermAI is an AI-powered tool for educational purposes only. It is not a medical device.
          Always consult a qualified healthcare professional for medical advice.
        </p>
        <p style={{ color: 'var(--dark-400)', fontSize: '0.8rem', marginTop: '8px' }}>
          © 2024 DermAI Platform. Built with PyTorch + FastAPI + React.
        </p>
      </footer>
    </div>
  );
};

export default LandingPage;
