/**
 * chatStore.ts — Zustand store for cross-session chat state
 *
 * Manages the global list of sessions and the active session ID.
 * Individual message state is handled via useReducer in ChatPage.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Session {
  id: string;
  title: string;
  createdAt: string;
  messageCount: number;
}

interface ChatStore {
  sessions: Session[];
  activeSessionId: string | null;

  setActiveSession: (id: string) => void;
  addSession: (session: Session) => void;
  removeSession: (id: string) => void;
  updateSessionTitle: (id: string, title: string) => void;
  incrementMessageCount: (id: string) => void;
  clearSessions: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      sessions: [],
      activeSessionId: null,

      setActiveSession: (id: string) =>
        set({ activeSessionId: id }),

      addSession: (session: Session) =>
        set((state) => ({
          sessions: [session, ...state.sessions],
          activeSessionId: session.id,
        })),

      removeSession: (id: string) =>
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== id),
          activeSessionId:
            state.activeSessionId === id
              ? state.sessions.find((s) => s.id !== id)?.id ?? null
              : state.activeSessionId,
        })),

      updateSessionTitle: (id: string, title: string) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, title } : s
          ),
        })),

      incrementMessageCount: (id: string) =>
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, messageCount: s.messageCount + 1 } : s
          ),
        })),

      clearSessions: () =>
        set({ sessions: [], activeSessionId: null }),
    }),
    {
      name: 'dermai-chat-store',
    }
  )
);
