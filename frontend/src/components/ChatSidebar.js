import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Divider,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { formatDistanceToNow } from 'date-fns';

const ChatSidebar = ({ 
  chats, 
  selectedChatId, 
  onChatSelect, 
  onChatDelete 
}) => {
  return (
    <Box
      sx={{
        width: 280,
        borderRight: '1px solid rgba(0, 0, 0, 0.12)',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)' }}>
        <Typography variant="h6">Chats</Typography>
      </Box>
      <List sx={{ flexGrow: 1, overflowY: 'auto' }}>
        {chats.map((chat) => (
          <React.Fragment key={chat.id}>
            <ListItem disablePadding>
              <ListItemButton
                selected={selectedChatId === chat.id}
                onClick={() => onChatSelect(chat)}
                sx={{
                  '&.Mui-selected': {
                    bgcolor: 'action.selected',
                  },
                }}
              >
                <ListItemText
                  primary={chat.title}
                  secondary={
                    <Box>
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.secondary"
                        sx={{ display: 'block' }}
                      >
                        {chat.document_name}
                      </Typography>
                      {chat.messages.length > 0 && (
                        <Typography
                          component="span"
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            display: 'block',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            maxWidth: '200px',
                            fontSize: '0.8rem',
                            mt: 0.5,
                          }}
                        >
                          {chat.messages[chat.messages.length - 1]?.content}
                        </Typography>
                      )}
                      <Typography
                        component="span"
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 0.5, display: 'block' }}
                      >
                        {formatDistanceToNow(new Date(chat.updated_at), { addSuffix: true })}
                      </Typography>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    aria-label="delete"
                    onClick={() => onChatDelete(chat.id)}
                    size="small"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItemButton>
            </ListItem>
            <Divider />
          </React.Fragment>
        ))}
        {chats.length === 0 && (
          <ListItem>
            <ListItemText
              secondary="No chats yet"
              sx={{ textAlign: 'center', color: 'text.secondary' }}
            />
          </ListItem>
        )}
      </List>
    </Box>
  );
};

export default ChatSidebar;
