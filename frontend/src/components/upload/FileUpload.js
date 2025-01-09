import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
    Box,
    Button,
    FormControl,
    InputLabel,
    MenuItem,
    Select,
    Typography,
    Paper,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    IconButton,
    Alert,
    CircularProgress
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { uploadTransactions } from '../../services/dataService';

const BROKER_TYPES = [
    { value: 'autodetect', label: 'Auto Detect' },
    { value: 'fidelity', label: 'Fidelity' },
    { value: 'schwab', label: 'Charles Schwab' },
    { value: 'etrade', label: 'E-Trade' }
];

const FileUpload = () => {
    const [files, setFiles] = useState([]);
    const [broker, setBroker] = useState('autodetect');
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    const onDrop = useCallback((acceptedFiles) => {
        setFiles(prev => [...prev, ...acceptedFiles]);
        setError(null);
        setSuccess(false);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv']
        },
        multiple: true
    });

    const handleRemoveFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
        setError(null);
        setSuccess(false);
    };

    const handleUpload = async () => {
        if (!broker) {
            setError('Please select a broker type');
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
            await uploadTransactions(files, broker);
            setSuccess(true);
            setFiles([]);
            setBroker('autodetect');
        } catch (err) {
            setError(err.message || 'Failed to upload files');
        } finally {
            setUploading(false);
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
                Upload Transaction Files
            </Typography>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {success && (
                <Alert severity="success" sx={{ mb: 2 }}>
                    Files uploaded successfully!
                </Alert>
            )}

            <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Broker</InputLabel>
                <Select
                    value={broker}
                    label="Broker"
                    onChange={(e) => setBroker(e.target.value)}
                >
                    {BROKER_TYPES.map(({ value, label }) => (
                        <MenuItem key={value} value={value}>
                            {label}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>

            <Paper
                {...getRootProps()}
                sx={{
                    p: 3,
                    textAlign: 'center',
                    backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
                    border: '2px dashed',
                    borderColor: isDragActive ? 'primary.main' : 'divider',
                    cursor: 'pointer'
                }}
            >
                <input {...getInputProps()} />
                <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                <Typography>
                    {isDragActive
                        ? 'Drop the files here'
                        : 'Drag and drop CSV files here, or click to select files'}
                </Typography>
            </Paper>

            {files.length > 0 && (
                <Paper sx={{ mt: 2 }}>
                    <List>
                        {files.map((file, index) => (
                            <ListItem key={index}>
                                <ListItemText
                                    primary={file.name}
                                    secondary={`${(file.size / 1024).toFixed(1)} KB`}
                                />
                                <ListItemSecondaryAction>
                                    <IconButton
                                        edge="end"
                                        onClick={() => handleRemoveFile(index)}
                                    >
                                        <DeleteIcon />
                                    </IconButton>
                                </ListItemSecondaryAction>
                            </ListItem>
                        ))}
                    </List>
                </Paper>
            )}

            <Button
                variant="contained"
                onClick={handleUpload}
                disabled={uploading || files.length === 0 || !broker}
                sx={{ mt: 2 }}
                startIcon={uploading ? <CircularProgress size={20} /> : null}
            >
                {uploading ? 'Uploading...' : 'Upload Files'}
            </Button>
        </Box>
    );
};

export default FileUpload; 