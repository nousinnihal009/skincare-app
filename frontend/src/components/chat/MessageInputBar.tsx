/**
 * MessageInputBar.tsx — Textarea input with send button and optional attachments
 *
 * Supports:
 * - Shift+Enter for newlines, Enter to submit
 * - Disabled state during streaming
 * - Optional location and image attachment triggers
 */

import React, { useRef, useEffect } from 'react';

interface MessageInputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onAttachLocation: () => void;
  onAttachImage: () => void;
  isStreaming: boolean;
  hasLocation: boolean;
}

const MessageInputBar: React.FC<MessageInputBarProps> = ({
  value,
  onChange,
  onSubmit,
  onAttachLocation,
  onAttachImage,
  isStreaming,
  hasLocation,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isStreaming) {
        onSubmit();
      }
    }
  };

  const canSend = value.trim().length > 0 && !isStreaming;

  return (
    <div className="chat-input-area" role="form" aria-label="Message input">
      {/* Attachment buttons */}
      <div className="chat-input-area__attachments">
        <button
          className={`chat-input-area__attach-btn ${hasLocation ? 'chat-input-area__attach-btn--active' : ''}`}
          onClick={onAttachLocation}
          disabled={isStreaming}
          aria-label={hasLocation ? 'Location attached' : 'Share location'}
          title={hasLocation ? 'Location attached' : 'Share location for weather-aware advice'}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
        </button>
        <button
          className="chat-input-area__attach-btn"
          onClick={onAttachImage}
          disabled={isStreaming}
          aria-label="Attach image"
          title="Attach image for analysis"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
        </button>
      </div>

      {/* Textarea */}
      <textarea
        ref={textareaRef}
        className="chat-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask Derm about skin conditions, routines, ingredients…"
        disabled={isStreaming}
        rows={1}
        id="chat-input"
        aria-label="Type your message"
      />

      {/* Send button */}
      <button
        className="chat-send-btn"
        onClick={onSubmit}
        disabled={!canSend}
        id="chat-send"
        aria-label="Send message"
      >
        {isStreaming ? (
          <div className="chat-send-btn__spinner" aria-label="Sending">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" strokeDasharray="60" strokeDashoffset="15" />
            </svg>
          </div>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        )}
      </button>
    </div>
  );
};

export default MessageInputBar;
