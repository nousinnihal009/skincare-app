/**
 * sw.js — ServiceWorker stub for DermAI skincare routine reminders
 *
 * Scaffolded with SCHEDULE_REMINDER message listener.
 * Full push notification implementation is planned for a future release.
 */

/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'dermai-routine-v1';

// ─── Install ─────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  console.log('[DermAI SW] Installed');
  self.skipWaiting();
});

// ─── Activate ────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  console.log('[DermAI SW] Activated');
  event.waitUntil(self.clients.claim());
});

// ─── Message handler — SCHEDULE_REMINDER ─────────────────────
self.addEventListener('message', (event) => {
  const { type, payload } = event.data || {};

  if (type === 'SCHEDULE_REMINDER') {
    console.log('[DermAI SW] Received SCHEDULE_REMINDER for session:', payload?.sessionId);

    // Future implementation:
    // 1. Store the routine schedule in IndexedDB via the SW context
    // 2. Register a periodic sync (if supported) or use setTimeout
    // 3. Show a push notification at the scheduled times
    // 4. On notification click, open the app to the routine view

    // For now, acknowledge receipt
    if (event.source) {
      event.source.postMessage({
        type: 'REMINDER_SCHEDULED',
        payload: {
          sessionId: payload?.sessionId,
          status: 'pending_implementation',
        },
      });
    }
  }
});

// ─── Fetch handler (pass-through for now) ────────────────────
self.addEventListener('fetch', (event) => {
  // No caching strategy for now — let all requests pass through
  return;
});
