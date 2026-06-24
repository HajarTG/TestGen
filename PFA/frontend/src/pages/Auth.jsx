import { useState } from 'react';
import { api } from '../api/client';

export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    
    try {
      if (isLogin) {
        await api.login(email, password);
        onLogin();
      } else {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, full_name: fullName })
        });
        
        if (!response.ok) {
          let errorMsg = 'Registration failed';
          try {
            const data = await response.json();
            if (typeof data.detail === 'string') {
              errorMsg = data.detail;
            } else if (Array.isArray(data.detail)) {
              // Pydantic validation errors come as an array of objects
              errorMsg = data.detail.map(e => `${e.loc?.slice(-1)?.[0] || 'field'}: ${e.msg}`).join(', ');
            }
          } catch {
            errorMsg = `Server error (${response.status})`;
          }
          throw new Error(errorMsg);
        }
        
        await api.login(email, password);
        onLogin();
      }
    } catch (err) {
      setError(err.message || 'An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', backgroundColor: '#0b0f19', fontFamily: 'Inter, sans-serif' }}>
      <div style={{ background: '#1e293b', padding: '2.5rem', borderRadius: '12px', width: '100%', maxWidth: '400px', border: '1px solid #334155', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '48px', height: '48px', borderRadius: '12px', background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', color: 'white', fontWeight: 800, fontSize: '1.5rem', marginBottom: '1rem' }}>
            A
          </div>
          <h1 style={{ color: 'white', margin: '0', fontSize: '1.5rem' }}>
            {isLogin ? 'Welcome Back' : 'Create Account'}
          </h1>
          <p style={{ color: '#94a3b8', margin: '0.5rem 0 0', fontSize: '0.9rem' }}>
            {isLogin ? 'Sign in to access your dashboard' : 'Sign up for a new account'}
          </p>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '0.75rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.9rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {!isLogin && (
            <div>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 500 }}>Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                required={!isLogin}
                style={{ width: '100%', padding: '0.75rem 1rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', color: 'white', outline: 'none', boxSizing: 'border-box' }}
                placeholder="John Doe"
              />
            </div>
          )}
          
          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 500 }}>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              style={{ width: '100%', padding: '0.75rem 1rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', color: 'white', outline: 'none', boxSizing: 'border-box' }}
              placeholder="name@company.com"
            />
          </div>

          <div>
            <label style={{ display: 'block', color: '#cbd5e1', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 500 }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '0.75rem 1rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', color: 'white', outline: 'none', boxSizing: 'border-box' }}
              placeholder="********"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{ width: '100%', padding: '0.875rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 600, marginTop: '1rem', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, transition: 'background 0.2s' }}
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: '#94a3b8' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            type="button"
            onClick={() => { setIsLogin(!isLogin); setError(null); }}
            style={{ background: 'none', border: 'none', color: '#3b82f6', fontWeight: 600, cursor: 'pointer', padding: 0 }}
          >
            {isLogin ? 'Sign up' : 'Sign in'}
          </button>
        </div>
      </div>
    </div>
  );
}
