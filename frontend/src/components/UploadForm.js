import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { getHeaders } from '../services/userService';

function UploadForm() {
  const [files, setFiles] = useState([]);
  const [broker, setBroker] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(acceptedFiles);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: true,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!broker) {
      setError('Please select a broker');
      return;
    }
    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('broker', broker);
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: getHeaders(),
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      setSuccess(true);
      setFiles([]);
      setBroker('');
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Upload Transaction Files</Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>Files uploaded successfully!</Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel id="broker-select-label">Broker</InputLabel>
            <Select
              labelId="broker-select-label"
              value={broker}
              label="Broker"
              onChange={(e) => setBroker(e.target.value)}
            >
              <MenuItem value="fidelity">Fidelity</MenuItem>
              <MenuItem value="schwab">Charles Schwab</MenuItem>
              <MenuItem value="etrade">E*TRADE</MenuItem>
            </Select>
          </FormControl>

          <Paper
            {...getRootProps()}
            sx={{
              p: 3,
              mb: 3,
              border: '2px dashed #ccc',
              borderRadius: 2,
              backgroundColor: isDragActive ? '#f0f0f0' : 'white',
              cursor: 'pointer',
              textAlign: 'center'
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            {isDragActive ? (
              <Typography>Drop the files here...</Typography>
            ) : (
              <Typography>
                Drag and drop CSV files here, or click to select files
              </Typography>
            )}
          </Paper>

          {files.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>Selected Files:</Typography>
              {files.map((file, index) => (
                <Typography key={index} color="text.secondary">
                  {file.name}
                </Typography>
              ))}
            </Box>
          )}

          <Button
            type="submit"
            variant="contained"
            disabled={loading || files.length === 0 || !broker}
            fullWidth
          >
            {loading ? <CircularProgress size={24} /> : 'Upload Files'}
          </Button>
        </form>
      </Paper>
    </Box>
  );
}

export default UploadForm; 