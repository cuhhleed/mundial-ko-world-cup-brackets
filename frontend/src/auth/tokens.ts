export function parseJwtPayload(token: string): Record<string, unknown> {
  const segment = token.split('.')[1]
  const padded = segment + '=='.slice(0, (4 - (segment.length % 4)) % 4)
  const decoded = atob(padded.replace(/-/g, '+').replace(/_/g, '/'))
  return JSON.parse(decoded) as Record<string, unknown>
}

export function isTokenExpired(token: string, bufferSeconds = 300): boolean {
  const payload = parseJwtPayload(token)
  const exp = payload['exp'] as number
  return Date.now() / 1000 + bufferSeconds >= exp
}

export function saveToken(idToken: string): void {
  sessionStorage.setItem('idToken', idToken)
}

export function loadToken(): string | null {
  return sessionStorage.getItem('idToken')
}

export function clearToken(): void {
  sessionStorage.removeItem('idToken')
}
