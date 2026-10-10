import type { RiskAssessment } from '../types'
import { formatDateTime, formatTime, minutesSince } from '../lib/format'
import { DataStatusChip, RiskLevelBadge, SimulatedBadge } from './Badges'
import { StaleNotice } from './StatusStates'

// Risk scores older than this are flagged as stale in the UI (prototype display rule).
const STALE_AFTER_MINUTES = 60

function ComponentBar({ label, points, max }: { label: string; points: number | null; max: number }) {
  if (points === null) {
    return (
      <div className="grid grid-cols-[130px_minmax(0,1fr)_72px] items-center gap-2.5 text-muted">
        <span>{label}</span>
        <div className="h-2 rounded border border-dashed border-[#9aa7b6]" aria-hidden="true" />
        <span className="text-right font-mono">n/a</span>
      </div>
    )
  }
  return (
    <div className="grid grid-cols-[130px_minmax(0,1fr)_72px] items-center gap-2.5">
      <span>{label}</span>
      <div className="h-2 rounded bg-line-soft" aria-hidden="true">
        <div className="h-2 rounded bg-accent" style={{ width: `${Math.min(100, (points / max) * 100)}%` }} />
      </div>
      <span className="text-right font-mono">
        {points.toFixed(1)} / {max}
      </span>
    </div>
  )
}

export default function RiskPanel({ assessment }: { assessment: RiskAssessment }) {
  const stale = minutesSince(assessment.calculated_at) > STALE_AFTER_MINUTES
  const c = assessment.score_components
  const latest = assessment.latest_available_info

  return (
    <section aria-labelledby="risk-heading" className="flex flex-col gap-2.5 rounded-lg border border-line-soft p-3.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id="risk-heading" className="m-0 text-[15px]">
          Estimated current risk
        </h3>
        {assessment.is_simulated && <SimulatedBadge />}
      </div>

      <div className="flex items-baseline gap-3">
        <div className="font-mono text-[44px] leading-none font-semibold">{assessment.risk_score ?? '–'}</div>
        <div className="text-sm text-muted">{assessment.risk_score === null ? 'No current score' : '/ 100 index'}</div>
        <span className="ml-auto">
          <RiskLevelBadge level={assessment.risk_level} />
        </span>
      </div>

      {stale && (
        <StaleNotice>
          This estimate was calculated {formatDateTime(assessment.calculated_at)} IST and may be out of date.
        </StaleNotice>
      )}

      {c && assessment.risk_score !== null && (
        <div className="flex flex-col gap-2 text-[13px]">
          <ComponentBar label="Rainfall forecast" points={c.rainfall_points} max={70} />
          <ComponentBar label="Historical exposure" points={c.historical_exposure_points} max={20} />
          <ComponentBar
            label="Citizen reports"
            points={assessment.data_status.reports === 'unavailable' ? null : c.citizen_report_points}
            max={10}
          />
        </div>
      )}

      <ul className="m-0 flex flex-col gap-1 pl-[18px] text-sm">
        {assessment.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>

      {latest && (
        <div className="rounded-md bg-unknown-bg p-2.5 text-[13px] text-unknown-ink">
          <strong>Latest available {latest.kind}</strong> (context only, not a new score): {latest.precipitation_mm}{' '}
          {latest.unit}
          {latest.forecast_valid_at && ` valid ${formatTime(latest.forecast_valid_at)} IST`}
          {latest.observed_at && ` observed ${formatTime(latest.observed_at)} IST`}, retrieved{' '}
          {formatTime(latest.retrieved_at)} IST from {latest.source}
          {latest.is_simulated && ' (simulated)'}.
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        <DataStatusChip label="Rainfall" status={assessment.data_status.rainfall} />
        <DataStatusChip label="Baseline" status={assessment.data_status.historical_baseline} />
        <DataStatusChip label="Reports" status={assessment.data_status.reports} />
      </div>
      <div className="font-mono text-xs text-muted">
        Calculated {formatDateTime(assessment.calculated_at)} IST · method {assessment.method}
      </div>
      <div className="text-[13px] text-muted">
        An index, not a probability of flooding. Rainfall comes from one representative Mumbai point, not this ward.
      </div>
    </section>
  )
}
