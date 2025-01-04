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
} from '@mui/material';
import { PieChart } from './Charts';

function Portfolio() {
  const [holdings, setHoldings] = useState([]);
  const [gainLoss, setGainLoss] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHoldings = useCallback(async () => {
    try {
      const response = await fetch('/api/portfolio/holdings');
      if (!response.ok) {
        throw new Error('Failed to fetch holdings');
      }
      const data = await response.json();
      setHoldings(Array.isArray(data) ? data : []);
    } catch (error) {
      setError('Failed to fetch holdings');
      setHoldings([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchGainLoss = useCallback(async () => {
    try {
      const response = await fetch('/api/portfolio/gain-loss');
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

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
                {formatCurrency(gainLoss.total_value)}
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
              <Typography variant="h5" color={gainLoss.total_return >= 0 ? 'success.main' : 'error.main'}>
                {formatCurrency(gainLoss.total_return)}
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
              <Typography variant="h5" color={gainLoss.unrealized_gain_loss >= 0 ? 'success.main' : 'error.main'}>
                {formatCurrency(gainLoss.unrealized_gain_loss)}
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
                {formatCurrency(gainLoss.dividend_income)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Portfolio Allocation Chart */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Portfolio Allocation</Typography>
            <PieChart />
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Gain/Loss Analysis</Typography>
            <TableContainer>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell>Total Return</TableCell>
                    <TableCell align="right">{formatCurrency(gainLoss.total_return)}</TableCell>
                    <TableCell align="right">{formatPercent(gainLoss.total_return_percent)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Realized Gain/Loss</TableCell>
                    <TableCell align="right">{formatCurrency(gainLoss.realized_gain_loss)}</TableCell>
                    <TableCell align="right">{formatPercent(gainLoss.realized_gain_loss_percent)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Unrealized Gain/Loss</TableCell>
                    <TableCell align="right">{formatCurrency(gainLoss.unrealized_gain_loss)}</TableCell>
                    <TableCell align="right">{formatPercent(gainLoss.unrealized_gain_loss_percent)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Dividend Income</TableCell>
                    <TableCell align="right">{formatCurrency(gainLoss.dividend_income)}</TableCell>
                    <TableCell align="right">{formatPercent(gainLoss.dividend_yield)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Option Gains/Losses</TableCell>
                    <TableCell align="right">{formatCurrency(gainLoss.option_gain_loss)}</TableCell>
                    <TableCell align="right">{formatPercent(gainLoss.option_gain_loss_percent)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
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