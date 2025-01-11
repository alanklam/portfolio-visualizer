import React from 'react';
import Plot from 'react-plotly.js';
import { Box, Typography, Grid, Paper } from '@mui/material';
import { formatCurrency } from '../../utils/formatters';  // Add this import

export const PieChart = ({ data }) => {
    if (!data || !data.values || data.values.length === 0) {
        return <Box>No allocation data available</Box>;
    }

    return (
        <Plot
            data={[{
                values: data.values,
                labels: data.labels,
                type: 'pie',
                hoverinfo: 'label+percent',
                textinfo: 'label+percent'
            }]}
            layout={{
                showlegend: true,
                height: 400,
                margin: { t: 0, b: 0, l: 0, r: 0 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                legend: {
                    textwrap: 'true'
                }
            }}
            config={{ responsive: true }}
        />
    );
};

export const PerformanceChart = ({ data }) => {
    if (!data || !data.dates || data.dates.length === 0) {
        return <Box>No performance data available</Box>;
    }

    const { metrics } = data;

    return (
        <Box>
            <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={4}>
                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                        <Typography variant="subtitle2" color="textSecondary">
                            Annualized Return
                        </Typography>
                        <Typography variant="body1">
                            {metrics?.annualized_return ? (metrics.annualized_return * 100).toFixed(2) + '%' : 'N/A'}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={4}>
                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                        <Typography variant="subtitle2" color="textSecondary">
                            Volatility
                        </Typography>
                        <Typography variant="body1">
                            {metrics?.volatility ? (metrics.volatility * 100).toFixed(2) + '%' : 'N/A'}
                        </Typography>
                    </Paper>
                </Grid>
                <Grid item xs={4}>
                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                        <Typography variant="subtitle2" color="textSecondary">
                            Sharpe Ratio
                        </Typography>
                        <Typography variant="body1">
                            {metrics?.sharpe_ratio ? metrics.sharpe_ratio.toFixed(2) : 'N/A'}
                        </Typography>
                    </Paper>
                </Grid>
            </Grid>
            <Plot
                data={[
                    {
                        x: data.dates,
                        y: data.portfolio_values,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Portfolio Value',
                        line: { color: '#1976d2' }
                    },
                    {
                        x: data.dates,
                        y: data.invested_amounts,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Invested Amount',
                        line: { color: '#4caf50', dash: 'dash' }
                    }
                ]}
                layout={{
                    showlegend: true,
                    height: 400,
                    width: 1200,
                    margin: { t: 0, b: 40, l: 160, r: 20 },
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    xaxis: {
                        title: 'Date',
                        showgrid: true,
                        gridcolor: '#eee'
                    },
                    yaxis: {
                        title: 'Value ($)',
                        showgrid: true,
                        gridcolor: '#eee'
                    }
                }}
                config={{ responsive: true }}
            />
        </Box>
    );
};

export const AnnualReturnsChart = ({ data }) => {
    if (!data || !data.years || data.years.length === 0) {
        return <Box>No annual returns data available</Box>;
    }

    return (
        <Plot
            data={[{
                x: data.years,
                y: data.returns,
                type: 'bar',
                marker: {
                    color: data.returns.map(val => val >= 0 ? '#4caf50' : '#f44336')
                },
                text: data.returns.map(val => formatCurrency(val)),
                textposition: 'auto',
                hovertemplate: '%{text}<extra></extra>'
            }]}
            layout={{
                height: 300,
                margin: { t: 0, b: 40, l: 80, r: 20 },  // Increased left margin for dollar amounts
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: {
                    title: 'Year',
                    showgrid: false,
                    tickmode: 'array',
                    tickvals: data.years
                },
                yaxis: {
                    title: 'Dollar Return',
                    showgrid: true,
                    gridcolor: '#eee',
                    tickformat: '$.3s' // Format large numbers with SI prefix (K, M, B)
                }
            }}
            config={{ responsive: true }}
        />
    );
};
