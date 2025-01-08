import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Box, CircularProgress, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { getHeaders, handleApiError } from '../services/userService';

export function PieChart() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/portfolio/allocation', {
          headers: getHeaders()
        });
        const result = await handleApiError(response);
        const chartData = JSON.parse(result.data);
        setData([{
          values: chartData.values,
          labels: chartData.labels,
          type: 'pie',
          textinfo: 'label+percent',
          hoverinfo: 'label+value+percent',
          hole: 0.4
        }]);
      } catch (error) {
        console.error('Error fetching allocation data:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ height: '400px', width: '100%' }}>
      <Plot
        data={data}
        layout={{
          showlegend: true,
          legend: { orientation: 'h', y: -0.2 },
          margin: { t: 30, b: 30, l: 30, r: 30 },
          height: 400,
          width: null
        }}
        config={{ responsive: true }}
        style={{ width: '100%', height: '100%' }}
      />
    </Box>
  );
}

export function PerformanceChart({ timeframe }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/portfolio/performance?timeframe=${timeframe}`, {
          headers: getHeaders()
        });
        const result = await handleApiError(response);
        const chartData = JSON.parse(result.data);
        setData([
          {
            x: chartData.dates,
            y: chartData.portfolio_value,
            type: 'scatter',
            mode: 'lines',
            name: 'Portfolio Value',
            line: { color: '#2196f3' }
          },
          {
            x: chartData.dates,
            y: chartData.invested_amount,
            type: 'scatter',
            mode: 'lines',
            name: 'Invested Amount',
            line: { color: '#4caf50', dash: 'dash' }
          }
        ]);
      } catch (error) {
        console.error('Error fetching performance data:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeframe]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ height: '400px', width: '100%' }}>
      <Plot
        data={data}
        layout={{
          title: 'Portfolio Performance',
          showlegend: true,
          legend: { orientation: 'h', y: -0.2 },
          margin: { t: 50, b: 50, l: 50, r: 30 },
          height: 400,
          width: null,
          xaxis: {
            title: 'Date',
            rangeslider: { visible: true }
          },
          yaxis: {
            title: 'Value ($)',
            tickformat: ',.0f'
          }
        }}
        config={{
          responsive: true,
          scrollZoom: true,
          displayModeBar: true,
          modeBarButtonsToAdd: ['zoom2d', 'pan2d', 'resetScale2d']
        }}
        style={{ width: '100%', height: '100%' }}
      />
    </Box>
  );
}

export function AnnualReturnsChart() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/portfolio/annual-returns', {
          headers: getHeaders()
        });
        const result = await handleApiError(response);
        const chartData = JSON.parse(result.data);
        setData([{
          x: chartData.years,
          y: chartData.returns,
          type: 'bar',
          marker: {
            color: chartData.returns.map(value => value >= 0 ? '#4caf50' : '#f44336')
          }
        }]);
      } catch (error) {
        console.error('Error fetching annual returns data:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ height: '400px', width: '100%' }}>
      <Plot
        data={data}
        layout={{
          title: 'Annual Returns',
          showlegend: false,
          margin: { t: 50, b: 50, l: 50, r: 30 },
          height: 400,
          width: null,
          xaxis: { title: 'Year' },
          yaxis: {
            title: 'Return (%)',
            tickformat: '.1f',
            ticksuffix: '%'
          }
        }}
        config={{ responsive: true }}
        style={{ width: '100%', height: '100%' }}
      />
    </Box>
  );
} 