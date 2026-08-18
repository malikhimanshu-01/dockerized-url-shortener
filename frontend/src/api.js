// Relative ('') is correct in every real run mode: nginx serves both under one origin in
// prod, and Vite's own dev-server proxy (vite.config.js) forwards the same relative paths
// when running `npm run dev`. config.js (prod) may set this to '' explicitly; ?? still
// falls through to '' when it's undefined (dev, no config.js present at all).
const API_BASE_URL = window.__API_BASE_URL__ ?? ''

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const listLinks = () => request('/api/links')

export const createLink = (payload) =>
  request('/api/links', { method: 'POST', body: JSON.stringify(payload) })

export const deleteLink = (shortCode) =>
  request(`/api/links/${shortCode}`, { method: 'DELETE' })

export const topLinks = (limit = 10) => request(`/api/analytics/top-links?limit=${limit}`)

export const clicksOverTime = (days = 7) => request(`/api/analytics/clicks-over-time?days=${days}`)

export { API_BASE_URL }
