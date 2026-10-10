import type { DataStatus, RiskLevel, VerificationStatus } from '../types'
import { capitalize } from '../lib/format'

export function SimulatedBadge({ label = 'Simulated' }: { label?: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-dashed border-sim px-2.5 py-0.5 text-xs font-semibold text-sim">
      {label}
    </span>
  )
}

const LEVEL_STYLES: Record<RiskLevel, string> = {
  low: 'bg-exp-1 text-accent-dark',
  moderate: 'bg-moderate-bg text-moderate-ink',
  high: 'bg-high text-white',
  unknown: 'bg-unknown-bg text-unknown-ink',
}

export function RiskLevelBadge({ level }: { level: RiskLevel }) {
  return (
    <span className={`inline-flex rounded-md px-3 py-1 text-sm font-semibold ${LEVEL_STYLES[level]}`}>
      {capitalize(level)}
    </span>
  )
}

export function VerificationBadge({ status }: { status: VerificationStatus }) {
  return status === 'verified' ? (
    <span className="rounded bg-exp-1 px-2 py-0.5 text-[13px] font-semibold text-accent-dark">Verified</span>
  ) : (
    <span className="rounded bg-unknown-bg px-2 py-0.5 text-[13px] text-unknown-ink">Unverified</span>
  )
}

export function DataStatusChip({ label, status }: { label: string; status: DataStatus }) {
  const style =
    status === 'available'
      ? 'bg-exp-1 text-accent-dark'
      : status === 'simulated'
        ? 'border border-dashed border-sim text-sim'
        : status === 'stale'
          ? 'bg-moderate-bg text-moderate-ink'
          : 'bg-unknown-bg text-unknown-ink'
  return (
    <span className={`rounded px-2 py-0.5 text-xs ${style}`}>
      {label}: {status}
    </span>
  )
}
