import React, { useState, useEffect } from 'react';
import { authRegister, authLogin, getProfile, updateProfile } from '../api';

const AuthProfile: React.FC = () => {
  const [mode, setMode] = useState<'login' | 'register' | 'profile'>('login');
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form fields
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [skinType, setSkinType] = useState('normal');
  const [age, setAge] = useState(25);

  useEffect(() => {
    const saved = localStorage.getItem('dermaiToken');
    if (saved) {
      setToken(saved);
      fetchProfile(saved);
    }
  }, []);

  const fetchProfile = async (t: string) => {
    try {
      const data = await getProfile(t);
      setUser(data);
      setFullName(data.full_name || '');
      setSkinType(data.skin_type || 'normal');
      setAge(data.age || 25);
      setMode('profile');
    } catch {
      localStorage.removeItem('dermaiToken');
      setToken(null);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await authLogin({ email, password });
      localStorage.setItem('dermaiToken', data.token);
      setToken(data.token);
      setUser(data.user);
      setFullName(data.user.full_name || '');
      setSkinType(data.user.skin_type || 'normal');
      setAge(data.user.age || 25);
      setMode('profile');
      setSuccess('Welcome back!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
    setLoading(false);
  };

  const handleRegister = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await authRegister({ email, username, password, full_name: fullName, skin_type: skinType, age });
      localStorage.setItem('dermaiToken', data.token);
      setToken(data.token);
      setUser(data.user);
      setMode('profile');
      setSuccess('Account created successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    }
    setLoading(false);
  };

  const handleUpdateProfile = async () => {
    if (!token) return;
    setLoading(true);
    setError('');
    try {
      await updateProfile(token, { full_name: fullName, skin_type: skinType, age });
      setSuccess('Profile updated!');
      setTimeout(() => setSuccess(''), 3000);
      await fetchProfile(token);
    } catch (err: any) {
      setError(err.message || 'Update failed');
    }
    setLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('dermaiToken');
    setToken(null);
    setUser(null);
    setMode('login');
    setEmail('');
    setPassword('');
    setUsername('');
    setFullName('');
    setSuccess('Logged out successfully');
    setTimeout(() => setSuccess(''), 3000);
  };

  return (
    <div className="page-container" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">
          {mode === 'profile' ? '👤 My Profile' : mode === 'register' ? '✨ Create Account' : '🔐 Sign In'}
        </h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          {mode === 'profile'
            ? 'Manage your account and skin profile settings.'
            : 'Secure your skin health data with a personal account.'}
        </p>
      </div>

      {success && (
        <div className="animate-fade-in" style={{
          padding: '12px 16px', borderRadius: '10px', marginBottom: '16px',
          background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)',
          color: '#34d399', textAlign: 'center', fontSize: '0.9rem',
        }}>
          ✅ {success}
        </div>
      )}

      {error && (
        <div className="animate-fade-in" style={{
          padding: '12px 16px', borderRadius: '10px', marginBottom: '16px',
          background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)',
          color: '#fb7185', textAlign: 'center', fontSize: '0.9rem',
        }}>
          {error}
        </div>
      )}

      <div className="glass-card animate-fade-in-up stagger-2">
        {mode === 'profile' && user ? (
          <>
            {/* Profile Header */}
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
              <div style={{
                width: '80px', height: '80px', borderRadius: '50%',
                background: 'var(--gradient-primary)', display: 'flex',
                alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px',
                fontSize: '2rem', fontWeight: 700, color: 'white',
              }}>
                {(user.full_name || user.username || '?').charAt(0).toUpperCase()}
              </div>
              <h3 style={{ color: 'white', fontWeight: 700 }}>{user.full_name || user.username}</h3>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.85rem' }}>{user.email}</p>
              <span className="badge badge-blue" style={{ marginTop: '8px' }}>Since {new Date(user.created_at).toLocaleDateString()}</span>
            </div>

            {/* Edit Profile Fields */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Full Name</label>
                <input className="input-field" value={fullName} onChange={e => setFullName(e.target.value)} id="profile-name" />
              </div>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Skin Type</label>
                <select className="select-field" value={skinType} onChange={e => setSkinType(e.target.value)} id="profile-skin-type">
                  <option value="normal">Normal</option>
                  <option value="dry">Dry</option>
                  <option value="oily">Oily</option>
                  <option value="combination">Combination</option>
                  <option value="sensitive">Sensitive</option>
                </select>
              </div>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Age</label>
                <input className="input-field" type="number" value={age} onChange={e => setAge(parseInt(e.target.value) || 25)} min={10} max={120} id="profile-age" />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
              <button className="btn-primary" onClick={handleUpdateProfile} disabled={loading} style={{ flex: 1 }}>
                {loading ? 'Saving...' : '💾 Save Changes'}
              </button>
              <button className="btn-secondary" onClick={handleLogout} style={{ flexShrink: 0 }}>
                Sign Out
              </button>
            </div>

            {/* Security Notice */}
            <div style={{
              marginTop: '24px', padding: '14px 16px', borderRadius: '10px',
              background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)',
            }}>
              <p style={{ color: 'var(--primary-300)', fontSize: '0.85rem', fontWeight: 600, marginBottom: '6px' }}>
                🔒 Security & Privacy
              </p>
              <p style={{ color: 'var(--dark-200)', fontSize: '0.8rem', lineHeight: 1.5 }}>
                Your data is stored locally with industry-standard encryption. Passwords are hashed using bcrypt.
                JWT tokens expire after 24 hours. We follow HIPAA-inspired data handling practices to protect your medical information.
              </p>
            </div>
          </>
        ) : mode === 'register' ? (
          <>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Email</label>
                <input className="input-field" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" id="register-email" />
              </div>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Username</label>
                <input className="input-field" value={username} onChange={e => setUsername(e.target.value)} placeholder="Choose a username" id="register-username" />
              </div>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Full Name</label>
                <input className="input-field" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Your full name" id="register-name" />
              </div>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Password</label>
                <input className="input-field" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Min 6 characters" id="register-password" />
              </div>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Skin Type</label>
                <select className="select-field" value={skinType} onChange={e => setSkinType(e.target.value)} id="register-skin-type">
                  <option value="normal">Normal</option>
                  <option value="dry">Dry</option>
                  <option value="oily">Oily</option>
                  <option value="combination">Combination</option>
                  <option value="sensitive">Sensitive</option>
                </select>
              </div>
            </div>

            <button className="btn-primary" onClick={handleRegister} disabled={loading} style={{ width: '100%', marginTop: '20px', padding: '14px' }}>
              {loading ? 'Creating...' : '✨ Create Account'}
            </button>

            <p style={{ textAlign: 'center', marginTop: '16px', color: 'var(--dark-200)', fontSize: '0.9rem' }}>
              Already have an account?{' '}
              <button className="btn-ghost" onClick={() => { setMode('login'); setError(''); }} style={{ color: 'var(--primary-400)', textDecoration: 'underline' }}>
                Sign In
              </button>
            </p>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Email</label>
                <input className="input-field" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com"
                  onKeyDown={e => e.key === 'Enter' && handleLogin()} id="login-email" />
              </div>
              <div>
                <label style={{ color: 'var(--dark-100)', fontSize: '0.85rem', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Password</label>
                <input className="input-field" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Your password"
                  onKeyDown={e => e.key === 'Enter' && handleLogin()} id="login-password" />
              </div>
            </div>

            <button className="btn-primary" onClick={handleLogin} disabled={loading} style={{ width: '100%', marginTop: '20px', padding: '14px' }}>
              {loading ? 'Signing in...' : '🔐 Sign In'}
            </button>

            <p style={{ textAlign: 'center', marginTop: '16px', color: 'var(--dark-200)', fontSize: '0.9rem' }}>
              Don't have an account?{' '}
              <button className="btn-ghost" onClick={() => { setMode('register'); setError(''); }} style={{ color: 'var(--primary-400)', textDecoration: 'underline' }}>
                Create Account
              </button>
            </p>
          </>
        )}
      </div>

      {/* HIPAA Notice */}
      <div className="disclaimer" style={{ marginTop: '24px' }}>
        <span>🔒</span>
        <span>
          DermAI follows HIPAA-inspired data handling practices. Your medical data is encrypted at rest,
          passwords are bcrypt-hashed, and sessions use JWT tokens with automatic expiry.
          No medical data is shared with third parties.
        </span>
      </div>
    </div>
  );
};

export default AuthProfile;
