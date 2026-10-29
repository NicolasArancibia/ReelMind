export interface Source {
  id: string
  original_url: string
  title: string | null
  platform: string
  status: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface SourcePage { items: Source[]; total: number; active_total: number; trash_total: number; offset: number; limit: number }
export interface Health {
  status: string
  database: string
  processing: { state: string; available: boolean; autostart: boolean; concurrency: number }
}

export class ApiError extends Error {
  status: number
  existingSource?: Source
  constructor(message: string, status: number, existingSource?: Source) {
    super(message)
    this.status = status
    this.existingSource = existingSource
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
    throw new ApiError(typeof body?.detail === 'string' ? body.detail : 'No pudimos completar la solicitud. Inténtalo nuevamente.', response.status, body?.existing_source)
  }
  return response.json() as Promise<T>
}
