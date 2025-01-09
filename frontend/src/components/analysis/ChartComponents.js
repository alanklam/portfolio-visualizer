import React from 'react';
import Plot from 'react-plotly.js';
import { Box } from '@mui/material';

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
                hole: 0.4,
                hoverinfo: 'label+percent',
                textinfo: 'label+percent'
            }]}
            layout={{
                showlegend: true,
                height: 400,
                margin: { t: 0, b: 0, l: 0, r: 0 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent'
            }}
            config={{ responsive: true }}
        />
    );
};

export const PerformanceChart = ({ data }) => {
    if (!data || !data.dates || data.dates.length === 0) {
        return <Box>No performance data available</Box>;
    }

    return (
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
                margin: { t: 0, b: 40, l: 60, r: 20 },
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
                }
            }]}
            layout={{
                height: 300,
                margin: { t: 0, b: 40, l: 60, r: 20 },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                xaxis: {
                    title: 'Year',
                    showgrid: false
                },
                yaxis: {
                    title: 'Return (%)',
                    showgrid: true,
                    gridcolor: '#eee',
                    tickformat: '.1%'
                }
            }}
            config={{ responsive: true }}
        />
    );
}; 