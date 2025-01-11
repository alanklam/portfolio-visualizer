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

export const HoldingsTable = ({ holdings }) => {
    if (!holdings || holdings.length === 0) {
        return null;
    }

    return (
        <TableContainer component={Paper}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell align="right">Units</TableCell>
                        <TableCell align="right">Last Price</TableCell>
                        <TableCell align="right">Weight</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {holdings.map((holding) => (
                        <TableRow key={holding.symbol}>
                            <TableCell>{holding.symbol}</TableCell>
                            <TableCell>{holding.security_type}</TableCell>
                            <TableCell align="right">{holding.units.toFixed(2)}</TableCell>
                            <TableCell align="right">{formatCurrency(holding.last_price)}</TableCell>
                            <TableCell align="right">{formatPercent(holding.weight)}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};