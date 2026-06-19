import { config } from '@/config'

let authToken: string | null = null
let onUnauthorized: (() => Promise<string | null>) | null = null

export function setAuthToken(token: string | null): void {
  authToken = token
}

export function setOnUnauthorized(fn: () => Promise<string | null>): void {
  onUnauthorized = fn
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const url = `${config.apiUrl}${path}`
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (response.status === 401 && onUnauthorized) {
    // No refresh token (ADR-004b): notify the auth context to clear state and
    // re-prompt Google Sign-In. The caller will receive a thrown error.
    await onUnauthorized()
    throw new Error('API error: 401 Unauthorized')
  }

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>('GET', path)
  },
  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>('POST', path, body)
  },
  put<T>(path: string, body: unknown): Promise<T> {
    return request<T>('PUT', path, body)
  },
  patch<T>(path: string, body: unknown): Promise<T> {
    return request<T>('PATCH', path, body)
  },
  delete<T>(path: string): Promise<T> {
    return request<T>('DELETE', path)
  },
}
