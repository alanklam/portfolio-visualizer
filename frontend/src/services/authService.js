import { createApiEndpoint, handleApiError } from './apiClient';

export const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(createApiEndpoint('/api/auth/login'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    });
    return handleApiError(response);
};

export const signup = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(createApiEndpoint('/api/auth/signup'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    });
    return handleApiError(response);
};

export const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
};

export const isAuthenticated = () => {
    return !!localStorage.getItem('token');
}; 