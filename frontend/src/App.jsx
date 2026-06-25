import { lazy, Suspense, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { getAuthToken } from './api/client';
import Layout from './components/Layout/Layout';
import Auth from './pages/Auth';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const RunHistory = lazy(() => import('./pages/RunHistory'));
const RunDetail = lazy(() => import('./pages/RunDetail'));
const Reports = lazy(() => import('./pages/Reports'));

const routeFallback = (
  <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
    Loading...
  </div>
);

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!getAuthToken());

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <BrowserRouter>
      <Layout onLogout={handleLogout}>
        <Suspense fallback={routeFallback}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/history" element={<RunHistory />} />
            <Route path="/runs/:id" element={<RunDetail />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </BrowserRouter>
  );
}
