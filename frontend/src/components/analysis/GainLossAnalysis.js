import React from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper
} from '@mui/material';
import { formatCurrency, formatPercent } from '../../utils/formatters';

export const GainLossAnalysis = ({ data }) => {
    if (!data || Object.keys(data).length === 0) {
        return null;
    }

    return (
        <TableContainer component={Paper}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell align="right">Units</TableCell>
                        <TableCell align="right">Market Value</TableCell>
                        <TableCell align="right">Cost Basis</TableCell>
                        <TableCell align="right">Realized G/L</TableCell>
                        <TableCell align="right">Unrealized G/L</TableCell>
                        <TableCell align="right">Total Return</TableCell>
                        <TableCell align="right">Return %</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {Object.entries(data).map(([symbol, details]) => (
                        <TableRow key={symbol}>
                            <TableCell>{symbol}</TableCell>
                            <TableCell align="right">{details.current_units.toFixed(2)}</TableCell>
                            <TableCell align="right">{formatCurrency(details.market_value)}</TableCell>
                            <TableCell align="right">{formatCurrency(details.total_cost_basis)}</TableCell>
                            <TableCell 
                                align="right"
                                sx={{ 
                                    color: details.realized_gain_loss >= 0 ? 'success.main' : 'error.main'
                                }}
                            >
                                {formatCurrency(details.realized_gain_loss)}
                            </TableCell>
                            <TableCell 
                                align="right"
                                sx={{ 
                                    color: details.unrealized_gain_loss >= 0 ? 'success.main' : 'error.main'
                                }}
                            >
                                {formatCurrency(details.unrealized_gain_loss)}
                            </TableCell>
                            <TableCell 
                                align="right"
                                sx={{ 
                                    color: details.total_return >= 0 ? 'success.main' : 'error.main'
                                }}
                            >
                                {formatCurrency(details.total_return)}
                            </TableCell>
                            <TableCell 
                                align="right"
                                sx={{ 
                                    color: details.total_return_pct >= 0 ? 'success.main' : 'error.main'
                                }}
                            >
                                {formatPercent(details.total_return_pct)}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}; 