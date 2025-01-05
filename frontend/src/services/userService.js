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

export const getHeaders = () => ({
  'X-User-ID': getUserId(),
});

export const handleApiError = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'An error occurred');
  }
  return response.json();
}; 