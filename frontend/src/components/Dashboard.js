// frontend/src/components/Dashboard.js
import React from 'react';

const Dashboard = () => {
    return (
        <div>
            <h1>Flagged Reviews Dashboard</h1>
            <table>
                <thead>
                    <tr>
                        <th>Review ID</th>
                        <th>Review Text</th>
                        <th>Flag Patterns</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {/* Data will be loaded here */}
                    <tr>
                        <td>...</td>
                        <td>...</td>
                        <td>...</td>
                        <td>...</td>
                        <td>...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    );
};

export default Dashboard;