const USER_ID_KEY = 'portfolio_user_id';

export const getUserId = () => {
  let userId = localStorage.getItem(USER_ID_KEY);
  if (!userId) {
    // Generate a random user ID if none exists
    userId = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem(USER_ID_KEY, userId);
  }
  return userId;
};

export const getHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

export const handleApiError = async (response) => {
  if (!response.ok) {
    if (response.status === 401) {
      // Unauthorized, clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      window.location.href = '/login';
    }
    const error = await response.json();
    throw new Error(error.detail || 'API request failed');
  }
  return response.json();
}; 