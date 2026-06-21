import { config } from '@/config'

let authToken: string | null = null
let onUnauthorized: (() => Promise<string | null>) | null = null

export function setAuthToken(token: string | null): void {
  authToken = token
}

export function setOnUnauthorized(fn: () => Promise<string | null>): void {
  onUnauthorized = fn
}

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, statusText: string, body: unknown) {
    super(`API error: ${status} ${statusText}`)
    this.status = status
    this.body = body
  }
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
    throw new ApiError(401, 'Unauthorized', null)
  }

  if (!response.ok) {
    const responseBody = await response.json().catch(() => null)
    throw new ApiError(response.status, response.statusText, responseBody)
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
