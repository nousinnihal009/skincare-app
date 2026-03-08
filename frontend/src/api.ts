/**
 * api.ts — Centralized API client for SkinCare AI
 */

const API_BASE = 'http://127.0.0.1:8000';

async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API request failed');
  }
  return res.json();
}

// ── Analysis ─────────────────────────────────────────────
export async function analyzeSkin(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return apiRequest('/api/analyze', { method: 'POST', body: formData });
}

// ── Chat ─────────────────────────────────────────────────
export async function sendChatMessage(message: string) {
  return apiRequest('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

// ── Recommendations ──────────────────────────────────────
export async function getSkincareRoutine(condition: string, skinType: string = 'normal') {
  return apiRequest('/api/skincare-routine', {
    method: 'POST',
    body: JSON.stringify({ condition, skin_type: skinType }),
  });
}

export async function getMedicines(condition: string) {
  return apiRequest(`/api/medicines/${encodeURIComponent(condition)}`);
}

export async function checkIngredients(ingredients: string[]) {
  return apiRequest('/api/ingredient-check', {
    method: 'POST',
    body: JSON.stringify({ ingredients }),
  });
}

// ── Doctors ──────────────────────────────────────────────
export async function searchDoctors(params: {
  specialty?: string;
  city?: string;
  telemedicine?: boolean;
} = {}) {
  const query = new URLSearchParams();
  if (params.specialty) query.set('specialty', params.specialty);
  if (params.city) query.set('city', params.city);
  if (params.telemedicine !== undefined) query.set('telemedicine', String(params.telemedicine));
  return apiRequest(`/api/doctors/search?${query.toString()}`);
}

// ── Environment ──────────────────────────────────────────
export async function getEnvironmentRisks(params: {
  uv_index?: number;
  humidity?: number;
  pollution_aqi?: number;
  temperature?: number;
} = {}) {
  const query = new URLSearchParams();
  if (params.uv_index !== undefined) query.set('uv_index', String(params.uv_index));
  if (params.humidity !== undefined) query.set('humidity', String(params.humidity));
  if (params.pollution_aqi !== undefined) query.set('pollution_aqi', String(params.pollution_aqi));
  if (params.temperature !== undefined) query.set('temperature', String(params.temperature));
  return apiRequest(`/api/environment/risks?${query.toString()}`);
}
