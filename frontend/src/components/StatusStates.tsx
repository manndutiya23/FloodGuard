import { useEffect, useState } from 'react'
import { ApiError } from '../services/api'

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 p-4 text-sm text-muted">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-accent" aria-hidden="true" />
      {label}
    </div>
  )
}

export function ErrorState({
  error,
  onRetry,
  what,
  title,
}: {
  error: Error
  onRetry?: () => void
  what: string
  title?: string
}) {
  const notAvailable = error instanceof ApiError && error.code === 'NOT_AVAILABLE'
  return (
    <div role="alert" className="rounded-lg border border-warn-line bg-warn-bg p-4 text-sm text-warn-ink">
      <p className="m-0 font-semibold">{title ?? (notAvailable ? `Not available on the API yet: ${what}.` : `Could not load ${what}.`)}</p>
      <p className="m-0 mt-1">
        {notAvailable ? 'The backend does not provide this endpoint yet. Mock mode (VITE_USE_MOCKS=true) shows simulated data.' : error.message}
      </p>
      {error instanceof ApiError && error.requestId && (
        <p className="m-0 mt-1 font-mono text-xs">Request ID: {error.requestId}</p>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 min-h-10 rounded-md border border-warn-ink bg-white px-3 font-semibold text-warn-ink hover:bg-warn-bg"
        >
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border border-dashed border-line p-4 text-sm text-muted">{children}</div>
}

export function StaleNotice({ children }: { children: React.ReactNode }) {
  return (
    <div role="status" className="rounded-md bg-moderate-bg px-3 py-2 text-sm text-moderate-ink">
      {children}
    </div>
  )
}

export function OfflineBanner() {
  const [online, setOnline] = useState(() => navigator.onLine)
  useEffect(() => {
    const up = () => setOnline(true)
    const down = () => setOnline(false)
    window.addEventListener('online', up)
    window.addEventListener('offline', down)
    return () => {
      window.removeEventListener('online', up)
      window.removeEventListener('offline', down)
    }
  }, [])
  if (online) return null
  return (
    <div role="alert" className="bg-high px-6 py-2 text-center text-sm font-semibold text-white">
      You are offline. Data shown may be out of date, and reports cannot be sent until you reconnect.
    </div>
  )
}
