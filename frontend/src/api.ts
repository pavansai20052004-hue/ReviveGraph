export const publicDemo = import.meta.env.VITE_PUBLIC_DEMO === '1'

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/v1${path}`, { ...options, signal: options.signal ?? AbortSignal.timeout(15000) })
  } catch {
    throw new Error(publicDemo ? 'Cannot reach the demo server. A free Render server may need about a minute to wake up. Wait, then retry. Hosted data is temporary.' : 'Cannot reach the backend. Start FastAPI on 127.0.0.1:8000, then retry. Existing inventory is kept in SQLite.')
  }
  if (publicDemo && !response.headers.get('content-type')?.includes('application/json')) {
    throw new Error(`The demo server is starting or unavailable (${response.status}). Wait about a minute, then retry.`)
  }
  const payload = await response.json()
  if (!response.ok) {
    const error = payload.error
    throw new Error(error ? `${error.message} (${error.code})` : `Request failed (${response.status}). Retry or check the backend terminal.`)
  }
  return payload as T
}
export function mutationHeaders(key: string = crypto.randomUUID()) {
  return { 'X-Actor-ID': 'local-demo-operator', 'Idempotency-Key': key }
}
export function jsonMutation(body: unknown, key?: string): RequestInit {
  return { method: 'POST', headers: { ...mutationHeaders(key), 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
}
