const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export async function fetchAPI(endpoint: string, options?: RequestInit) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  })

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`)
  }

  return res.json()
}

export const api = {
  // Public (no auth)
  calculateRisk: (data: any) => fetchAPI('/api/v1/public/cost-calculator', { method: 'POST', body: JSON.stringify(data) }),
  chat: (message: string) => fetchAPI(`/api/v1/public/chat?message=${encodeURIComponent(message)}`, { method: 'POST' }),

  // Auth
  login: (email: string, password: string, tenant: string) => fetchAPI('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password, tenant_slug: tenant }) }),

  // Protected
  getSchedule: (start: string, end: string) => fetchAPI(`/api/v1/schedule?start_date=${start}&end_date=${end}`),
  checkCompliance: () => fetchAPI('/api/v1/schedule/check-compliance', { method: 'POST' }),
  getHoursDashboard: () => fetchAPI('/api/v1/hours/dashboard'),
  findCoverage: (data: any) => fetchAPI('/api/v1/coverage/find', { method: 'POST', body: JSON.stringify(data) }),
  getFairnessReport: () => fetchAPI('/api/v1/coverage/fairness-report'),
  getLeaveBalances: (empId: string) => fetchAPI(`/api/v1/leave/balances/${empId}`),
  requestTimeOff: (data: any) => fetchAPI('/api/v1/requests/time-off', { method: 'POST', body: JSON.stringify(data) }),
  getAlerts: () => fetchAPI('/api/v1/alerts'),
  getQueueSummary: () => fetchAPI('/api/v1/queue/summary'),
}
