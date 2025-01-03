import React from 'react';
import Plot from 'react-plotly.js';

export const PieChart = ({ data }) => {
  return (
    <Plot
      data={[{
        values: data.values,
        labels: data.labels,
        type: 'pie'
      }]}
      layout={{ title: 'Portfolio Allocation' }}
    />
  );
};

export const LineChart = ({ data }) => {
  return (
    <Plot
      data={[{
        x: data.dates,
        y: data.values,
        type: 'scatter',
        mode: 'lines+markers'
      }]}
      layout={{ title: 'Portfolio Performance' }}
    />
  );
};

export const BarChart = ({ data }) => {
  return (
    <Plot
      data={[{
        x: data.labels,
        y: data.values,
        type: 'bar'
      }]}
      layout={{ title: 'Annual Returns' }}
    />
  );
}; 