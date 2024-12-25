import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Paper, CircularProgress } from '@mui/material';
import FolderIcon from '@mui/icons-material/Folder';
import config from '../config';
import { withErrorHandler, uploadDocument, createChat } from '../services/api';
import ErrorSnackbar from './ErrorSnackbar';

const FileUpload = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);

    try {
      // First upload the document
      await withErrorHandler(async () => {
        await uploadDocument(file);
      });

      // Then create a new chat session
      const chatTitle = `Chat about ${file.name}`;
      const chat = await withErrorHandler(async () => {
        return await createChat(chatTitle, file.name);
      });

      // Navigate to chat with the new chat session
      navigate('/chat', { 
        state: { 
          chatId: chat.id,
          isNewUpload: true
        }
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: config.upload.acceptedFileTypes,
    maxSize: config.upload.maxFileSize,
    multiple: false,
  });

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
        position: 'relative',
      }}
    >
      <Paper
        {...getRootProps()}
        sx={{
          width: '100%',
          maxWidth: 600,
          height: 400,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          border: '2px dashed #ccc',
          borderRadius: 2,
          cursor: isLoading ? 'default' : 'pointer',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          '&:hover': {
            bgcolor: isLoading ? 'background.paper' : 'action.hover',
          },
          position: 'relative',
        }}
      >
        <input {...getInputProps()} disabled={isLoading} />
        
        {isLoading ? (
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress sx={{ mb: 2 }} />
            <Typography>Uploading file...</Typography>
          </Box>
        ) : (
          <>
            <FolderIcon sx={{ fontSize: 64, color: 'action.active', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Drop your file here (PDF, Docs)
            </Typography>
            <Typography variant="body2" color="text.secondary">
              or click here to select file
            </Typography>
          </>
        )}
      </Paper>
      
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ mt: 2, maxWidth: 600 }}
      >
        Maximum file size: {config.upload.maxFileSize / (1024 * 1024)}MB
      </Typography>

      <ErrorSnackbar
        open={!!error}
        message={error || ''}
        onClose={() => setError(null)}
      />
    </Box>
  );
};

export default FileUpload;
