import React from 'react';
import { Fab } from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';

const ScrollToBottom = ({ onClick, show }) => {
  if (!show) return null;

  return (
    <Fab
      size="small"
      color="primary"
      aria-label="scroll to bottom"
      onClick={onClick}
      sx={{
        position: 'absolute',
        right: 16,
        bottom: 16,
        opacity: 0.8,
        '&:hover': {
          opacity: 1,
        },
      }}
    >
      <KeyboardArrowDownIcon />
    </Fab>
  );
};

export default ScrollToBottom;
