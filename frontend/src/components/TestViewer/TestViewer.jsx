import { useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import './TestViewer.css';

export default function TestViewer({ reports = [] }) {
  const [selectedReportIndex, setSelectedReportIndex] = useState(0);
  const [activeTab, setActiveTab] = useState('test'); // 'test' | 'source' | 'validation'

  if (!reports || reports.length === 0) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No reports generated for this run yet.
      </div>
    );
  }

  const safeSelectedIndex = Math.min(selectedReportIndex, reports.length - 1);
  const selectedReport = reports[safeSelectedIndex];

  return (
    <div className="viewer-container">
      {/* Sidebar List of Classes */}
      <aside className="viewer-sidebar">
        <div className="viewer-sidebar-header">Classes Analyzed</div>
        <ul className="class-list">
          {reports.map((report, idx) => (
            <li
              key={report.id || idx}
              className={`class-list-item ${safeSelectedIndex === idx ? 'selected' : ''}`}
              onClick={() => setSelectedReportIndex(idx)}
            >
              <div className="class-name-txt">{report.class_name || 'Class'}</div>
              <div className="class-details-txt">
                {report.method_name} - Score: {report.score !== null ? report.score : 'Pending'}
              </div>
            </li>
          ))}
        </ul>
      </aside>

      {/* Main View Area */}
      <div className="viewer-content">
        {/* Tab Headers */}
        <div className="viewer-tabs">
          <button
            className={`viewer-tab-btn ${activeTab === 'test' ? 'active' : ''}`}
            onClick={() => setActiveTab('test')}
          >
            Generated JUnit Test
          </button>
          <button
            className={`viewer-tab-btn ${activeTab === 'source' ? 'active' : ''}`}
            onClick={() => setActiveTab('source')}
          >
            Target Code Snippet
          </button>
          <button
            className={`viewer-tab-btn ${activeTab === 'validation' ? 'active' : ''}`}
            onClick={() => setActiveTab('validation')}
          >
            Validation & Score
          </button>
        </div>

        {/* Tab Panel Context */}
        <div className="code-viewport">
          {activeTab === 'test' && (
            <pre className="code-container">
              <code>{selectedReport.generated_test || '// No test generated'}</code>
            </pre>
          )}

          {activeTab === 'source' && (
            <pre className="code-container">
              <code>{selectedReport.method_source || '// No source code snippet available'}</code>
            </pre>
          )}

          {activeTab === 'validation' && (
            <div className="validation-view">
              <div className="validation-header">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'white' }}>
                    Compilation Verification
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Using JDK 17 to compile test code
                  </span>
                </div>

                <div
                  className={`validation-status-badge ${
                    selectedReport.compiled ? 'success' : 'fail'
                  }`}
                >
                  {selectedReport.compiled ? (
                    <>
                      <CheckCircle size={16} />
                      <span>Compiled Successfully</span>
                    </>
                  ) : (
                    <>
                      <XCircle size={16} />
                      <span>Compilation Failed</span>
                    </>
                  )}
                </div>
              </div>

              {/* Score Widget */}
              <div className="score-widget-container">
                <div
                  className="radial-score-box"
                  style={{ '--score-pct': selectedReport.score || 0 }}
                >
                  <span className="score-num">{selectedReport.score || 0}</span>
                  <span className="score-lbl">Quality Score</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <h4 style={{ margin: 0, color: 'white' }}>Score Attribution Details:</h4>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                    <li>Structure Integrity: <strong>{selectedReport.score >= 15 ? 'Passed (+15 pts)' : 'Failed (0 pts)'}</strong></li>
                    <li>Code Compilation: <strong>{selectedReport.compiled ? 'Passed (+35 pts)' : 'Failed (0 pts)'}</strong></li>
                    <li>Test Methods Assertions: <strong>{selectedReport.assertion_count || 0} assertions generated</strong></li>
                    <li>Strategy Selected: <strong>{selectedReport.strategy ? selectedReport.strategy.replace('_', ' ') : 'default'}</strong></li>
                  </ul>
                </div>
              </div>

              {/* Compilation Error logs */}
              {!selectedReport.compiled && selectedReport.compilation_error && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ef4444' }}>
                    Compiler Logs (javac Output):
                  </span>
                  <pre className="compilation-error-box">
                    <code>{selectedReport.compilation_error}</code>
                  </pre>
                </div>
              )}

              {/* LLM Usage Info */}
              <div className="stats-card-grid">
                <div className="stats-mini-card">
                  <span className="lbl">Tokens Consumed</span>
                  <span className="val">{selectedReport.gpt_tokens_used || 0}</span>
                </div>
                <div className="stats-mini-card">
                  <span className="lbl">Generation Cost</span>
                  <span className="val">
                    ${selectedReport.gpt_cost_usd ? selectedReport.gpt_cost_usd.toFixed(4) : '0.0000'}
                  </span>
                </div>
                <div className="stats-mini-card">
                  <span className="lbl">Assertions Found</span>
                  <span className="val">{selectedReport.assertion_count || 0}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
