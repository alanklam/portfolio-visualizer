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
    // Changed this line to avoid initializing from settings here:
    const [assignedWeights, setAssignedWeights] = useState({});
    
    const [editingRow, setEditingRow] = useState(null);
    const [tempWeight, setTempWeight] = useState('');

    // Update when settings change
    useEffect(() => {
        if (settings) {
            const weightMap = settings.reduce((acc, setting) => ({
                ...acc,
                [setting.stock]: setting.target_weight
            }), {});
            console.log('Settings updated:', weightMap);
            setAssignedWeights(weightMap);
        }
    }, [settings]);
    
    // Calculate total portfolio value
    const totalPortfolioValue = holdings.reduce((sum, holding) => sum + holding.market_value, 0);

    // Calculate value to change for each holding
    const calculateValueToChange = (holding, targetWeight) => {
        const targetValue = totalPortfolioValue * targetWeight;
        return targetValue - holding.market_value;
    };

    // Modify the click handler to show percentage value
    const handleWeightClick = (symbol, weight) => {
        setEditingRow(symbol);
        // Convert decimal to percentage for display
        setTempWeight((weight * 100).toString());
    };

    const handleWeightChange = (event) => {
        setTempWeight(event.target.value);
    };

    // Modify handleWeightSave to refresh weights after save
    const handleWeightSave = async (symbol) => {
        const percentValue = parseFloat(tempWeight);
        if (!isNaN(percentValue) && percentValue >= 0 && percentValue <= 100) {
            try {
                const decimalWeight = percentValue / 100;
                const newWeights = { ...assignedWeights, [symbol]: decimalWeight };
                
                // Call parent's update function and wait for it to complete
                await onWeightUpdate(newWeights);
                
                // Reset editing state
                setEditingRow(null);
                setTempWeight('');
                
                // Refresh weights from database
                const response = await getSettings();
                const updatedWeights = response.reduce((acc, setting) => ({
                    ...acc,
                    [setting.stock]: setting.target_weight
                }), {});
                setAssignedWeights(updatedWeights);
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
                        <TableCell align="right">Value to Change</TableCell>
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
                                                assignedWeights[holding.symbol] || 0
                                            )}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            {formatPercent(assignedWeights[holding.symbol] || 0)}
                                        </div>
                                    </Tooltip>
                                )}
                            </TableCell>
                            <TableCell 
                                align="right"
                                sx={{ 
                                    color: calculateValueToChange(
                                        holding, 
                                        assignedWeights[holding.symbol] || 0
                                    ) >= 0 ? 'success.main' : 'error.main'
                                }}
                            >
                                {formatCurrency(calculateValueToChange(
                                    holding,
                                    assignedWeights[holding.symbol] || 0
                                ))}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};