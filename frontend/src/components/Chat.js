import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Button,
  Stack,
  CircularProgress,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import config from '../config';
import { withErrorHandler, queryDocument, listChats, deleteChat } from '../services/api';
import ChatSidebar from './ChatSidebar';
import ErrorSnackbar from './ErrorSnackbar';
import ScrollToBottom from './ScrollToBottom';

const Chat = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const chatEndRef = useRef(null);
  const chatContainerRef = useRef(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  
  // Load chats on mount
  useEffect(() => {
    loadChats();
  }, []);

  // Set initial chat from location state
  useEffect(() => {
    if (location.state?.chatId) {
      const chat = chats.find(c => c.id === location.state.chatId);
      if (chat) {
        setSelectedChat(chat);
      }
    }
  }, [location.state, chats]);

  const loadChats = async () => {
    try {
      const chatList = await withErrorHandler(listChats);
      setChats(chatList);
      
      // If we have a new upload, select it
      if (location.state?.isNewUpload && chatList.length > 0) {
        setSelectedChat(chatList[0]);
      }
    } catch (error) {
      setError(error.message);
    }
  };

  const handleChatSelect = (chat) => {
    setSelectedChat(chat);
    setTimeout(() => scrollToBottom('auto'), 100);
  };

  const handleChatDelete = async (chatId) => {
    try {
      await withErrorHandler(() => deleteChat(chatId));
      if (selectedChat?.id === chatId) {
        setSelectedChat(null);
      }
      await loadChats();
    } catch (error) {
      setError(error.message);
    }
  };

  const scrollToBottom = (behavior = 'smooth') => {
    chatEndRef.current?.scrollIntoView({ behavior });
  };

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setShowScrollButton(!isNearBottom);
  };

  useEffect(() => {
    const container = chatContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, []);

  useEffect(() => {
    if (!isLoading) {
      scrollToBottom();
    }
  }, [selectedChat?.messages, isLoading]);

  const handleSend = async (question) => {
    if (!selectedChat) {
      setError("Please select a chat first");
      return;
    }
    if (!question.trim() || isLoading) return;

    setInput('');
    setError(null);

    // Immediately add user's message to UI
    const tempMessage = {
      id: Date.now().toString(),
      content: question,
      type: 'question',
      created_at: new Date().toISOString(),
    };
    
    setSelectedChat(prev => ({
      ...prev,
      messages: [...prev.messages, tempMessage]
    }));

    // Show loading state
    setIsLoading(true);

    try {
      const response = await withErrorHandler(async () => {
        return await queryDocument(selectedChat.id, question);
      });

      // Update with the official response
      setSelectedChat(response.chat);
      
      // Update the chat in the list
      setChats(prevChats => 
        prevChats.map(chat => 
          chat.id === response.chat.id ? response.chat : chat
        )
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend(input);
    }
  };

  const handleNewChat = () => {
    navigate('/upload');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex' }}>
      <ChatSidebar
        chats={chats}
        selectedChatId={selectedChat?.id}
        onChatSelect={handleChatSelect}
        onChatDelete={handleChatDelete}
      />
      
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Paper 
          elevation={1} 
          sx={{ 
            p: 2, 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            borderRadius: 0,
            borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
          }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
            {selectedChat ? selectedChat.document_name : 'Select a chat'}
          </Typography>
          <Box>
            <IconButton 
              onClick={handleNewChat} 
              size="small"
              title="New Chat"
            >
              <AddIcon />
            </IconButton>
          </Box>
        </Paper>

        {selectedChat ? (
          <Box 
            ref={chatContainerRef}
            sx={{ 
              flexGrow: 1, 
              overflowY: 'auto', 
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              bgcolor: '#f5f5f5',
              position: 'relative',
            }}
          >
            {selectedChat.messages.map((message, index) => (
              <Box
                key={message.id}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: message.type === 'question' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  alignSelf: message.type === 'question' ? 'flex-end' : 'flex-start',
                }}
              >
                <Paper
                  sx={{
                    p: 2,
                    bgcolor: message.type === 'question' ? 'primary.main' : 'background.paper',
                    color: message.type === 'question' ? 'white' : 'text.primary',
                    borderRadius: 2,
                    boxShadow: 1,
                  }}
                >
                  <Typography>{message.content}</Typography>
                </Paper>
                <Typography
                  variant="caption"
                  sx={{
                    mt: 0.5,
                    color: 'text.secondary',
                    fontSize: '0.75rem',
                  }}
                >
                  {new Date(message.created_at).toLocaleTimeString()}
                </Typography>
              </Box>
            ))}
            {isLoading && (
              <Paper 
                sx={{ 
                  p: 2, 
                  maxWidth: '80%', 
                  alignSelf: 'flex-start',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <CircularProgress size={20} />
                <Typography>Thinking...</Typography>
              </Paper>
            )}
            <div ref={chatEndRef} />
            <ScrollToBottom show={showScrollButton} onClick={() => scrollToBottom()} />
          </Box>
        ) : (
          <Box
            sx={{
              flexGrow: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              bgcolor: '#f5f5f5',
            }}
          >
            <Typography color="text.secondary">
              Select a chat from the sidebar or upload a new document
            </Typography>
          </Box>
        )}

        {/* Suggestion Buttons */}
        <Stack
          direction="row"
          spacing={2}
          sx={{ 
            p: 2, 
            overflowX: 'auto',
            bgcolor: 'background.paper',
            borderTop: '1px solid rgba(0, 0, 0, 0.12)',
          }}
        >
          {config.suggestions.defaultQuestions.map((question, index) => (
            <Button
              key={index}
              variant="outlined"
              onClick={() => handleSend(question)}
              sx={{ 
                whiteSpace: 'nowrap',
                borderRadius: 4,
                textTransform: 'none',
              }}
              disabled={isLoading || !selectedChat}
            >
              {question}
            </Button>
          ))}
        </Stack>

        {/* Input Area */}
        <Paper 
          elevation={3}
          sx={{ 
            p: 2,
            borderRadius: 0,
            bgcolor: 'background.paper',
            borderTop: '1px solid rgba(0, 0, 0, 0.12)',
          }}
        >
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Type your question and press Enter..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            multiline
            maxRows={4}
            disabled={isLoading || !selectedChat}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              },
            }}
          />
        </Paper>

        <ErrorSnackbar
          open={!!error}
          message={error || ''}
          onClose={() => setError(null)}
        />
      </Box>
    </Box>
  );
};

export default Chat;
