import React, { useState, useEffect } from 'react';

function Settings() {
  const [settings, setSettings] = useState([]);
  const [newSetting, setNewSetting] = useState({ stock: '', target_weight: 0 });

  useEffect(() => {
    // Fetch current settings
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Handle form submission
  };

  const handleDelete = async (stock) => {
    // Handle setting deletion
  };

  return (
    <div className="settings">
      <h2>Portfolio Settings</h2>
      
      <form onSubmit={handleSubmit}>
        <div>
          <input
            type="text"
            placeholder="Stock Symbol"
            value={newSetting.stock}
            onChange={(e) => setNewSetting({...newSetting, stock: e.target.value})}
          />
          <input
            type="number"
            placeholder="Target Weight (%)"
            value={newSetting.target_weight}
            onChange={(e) => setNewSetting({...newSetting, target_weight: parseFloat(e.target.value)})}
          />
          <button type="submit">Add</button>
        </div>
      </form>

      <table>
        <thead>
          <tr>
            <th>Stock</th>
            <th>Target Weight (%)</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {settings.map((setting) => (
            <tr key={setting.stock}>
              <td>{setting.stock}</td>
              <td>{setting.target_weight}</td>
              <td>
                <button onClick={() => handleDelete(setting.stock)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Settings; 