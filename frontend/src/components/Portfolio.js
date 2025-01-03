import React, { useState, useEffect } from 'react';
import { PieChart, LineChart, BarChart } from './Charts';

function Portfolio() {
  const [holdings, setHoldings] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    // Fetch portfolio data
    fetchPortfolioData();
  }, []);

  const fetchPortfolioData = async () => {
    // Fetch holdings, performance, and analysis data
  };

  return (
    <div className="portfolio">
      <h2>Portfolio Overview</h2>
      
      <div className="charts-container">
        {holdings.length > 0 && (
          <PieChart data={{
            values: holdings.map(h => h.total_value),
            labels: holdings.map(h => h.stock)
          }} />
        )}
        
        {performance && (
          <LineChart data={performance} />
        )}
        
        {analysis && (
          <BarChart data={analysis} />
        )}
      </div>

      <div className="holdings-table">
        <h3>Current Holdings</h3>
        <table>
          <thead>
            <tr>
              <th>Stock</th>
              <th>Shares</th>
              <th>Average Cost</th>
              <th>Current Price</th>
              <th>Total Value</th>
              <th>Gain/Loss</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((holding) => (
              <tr key={holding.stock}>
                <td>{holding.stock}</td>
                <td>{holding.total_units}</td>
                <td>${holding.average_cost.toFixed(2)}</td>
                <td>${holding.current_price.toFixed(2)}</td>
                <td>${(holding.total_units * holding.current_price).toFixed(2)}</td>
                <td>${((holding.current_price - holding.average_cost) * holding.total_units).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Portfolio; 