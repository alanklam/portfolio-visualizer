export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const getUserId = () => {
    let userId = localStorage.getItem('USER_ID_KEY');
    if (!userId) {
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('USER_ID_KEY', userId);
    }
    return userId;
};

export const getHeaders = (isFormData = false) => {
    const token = localStorage.getItem('token');
    const headers = {
        'Authorization': token ? `Bearer ${token}` : '',
        'X-User-ID': getUserId()
    };
    
    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }
    
    return headers;
};

export const handleApiError = async (response) => {
    if (!response.ok) {
        if (response.status === 401) {
            // Unauthorized, clear token and redirect to login
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            window.location.href = '/';
        }
        
        const errorData = await response.json().catch(() => ({ detail: 'API request failed' }));
        const errorMessage = errorData.detail || 
            (typeof errorData === 'object' ? JSON.stringify(errorData) : 'API request failed');
        throw new Error(errorMessage);
    }
    return response.json();
};

export const createApiEndpoint = (endpoint) => `${API_BASE_URL}${endpoint}`;

class ApiClient {
    async get(endpoint) {
        const response = await fetch(createApiEndpoint(endpoint), {
            headers: getHeaders()
        });
        return handleApiError(response);
    }

    async post(endpoint, data, options = {}) {
        const isFormData = data instanceof FormData;
        const response = await fetch(createApiEndpoint(endpoint), {
            method: 'POST',
            headers: {
                ...getHeaders(isFormData),
                ...options.headers
            },
            body: isFormData ? data : JSON.stringify(data)
        });
        return handleApiError(response);
    }

    async put(endpoint, data) {
        const response = await fetch(createApiEndpoint(endpoint), {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(data)
        });
        return handleApiError(response);
    }

    async delete(endpoint) {
        const response = await fetch(createApiEndpoint(endpoint), {
            method: 'DELETE',
            headers: getHeaders()
        });
        return handleApiError(response);
    }
}

export const apiClient = new ApiClient();