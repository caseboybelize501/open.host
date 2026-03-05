import React from 'react';

const DeploymentHistory = () => {
  return (
    <div className="deployment-history">
      <h1>Deployment History</h1>
      <table>
        <thead>
          <tr>
            <th>Project</th>
            <th>Platform</th>
            <th>Status</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>My React App</td>
            <td>Netlify</td>
            <td>Success</td>
            <td>2023-10-01</td>
          </tr>
          <tr>
            <td>Python API</td>
            <td>Render</td>
            <td>Success</td>
            <td>2023-10-02</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default DeploymentHistory;
