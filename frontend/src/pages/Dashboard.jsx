import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [systemProfile, setSystemProfile] = useState(null);
  const [health, setHealth] = useState(null);
  const [deploying, setDeploying] = useState(false);
  const [projectPath, setProjectPath] = useState('');
  const [lastDeployment, setLastDeployment] = useState(null);

  useEffect(() => {
    fetchSystemProfile();
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchSystemProfile = async () => {
    try {
      const res = await fetch('/api/system/profile');
      const data = await res.json();
      setSystemProfile(data);
    } catch (err) {
      console.error('Failed to fetch system profile:', err);
    }
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch('/health');
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      console.error('Failed to fetch health:', err);
    }
  };

  const handleDeploy = async (e) => {
    e.preventDefault();
    if (!projectPath.trim()) return;

    setDeploying(true);
    try {
      const res = await fetch('/api/deploy/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_path: projectPath })
      });
      const data = await res.json();
      setLastDeployment(data);
      fetchHealth();
    } catch (err) {
      console.error('Deployment failed:', err);
    } finally {
      setDeploying(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🚀 Open.Host Jarvis</h1>
        <p className="subtitle">Autonomous Hosting Deployment System</p>
      </header>

      {health && (
        <div className="health-banner">
          <span className={`status-indicator ${health.status === 'healthy' ? 'healthy' : 'unhealthy'}`}></span>
          System Status: <strong>{health.status.toUpperCase()}</strong>
          <span className="memory-hint">
            Memory Hit Rate: {(health.memory_hit_rate * 100).toFixed(0)}%
          </span>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🛠️</div>
          <div className="stat-content">
            <h3>Tools Detected</h3>
            <p className="stat-value">{health?.tools_detected || 0}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">☁️</div>
          <div className="stat-content">
            <h3>Platforms Available</h3>
            <p className="stat-value">{health?.platforms_available || 0}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>Consecutive Passes</h3>
            <p className="stat-value">{health?.consecutive_passes || 0}/7</p>
            <small>{health?.consecutive_passes >= 7 ? '🎯 STABLE' : 'Progress to STABLE'}</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <h3>Total Deployments</h3>
            <p className="stat-value">{health?.deployments_count || 0}</p>
          </div>
        </div>
      </div>

      <div className="deploy-section">
        <h2>Deploy New Project</h2>
        <form onSubmit={handleDeploy} className="deploy-form">
          <input
            type="text"
            placeholder="Enter project path (e.g., /path/to/project)"
            value={projectPath}
            onChange={(e) => setProjectPath(e.target.value)}
            className="project-input"
            disabled={deploying}
          />
          <button type="submit" className="deploy-btn" disabled={deploying}>
            {deploying ? '🔄 Deploying...' : '🚀 Deploy'}
          </button>
        </form>

        {lastDeployment && (
          <div className="deployment-result">
            <h4>Latest Deployment</h4>
            <div className="result-details">
              <p><strong>ID:</strong> {lastDeployment.deployment_id}</p>
              <p><strong>Status:</strong> {lastDeployment.status}</p>
              {lastDeployment.url && (
                <p><strong>URL:</strong> <a href={lastDeployment.url} target="_blank" rel="noopener noreferrer">{lastDeployment.url}</a></p>
              )}
              <p><strong>Validation:</strong> {lastDeployment.validation_passed ? '✅ Passed' : '❌ Failed'}</p>
            </div>
          </div>
        )}
      </div>

      {systemProfile && systemProfile.tools && Object.keys(systemProfile.tools).length > 0 && (
        <div className="tools-section">
          <h3>Detected Tools</h3>
          <div className="tools-list">
            {Object.entries(systemProfile.tools).map(([tool, version]) => (
              <div key={tool} className="tool-badge">
                <span className="tool-name">{tool}</span>
                <span className="tool-version">{version}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
