import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    TextField,
    Typography,
    Paper,
    Alert,
    CircularProgress
} from '@mui/material';
import { login, signup } from '../../services/authService';

const LoginForm = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isSignup, setIsSignup] = useState(false);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const authFn = isSignup ? signup : login;
            const response = await authFn(username, password);
            
            if (response.access_token) {
                localStorage.setItem('token', response.access_token);
                localStorage.setItem('username', response.username);
                navigate('/portfolio');
            }
        } catch (err) {
            setError(err.message || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                bgcolor: 'background.default'
            }}
        >
            <Paper
                elevation={3}
                sx={{
                    p: 4,
                    maxWidth: 400,
                    width: '90%'
                }}
            >
                <Typography variant="h5" component="h1" gutterBottom align="center">
                    {isSignup ? 'Create Account' : 'Login'}
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                <form onSubmit={handleSubmit}>
                    <TextField
                        fullWidth
                        label="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        margin="normal"
                        required
                    />
                    <TextField
                        fullWidth
                        label="Password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        margin="normal"
                        required
                    />
                    <Button
                        fullWidth
                        type="submit"
                        variant="contained"
                        sx={{ mt: 3 }}
                        disabled={loading}
                    >
                        {loading ? (
                            <CircularProgress size={24} />
                        ) : isSignup ? (
                            'Sign Up'
                        ) : (
                            'Login'
                        )}
                    </Button>
                </form>

                <Button
                    fullWidth
                    onClick={() => setIsSignup(!isSignup)}
                    sx={{ mt: 2 }}
                >
                    {isSignup
                        ? 'Already have an account? Login'
                        : "Don't have an account? Sign Up"}
                </Button>
            </Paper>
        </Box>
    );
};

export default LoginForm; 