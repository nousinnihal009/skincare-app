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
  city?: string;
  lat?: number;
  lon?: number;
  uv_index?: number;
  humidity?: number;
  pollution_aqi?: number;
  temperature?: number;
} = {}) {
  const query = new URLSearchParams();
  if (params.city) query.set('city', params.city);
  if (params.lat !== undefined) query.set('lat', String(params.lat));
  if (params.lon !== undefined) query.set('lon', String(params.lon));
  if (params.uv_index !== undefined) query.set('uv_index', String(params.uv_index));
  if (params.humidity !== undefined) query.set('humidity', String(params.humidity));
  if (params.pollution_aqi !== undefined) query.set('pollution_aqi', String(params.pollution_aqi));
  if (params.temperature !== undefined) query.set('temperature', String(params.temperature));
  return apiRequest(`/api/environment/risks?${query.toString()}`);
}

// ── PDF Report ───────────────────────────────────────────
export async function generatePDFReport(data: any): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/report/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'PDF generation failed');
  }
  return res.blob();
}

// ── Skin Type Detection ──────────────────────────────────
export async function detectSkinType(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return apiRequest('/api/skin-type/detect', { method: 'POST', body: formData });
}

export async function getSkinTypeInfo(skinType: string) {
  return apiRequest(`/api/skin-type/info/${encodeURIComponent(skinType)}`);
}

// ── Aging Prediction ─────────────────────────────────────
export async function predictAging(data: {
  age: number;
  skin_type: string;
  sun_exposure: string;
  smoking: boolean;
  detected_condition?: string;
  uv_index?: number;
  humidity?: number;
}) {
  return apiRequest('/api/aging/predict', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── Auth ─────────────────────────────────────────────────
export async function authRegister(data: {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  skin_type?: string;
  age?: number;
}) {
  return apiRequest('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function authLogin(data: { email: string; password: string }) {
  return apiRequest('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getProfile(token: string) {
  return apiRequest('/api/auth/profile', {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateProfile(token: string, data: {
  full_name?: string;
  skin_type?: string;
  age?: number;
}) {
  return apiRequest('/api/auth/profile', {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(data),
  });
}
