import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { LoginForm, Dashboard, FileUpload } from './components/components';
import Navigation from './components/Navigation';

const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#1976d2',
        },
        secondary: {
            main: '#dc004e',
        },
    },
});

function PrivateRoute({ children }) {
    const token = localStorage.getItem('token');
    return token ? children : <Navigate to="/" replace />;
}

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Navigation />
            <Routes>
                <Route path="/" element={<LoginForm />} />
                <Route
                    path="/portfolio"
                    element={
                        <PrivateRoute>
                            <Dashboard />
                        </PrivateRoute>
                    }
                />
                <Route
                    path="/upload"
                    element={
                        <PrivateRoute>
                            <FileUpload />
                        </PrivateRoute>
                    }
                />
            </Routes>
        </ThemeProvider>
    );
}

export default App;