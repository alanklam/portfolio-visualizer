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

export const fetchSettings = () => {
    return apiClient.get('/api/portfolio/settings');
};

export const updateSettings = (weights) => {
    return apiClient.post('/api/portfolio/settings', weights);
};

export const fetchAnnualReturns = () => {
    return apiClient.get('/api/portfolio/annual-returns');
}; 