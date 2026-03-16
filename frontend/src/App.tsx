import React, { useState } from 'react';
import LandingPage from './components/LandingPage';
import SkinAnalysis from './components/SkinAnalysis';
import ResultsPage from './components/ResultsPage';
import Dashboard from './components/Dashboard';
import ChatPage from './components/ChatPage';
import DoctorFinder from './components/DoctorFinder';
import SkincareRecommendations from './components/SkincareRecommendations';
import IngredientScanner from './components/IngredientScanner';
import ProgressTracker from './components/ProgressTracker';
import AgingPrediction from './components/AgingPrediction';
import SkinTypeDetection from './components/SkinTypeDetection';
import AuthProfile from './components/AuthProfile';
import MedicalPage from './components/MedicalPage';

export type Page = 'landing' | 'analysis' | 'results' | 'dashboard' | 'chat' | 'doctors' | 'recommendations' | 'ingredients' | 'progress' | 'aging' | 'skin-type' | 'profile' | 'medical';

// Shared state for analysis results
export interface SkinMetricData {
  key: string;
  display_name: string;
  percentage: number;
  level: string;
  interpretation: string;
  reference_note: string;
}

export interface AnalysisResult {
  // ── Existing fields ─────────────────────────────
  prediction: { class_name: string; display_name: string; confidence: number; category: string };
  top3: { class_name: string; display_name: string; confidence: number; category: string }[];
  risk_assessment: { level: string; label: string; color: string; action: string; is_cancerous: boolean; urgency: string };
  condition_info: { description: string; severity: string; causes: string[]; symptoms: string[]; medical_explanation: string; when_to_see_doctor: string };
  treatments: { otc: string[]; prescription: string[]; natural: string[] };
  skincare_routine: any;
  gradcam_heatmap: string | null;
  confidence_distribution: Record<string, number>;
  urgent_warning?: string;
  disclaimer: string;

  // ── New fields (additive) ───────────────────────
  skin_metrics?: SkinMetricData[];
  assessment_paragraph?: string;
  visible_features?: string[];
  refer_to_dermatologist?: boolean;
  llm_enriched?: boolean;
  llm_overrode_resnet?: boolean;
  second_prediction?: string;
  second_confidence?: number;
  validation_meta?: { blur_score: number; brightness: number; skin_ratio: number };
}

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);

  const navigate = (page: Page) => {
    setCurrentPage(page);
    setMobileMenuOpen(false);
    window.scrollTo(0, 0);
  };

  const handleAnalysisComplete = (result: AnalysisResult, imageUrl: string) => {
    setAnalysisResult(result);
    setUploadedImageUrl(imageUrl);
    navigate('results');
  };

  const navItems: { id: Page; label: string; icon?: string }[] = [
    { id: 'landing', label: 'Home' },
    { id: 'analysis', label: 'Analyze' },
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'chat', label: 'AI Chat' },
    { id: 'doctors', label: 'Doctors' },
    { id: 'recommendations', label: 'Skincare' },
    { id: 'medical', label: 'Medical' },
    { id: 'ingredients', label: 'Ingredients' },
    { id: 'progress', label: 'Progress' },
    { id: 'skin-type', label: 'Skin Type' },
    { id: 'aging', label: 'Aging' },
    { id: 'profile', label: '👤' },
  ];

  // Fix D Correction: NEW badge with hardcoded 30-day expiry from launch date
  const MEDICAL_LAUNCH_TS = new Date('2025-03-13').getTime()
  const SHOW_NEW_BADGE = Date.now() - MEDICAL_LAUNCH_TS < 30 * 24 * 60 * 60 * 1000

  const renderPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onNavigate={navigate} />;
      case 'analysis':
        return <SkinAnalysis onAnalysisComplete={handleAnalysisComplete} />;
      case 'results':
        return <ResultsPage result={analysisResult} uploadedImageUrl={uploadedImageUrl} onNavigate={navigate} />;
      case 'dashboard':
        return <Dashboard onNavigate={navigate} />;
      case 'chat':
        return <ChatPage />;
      case 'doctors':
        return <DoctorFinder />;
      case 'recommendations':
        return <SkincareRecommendations result={analysisResult} />;
      case 'ingredients':
        return <IngredientScanner />;
      case 'progress':
        return <ProgressTracker onNavigate={navigate} />;
      case 'aging':
        return <AgingPrediction />;
      case 'skin-type':
        return <SkinTypeDetection />;
      case 'profile':
        return <AuthProfile />;
      case 'medical':
        return <MedicalPage onNavigate={navigate} />;
      default:
        return <LandingPage onNavigate={navigate} />;
    }
  };

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-inner">
          <div className="navbar-brand" onClick={() => navigate('landing')}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#grad1)" strokeWidth="2">
              <defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="#4f46e5"/><stop offset="100%" stopColor="#06b6d4"/></linearGradient></defs>
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" strokeLinecap="round"/>
              <path d="M8 12s1.5-4 4-4 4 4 4 4-1.5 4-4 4-4-4-4-4z" strokeLinecap="round"/>
            </svg>
            DermAI
          </div>

          <div className={`navbar-links ${mobileMenuOpen ? 'open' : ''}`}>
            {navItems.map(item => (
              <button
                key={item.id}
                className={`nav-link ${currentPage === item.id ? 'active' : ''}`}
                aria-label={`Navigate to ${item.label} page`}
                onClick={() => {
                  navigate(item.id)
                }}
                style={{ position: 'relative' }}
              >
                {item.label}
                {item.id === 'medical' && SHOW_NEW_BADGE && (
                  <span style={{
                    position: 'absolute', top: '-4px', right: '-8px',
                    background: 'linear-gradient(135deg, #ef4444, #f97316)',
                    color: '#fff', fontSize: '0.55rem', fontWeight: 700,
                    padding: '1px 5px', borderRadius: '6px',
                    lineHeight: '1.3', letterSpacing: '0.04em',
                    animation: 'pulse-badge 2s infinite',
                  }}>
                    NEW
                  </span>
                )}
              </button>
            ))}
          </div>

          <button 
            className="mobile-menu-btn" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileMenuOpen ? (
                <path d="M6 18L18 6M6 6l12 12" strokeLinecap="round"/>
              ) : (
                <><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></>
              )}
            </svg>
          </button>
        </div>
      </nav>

      {/* Page Content */}
      {renderPage()}
    </div>
  );
};

export default App;

// Fix 7 keyframes — injected globally
const styleEl = document.createElement('style')
styleEl.textContent = `@keyframes pulse-badge { 0%,100%{transform:scale(1)} 50%{transform:scale(1.15)} }`
document.head.appendChild(styleEl)
