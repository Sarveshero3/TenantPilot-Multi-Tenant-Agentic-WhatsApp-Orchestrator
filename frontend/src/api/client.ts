import type {
  BroadcastRequest,
  BroadcastResponse,
  ChatSession,
  HealthResponse,
  MessageLog,
  Tenant,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    let message = `Request failed with ${response.status}`
    try {
      const body = await response.json()
      message = body.detail ?? body.message ?? message
    } catch {
      // Keep the generic status message when the backend returns non-JSON.
    }
    throw new ApiError(message, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const api = {
  health: () => request<HealthResponse>('/health'),
  listTenants: () => request<Tenant[]>('/api/tenants'),
  getTenant: (tenantId: string) => request<Tenant>(`/api/tenants/${tenantId}`),
  listSessions: (tenantId: string) =>
    request<ChatSession[]>(`/api/sessions?tenant_id=${encodeURIComponent(tenantId)}`),
  getMessages: (sessionId: string) =>
    request<MessageLog[]>(`/api/sessions/${encodeURIComponent(sessionId)}/messages`),
  broadcast: (body: BroadcastRequest) =>
    request<BroadcastResponse>('/api/broadcast', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}

export { ApiError, API_BASE_URL }
