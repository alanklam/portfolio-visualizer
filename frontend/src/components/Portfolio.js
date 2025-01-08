import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { PieChart, PerformanceChart, AnnualReturnsChart } from './Charts';
import { getHeaders, handleApiError } from '../services/userService';

function Portfolio() {
  const [holdings, setHoldings] = useState([]);
  const [gainLoss, setGainLoss] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('1Y');

  const fetchHoldings = useCallback(async () => {
    try {
      const response = await fetch('/api/portfolio/holdings', {
        headers: getHeaders()
      });
      const data = await handleApiError(response);
      setHoldings(Array.isArray(data) ? data : []);
    } catch (error) {
      setError(error.message);
      setHoldings([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchGainLoss = useCallback(async () => {
    try {
      const response = await fetch('/api/portfolio/gain-loss', {
        headers: getHeaders()
      });
      if (!response.ok) {
        throw new Error('Failed to fetch gain/loss data');
      }
      const data = await response.json();
      setGainLoss(data || {});
    } catch (error) {
      setError('Failed to fetch gain/loss data');
      setGainLoss({});
    }
  }, []);

  useEffect(() => {
    fetchHoldings();
    fetchGainLoss();
  }, [fetchHoldings, fetchGainLoss]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  const formatPercent = (value) => {
    return `${((value || 0) * 100).toFixed(2)}%`;
  };

  const calculateTotals = (gainLossData) => {
    return Object.values(gainLossData).reduce((totals, holding) => {
      return {
        total_value: (totals.total_value || 0) + holding.market_value,
        total_cost: (totals.total_cost || 0) + holding.total_cost_basis,
        total_gain_loss: (totals.total_gain_loss || 0) + holding.total_return,
        realized_gain_loss: (totals.realized_gain_loss || 0) + holding.realized_gain_loss,
        unrealized_gain_loss: (totals.unrealized_gain_loss || 0) + holding.unrealized_gain_loss,
        dividend_income: (totals.dividend_income || 0) + holding.dividend_income,
        option_gain_loss: (totals.option_gain_loss || 0) + holding.option_gain_loss
      };
    }, {});
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  const totals = calculateTotals(gainLoss);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Portfolio Overview</Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}

      {/* Portfolio Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Value
              </Typography>
              <Typography variant="h5">
                {formatCurrency(totals.total_value)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Return
              </Typography>
              <Typography variant="h5" color={totals.total_gain_loss >= 0 ? 'success.main' : 'error.main'}>
                {formatCurrency(totals.total_gain_loss)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Unrealized Gain/Loss
              </Typography>
              <Typography variant="h5" color={totals.unrealized_gain_loss >= 0 ? 'success.main' : 'error.main'}>
                {formatCurrency(totals.unrealized_gain_loss)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Dividend Income
              </Typography>
              <Typography variant="h5" color="success.main">
                {formatCurrency(totals.dividend_income)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Portfolio Allocation */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Portfolio Allocation</Typography>
            <PieChart />
          </Paper>
        </Grid>

        {/* Gain/Loss Analysis */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Gain/Loss Analysis</Typography>
            <TableContainer>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell>Total Return</TableCell>
                    <TableCell align="right">{formatCurrency(totals.total_gain_loss)}</TableCell>
                    <TableCell align="right">{formatPercent(totals.total_gain_loss / totals.total_cost)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Realized Gain/Loss</TableCell>
                    <TableCell align="right">{formatCurrency(totals.realized_gain_loss)}</TableCell>
                    <TableCell align="right">{formatPercent(totals.realized_gain_loss / totals.total_cost)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Unrealized Gain/Loss</TableCell>
                    <TableCell align="right">{formatCurrency(totals.unrealized_gain_loss)}</TableCell>
                    <TableCell align="right">{formatPercent(totals.unrealized_gain_loss / totals.total_cost)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Dividend Income</TableCell>
                    <TableCell align="right">{formatCurrency(totals.dividend_income)}</TableCell>
                    <TableCell align="right">{formatPercent(totals.dividend_income / totals.total_cost)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Option Gains/Losses</TableCell>
                    <TableCell align="right">{formatCurrency(totals.option_gain_loss)}</TableCell>
                    <TableCell align="right">{formatPercent(totals.option_gain_loss / totals.total_cost)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Performance Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Portfolio Performance</Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Timeframe</InputLabel>
                <Select
                  label="Timeframe"
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                >
                  <MenuItem value="1M">1 Month</MenuItem>
                  <MenuItem value="3M">3 Months</MenuItem>
                  <MenuItem value="6M">6 Months</MenuItem>
                  <MenuItem value="1Y">1 Year</MenuItem>
                  <MenuItem value="ALL">All Time</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <PerformanceChart timeframe={timeframe} />
          </Paper>
        </Grid>

        {/* Annual Returns Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Annual Returns</Typography>
            <AnnualReturnsChart />
          </Paper>
        </Grid>
      </Grid>

      {/* Holdings Table */}
      <Paper>
        <Typography variant="h6" sx={{ p: 2 }}>Current Holdings</Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Security Type</TableCell>
                <TableCell align="right">Units</TableCell>
                <TableCell align="right">Last Price</TableCell>
                <TableCell align="right">Market Value</TableCell>
                <TableCell align="right">Cost Basis</TableCell>
                <TableCell align="right">Gain/Loss</TableCell>
                <TableCell align="right">Weight</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {holdings.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No holdings found. Please upload transaction files.
                  </TableCell>
                </TableRow>
              ) : (
                holdings.map((holding) => (
                  <TableRow key={holding.symbol}>
                    <TableCell>{holding.symbol}</TableCell>
                    <TableCell>{holding.security_type}</TableCell>
                    <TableCell align="right">{holding.units.toFixed(2)}</TableCell>
                    <TableCell align="right">{formatCurrency(holding.last_price)}</TableCell>
                    <TableCell align="right">{formatCurrency(holding.market_value)}</TableCell>
                    <TableCell align="right">{formatCurrency(holding.cost_basis)}</TableCell>
                    <TableCell 
                      align="right"
                      sx={{ color: holding.unrealized_gain_loss >= 0 ? 'success.main' : 'error.main' }}
                    >
                      {formatCurrency(holding.unrealized_gain_loss)}
                    </TableCell>
                    <TableCell align="right">{formatPercent(holding.weight)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}

export default Portfolio; 