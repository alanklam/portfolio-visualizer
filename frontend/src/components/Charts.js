import React, { useState, useEffect, useCallback } from 'react';
import { Box, Paper, Typography, FormControl, Select, MenuItem, Grid } from '@mui/material';
import Plot from 'react-plotly.js';

export function PieChart() {
  const [data, setData] = useState(null);

  const fetchAllocationData = useCallback(async () => {
    try {
      const response = await fetch('/api/portfolio/allocation');
      const chartData = await response.json();
      setData(chartData);
    } catch (error) {
      console.error('Failed to fetch allocation data:', error);
    }
  }, []);

  useEffect(() => {
    fetchAllocationData();
  }, [fetchAllocationData]);

  if (!data) return null;

  return (
    <Plot
      data={[{
        values: data.values,
        labels: data.labels,
        type: 'pie',
        textinfo: 'label+percent',
        hoverinfo: 'label+value+percent',
        hole: 0.4
      }]}
      layout={{
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 },
        margin: { t: 0, b: 0, l: 0, r: 0 },
        height: 300,
        width: '100%'
      }}
      config={{ responsive: true }}
    />
  );
}

export function PerformanceChart() {
  const [data, setData] = useState(null);
  const [timeframe, setTimeframe] = useState('1Y');

  const fetchPerformanceData = useCallback(async () => {
    try {
      const response = await fetch(`/api/portfolio/performance?timeframe=${timeframe}`);
      const chartData = await response.json();
      setData(chartData);
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
    }
  }, [timeframe]);

  useEffect(() => {
    fetchPerformanceData();
  }, [fetchPerformanceData]);

  if (!data) return null;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Portfolio Performance</Typography>
        <FormControl size="small">
          <Select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
          >
            <MenuItem value="1M">1 Month</MenuItem>
            <MenuItem value="3M">3 Months</MenuItem>
            <MenuItem value="6M">6 Months</MenuItem>
            <MenuItem value="1Y">1 Year</MenuItem>
            <MenuItem value="3Y">3 Years</MenuItem>
            <MenuItem value="5Y">5 Years</MenuItem>
            <MenuItem value="ALL">All Time</MenuItem>
          </Select>
        </FormControl>
      </Box>
      <Plot
        data={[
          {
            x: data.dates,
            y: data.portfolio_values,
            type: 'scatter',
            mode: 'lines',
            name: 'Portfolio Value',
            line: { color: '#2196f3' }
          },
          {
            x: data.dates,
            y: data.cost_basis,
            type: 'scatter',
            mode: 'lines',
            name: 'Cost Basis',
            line: { color: '#9e9e9e', dash: 'dash' }
          }
        ]}
        layout={{
          showlegend: true,
          legend: { orientation: 'h', y: -0.2 },
          margin: { t: 0, b: 30, l: 60, r: 20 },
          height: 300,
          width: '100%',
          yaxis: {
            title: 'Value ($)',
            tickformat: ',.0f'
          }
        }}
        config={{ responsive: true }}
      />
    </Box>
  );
}

export function AnnualReturnsChart() {
  const [data, setData] = useState(null);

  const fetchAnnualReturnsData = useCallback(async () => {
    try {
      const response = await fetch('/api/portfolio/annual-returns');
      const chartData = await response.json();
      setData(chartData);
    } catch (error) {
      console.error('Failed to fetch annual returns data:', error);
    }
  }, []);

  useEffect(() => {
    fetchAnnualReturnsData();
  }, [fetchAnnualReturnsData]);

  if (!data) return null;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Annual Returns</Typography>
      <Plot
        data={[{
          x: data.years,
          y: data.returns,
          type: 'bar',
          marker: {
            color: data.returns.map(value => value >= 0 ? '#4caf50' : '#f44336')
          }
        }]}
        layout={{
          margin: { t: 0, b: 30, l: 60, r: 20 },
          height: 300,
          width: '100%',
          yaxis: {
            title: 'Return (%)',
            tickformat: '.1%'
          }
        }}
        config={{ responsive: true }}
      />
    </Box>
  );
}

function Charts() {
  return (
    <Box sx={{ mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <PieChart />
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <PerformanceChart />
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <AnnualReturnsChart />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Charts; 