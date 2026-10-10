// FloodGuard API client. Response shapes follow docs/API_CONTRACT.md.
// With VITE_USE_MOCKS=true, calls return simulated data from src/mocks instead.

import wardsJson from '../mocks/wards.json'
import { mockReports, mockRisk, mockWeather } from '../mocks/simulated'
import type {
  CreatedReport,
  NewReport,
  Report,
  ReportFilters,
  ReportStatus,
  RiskResponse,
  Weather,
  WardsResponse,
} from '../types'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')
export const USE_MOCKS = (import.meta.env.VITE_USE_MOCKS ?? 'true') !== 'false'

const MOCK_LATENCY_MS = 300
const REQUEST_TIMEOUT_MS = 15000

export class ApiError extends Error {
  code: string
  status: number | null
  requestId?: string

  constructor(code: string, message: string, status: number | null, requestId?: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.requestId = requestId
  }
}

// Reads the contract's { error: { code, message }, request_id } shape, falling back to
// FastAPI's default { detail } shape, which the current backend still returns.
async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    // Non-JSON error body; use the status text below.
  }
  const obj = (body ?? {}) as Record<string, unknown>
  const err = obj.error as { code?: string; message?: string } | undefined
  if (err?.message) {
    return new ApiError(err.code ?? 'API_ERROR', err.message, response.status, obj.request_id as string | undefined)
  }
  // FastAPI's generic 404/405 means the route itself does not exist yet.
  const routeMissing = obj.detail === undefined || obj.detail === 'Not Found' || obj.detail === 'Method Not Allowed'
  if ((response.status === 404 || response.status === 405) && routeMissing) {
    return new ApiError('NOT_AVAILABLE', 'This feature is not available on the API yet.', response.status)
  }
  if (typeof obj.detail === 'string') {
    return new ApiError(`HTTP_${response.status}`, obj.detail, response.status)
  }
  if (response.status === 404 || response.status === 405) {
    return new ApiError('NOT_AVAILABLE', 'This feature is not available on the API yet.', response.status)
  }
  return new ApiError(`HTTP_${response.status}`, `The API returned an error (${response.status}).`, response.status)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...(init?.body ? { 'Content-Type': 'application/json' } : {}) },
      signal: controller.signal,
    })
  } catch {
    if (controller.signal.aborted) {
      throw new ApiError('TIMEOUT', 'The API took too long to respond.', null)
    }
    const offline = typeof navigator !== 'undefined' && !navigator.onLine
    throw new ApiError(
      offline ? 'OFFLINE' : 'NETWORK_ERROR',
      offline ? 'You appear to be offline.' : 'Could not reach the FloodGuard API.',
      null,
    )
  } finally {
    clearTimeout(timer)
  }
  if (!response.ok) throw await toApiError(response)
  return (await response.json()) as T
}

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(structuredClone(value)), MOCK_LATENCY_MS))
}

// In-memory report store for mock mode; resets on page reload.
let mockReportStore: Report[] | null = null
function reportStore(): Report[] {
  if (!mockReportStore) mockReportStore = mockReports()
  return mockReportStore
}

export async function getHealth(): Promise<{ status: string; service: string }> {
  if (USE_MOCKS) return delay({ status: 'ok', service: 'floodguard-api (mock)' })
  return request('/health')
}

export async function getWards(): Promise<WardsResponse> {
  if (USE_MOCKS) return delay(wardsJson as WardsResponse)
  return request('/wards')
}

export async function getWeather(): Promise<Weather> {
  if (USE_MOCKS) return delay(mockWeather())
  const body = await request<{ data: Weather }>('/weather')
  return body.data
}

export async function getRisk(wardCode?: string): Promise<RiskResponse> {
  if (USE_MOCKS) {
    const risk = mockRisk()
    if (wardCode) risk.data = risk.data.filter((r) => r.ward_code === wardCode)
    return delay(risk)
  }
  const query = wardCode ? `?ward_code=${encodeURIComponent(wardCode)}` : ''
  return request(`/risk${query}`)
}

export async function getReports(filters: ReportFilters = {}): Promise<Report[]> {
  if (USE_MOCKS) {
    let reports = [...reportStore()].sort((a, b) => b.reported_at.localeCompare(a.reported_at))
    if (filters.status) reports = reports.filter((r) => r.status === filters.status)
    if (filters.ward_code) reports = reports.filter((r) => r.ward_code === filters.ward_code)
    if (filters.limit) reports = reports.slice(0, filters.limit)
    return delay(reports)
  }
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.ward_code) params.set('ward_code', filters.ward_code)
  if (filters.limit) params.set('limit', String(filters.limit))
  const query = params.toString() ? `?${params}` : ''
  const body = await request<{ data: Report[] }>(`/reports${query}`)
  return body.data
}

export async function createReport(report: NewReport): Promise<CreatedReport> {
  if (USE_MOCKS) {
    const created: Report = {
      report_id: `sim-${Date.now().toString(36)}`,
      ward_code: report.ward_code ?? null,
      latitude: report.latitude,
      longitude: report.longitude,
      category: report.category,
      description: report.description ?? null,
      status: 'new',
      verification_status: 'unverified',
      reported_at: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
      is_simulated: true,
    }
    reportStore().push(created)
    const { report_id, status, verification_status, reported_at, is_simulated } = created
    return delay({ report_id, status, verification_status, reported_at, is_simulated })
  }
  const body = await request<{ data: CreatedReport }>('/reports', {
    method: 'POST',
    body: JSON.stringify(report),
  })
  return body.data
}

export async function updateReportStatus(reportId: string, status: ReportStatus): Promise<Report> {
  if (USE_MOCKS) {
    const report = reportStore().find((r) => r.report_id === reportId)
    if (!report) throw new ApiError('NOT_FOUND', 'Report not found.', 404)
    report.status = status
    return delay(report)
  }
  const body = await request<{ data: Report }>(`/reports/${encodeURIComponent(reportId)}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
  return body.data
}
