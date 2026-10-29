export interface Source {
  id: string
  original_url: string
  title: string | null
  platform: string
  status: string
  created_at: string
}

export interface SourcePage { items: Source[]; total: number }
export interface Health {
  status: string
  database: string
  processing: { state: string; available: boolean; autostart: boolean; concurrency: number }
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, { ...options, signal: AbortSignal.timeout(10000) })
  } catch {
    throw new ApiError('No pudimos conectar con tu biblioteca local. Comprueba que ReelMind esté iniciado y vuelve a intentarlo.', 0)
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(typeof body?.detail === 'string' ? body.detail : 'No pudimos completar la solicitud. Inténtalo nuevamente.', response.status)
  }
  return response.json() as Promise<T>
}
