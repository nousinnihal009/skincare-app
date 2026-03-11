/**
 * MessageList.tsx — Virtualized message list with auto-scroll behavior
 *
 * Auto-scrolls to bottom on new messages, but pauses auto-scroll
 * if the user has manually scrolled up.
 */

import React, { useRef, useEffect, useCallback } from 'react';
import AssistantMessage, {
  RoutinePayload,
  ToolCallStatus,
} from './AssistantMessage';

// ─── Types ───────────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  toolCalls?: ToolCallStatus[];
  routine?: RoutinePayload | null;
  isStreaming?: boolean;
}

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

// ─── UserMessage ─────────────────────────────────────────────

const UserMessage: React.FC<{ content: string }> = ({ content }) => (
  <div className="chat-bubble user" role="article" aria-label="Your message">
    <div className="chat-bubble__content">
      <div className="chat-bubble__text">{content}</div>
    </div>
  </div>
);

// ─── TypingIndicator ─────────────────────────────────────────

const TypingIndicator: React.FC = () => (
  <div
    className="chat-bubble assistant typing-indicator"
    role="status"
    aria-label="Assistant is typing"
  >
    <div className="chat-bubble__avatar" aria-hidden="true">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
        <path d="M8 12s1.5-4 4-4 4 4 4 4-1.5 4-4 4-4-4-4-4z" />
      </svg>
    </div>
    <div className="typing-dots">
      <div className="typing-dot" style={{ animationDelay: '0ms' }} />
      <div className="typing-dot" style={{ animationDelay: '200ms' }} />
      <div className="typing-dot" style={{ animationDelay: '400ms' }} />
    </div>
  </div>
);

// ─── MessageList ─────────────────────────────────────────────

const MessageList: React.FC<MessageListProps> = ({ messages, isStreaming }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const userScrolledUpRef = useRef(false);

  // Detect manual scroll up
  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    // If user is more than 100px from bottom, they've scrolled up
    userScrolledUpRef.current = distanceFromBottom > 100;
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (!userScrolledUpRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming]);

  // Show initial typing indicator only when streaming starts and no content yet
  const lastMessage = messages[messages.length - 1];
  const showTypingIndicator =
    isStreaming && (!lastMessage || lastMessage.role !== 'assistant' || !lastMessage.content);

  return (
    <div
      className="chat-messages"
      ref={containerRef}
      onScroll={handleScroll}
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
    >
      {messages.map((msg) => {
        if (msg.role === 'user') {
          return <UserMessage key={msg.id} content={msg.content} />;
        }
        return (
          <AssistantMessage
            key={msg.id}
            content={msg.content}
            toolCalls={msg.toolCalls ?? []}
            routine={msg.routine ?? null}
            isStreaming={msg.isStreaming ?? false}
          />
        );
      })}

      {showTypingIndicator && <TypingIndicator />}

      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
