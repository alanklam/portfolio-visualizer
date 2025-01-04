import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
  Paper,
  CircularProgress,
  Alert,
} from '@mui/material';
import { styled } from '@mui/material/styles';

const DropzoneArea = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  textAlign: 'center',
  cursor: 'pointer',
  borderStyle: 'dashed',
  borderWidth: 2,
  borderColor: theme.palette.divider,
  backgroundColor: theme.palette.background.default,
  '&:hover': {
    borderColor: theme.palette.primary.main,
  },
}));

const UploadForm = () => {
  const [files, setFiles] = useState([]);
  const [broker, setBroker] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(acceptedFiles);
    setError(null);
    setSuccess(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: true,
  });

  const handleBrokerChange = (event) => {
    setBroker(event.target.value);
    setError(null);
  };

  const handleUpload = async () => {
    if (!broker) {
      setError('Please select a broker');
      return;
    }

    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(false);

    try {
      for (const file of files) {
        const reader = new FileReader();
        reader.onload = async (e) => {
          const content = e.target.result;
          try {
            await axios.post('/api/upload', {
              broker,
              file_content: content,
            });
          } catch (err) {
            setError(`Error uploading ${file.name}: ${err.message}`);
            setUploading(false);
            return;
          }
        };
        reader.readAsText(file);
      }
      setSuccess(true);
      setFiles([]);
      setBroker('');
    } catch (err) {
      setError(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Upload Transaction Files
      </Typography>

      <FormControl fullWidth sx={{ mb: 3 }}>
        <InputLabel>Broker</InputLabel>
        <Select value={broker} onChange={handleBrokerChange}>
          <MenuItem value="fidelity">Fidelity</MenuItem>
          <MenuItem value="schwab">Charles Schwab</MenuItem>
          <MenuItem value="etrade">E-Trade</MenuItem>
        </Select>
      </FormControl>

      <DropzoneArea {...getRootProps()}>
        <input {...getInputProps()} />
        {isDragActive ? (
          <Typography>Drop the CSV files here...</Typography>
        ) : (
          <Typography>
            Drag and drop CSV files here, or click to select files
          </Typography>
        )}
      </DropzoneArea>

      {files.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle1">Selected Files:</Typography>
          {files.map((file) => (
            <Typography key={file.name} variant="body2">
              {file.name}
            </Typography>
          ))}
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mt: 2 }}>
          Files uploaded successfully!
        </Alert>
      )}

      <Button
        variant="contained"
        color="primary"
        onClick={handleUpload}
        disabled={uploading || files.length === 0 || !broker}
        sx={{ mt: 3 }}
        fullWidth
      >
        {uploading ? <CircularProgress size={24} /> : 'Upload'}
      </Button>
    </Box>
  );
};

export default UploadForm; 