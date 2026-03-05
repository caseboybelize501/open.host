import React from 'react';

const Dashboard = () => {
  return (
    <div className="dashboard">
      <h1>Open.Host Jarvis</h1>
      <p>Autonomous Hosting Finder</p>
      <div className="stats">
        <div className="stat-card">
          <h3>Tools Detected</h3>
          <p>7</p>
        </div>
        <div className="stat-card">
          <h3>Platforms Available</h3>
          <p>5</p>
        </div>
        <div className="stat-card">
          <h3>Consecutive Passes</h3>
          <p>0</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
