import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { BarChart3, TrendingUp, DollarSign, CheckCircle } from 'lucide-react';
import { useRuns } from '../api/hooks';

export default function Reports() {
  const { data: runs, loading, error } = useRuns();

  if (loading) {
    return <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading analytics...</div>;
  }

  if (error) {
    return <div style={{ padding: '4rem', textAlign: 'center', color: '#ef4444' }}>Error: {error}</div>;
  }

  // Filter completed runs that have valid score/metrics
  const completedRuns = runs
    ? [...runs]
        .filter((r) => r.status === 'completed' && r.tests_generated > 0)
        .reverse() // show in chronological order
    : [];

  // 1. Prepare Chart Data for Line (Quality Scores over time) & Bar (Cost)
  const runChartData = completedRuns.map((r) => ({
    name: `Run #${r.id}`,
    score: parseFloat((r.avg_score ?? (r.tests_compiled / r.tests_generated) * 100).toFixed(1)),
    cost: parseFloat((r.total_gpt_cost_usd ?? 0).toFixed(4)),
    generated: r.tests_generated,
    compiled: r.tests_compiled,
  }));

  // 2. Prepare Pie Chart Data (Compilation Success rate)
  const totalGenerated = completedRuns.reduce((sum, r) => sum + (r.tests_generated || 0), 0);
  const totalCompiled = completedRuns.reduce((sum, r) => sum + (r.tests_compiled || 0), 0);
  const totalFailed = totalGenerated - totalCompiled;

  const pieData = [
    { name: 'Compiled', value: totalCompiled, color: '#10b981' },
    { name: 'Failed Compile', value: totalFailed, color: '#ef4444' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div>
        <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: 800 }}>Analytics & Reports</h1>
        <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>
          Detailed quality insights, compiler status breakdown, and LLM consumption trends.
        </p>
      </div>

      {completedRuns.length === 0 ? (
        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No completed runs available. Execute test generation jobs first to populate reports.
        </div>
      ) : (
        <>
          {/* Main Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>
            {/* Quality Trend Chart */}
            <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <TrendingUp size={18} style={{ color: 'var(--primary)' }} />
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>Quality Score Trend</h3>
              </div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={runChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} />
                    <YAxis stroke="var(--text-muted)" domain={[0, 100]} fontSize={11} />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'var(--bg-dark)', borderColor: 'var(--border-color)', color: 'white' }}
                      labelStyle={{ fontWeight: 700 }}
                    />
                    <Line type="monotone" dataKey="score" stroke="var(--primary)" strokeWidth={3} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Cost Spend Chart */}
            <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <DollarSign size={18} style={{ color: '#f59e0b' }} />
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>LLM Consumption Spend</h3>
              </div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <BarChart data={runChartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} />
                    <YAxis stroke="var(--text-muted)" fontSize={11} />
                    <Tooltip
                      contentStyle={{ backgroundColor: 'var(--bg-dark)', borderColor: 'var(--border-color)', color: 'white' }}
                      formatter={(value) => [`$${value.toFixed(4)}`, 'Cost']}
                    />
                    <Bar dataKey="cost" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Lower Row: compilation status and metadata summary */}
          <div style={{ display: 'grid', gridTemplateColumns: '0.7fr 1.3fr', gap: '2rem' }}>
            {/* Pie Chart: Compilation Success rate */}
            <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', alignSelf: 'flex-start' }}>
                <CheckCircle size={18} style={{ color: '#10b981' }} />
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>Compilation Breakdown</h3>
              </div>
              <div style={{ width: '100%', height: 200, display: 'flex', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10b981' }}></span>
                  <span style={{ color: 'var(--text-muted)' }}>Compiled: {totalCompiled} ({((totalCompiled / totalGenerated) * 100).toFixed(1)}%)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#ef4444' }}></span>
                  <span style={{ color: 'var(--text-muted)' }}>Failed: {totalFailed} ({((totalFailed / totalGenerated) * 100).toFixed(1)}%)</span>
                </div>
              </div>
            </div>

            {/* Aggregated Statistics Summary Table */}
            <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <BarChart3 size={18} style={{ color: 'var(--secondary)' }} />
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'white' }}>Aggregated Statistics</h3>
              </div>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '0.5rem 0', fontWeight: 600 }}>Metric Metric</th>
                      <th style={{ padding: '0.5rem 0', fontWeight: 600, textAlign: 'right' }}>Cumulative Performance</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                      <td style={{ padding: '0.75rem 0', color: 'var(--text-muted)' }}>Total Executions Analyzed</td>
                      <td style={{ padding: '0.75rem 0', textAlign: 'right', fontWeight: 700, color: 'white' }}>{completedRuns.length}</td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                      <td style={{ padding: '0.75rem 0', color: 'var(--text-muted)' }}>Total Tests Generated</td>
                      <td style={{ padding: '0.75rem 0', textAlign: 'right', fontWeight: 700, color: 'white' }}>{totalGenerated} tests</td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                      <td style={{ padding: '0.75rem 0', color: 'var(--text-muted)' }}>Successfully Compiled Tests</td>
                      <td style={{ padding: '0.75rem 0', textAlign: 'right', fontWeight: 700, color: '#10b981' }}>{totalCompiled} tests</td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                      <td style={{ padding: '0.75rem 0', color: 'var(--text-muted)' }}>Average Compilation Success Rate</td>
                      <td style={{ padding: '0.75rem 0', textAlign: 'right', fontWeight: 700, color: 'white' }}>
                        {((totalCompiled / Math.max(1, totalGenerated)) * 100).toFixed(1)}%
                      </td>
                    </tr>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                      <td style={{ padding: '0.75rem 0', color: 'var(--text-muted)' }}>Average Quality Score Across Runs</td>
                      <td style={{ padding: '0.75rem 0', textAlign: 'right', fontWeight: 700, color: 'var(--primary)' }}>
                        {(completedRuns.reduce((sum, r) => sum + (r.avg_score || 0), 0) / completedRuns.length).toFixed(1)}/100
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
