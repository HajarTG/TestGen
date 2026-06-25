import { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Cpu, Layers, Award, ShieldCheck } from 'lucide-react';
import { useRunDetails } from '../api/hooks';
import TestViewer from '../components/TestViewer/TestViewer';

export default function RunDetail() {
  const { id } = useParams();
  const runId = parseInt(id, 10);
  const { run, reports, metrics, loading, error, refetch } = useRunDetails(runId);
  const runStatus = run?.status;

  // Poll in-progress runs every 5 seconds
  useEffect(() => {
    let timer;
    if (runStatus && !['completed', 'failed'].includes(runStatus)) {
      timer = setInterval(() => {
        refetch();
      }, 5000);
    }
    return () => {
      if (timer) clearInterval(timer);
    }
  }, [runStatus, refetch]);

  if (loading && !run) {
    return <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading run details...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: '4rem', textAlign: 'center' }}>
        <h3 style={{ color: '#ef4444' }}>Failed to load run</h3>
        <p style={{ color: 'var(--text-muted)' }}>{error}</p>
        <Link to="/history" style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 600 }}>
          Back to History
        </Link>
      </div>
    );
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return '#10b981';
      case 'failed':
        return '#ef4444';
      default:
        return '#3b82f6';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Back button */}
      <div>
        <Link to="/history" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600, transition: 'color 0.2s' }} onMouseEnter={(e) => e.target.style.color = 'var(--text-main)'} onMouseLeave={(e) => e.target.style.color = 'var(--text-muted)'}>
          <ArrowLeft size={16} />
          <span>Back to History</span>
        </Link>
      </div>

      {/* Hero Stats Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ margin: 0, fontSize: '1.8rem', fontWeight: 800 }}>Execution Run #{runId}</h1>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, padding: '0.25rem 0.6rem', borderRadius: '12px', background: getStatusColor(run.status) + '15', color: getStatusColor(run.status), border: `1px solid ${getStatusColor(run.status)}30`, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {run.status}
            </span>
          </div>
          <p style={{ margin: '0.4rem 0 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Target source: <strong style={{ color: 'var(--text-main)' }}>{run.file_name || 'Project upload'}</strong>
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={refetch}
            style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', color: 'white', padding: '0.6rem 1rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}
          >
            <RefreshCw size={14} />
            <span>Refetch</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      {metrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ color: 'var(--primary)', background: 'rgba(59, 130, 246, 0.1)', padding: '0.5rem', borderRadius: '8px' }}>
              <Layers size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Classes / Methods</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{metrics.total_classes} / {metrics.total_methods}</div>
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ color: '#10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '0.5rem', borderRadius: '8px' }}>
              <ShieldCheck size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Gen / Compiled</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{metrics.tests_generated} / {metrics.tests_compiled}</div>
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ color: 'var(--secondary)', background: 'rgba(139, 92, 246, 0.1)', padding: '0.5rem', borderRadius: '8px' }}>
              <Award size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Quality Score</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>{metrics.avg_score.toFixed(1)}/100</div>
            </div>
          </div>

          <div style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ color: '#f59e0b', background: 'rgba(245, 158, 11, 0.1)', padding: '0.5rem', borderRadius: '8px' }}>
              <Cpu size={18} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Cost Spend</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'white' }}>${metrics.total_gpt_cost_usd.toFixed(4)}</div>
            </div>
          </div>
        </div>
      )}

      {/* If still processing, show in-progress screen */}
      {!['completed', 'failed'].includes(run.status) ? (
        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '4rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ width: '48px', height: '48px', border: '3px solid rgba(59, 130, 246, 0.2)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
          <div>
            <h3 style={{ margin: 0, color: 'white' }}>Executing Pipeline Status: {run.status.replace('_', ' ')}</h3>
            <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Please wait while the Java Parser runs AST extraction and GPT builds assertions...
            </p>
          </div>
        </div>
      ) : (
        /* Render Report Code Viewer */
        <TestViewer reports={reports} />
      )}

      {/* CSS Animation helper */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
