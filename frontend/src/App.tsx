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

export type Page = 'landing' | 'analysis' | 'results' | 'dashboard' | 'chat' | 'doctors' | 'recommendations' | 'ingredients' | 'progress' | 'aging' | 'skin-type' | 'profile';

// Shared state for analysis results
export interface AnalysisResult {
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
    { id: 'ingredients', label: 'Ingredients' },
    { id: 'progress', label: 'Progress' },
    { id: 'skin-type', label: 'Skin Type' },
    { id: 'aging', label: 'Aging' },
    { id: 'profile', label: '👤' },
  ];

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
                onClick={() => navigate(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          <button className="mobile-menu-btn" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
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
