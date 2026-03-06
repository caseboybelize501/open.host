import React, { useState, useEffect } from 'react';

const MemoryView = () => {
  const [activeTab, setActiveTab] = useState('failures');
  const [failures, setFailures] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [strategies, setStrategies] = useState({});
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllMemory();
  }, []);

  const fetchAllMemory = async () => {
    try {
      const [failuresRes, patternsRes, strategiesRes, metaRes] = await Promise.all([
        fetch('/api/memory/failures'),
        fetch('/api/memory/patterns'),
        fetch('/api/memory/strategies'),
        fetch('/api/memory/meta')
      ]);

      const failuresData = await failuresRes.json();
      const patternsData = await patternsRes.json();
      const strategiesData = await strategiesRes.json();
      const metaData = await metaRes.json();

      setFailures(failuresData.failures || []);
      setPatterns(patternsData.patterns || []);
      setStrategies(strategiesData.strategies || {});
      setMeta(metaData);
    } catch (err) {
      console.error('Failed to fetch memory data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getTabCount = (tab) => {
    switch (tab) {
      case 'failures': return failures.length;
      case 'patterns': return patterns.length;
      case 'strategies': return Object.keys(strategies).length;
      case 'meta': return meta?.training_data_points || 0;
      default: return 0;
    }
  };

  return (
    <div className="memory-view">
      <header className="page-header">
        <h1>🧠 Memory System</h1>
        <p className="subtitle">4-Layer Learning Memory</p>
      </header>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'failures' ? 'active' : ''}`}
          onClick={() => setActiveTab('failures')}
        >
          Layer 1: Failures ({getTabCount('failures')})
        </button>
        <button 
          className={`tab ${activeTab === 'patterns' ? 'active' : ''}`}
          onClick={() => setActiveTab('patterns')}
        >
          Layer 2: Patterns ({getTabCount('patterns')})
        </button>
        <button 
          className={`tab ${activeTab === 'strategies' ? 'active' : ''}`}
          onClick={() => setActiveTab('strategies')}
        >
          Layer 3: Strategies ({getTabCount('strategies')})
        </button>
        <button 
          className={`tab ${activeTab === 'meta' ? 'active' : ''}`}
          onClick={() => setActiveTab('meta')}
        >
          Layer 4: Meta-Learning ({getTabCount('meta')})
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading memory data...</div>
      ) : (
        <div className="tab-content">
          {activeTab === 'failures' && <FailuresTab failures={failures} />}
          {activeTab === 'patterns' && <PatternsTab patterns={patterns} />}
          {activeTab === 'strategies' && <StrategiesTab strategies={strategies} />}
          {activeTab === 'meta' && <MetaTab meta={meta} />}
        </div>
      )}

      <style jsx>{`
        .memory-view {
          padding: 20px;
        }
        .page-header {
          margin-bottom: 20px;
        }
        .subtitle {
          color: #666;
        }
        .tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
          border-bottom: 2px solid #eee;
          padding-bottom: 10px;
        }
        .tab {
          padding: 10px 16px;
          border: none;
          background: #f5f5f5;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        }
        .tab:hover {
          background: #e5e5e5;
        }
        .tab.active {
          background: #3b82f6;
          color: white;
        }
        .loading {
          text-align: center;
          padding: 40px;
          color: #666;
        }
        .tab-content {
          background: #fff;
          border-radius: 8px;
          padding: 20px;
        }
      `}</style>
    </div>
  );
};

const FailuresTab = ({ failures }) => {
  if (failures.length === 0) {
    return <EmptyState message="No failure patterns recorded yet" />;
  }

  return (
    <div className="failures-tab">
      <h3>Deployment Failure Patterns</h3>
      <p className="description">
        Historical failures stored to avoid repeating mistakes
      </p>
      <table>
        <thead>
          <tr>
            <th>Project Type</th>
            <th>Platform</th>
            <th>Failure Stage</th>
            <th>Error</th>
            <th>Fix Applied</th>
          </tr>
        </thead>
        <tbody>
          {failures.map((failure, idx) => (
            <tr key={idx}>
              <td>{failure.project_type}</td>
              <td>{failure.platform}</td>
              <td>Stage {failure.failure_stage}</td>
              <td className="error-text">{failure.error_message?.slice(0, 50)}...</td>
              <td>{failure.fix_applied}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const PatternsTab = ({ patterns }) => {
  return (
    <div className="patterns-tab">
      <h3>Project → Platform Pattern Graph</h3>
      <p className="description">
        Neo4j graph of project types and their platform success relationships
      </p>
      {patterns.length === 0 ? (
        <EmptyState message="No patterns in graph yet. Deployments will populate this." />
      ) : (
        <div className="patterns-list">
          {patterns.map((pattern, idx) => (
            <div key={idx} className="pattern-card">
              <span className="pattern-node">{pattern.project_type}</span>
              <span className="pattern-edge">→</span>
              <span className="pattern-node">{pattern.platform}</span>
              <span className="pattern-outcome">{pattern.outcome}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const StrategiesTab = ({ strategies }) => {
  const strategyEntries = Object.entries(strategies);

  if (strategyEntries.length === 0) {
    return <EmptyState message="No build strategies learned yet" />;
  }

  return (
    <div className="strategies-tab">
      <h3>Build Strategy Library</h3>
      <p className="description">
        Effective build configurations per project type + platform
      </p>
      {strategyEntries.map(([key, strategies]) => {
        const [projectType, platform] = key.split(':');
        const bestStrategy = strategies[strategies.length - 1];
        
        return (
          <div key={key} className="strategy-card">
            <div className="strategy-header">
              <span className="strategy-project">{projectType}</span>
              <span className="strategy-on">on</span>
              <span className="strategy-platform">{platform}</span>
            </div>
            <div className="strategy-details">
              <p><strong>Build Command:</strong> {bestStrategy?.build_command || 'N/A'}</p>
              <p><strong>Success:</strong> {bestStrategy?.success ? '✅' : '❌'}</p>
              <p><strong>Performance Score:</strong> {bestStrategy?.performance_score || 'N/A'}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const MetaTab = ({ meta }) => {
  if (!meta) {
    return <EmptyState message="No meta-learning data available" />;
  }

  return (
    <div className="meta-tab">
      <h3>Meta-Learning Index</h3>
      <p className="description">
        Predicts cycles-to-stable based on historical deployment approaches
      </p>
      
      <div className="meta-stats">
        <div className="meta-stat">
          <h4>Training Data Points</h4>
          <p className="stat-value">{meta.training_data_points || 0}</p>
        </div>
        <div className="meta-stat">
          <h4>Model Trained</h4>
          <p className="stat-value">{meta.model_trained ? '✅ Yes' : '❌ No'}</p>
        </div>
      </div>

      {meta.recent_predictions && meta.recent_predictions.length > 0 && (
        <div className="predictions-section">
          <h4>Recent Predictions</h4>
          <ul>
            {meta.recent_predictions.map((pred, idx) => (
              <li key={idx}>
                {pred.project_type} → {pred.predicted_cycles} cycles (approach: {pred.approach})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

const EmptyState = ({ message }) => (
  <div className="empty-state">
    <p>{message}</p>
  </div>
);

export default MemoryView;
