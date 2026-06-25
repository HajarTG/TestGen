import { useNavigate } from 'react-router-dom';
import { Layers, CheckCircle2, DollarSign, Award, ArrowRight } from 'lucide-react';
import { useRuns, useGlobalStats } from '../api/hooks';
import UploadZone from '../components/UploadZone/UploadZone';
import RunCard from '../components/RunCard/RunCard';
import ErrorBoundary from '../components/ErrorBoundary/ErrorBoundary';

export default function Dashboard() {
  const { data: runs, execute: refetchRuns } = useRuns();
  const { data: stats } = useGlobalStats();
  const navigate = useNavigate();

  const handleUploadSuccess = (newRun) => {
    refetchRuns();
    // Redirect directly to the newly queued run detail page
    if (newRun && newRun.id) {
      navigate(`/runs/${newRun.id}`);
    }
  };

  // Extract stats or provide defaults
  const totalRuns = stats?.total_runs ?? runs?.length ?? 0;
  const successRate = stats?.compilation_success_rate ?? stats?.compilation_rate ?? 0;
  const avgScore = stats?.avg_score ?? 0;
  const totalCost = stats?.total_gpt_cost_usd ?? 0;

  // Recent 3 runs
  const recentRuns = runs ? [...runs].slice(0, 3) : [];

  return (
    <ErrorBoundary>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: 800 }}>Platform Dashboard</h1>
        <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>
          Upload Java resources to generate verified JUnit test suites with OpenAI GPT models.
        </p>
      </div>

      {/* Metrics Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem' }}>
        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Total Runs</span>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'white', marginTop: '0.25rem' }}>{totalRuns}</div>
          </div>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--primary)' }}>
            <Layers size={24} />
          </div>
        </div>

        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Avg Quality Score</span>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'white', marginTop: '0.25rem' }}>{avgScore.toFixed(1)}/100</div>
          </div>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(139, 92, 246, 0.1)', color: 'var(--secondary)' }}>
            <Award size={24} />
          </div>
        </div>

        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>Compilation Success</span>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'white', marginTop: '0.25rem' }}>{successRate.toFixed(1)}%</div>
          </div>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
            <CheckCircle2 size={24} />
          </div>
        </div>

        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700 }}>LLM Spend</span>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'white', marginTop: '0.25rem' }}>${totalCost.toFixed(4)}</div>
          </div>
          <div style={{ padding: '0.75rem', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
            <DollarSign size={24} />
          </div>
        </div>
      </div>

      {/* Main Grid: Upload left, Recent runs right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem' }}>
        <div>
          <UploadZone onUploadSuccess={handleUploadSuccess} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Recent Executions</h3>
            <button
              onClick={() => navigate('/history')}
              style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              <span>View all</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {recentRuns.length > 0 ? (
              recentRuns.map((run) => (
                <RunCard key={run.id} run={run} />
              ))
            ) : (
              <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                No generation jobs executed yet. Upload code to start.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
}
