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
  TextField,
  Button,
  Alert,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import { fetchHoldings, fetchSettings, updateSettings } from '../services/dataService';

function Settings() {
  const [holdings, setHoldings] = useState([]);
  const [targetWeights, setTargetWeights] = useState({});
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const fetchHoldingsData = useCallback(async () => {
    try {
      const data = await fetchHoldings();
      setHoldings(data);
      
      // Initialize target weights with current weights if not set
      const weights = {};
      data.forEach(holding => {
        weights[holding.symbol] = targetWeights[holding.symbol] || (holding.weight * 100);
      });
      setTargetWeights(weights);
    } catch (error) {
      setError('Failed to fetch holdings');
    }
  }, [targetWeights]);

  const fetchTargetWeights = useCallback(async () => {
    try {
      const data = await fetchSettings();
      setTargetWeights(data.target_weights || {});
    } catch (error) {
      console.error('Failed to fetch target weights:', error);
    }
  }, []);

  useEffect(() => {
    fetchHoldingsData();
    fetchTargetWeights();
  }, [fetchHoldingsData, fetchTargetWeights]);

  const handleWeightChange = (symbol, value) => {
    setTargetWeights(prev => ({
      ...prev,
      [symbol]: parseFloat(value) || 0
    }));
  };

  const validateWeights = () => {
    const total = Object.values(targetWeights).reduce((sum, weight) => sum + weight, 0);
    return Math.abs(total - 100) < 0.01; // Allow small rounding errors
  };

  const handleSave = async () => {
    if (!validateWeights()) {
      setError('Target weights must sum to 100%');
      return;
    }

    try {
      await updateSettings({
        target_weights: Object.fromEntries(
          Object.entries(targetWeights).map(([k, v]) => [k, v / 100])
        )
      });
      setSuccess(true);
      setError(null);
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      setError('Failed to save target weights');
    }
  };

  const calculateRebalancing = () => {
    if (!validateWeights()) return [];

    const totalValue = holdings.reduce((sum, h) => sum + (h.units * h.last_price), 0);
    return holdings.map(holding => {
      const currentValue = holding.units * holding.last_price;
      const currentWeight = (currentValue / totalValue) * 100;
      const targetWeight = targetWeights[holding.symbol] || 0;
      const difference = targetWeight - currentWeight;
      const valueToTrade = (difference / 100) * totalValue;
      const unitsToTrade = valueToTrade / holding.last_price;

      return {
        symbol: holding.symbol,
        currentWeight: currentWeight,
        targetWeight: targetWeight,
        difference: difference,
        unitsToTrade: unitsToTrade
      };
    });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Portfolio Settings</Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>Settings saved successfully!</Alert>
      )}

      {/* Target Weights Table */}
      <Paper sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ p: 2 }}>Target Portfolio Weights</Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Security Type</TableCell>
                <TableCell align="right">Current Weight (%)</TableCell>
                <TableCell align="right">Target Weight (%)</TableCell>
                <TableCell align="right">Difference (%)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {holdings.map((holding) => (
                <TableRow key={holding.symbol}>
                  <TableCell>{holding.symbol}</TableCell>
                  <TableCell>{holding.security_type}</TableCell>
                  <TableCell align="right">
                    {(holding.weight * 100).toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">
                    <TextField
                      type="number"
                      size="small"
                      value={targetWeights[holding.symbol] || 0}
                      onChange={(e) => handleWeightChange(holding.symbol, e.target.value)}
                      inputProps={{ step: "0.1" }}
                      sx={{ width: '100px' }}
                    />
                  </TableCell>
                  <TableCell align="right">
                    {((targetWeights[holding.symbol] || 0) - (holding.weight * 100)).toFixed(2)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
          >
            Save Target Weights
          </Button>
        </Box>
      </Paper>

      {/* Rebalancing Suggestions */}
      <Paper>
        <Typography variant="h6" sx={{ p: 2 }}>Rebalancing Suggestions</Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell align="right">Action</TableCell>
                <TableCell align="right">Units</TableCell>
                <TableCell align="right">Current Weight (%)</TableCell>
                <TableCell align="right">Target Weight (%)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {calculateRebalancing().map((item) => (
                <TableRow key={item.symbol}>
                  <TableCell>{item.symbol}</TableCell>
                  <TableCell align="right">
                    {item.unitsToTrade > 0 ? 'Buy' : 'Sell'}
                  </TableCell>
                  <TableCell align="right">
                    {Math.abs(item.unitsToTrade).toFixed(2)}
                  </TableCell>
                  <TableCell align="right">
                    {item.currentWeight.toFixed(2)}%
                  </TableCell>
                  <TableCell align="right">
                    {item.targetWeight.toFixed(2)}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}

export default Settings; 