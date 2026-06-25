import { NavLink } from 'react-router-dom';
import { LayoutDashboard, History, BarChart3, Cpu } from 'lucide-react';
import { useHealth } from '../../api/hooks';
import './Layout.css';

export default function Layout({ children, onLogout }) {
  const { health } = useHealth();
  const isHealthy = health && health.status === 'ok';

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">
            <Cpu size={20} />
          </div>
          <span className="logo-text">TestGen AI</span>
        </div>

        <nav className="nav-links">
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </NavLink>

          <NavLink to="/history" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <History size={18} />
            <span>Run History</span>
          </NavLink>

          <NavLink to="/reports" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <BarChart3 size={18} />
            <span>Quality Reports</span>
          </NavLink>
        </nav>

        {/* System Health Widget */}
        <div className="health-indicator">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>API Status</span>
          <div className="health-status">
            <span className={`status-dot ${isHealthy ? 'status-online' : 'status-offline'}`}></span>
            <span style={{ color: isHealthy ? '#10b981' : '#ef4444' }}>
              {isHealthy ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main content viewport */}
      <div className="main-content">
        <header className="top-bar">
          <div className="user-profile">
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#3b82f6' }}></div>
            <span>Developer Space</span>
          </div>
          <button 
            onClick={onLogout}
            style={{ marginLeft: 'auto', background: 'transparent', border: '1px solid #334155', color: '#cbd5e1', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            Logout
          </button>
        </header>

        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
}
