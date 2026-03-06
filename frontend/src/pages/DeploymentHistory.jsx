import React, { useState, useEffect } from 'react';

const DeploymentHistory = () => {
  const [deployments, setDeployments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchDeployments();
  }, []);

  const fetchDeployments = async () => {
    try {
      const res = await fetch('/api/history/deployments?limit=50');
      const data = await res.json();
      setDeployments(data.deployments || []);
    } catch (err) {
      console.error('Failed to fetch deployments:', err);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredDeployments = () => {
    if (filter === 'all') return deployments;
    if (filter === 'stable') return deployments.filter(d => d.stable);
    if (filter === 'failed') return deployments.filter(d => d.status === 'failed');
    return deployments;
  };

  const getStatusBadge = (deployment) => {
    if (deployment.stable) return <span className="badge stable">🎯 STABLE</span>;
    if (deployment.status === 'deployed') return <span className="badge success">✅ Deployed</span>;
    if (deployment.status === 'deploying') return <span className="badge pending">🔄 Deploying</span>;
    if (deployment.status === 'failed') return <span className="badge error">❌ Failed</span>;
    return <span className="badge unknown">{deployment.status}</span>;
  };

  const getValidationSummary = (deployment) => {
    const stages = deployment.stages || [];
    const passed = stages.filter(s => s.passed).length;
    const total = stages.length || 10;
    return `${passed}/${total} stages`;
  };

  return (
    <div className="deployment-history">
      <header className="page-header">
        <h1>📜 Deployment History</h1>
        <div className="filter-controls">
          <label>Filter: </label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="stable">Stable</option>
            <option value="deployed">Deployed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </header>

      {loading ? (
        <div className="loading">Loading deployments...</div>
      ) : deployments.length === 0 ? (
        <div className="empty-state">
          <p>No deployments yet. Start by deploying a project from the Dashboard.</p>
        </div>
      ) : (
        <div className="deployments-table">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Project Type</th>
                <th>Platform</th>
                <th>Status</th>
                <th>Validation</th>
                <th>Consecutive Passes</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {getFilteredDeployments().map((deployment) => (
                <tr key={deployment.id} className={deployment.stable ? 'stable-row' : ''}>
                  <td className="deploy-id">{deployment.id.slice(0, 8)}...</td>
                  <td>{deployment.project_type || 'Unknown'}</td>
                  <td>
                    {deployment.plan?.platforms?.[0]?.name || 
                     deployment.deployment_result?.platform || 
                     '-'}
                  </td>
                  <td>{getStatusBadge(deployment)}</td>
                  <td>{getValidationSummary(deployment)}</td>
                  <td>
                    <div className="passes-indicator">
                      {deployment.consecutive_passes || 0}/7
                      {deployment.consecutive_passes >= 7 && ' 🎯'}
                    </div>
                  </td>
                  <td className="timestamp">
                    {deployment.timestamp ? new Date(deployment.timestamp).toLocaleString() : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <style jsx>{`
        .deployment-history {
          padding: 20px;
        }
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }
        .filter-controls {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .filter-controls select {
          padding: 8px 12px;
          border-radius: 4px;
          border: 1px solid #ccc;
        }
        .loading, .empty-state {
          text-align: center;
          padding: 40px;
          color: #666;
        }
        .deployments-table {
          overflow-x: auto;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          background: #fff;
          border-radius: 8px;
          overflow: hidden;
        }
        th, td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #eee;
        }
        th {
          background: #f5f5f5;
          font-weight: 600;
        }
        tr:hover {
          background: #f9f9f9;
        }
        .stable-row {
          background: #f0fff4;
        }
        .deploy-id {
          font-family: monospace;
          color: #666;
        }
        .badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }
        .badge.stable {
          background: #10b981;
          color: white;
        }
        .badge.success {
          background: #34d399;
          color: white;
        }
        .badge.pending {
          background: #fbbf24;
          color: white;
        }
        .badge.error {
          background: #ef4444;
          color: white;
        }
        .passes-indicator {
          font-weight: 500;
        }
        .timestamp {
          font-size: 12px;
          color: #666;
        }
      `}</style>
    </div>
  );
};

export default DeploymentHistory;
