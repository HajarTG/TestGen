import { Link } from 'react-router-dom';
import { ArrowRight, Code, Calendar, Terminal } from 'lucide-react';
import './RunCard.css';

export default function RunCard({ run }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Pending...';
    const d = new Date(dateStr);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'completed';
      case 'failed':
        return 'failed';
      case 'pending':
        return 'pending';
      default:
        return 'running'; // covers analyzing, strategizing, generating, etc.
    }
  };

  return (
    <div className="run-card">
      <div className="run-card-header">
        <div className="run-id-title">
          <Terminal size={18} style={{ color: 'var(--primary)' }} />
          <span>Run #{run.id}</span>
        </div>
        <span className={`run-status-badge ${getStatusClass(run.status)}`}>
          {run.status}
        </span>
      </div>

      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Code size={14} />
        <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '250px' }}>
          {run.file_name || 'Upload source code'}
        </span>
      </div>

      <div className="run-card-stats">
        <div className="stat-box">
          <div className="stat-label">Methods</div>
          <div className="stat-value">{run.total_methods !== null ? run.total_methods : '-'}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Gen / Compiled</div>
          <div className="stat-value">
            {run.tests_generated !== null ? `${run.tests_generated}/${run.tests_compiled}` : '-'}
          </div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Strategy</div>
          <div className="stat-value" style={{ textTransform: 'capitalize', fontSize: '0.75rem' }}>
            {run.strategy ? run.strategy.replace('_', ' ') : 'Unit'}
          </div>
        </div>
      </div>

      <div className="run-card-footer">
        <div style={{ display: 'flex', gap: '1rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Calendar size={12} />
            {formatDate(run.uploaded_at)}
          </span>
        </div>

        <Link to={`/runs/${run.id}`} className="view-details-link">
          <span>Details</span>
          <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  );
}
