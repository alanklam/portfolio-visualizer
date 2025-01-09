import React, { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Paper,
    Typography,
    AppBar,
    Toolbar,
    Button,
    CircularProgress,
    Alert
} from '@mui/material';
import { PieChart, PerformanceChart, AnnualReturnsChart } from './ChartComponents';
import { HoldingsTable } from './HoldingsTable';
import { GainLossAnalysis } from './GainLossAnalysis';
import { fetchHoldings, fetchGainLoss, fetchAllocation, fetchPerformance } from '../../services/dataService';
import { formatCurrency } from '../../utils/formatters';
import { Link } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';

const Dashboard = () => {
    const [holdings, setHoldings] = useState([]);
    const [gainLoss, setGainLoss] = useState({});
    const [allocation, setAllocation] = useState(null);
    const [performance, setPerformance] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [holdingsData, gainLossData, allocationData, performanceData] = await Promise.all([
                    fetchHoldings(),
                    fetchGainLoss(),
                    fetchAllocation(),
                    fetchPerformance()
                ]);
                setHoldings(holdingsData);
                setGainLoss(gainLossData);
                setAllocation(allocationData);
                setPerformance(performanceData);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ m: 2 }}>
                {error}
            </Alert>
        );
    }

    const totals = Object.values(gainLoss).reduce(
        (acc, curr) => ({
            total_value: acc.total_value + curr.market_value,
            total_gain: acc.total_gain + curr.total_return,
            unrealized_gain: acc.unrealized_gain + curr.unrealized_gain_loss,
            dividend_income: acc.dividend_income + curr.dividend_income
        }),
        { total_value: 0, total_gain: 0, unrealized_gain: 0, dividend_income: 0 }
    );

    return (
        <Box sx={{ p: 3 }}>
            <AppBar position="static" sx={{ mb: 4, background: 'linear-gradient(90deg, #1976d2, #42a5f5)', boxShadow: 3 }}>
                <Toolbar>
                    <DashboardIcon sx={{ mr: 1 }} />
                    <Typography variant="h5" sx={{ flexGrow: 1, fontWeight: 'bold', color: '#fff' }}>
                        Portfolio Dashboard
                    </Typography>
                </Toolbar>
            </AppBar>

            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography color="textSecondary" gutterBottom>
                            Total Value
                        </Typography>
                        <Typography variant="h5">
                            {formatCurrency(totals.total_value)}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography color="textSecondary" gutterBottom>
                            Total Return
                        </Typography>
                        <Typography
                            variant="h5"
                            color={totals.total_gain >= 0 ? 'success.main' : 'error.main'}
                        >
                            {formatCurrency(totals.total_gain)}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography color="textSecondary" gutterBottom>
                            Unrealized Gain/Loss
                        </Typography>
                        <Typography
                            variant="h5"
                            color={totals.unrealized_gain >= 0 ? 'success.main' : 'error.main'}
                        >
                            {formatCurrency(totals.unrealized_gain)}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography color="textSecondary" gutterBottom>
                            Dividend Income
                        </Typography>
                        <Typography variant="h5" color="success.main">
                            {formatCurrency(totals.dividend_income)}
                        </Typography>
                    </Paper>
                </Grid>
            </Grid>

            {/* Charts Grid */}
            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Portfolio Allocation
                        </Typography>
                        <PieChart data={{
                            values: allocation?.values || [],
                            labels: allocation?.labels || []
                        }} />
                    </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Performance
                        </Typography>
                        <PerformanceChart data={performance || {}} />
                    </Paper>
                </Grid>
                <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Annual Returns
                        </Typography>
                        <AnnualReturnsChart data={performance?.annual_returns || {}} />
                    </Paper>
                </Grid>
            </Grid>

            {/* Holdings Table */}
            <Paper sx={{ mt: 3, p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Current Holdings
                </Typography>
                <HoldingsTable holdings={holdings} />
            </Paper>

            {/* Gain/Loss Analysis */}
            <Paper sx={{ mt: 3, p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Gain/Loss Analysis
                </Typography>
                <GainLossAnalysis data={gainLoss} />
            </Paper>
        </Box>
    );
};

export default Dashboard; 