import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import {
  Box,
  Card,
  CardContent,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';

const Charts = () => {
  const [allocationData, setAllocationData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [returnsData, setReturnsData] = useState(null);
  const [stats, setStats] = useState(null);
  const [timeframe, setTimeframe] = useState('1Y');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchChartData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch all chart data in parallel
      const [allocation, performance, returns, portfolioStats] = await Promise.all([
        axios.get('/api/portfolio/allocation'),
        axios.get(`/api/portfolio/performance?timeframe=${timeframe}`),
        axios.get('/api/portfolio/annual-returns'),
        axios.get('/api/portfolio/stats'),
      ]);

      setAllocationData(JSON.parse(allocation.data.data));
      setPerformanceData(JSON.parse(performance.data.data));
      setReturnsData(JSON.parse(returns.data.data));
      setStats(portfolioStats.data);
    } catch (err) {
      setError('Failed to fetch chart data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChartData();
  }, [timeframe]);

  const handleTimeframeChange = (event, newTimeframe) => {
    if (newTimeframe !== null) {
      setTimeframe(newTimeframe);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Portfolio Stats */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  Total Value
                </Typography>
                <Typography variant="h6">
                  ${stats.total_value.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  Total Return
                </Typography>
                <Typography variant="h6" color={stats.total_return >= 0 ? 'success.main' : 'error.main'}>
                  {stats.total_return_pct.toFixed(2)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  Positions
                </Typography>
                <Typography variant="h6">
                  {stats.num_positions}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  Last Update
                </Typography>
                <Typography variant="h6">
                  {new Date(stats.last_update).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Performance Chart Timeframe Selector */}
      <Box sx={{ mb: 4 }}>
        <ToggleButtonGroup
          value={timeframe}
          exclusive
          onChange={handleTimeframeChange}
          aria-label="timeframe"
          size="small"
        >
          <ToggleButton value="1M">1M</ToggleButton>
          <ToggleButton value="3M">3M</ToggleButton>
          <ToggleButton value="6M">6M</ToggleButton>
          <ToggleButton value="1Y">1Y</ToggleButton>
          <ToggleButton value="ALL">ALL</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Charts Grid */}
      <Grid container spacing={3}>
        {/* Portfolio Allocation */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portfolio Allocation
              </Typography>
              {allocationData && (
                <Plot
                  data={allocationData.data}
                  layout={{
                    ...allocationData.layout,
                    showlegend: true,
                    height: 400,
                    margin: { t: 30, b: 30, l: 30, r: 30 },
                  }}
                  config={{ responsive: true }}
                  style={{ width: '100%' }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portfolio Performance
              </Typography>
              {performanceData && (
                <Plot
                  data={performanceData.data}
                  layout={{
                    ...performanceData.layout,
                    showlegend: true,
                    height: 400,
                    margin: { t: 30, b: 30, l: 50, r: 30 },
                  }}
                  config={{ responsive: true }}
                  style={{ width: '100%' }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Annual Returns */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Annual Returns
              </Typography>
              {returnsData && (
                <Plot
                  data={returnsData.data}
                  layout={{
                    ...returnsData.layout,
                    showlegend: false,
                    height: 400,
                    margin: { t: 30, b: 30, l: 50, r: 30 },
                  }}
                  config={{ responsive: true }}
                  style={{ width: '100%' }}
                />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Charts; 