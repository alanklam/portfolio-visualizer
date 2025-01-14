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
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions
} from '@mui/material';
import { PieChart, PerformanceChart, AnnualReturnsChart } from './ChartComponents';
import { HoldingsTable } from './HoldingsTable';
import { GainLossAnalysis } from './GainLossAnalysis';
import { fetchHoldings, fetchGainLoss, fetchAllocation, fetchPerformance, fetchAnnualReturns, getSettings, updateSettings } from '../../services/dataService';
import { formatCurrency } from '../../utils/formatters';
import DashboardIcon from '@mui/icons-material/Dashboard';

const Dashboard = () => {
    const [holdings, setHoldings] = useState([]);
    const [gainLoss, setGainLoss] = useState({});
    const [allocation, setAllocation] = useState(null);
    const [performance, setPerformance] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [annualReturns, setAnnualReturns] = useState(null);
    const [settings, setSettings] = useState(null);
    const [weightWarning, setWeightWarning] = useState(null);
    const [weightDialog, setWeightDialog] = useState({
        open: false,
        message: '',
        pendingWeights: null
    });

    useEffect(() => {
        const loadData = async () => {
            try {
                const [
                    holdingsData, 
                    gainLossData, 
                    allocationData, 
                    performanceData, 
                    annualReturnsData,
                    settingsData
                ] = await Promise.all([
                    fetchHoldings(),
                    fetchGainLoss(),
                    fetchAllocation(),
                    fetchPerformance(),
                    fetchAnnualReturns(),
                    getSettings()
                ]);

                if (Array.isArray(settingsData)) {
                    setSettings(settingsData);
                } else {
                    console.warn('Invalid settings data format:', settingsData);
                    setSettings([]); // Set empty array as fallback
                }
                
                setHoldings(holdingsData);
                setGainLoss(gainLossData);
                const parsedAllocationData = JSON.parse(allocationData.data);
                setAllocation({
                    chart_type: allocationData.chart_type,
                    values: parsedAllocationData.values,
                    labels: parsedAllocationData.labels
                });
                setPerformance(performanceData);
                
                // Update annual returns data format
                const annualReturns = {
                    years: annualReturnsData.annual_returns.map(item => item.year),
                    returns: annualReturnsData.annual_returns.map(item => item.return)
                };
                setAnnualReturns(annualReturns);
                console.log('Annual Returns Data:', annualReturns);
                
                setSettings(settingsData);
            } catch (err) {
                console.error('Dashboard data loading error:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    const handleWeightUpdate = async (newWeights) => {
        try {
            console.log('Sending weights to update:', newWeights);
            const response = await updateSettings(newWeights);
            console.log('Received settings response:', response);
            
            if (response.warning) {
                setWeightDialog({
                    open: true,
                    message: `Total weight exceeded 100% (${(response.total_weight * 100).toFixed(1)}%). Would you like to normalize the weights?`,
                    pendingWeights: response.settings
                });
            } else if (response.settings) {
                // Make sure we're setting the correct format
                setSettings(response.settings);
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            console.error('Weight update error:', error);
            setError('Failed to update weights: ' + error.message);
        }
    };

    const handleDialogConfirm = () => {
        if (weightDialog.pendingWeights) {
            setSettings(weightDialog.pendingWeights);
        }
        setWeightDialog({ open: false, message: '', pendingWeights: null });
    };

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

    const renderWeightWarning = () => {
        if (weightWarning) {
            return (
                <Alert 
                    severity="warning" 
                    sx={{ mb: 2 }}
                    onClose={() => setWeightWarning(null)}
                >
                    {weightWarning}
                </Alert>
            );
        }
        return null;
    };

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

            {/* Weight Warning Alert */}
            {renderWeightWarning()}

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
                            Annual Returns
                        </Typography>
                        <AnnualReturnsChart data={annualReturns} />
                    </Paper>
                </Grid>
                <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            Performance
                        </Typography>
                        <PerformanceChart data={performance || { dates: [], portfolio_values: [], invested_amounts: [], metrics: {} }} />
                    </Paper>
                </Grid>
            </Grid>

            {/* Holdings Table */}
            <Paper sx={{ mt: 3, p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Current Holdings
                </Typography>
                <HoldingsTable 
                    holdings={holdings} 
                    settings={settings}  // Pass settings to HoldingsTable
                    onWeightUpdate={handleWeightUpdate}
                />
            </Paper>

            {/* Gain/Loss Analysis */}
            <Paper sx={{ mt: 3, p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    Gain/Loss Analysis
                </Typography>
                <GainLossAnalysis data={gainLoss} />
            </Paper>

            {/* Weight Warning Dialog */}
            <Dialog
                open={weightDialog.open}
                onClose={() => setWeightDialog({ open: false, message: '', pendingWeights: null })}
            >
                <DialogTitle>Weight Adjustment Required</DialogTitle>
                <DialogContent>
                    <Typography>{weightDialog.message}</Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setWeightDialog({ open: false, message: '', pendingWeights: null })}>
                        Cancel
                    </Button>
                    <Button onClick={handleDialogConfirm} autoFocus>
                        Confirm
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default Dashboard;
