import React, { useState, useEffect } from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    TextField,
    IconButton,
    Tooltip
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import { formatCurrency, formatPercent } from '../../utils/formatters';
import { getSettings, updateSettings } from '../../services/dataService';

export const HoldingsTable = ({ holdings, settings, onWeightUpdate }) => {
    const [assignedWeights, setAssignedWeights] = useState({});
    const [editingRow, setEditingRow] = useState(null);
    const [tempWeight, setTempWeight] = useState('');

    useEffect(() => {
        if (settings) {
            // Convert settings array to object with stock as key
            const weightMap = settings.reduce((acc, setting) => ({
                ...acc,
                [setting.stock]: setting.target_weight
            }), {});
            setAssignedWeights(weightMap);
        }
    }, [settings]);

    // Modify the click handler to show percentage value
    const handleWeightClick = (symbol, weight) => {
        setEditingRow(symbol);
        // Convert decimal to percentage for display
        setTempWeight((weight * 100).toString());
    };

    const handleWeightChange = (event) => {
        setTempWeight(event.target.value);
    };

    const handleWeightSave = async (symbol) => {
        // Convert percentage input to decimal
        const percentValue = parseFloat(tempWeight);
        if (!isNaN(percentValue) && percentValue >= 0 && percentValue <= 100) {
            try {
                const decimalWeight = percentValue / 100;
                // Update local state
                const newWeights = { ...assignedWeights, [symbol]: decimalWeight };
                
                // Save to database
                await updateSettings(newWeights);
                setAssignedWeights(newWeights);
                setEditingRow(null);
                setTempWeight('');
            } catch (error) {
                console.error('Error saving weight:', error);
            }
        }
    };

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
                        <TableCell align="right">Assigned Weight</TableCell>
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
                            <TableCell align="right">
                                {editingRow === holding.symbol ? (
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                                        <TextField
                                            size="small"
                                            value={tempWeight}
                                            onChange={handleWeightChange}
                                            onKeyPress={(e) => {
                                                if (e.key === 'Enter') {
                                                    handleWeightSave(holding.symbol);
                                                }
                                            }}
                                            sx={{ width: '80px' }}
                                            InputProps={{
                                                endAdornment: <span>%</span>,
                                            }}
                                        />
                                        <IconButton 
                                            size="small" 
                                            onClick={() => handleWeightSave(holding.symbol)}
                                        >
                                            <SaveIcon />
                                        </IconButton>
                                    </div>
                                ) : (
                                    <Tooltip title="Click to edit">
                                        <div
                                            onClick={() => handleWeightClick(
                                                holding.symbol, 
                                                assignedWeights[holding.symbol] || holding.weight
                                            )}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            {formatPercent(assignedWeights[holding.symbol] || holding.weight)}
                                        </div>
                                    </Tooltip>
                                )}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};