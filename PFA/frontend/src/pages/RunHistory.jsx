import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Calendar, Terminal, ArrowRight, RefreshCw } from 'lucide-react';
import { usePaginatedRuns } from '../api/hooks';

export default function RunHistory() {
  const [page, setPage] = useState(1);
  const perPage = 20;
  const { data, loading, error, execute: refetch } = usePaginatedRuns(page, perPage);
  const runs = data?.runs || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / perPage) || 1;
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const navigate = useNavigate();

  const handleRowClick = (runId) => {
    navigate(`/runs/${runId}`);
  };

  const filteredRuns = runs ? runs.filter(run => {
    const matchesSearch = run.file_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || run.status === statusFilter;
    return matchesSearch && matchesStatus;
  }) : [];

  const getStatusBadgeStyles = (status) => {
    switch (status) {
      case 'completed':
        return { bg: 'rgba(16, 185, 129, 0.1)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.2)' };
      case 'failed':
        return { bg: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.2)' };
      case 'pending':
        return { bg: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.2)' };
      default:
        return { bg: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.2)' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: 800 }}>Execution History</h1>
          <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>
            Search, filter, and review all code analysis and test generation runs.
          </p>
        </div>
        <button
          onClick={refetch}
          style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-color)', color: 'var(--text-main)', padding: '0.6rem 1rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.85rem' }}
        >
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', background: 'var(--card-bg)', border: '1px solid var(--border-color)', padding: '1rem', borderRadius: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0 1rem', flex: 1, minWidth: '250px' }}>
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search by target filename..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: 'none', border: 'none', color: 'white', padding: '0.75rem 0', outline: 'none', width: '100%', fontFamily: 'inherit', fontSize: '0.9rem' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0 1rem', minWidth: '180px' }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ background: 'none', border: 'none', color: 'white', padding: '0.75rem 0', outline: 'none', width: '100%', fontFamily: 'inherit', fontSize: '0.9rem', cursor: 'pointer' }}
          >
            <option value="all" style={{ backgroundColor: 'var(--bg-dark)' }}>All Statuses</option>
            <option value="completed" style={{ backgroundColor: 'var(--bg-dark)' }}>Completed</option>
            <option value="failed" style={{ backgroundColor: 'var(--bg-dark)' }}>Failed</option>
            <option value="analyzing" style={{ backgroundColor: 'var(--bg-dark)' }}>Analyzing</option>
            <option value="generating" style={{ backgroundColor: 'var(--bg-dark)' }}>Generating</option>
            <option value="validating" style={{ backgroundColor: 'var(--bg-dark)' }}>Validating</option>
          </select>
        </div>
      </div>

      {/* Data Table */}
      <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', overflow: 'hidden', boxShadow: '0 10px 30px rgba(0,0,0,0.1)' }}>
        {loading ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading runs...</div>
        ) : error ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: '#ef4444' }}>Error: {error}</div>
        ) : filteredRuns.length === 0 ? (
          <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>No executions match the selected criteria.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: 'rgba(15, 23, 42, 0.6)', borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-muted)' }}>ID</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-muted)' }}>Source Code File</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-muted)' }}>Status</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-muted)' }}>Methods</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-muted)' }}>Generated / Compiled</th>
                <th style={{ padding: '1rem 1.5rem', fontWeight: 600, color: 'var(--text-muted)' }}>Triggered At</th>
                <th style={{ padding: '1rem 1.5rem' }}></th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.map((run) => {
                const styles = getStatusBadgeStyles(run.status);
                return (
                  <tr
                    key={run.id}
                    onClick={() => handleRowClick(run.id)}
                    style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.02)', cursor: 'pointer', transition: 'background 0.2s ease' }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.01)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <td style={{ padding: '1rem 1.5rem', fontWeight: 700, color: 'var(--primary)' }}>#{run.id}</td>
                    <td style={{ padding: '1rem 1.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Terminal size={14} style={{ color: 'var(--text-muted)' }} />
                        <span style={{ fontWeight: 600 }}>{run.file_name || 'Project source'}</span>
                      </div>
                    </td>
                    <td style={{ padding: '1rem 1.5rem' }}>
                      <span style={{ display: 'inline-block', fontSize: '0.75rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '12px', background: styles.bg, color: styles.color, border: styles.border, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {run.status}
                      </span>
                    </td>
                    <td style={{ padding: '1rem 1.5rem', fontWeight: 500 }}>{run.total_methods ?? '-'}</td>
                    <td style={{ padding: '1rem 1.5rem', color: 'white' }}>
                      {run.tests_generated !== null ? (
                        <span>
                          <strong>{run.tests_generated}</strong> generated -{' '}
                          <span style={{ color: run.tests_compiled === run.tests_generated ? '#10b981' : '#f59e0b' }}>
                            {run.tests_compiled} compiled
                          </span>
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td style={{ padding: '1rem 1.5rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem', borderBottom: 'none' }}>
                      <Calendar size={12} />
                      <span>{run.uploaded_at ? new Date(run.uploaded_at).toLocaleString() : '-'}</span>
                    </td>
                    <td style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>
                      <button style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                        <ArrowRight size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
          <button 
            disabled={page === 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            style={{ padding: '0.5rem 1rem', background: '#1e293b', color: 'white', border: '1px solid #334155', borderRadius: '8px', cursor: page === 1 ? 'not-allowed' : 'pointer', opacity: page === 1 ? 0.5 : 1 }}
          >
            Previous
          </button>
          <span style={{ color: 'var(--text-muted)' }}>Page {page} of {totalPages}</span>
          <button 
            disabled={page === totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            style={{ padding: '0.5rem 1rem', background: '#1e293b', color: 'white', border: '1px solid #334155', borderRadius: '8px', cursor: page === totalPages ? 'not-allowed' : 'pointer', opacity: page === totalPages ? 0.5 : 1 }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
