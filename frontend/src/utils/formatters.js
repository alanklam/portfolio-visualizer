const currencyFormatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
});

const percentFormatter = new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
});

const compactFormatter = new Intl.NumberFormat('en-US', {
    notation: 'compact',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
});

export const formatCurrency = (value) => {
    if (typeof value !== 'number' || isNaN(value)) {
        return '$0.00';
    }
    return currencyFormatter.format(value);
};

export const formatPercent = (value) => {
    if (typeof value !== 'number' || isNaN(value)) {
        return '0.00%';
    }
    return percentFormatter.format(value);
};

export const formatCompactNumber = (value) => {
    if (typeof value !== 'number' || isNaN(value)) {
        return '0';
    }
    return compactFormatter.format(value);
};

export const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
};

export const formatTimeframe = (timeframe) => {
    const now = new Date();
    switch (timeframe) {
        case '1M':
            return new Date(now.setMonth(now.getMonth() - 1));
        case '3M':
            return new Date(now.setMonth(now.getMonth() - 3));
        case '6M':
            return new Date(now.setMonth(now.getMonth() - 6));
        case '1Y':
            return new Date(now.setFullYear(now.getFullYear() - 1));
        case 'ALL':
            return null;
        default:
            return new Date(now.setFullYear(now.getFullYear() - 1));
    }
}; 