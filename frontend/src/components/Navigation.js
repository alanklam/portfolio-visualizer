import React from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Button } from '@mui/material';

function Navigation() {
  return (
    <AppBar position="static" sx={{ top: 'auto', bottom: 0 }}>
      <Toolbar sx={{ justifyContent: 'flex-end' }}>
        <Button color="inherit" component={Link} to="/portfolio">Portfolio</Button>
        <Button color="inherit" component={Link} to="/upload">Upload</Button>
        <Button color="inherit" component={Link} to="/settings">Settings</Button>
        <Button color="inherit" component={Link} to="/">Logout</Button>
      </Toolbar>
    </AppBar>
  );
}

export default Navigation; 