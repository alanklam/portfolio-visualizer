import { apiClient } from './apiClient';

export const fetchHoldings = () => {
    return apiClient.get('/api/portfolio/holdings');
};

export const fetchGainLoss = () => {
    return apiClient.get('/api/portfolio/gain-loss');
};

export const fetchAllocation = () => {
    return apiClient.get('/api/portfolio/allocation');
};

export const fetchPerformance = () => {
    return apiClient.get('/api/portfolio/performance');
};

export const uploadTransactions = async (files, broker) => {
    const results = [];
    const errors = [];
    
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('broker', broker);

        try {
            const result = await apiClient.post('/api/upload', formData);
            results.push({ file: file.name, success: true, result });
        } catch (error) {
            errors.push({ file: file.name, error: error.message });
        }
    }
    
    if (errors.length > 0) {
        const errorMessage = errors.map(e => `${e.file}: ${e.error}`).join('\n');
        throw new Error(errorMessage);
    }
    
    return results;
};

export const fetchAnnualReturns = () => {
    return apiClient.get('/api/portfolio/annual-returns');
};

// Keep these two functions as they're used by HoldingsTable
export const getSettings = async () => {
    try {
        const response = await apiClient.get('/api/portfolio/settings');
        return response.data;
    } catch (error) {
        console.error('Error fetching settings:', error);
        throw error;
    }
};

export const updateSettings = async (weights) => {
    try {
        // Add logging to debug the payload
        console.log('Sending weights payload:', {
            settings: Object.entries(weights).map(([stock, target_weight]) => ({
                stock,
                target_weight: parseFloat(target_weight)
            }))
        });

        const response = await apiClient.post('/api/portfolio/settings', {
            settings: Object.entries(weights).map(([stock, target_weight]) => ({
                stock,
                target_weight: parseFloat(target_weight)
            }))
        });
        
        // Add logging to debug the response
        console.log('Received response:', response);
        return response;
    } catch (error) {
        console.error('Error updating settings:', error);
        throw error;
    }
};
