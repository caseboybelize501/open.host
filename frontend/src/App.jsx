import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import DeploymentHistory from './pages/DeploymentHistory';
import MemoryView from './pages/MemoryView';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<DeploymentHistory />} />
          <Route path="/memory" element={<MemoryView />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
