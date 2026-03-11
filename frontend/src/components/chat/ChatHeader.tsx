/**
 * ChatHeader.tsx — Session title bar with new/clear controls
 */

import React from 'react';

interface ChatHeaderProps {
  sessionTitle: string;
  onNewChat: () => void;
  onClearChat: () => void;
  isStreaming: boolean;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  sessionTitle,
  onNewChat,
  onClearChat,
  isStreaming,
}) => {
  return (
    <div className="chat-header" role="banner">
      <div className="chat-header__left">
        <div className="chat-header__icon" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
            <path d="M8 12s1.5-4 4-4 4 4 4 4-1.5 4-4 4-4-4-4-4z" />
          </svg>
        </div>
        <div className="chat-header__info">
          <h1 className="chat-header__title">Derm AI Assistant</h1>
          <p className="chat-header__subtitle">
            {sessionTitle || 'New Conversation'}
          </p>
        </div>
      </div>
      <div className="chat-header__actions">
        <button
          className="chat-header__btn chat-header__btn--new"
          onClick={onNewChat}
          disabled={isStreaming}
          aria-label="Start new chat"
          title="New chat"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>New Chat</span>
        </button>
        <button
          className="chat-header__btn chat-header__btn--clear"
          onClick={onClearChat}
          disabled={isStreaming}
          aria-label="Clear conversation"
          title="Clear chat"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
            <path d="M10 11v6" />
            <path d="M14 11v6" />
          </svg>
          <span>Clear</span>
        </button>
      </div>
    </div>
  );
};

export default ChatHeader;
