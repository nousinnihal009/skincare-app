/**
 * ChatPage.tsx — Root chat page component
 *
 * Orchestrates all sub-components and manages:
 * - SSE stream connection via Fetch API ReadableStream
 * - Local useReducer for active message stream state
 * - Zustand store for cross-session state
 * - Geolocation for weather-aware advice
 */

import React, { useReducer, useState, useCallback, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import ChatHeader from './chat/ChatHeader';
import MessageList, { ChatMessage } from './chat/MessageList';
import SuggestionChips from './chat/SuggestionChips';
import MessageInputBar from './chat/MessageInputBar';
import { useChatStore } from '../store/chatStore';
import { ToolCallStatus, RoutinePayload } from './chat/AssistantMessage';

// ─── Constants ───────────────────────────────────────────────

const API_BASE = 'http://127.0.0.1:8000';

function generateSessionId(): string {
  return crypto.randomUUID();
}

function getAuthToken(): string | null {
  try {
    const raw = localStorage.getItem('dermaiToken');
    return raw;
  } catch {
    return null;
  }
}

// ─── SSE Event Types ─────────────────────────────────────────

interface SSETextDelta {
  type: 'text_delta';
  content: string;
}

interface SSEToolCall {
  type: 'tool_call';
  tool_name: string;
  status: 'running' | 'complete' | 'failed';
}

interface SSEStructuredRoutine {
  type: 'structured_routine';
  payload: RoutinePayload;
}

interface SSESuggestionChips {
  type: 'suggestion_chips';
  chips: string[];
}

interface SSEDone {
  type: 'done';
}

interface SSEError {
  type: 'error';
  message: string;
}

type SSEEvent =
  | SSETextDelta
  | SSEToolCall
  | SSEStructuredRoutine
  | SSESuggestionChips
  | SSEDone
  | SSEError;

// ─── Reducer ─────────────────────────────────────────────────

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  chips: string[];
  error: string | null;
  currentToolCalls: ToolCallStatus[];
  currentRoutine: RoutinePayload | null;
}

type ChatAction =
  | { type: 'ADD_USER_MESSAGE'; payload: ChatMessage }
  | { type: 'START_STREAMING' }
  | { type: 'APPEND_DELTA'; payload: string }
  | { type: 'SET_TOOL_CALL'; payload: ToolCallStatus }
  | { type: 'SET_ROUTINE'; payload: RoutinePayload }
  | { type: 'SET_CHIPS'; payload: string[] }
  | { type: 'FINISH_STREAMING' }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'LOAD_HISTORY'; payload: ChatMessage[] }
  | { type: 'RESET' };

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_USER_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
        chips: [],
        error: null,
      };

    case 'START_STREAMING': {
      const streamingMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        toolCalls: [],
        routine: null,
        isStreaming: true,
      };
      return {
        ...state,
        isStreaming: true,
        messages: [...state.messages, streamingMsg],
        currentToolCalls: [],
        currentRoutine: null,
        error: null,
      };
    }

    case 'APPEND_DELTA': {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = {
          ...last,
          content: last.content + action.payload,
        };
      }
      return { ...state, messages: msgs };
    }

    case 'SET_TOOL_CALL': {
      const updated = [...state.currentToolCalls];
      const existingIdx = updated.findIndex(
        (tc) => tc.toolName === action.payload.toolName
      );
      if (existingIdx >= 0) {
        updated[existingIdx] = action.payload;
      } else {
        updated.push(action.payload);
      }

      // Also update the last assistant message
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, toolCalls: [...updated] };
      }

      return { ...state, currentToolCalls: updated, messages: msgs };
    }

    case 'SET_ROUTINE': {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, routine: action.payload };
      }
      return { ...state, currentRoutine: action.payload, messages: msgs };
    }

    case 'SET_CHIPS':
      return { ...state, chips: action.payload };

    case 'FINISH_STREAMING': {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, isStreaming: false };
      }
      return { ...state, isStreaming: false, messages: msgs };
    }

    case 'SET_ERROR': {
      const msgs = [...state.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = {
          ...last,
          content: last.content || action.payload,
          isStreaming: false,
        };
      }
      return {
        ...state,
        isStreaming: false,
        error: action.payload,
        messages: msgs,
      };
    }

    case 'LOAD_HISTORY':
      return { ...state, messages: action.payload };

    case 'RESET':
      return initialChatState;

    default:
      return state;
  }
}

const initialChatState: ChatState = {
  messages: [],
  isStreaming: false,
  chips: [],
  error: null,
  currentToolCalls: [],
  currentRoutine: null,
};

// ─── SSE Parser ──────────────────────────────────────────────

async function parseSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  dispatch: React.Dispatch<ChatAction>
): Promise<void> {
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data: ')) continue;

      const jsonStr = trimmed.slice(6);
      let event: SSEEvent;
      try {
        event = JSON.parse(jsonStr) as SSEEvent;
      } catch {
        continue;
      }

      switch (event.type) {
        case 'text_delta':
          dispatch({ type: 'APPEND_DELTA', payload: event.content });
          break;
        case 'tool_call':
          dispatch({
            type: 'SET_TOOL_CALL',
            payload: { toolName: event.tool_name, status: event.status },
          });
          break;
        case 'structured_routine':
          dispatch({ type: 'SET_ROUTINE', payload: event.payload });
          break;
        case 'suggestion_chips':
          dispatch({ type: 'SET_CHIPS', payload: event.chips });
          break;
        case 'done':
          dispatch({ type: 'FINISH_STREAMING' });
          break;
        case 'error':
          dispatch({ type: 'SET_ERROR', payload: event.message });
          break;
      }
    }
  }
}

// ─── ChatPage Component ─────────────────────────────────────

const ChatPage: React.FC = () => {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);
  const [inputValue, setInputValue] = useState('');
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const {
    sessions: localSessions,
    activeSessionId,
    addSession,
    removeSession,
    incrementMessageCount,
  } = useChatStore();

  // Ensure we always have a session
  const sessionIdRef = useRef<string>(activeSessionId ?? generateSessionId());

  useEffect(() => {
    if (!activeSessionId) {
      const newId = generateSessionId();
      sessionIdRef.current = newId;
      addSession({
        id: newId,
        title: 'New Conversation',
        createdAt: new Date().toISOString(),
        messageCount: 0,
      });
    } else {
      sessionIdRef.current = activeSessionId;
    }
  }, [activeSessionId, addSession]);

  // ─── React Query: Fetch history on session load (FIX 5) ───

  const { data: history } = useQuery({
    queryKey: ['chat-history', activeSessionId],
    queryFn: async () => {
      const token = getAuthToken();
      if (!token) return [];
      const r = await fetch(`${API_BASE}/api/chat/history/${activeSessionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) return [];
      return r.json();
    },
    enabled: !!activeSessionId,
    staleTime: Infinity,
  });

  // Seed useReducer message state with resolved history
  const historyLoadedRef = useRef<string | null>(null);
  useEffect(() => {
    if (
      history &&
      Array.isArray(history) &&
      activeSessionId &&
      historyLoadedRef.current !== activeSessionId
    ) {
      historyLoadedRef.current = activeSessionId;
      const msgs: ChatMessage[] = history
        .filter((m: { role: string }) => m.role !== 'system')
        .map((m: { role: string; content: string }, i: number) => ({
          id: `history-${i}`,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: new Date().toISOString(),
        }));
      if (msgs.length > 0) {
        dispatch({ type: 'LOAD_HISTORY', payload: msgs });
      }
    }
  }, [history, activeSessionId]);

  // ─── React Query: Fetch sessions list (FIX 5) ────────────

  const { data: serverSessions } = useQuery<string[]>({
    queryKey: ['chat-sessions'],
    queryFn: async () => {
      const token = getAuthToken();
      if (!token) return [];
      const r = await fetch(`${API_BASE}/api/chat/sessions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) return [];
      return r.json();
    },
    staleTime: 30000,
  });

  // Merge server sessions with local sessions
  const safeServerSessions = Array.isArray(serverSessions) ? serverSessions : [];
  const sessions = localSessions.length > 0 ? localSessions : safeServerSessions.map((id: string) => ({
    id,
    title: 'Conversation',
    createdAt: '',
    messageCount: 0,
  }));

  // ─── Send message ────────────────────────────────────────

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || state.isStreaming) return;

      const token = getAuthToken();
      if (!token) {
        dispatch({
          type: 'SET_ERROR',
          payload: 'Please log in to use the AI assistant.',
        });
        return;
      }

      const sessionId = sessionIdRef.current;

      // Optimistic UI — add user message immediately
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      };
      dispatch({ type: 'ADD_USER_MESSAGE', payload: userMsg });
      dispatch({ type: 'START_STREAMING' });
      incrementMessageCount(sessionId);
      setInputValue('');

      // Build request body
      const body: Record<string, unknown> = {
        session_id: sessionId,
        message: trimmed,
      };
      if (location) {
        body.location = { lat: location.lat, lon: location.lon };
      }

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const resp = await fetch(`${API_BASE}/api/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        if (resp.status === 429) {
          dispatch({
            type: 'SET_ERROR',
            payload: 'You\'re sending messages too quickly. Please wait a moment.',
          });
          return;
        }

        if (!resp.ok) {
          dispatch({
            type: 'SET_ERROR',
            payload: 'Failed to connect to the AI assistant. Please try again.',
          });
          return;
        }

        if (!resp.body) {
          dispatch({ type: 'SET_ERROR', payload: 'No response received.' });
          return;
        }

        const reader = resp.body.getReader();
        await parseSSEStream(reader, dispatch);
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          dispatch({ type: 'FINISH_STREAMING' });
        } else {
          dispatch({
            type: 'SET_ERROR',
            payload: 'Connection lost. Please try again.',
          });
        }
      } finally {
        abortRef.current = null;
      }
    },
    [state.isStreaming, location, incrementMessageCount]
  );

  // ─── Handlers ────────────────────────────────────────────

  const handleSubmit = useCallback(() => {
    sendMessage(inputValue);
  }, [inputValue, sendMessage]);

  const handleChipClick = useCallback(
    (text: string) => {
      sendMessage(text);
    },
    [sendMessage]
  );

  const handleNewChat = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    dispatch({ type: 'RESET' });
    const newId = generateSessionId();
    sessionIdRef.current = newId;
    addSession({
      id: newId,
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      messageCount: 0,
    });
  }, [addSession]);

  const handleClearChat = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort();
    const sessionId = sessionIdRef.current;
    dispatch({ type: 'RESET' });

    const token = getAuthToken();
    if (token) {
      try {
        await fetch(`${API_BASE}/api/chat/session/${sessionId}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        // Silent fail — session cleanup is best-effort
      }
    }
    removeSession(sessionId);
    handleNewChat();
  }, [removeSession, handleNewChat]);

  const handleAttachLocation = useCallback(() => {
    if (location) {
      setLocation(null);
      return;
    }
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLocation({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
          });
        },
        () => {
          console.warn('Geolocation permission denied');
        }
      );
    }
  }, [location]);

  const handleAttachImage = useCallback(() => {
    // Image attachment is handled via the existing analysis flow.
    // For now we show a message directing users to the Analyze page.
    const infoMsg: ChatMessage = {
      id: `system-${Date.now()}`,
      role: 'assistant',
      content:
        '📷 To analyze a skin image, please use the **Analyze** page first. Once your image is analyzed, you can reference it here and I\'ll factor in the results!',
      timestamp: new Date().toISOString(),
    };
    dispatch({ type: 'ADD_USER_MESSAGE', payload: infoMsg });
  }, []);

  // ─── Welcome message on empty state ──────────────────────

  const showWelcome = state.messages.length === 0;

  return (
    <div className="page-container chat-page" style={{ paddingBottom: '0' }}>
      <div className="chat-container">
        <ChatHeader
          sessionTitle={
            sessions.find((s: { id: string }) => s.id === sessionIdRef.current)?.title ??
            'New Conversation'
          }
          onNewChat={handleNewChat}
          onClearChat={handleClearChat}
          isStreaming={state.isStreaming}
        />

        {showWelcome && (
          <div className="chat-welcome">
            <div className="chat-welcome__icon" aria-hidden="true">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#chat-grad)" strokeWidth="1.5" strokeLinecap="round">
                <defs>
                  <linearGradient id="chat-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#06b6d4" />
                  </linearGradient>
                </defs>
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
                <path d="M8 12s1.5-4 4-4 4 4 4 4-1.5 4-4 4-4-4-4-4z" />
              </svg>
            </div>
            <h2 className="chat-welcome__title">Hi, I'm Derm! 👋</h2>
            <p className="chat-welcome__text">
              Your AI dermatologist and skincare coach. Ask me about skin conditions,
              treatments, routines, or share your concerns — I'm here to help.
            </p>
            <div className="chat-welcome__starters">
              {[
                'What skincare routine should I follow?',
                'Tell me about treating acne',
                'Is this mole something to worry about?',
                'Help me with dry, sensitive skin',
              ].map((q) => (
                <button
                  key={q}
                  className="chat-welcome__starter"
                  onClick={() => sendMessage(q)}
                  disabled={state.isStreaming}
                  aria-label={`Ask: ${q}`}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <MessageList
          messages={state.messages}
          isStreaming={state.isStreaming}
        />

        <SuggestionChips
          chips={state.chips}
          onChipClick={handleChipClick}
          disabled={state.isStreaming}
        />

        {state.error && (
          <div className="chat-error-message" role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{state.error}</span>
          </div>
        )}

        <MessageInputBar
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          onAttachLocation={handleAttachLocation}
          onAttachImage={handleAttachImage}
          isStreaming={state.isStreaming}
          hasLocation={!!location}
        />
      </div>
    </div>
  );
};

export default ChatPage;
