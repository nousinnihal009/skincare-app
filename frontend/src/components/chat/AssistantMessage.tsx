/**
 * AssistantMessage.tsx — Renders an assistant message with support for:
 * - Markdown text content (via react-markdown + remark-gfm)
 * - ToolCallIndicator (animated status during tool execution)
 * - RoutineCard (structured AM/PM/Weekly skincare routine)
 */

import React, { useState } from 'react';

// ─── Types ───────────────────────────────────────────────────

export interface RoutineStep {
  step: number;
  action: string;
  ingredient_target: string;
  notes: string;
}

export interface RoutinePayload {
  am_routine: RoutineStep[];
  pm_routine: RoutineStep[];
  weekly_treatments: RoutineStep[];
}

export interface ToolCallStatus {
  toolName: string;
  status: 'running' | 'complete' | 'failed';
}

interface AssistantMessageProps {
  content: string;
  toolCalls: ToolCallStatus[];
  routine: RoutinePayload | null;
  isStreaming: boolean;
}

// ─── Tool name humanizer ─────────────────────────────────────

const TOOL_LABELS: Record<string, string> = {
  get_weather_advice: 'Checking your local weather…',
  get_vision_risk_assessment: 'Analyzing your skin image…',
  generate_skincare_routine: 'Creating your personalized routine…',
};

function humanizeToolName(toolName: string): string {
  return TOOL_LABELS[toolName] ?? `Running ${toolName}…`;
}

// ─── ToolCallIndicator ───────────────────────────────────────

const ToolCallIndicator: React.FC<{ tool: ToolCallStatus }> = ({ tool }) => {
  const statusIcons: Record<string, string> = {
    running: '⏳',
    complete: '✅',
    failed: '⚠️',
  };

  return (
    <div
      className={`tool-call-indicator tool-call-indicator--${tool.status}`}
      role="status"
      aria-label={`Tool ${tool.toolName}: ${tool.status}`}
    >
      <span className="tool-call-indicator__icon">
        {statusIcons[tool.status] ?? '⏳'}
      </span>
      <span className="tool-call-indicator__text">
        {tool.status === 'running'
          ? humanizeToolName(tool.toolName)
          : tool.status === 'complete'
            ? humanizeToolName(tool.toolName).replace('…', ' — done')
            : `${humanizeToolName(tool.toolName).replace('…', '')} — failed`}
      </span>
      {tool.status === 'running' && (
        <div className="tool-call-indicator__spinner" aria-hidden="true">
          <div className="spinner-dot" />
          <div className="spinner-dot" />
          <div className="spinner-dot" />
        </div>
      )}
    </div>
  );
};

// ─── RoutineCard ─────────────────────────────────────────────

const RoutineCard: React.FC<{
  routine: RoutinePayload;
  sessionId: string;
}> = ({ routine, sessionId }) => {
  const [activeTab, setActiveTab] = useState<'am' | 'pm' | 'weekly'>('am');

  const tabs = [
    { id: 'am' as const, label: '☀️ AM Routine', data: routine.am_routine },
    { id: 'pm' as const, label: '🌙 PM Routine', data: routine.pm_routine },
    { id: 'weekly' as const, label: '📅 Weekly', data: routine.weekly_treatments },
  ];

  const activeData = tabs.find((t) => t.id === activeTab)?.data ?? [];

  const copyRoutine = async () => {
    const lines: string[] = [];
    tabs.forEach((tab) => {
      lines.push(`\n${tab.label}\n${'─'.repeat(30)}`);
      tab.data.forEach((step) => {
        lines.push(
          `${step.step}. ${step.action}\n   Ingredient: ${step.ingredient_target}\n   Notes: ${step.notes}`
        );
      });
    });
    try {
      await navigator.clipboard.writeText(lines.join('\n'));
    } catch {
      // Clipboard API may fail in some contexts
    }
  };

  const addToReminders = async () => {
    try {
      // Store routine in IndexedDB
      const dbRequest = indexedDB.open('dermai_routines', 1);
      dbRequest.onupgradeneeded = () => {
        const db = dbRequest.result;
        if (!db.objectStoreNames.contains('routines')) {
          db.createObjectStore('routines', { keyPath: 'id' });
        }
      };
      dbRequest.onsuccess = () => {
        const db = dbRequest.result;
        const tx = db.transaction('routines', 'readwrite');
        const store = tx.objectStore('routines');
        store.put({
          id: `dermai:routines:${sessionId}`,
          routine,
          createdAt: new Date().toISOString(),
        });
      };

      // Register service worker and post message
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.register('/sw.js');
        if (registration.active) {
          registration.active.postMessage({
            type: 'SCHEDULE_REMINDER',
            payload: { sessionId, routine },
          });
        }
      }
    } catch (err) {
      console.warn('Reminder registration failed:', err);
    }
  };

  return (
    <div className="routine-card" role="region" aria-label="Skincare routine">
      {/* Tabs */}
      <div className="routine-card__tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`routine-card__tab ${activeTab === tab.id ? 'routine-card__tab--active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Steps */}
      <div className="routine-card__steps" role="tabpanel">
        {activeData.map((step) => (
          <div key={step.step} className="routine-card__step">
            <div className="routine-card__step-num">{step.step}</div>
            <div className="routine-card__step-body">
              <div className="routine-card__step-action">{step.action}</div>
              <span className="routine-card__step-ingredient">
                {step.ingredient_target}
              </span>
              <p className="routine-card__step-notes">{step.notes}</p>
            </div>
          </div>
        ))}
        {activeData.length === 0 && (
          <p className="routine-card__empty">No steps for this section.</p>
        )}
      </div>

      {/* Actions */}
      <div className="routine-card__actions">
        <button
          className="routine-card__btn routine-card__btn--copy"
          onClick={copyRoutine}
          aria-label="Copy routine to clipboard"
        >
          📋 Copy Routine
        </button>
        <button
          className="routine-card__btn routine-card__btn--remind"
          onClick={addToReminders}
          aria-label="Add routine to reminders"
        >
          🔔 Add to Reminders
        </button>
      </div>
    </div>
  );
};

// ─── Simple Markdown Renderer ────────────────────────────────
// Lightweight renderer that handles common markdown patterns
// without requiring react-markdown dependency

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    if (!line.trim()) {
      elements.push(<br key={`br-${i}`} />);
      return;
    }

    // Process inline formatting
    let processed = line
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/^### (.*)$/, '<h4>$1</h4>')
      .replace(/^## (.*)$/, '<h3>$1</h3>')
      .replace(/^# (.*)$/, '<h2>$1</h2>')
      .replace(/^- (.*)$/, '• $1')
      .replace(/^(\d+)\. (.*)$/, '$1. $2');

    elements.push(
      <div key={`line-${i}`} dangerouslySetInnerHTML={{ __html: processed }} />
    );
  });

  return elements;
}

// ─── Main Component ──────────────────────────────────────────

const AssistantMessage: React.FC<AssistantMessageProps> = ({
  content,
  toolCalls,
  routine,
  isStreaming,
}) => {
  // Extract sessionId from context or use empty
  const sessionId = '';

  return (
    <div className="chat-bubble assistant" role="article" aria-label="Assistant message">
      {/* Avatar */}
      <div className="chat-bubble__avatar" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" />
          <path d="M8 12s1.5-4 4-4 4 4 4 4-1.5 4-4 4-4-4-4-4z" />
        </svg>
      </div>

      <div className="chat-bubble__content">
        {/* Tool call indicators */}
        {toolCalls.map((tc, idx) => (
          <ToolCallIndicator key={`${tc.toolName}-${idx}`} tool={tc} />
        ))}

        {/* Text content */}
        {content && (
          <div className="chat-bubble__text">
            {renderMarkdown(content)}
          </div>
        )}

        {/* Streaming cursor */}
        {isStreaming && (
          <span className="streaming-cursor" aria-hidden="true">▊</span>
        )}

        {/* Routine card */}
        {routine && <RoutineCard routine={routine} sessionId={sessionId} />}
      </div>
    </div>
  );
};

export default AssistantMessage;
