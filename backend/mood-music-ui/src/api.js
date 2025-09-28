// api.js
// Small fetch helpers + typed endpoints to your FastAPI.
// Every function returns JSON from the server.

export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Generic GET wrapper
async function apiGet(path) {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json();
}

// Generic POST wrapper
async function apiPost(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} -> ${res.status} ${text}`);
  }
  return res.json();
}

// Generic DELETE wrapper
async function apiDelete(path) {
  const res = await fetch(`${API_URL}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE ${path} -> ${res.status}`);
  return res.json();
}

// Specific endpoints
export const getRecs     = (mood, limit = 5) => apiGet(`/recommendations?mood=${encodeURIComponent(mood)}&limit=${limit}`);
export const logMood     = (mood, track)     => apiPost("/moods/log", { mood, top_track: track });
export const getRecent   = (limit = 20)      => apiGet(`/moods/recent?limit=${limit}`);
export const addFavorite = (track)           => apiPost("/favorites/add", track);
export const getFavorites= ()                => apiGet("/favorites");
export const deleteFav   = (id)              => apiDelete(`/favorites/${id}`);
export const getStats    = ()                => apiGet("/stats/summary");
