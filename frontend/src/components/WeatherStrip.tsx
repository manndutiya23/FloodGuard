import type { Weather } from '../types'
import { formatTime, minutesSince } from '../lib/format'
import { SimulatedBadge } from './Badges'

const STALE_AFTER_MINUTES = 180

export default function WeatherStrip({ weather, now }: { weather: Weather; now: number }) {
  if (weather.status === 'unavailable') {
    return (
      <div role="status" className="rounded-[10px] border border-line bg-white px-4 py-3.5 text-sm">
        <strong>Rainfall forecast unavailable.</strong>{' '}
        {weather.message ?? 'No rainfall value has been substituted.'}
      </div>
    )
  }

  // Same window rule as the backend: the next three hourly values valid after now.
  const upcoming = weather.hours.filter((h) => Date.parse(h.forecast_valid_at) > now).slice(0, 3)
  const complete = upcoming.length === 3 && upcoming.every((h) => h.precipitation_mm !== null)
  const total = complete ? upcoming.reduce((sum, h) => sum + (h.precipitation_mm ?? 0), 0) : null
  const maxMm = Math.max(1, ...upcoming.map((h) => h.precipitation_mm ?? 0))
  const stale = minutesSince(weather.retrieved_at, now) > STALE_AFTER_MINUTES

  return (
    <div className="flex flex-wrap items-center gap-x-7 gap-y-3 rounded-[10px] border border-line bg-white px-4 py-3.5">
      <div>
        <div className="text-xs font-semibold tracking-wide text-muted uppercase">Rainfall forecast · next 3 h</div>
        <div className="font-mono text-[22px] font-semibold">{total === null ? 'Incomplete' : `${total.toFixed(1)} mm`}</div>
      </div>
      <ul className="m-0 flex list-none items-end gap-2 p-0" aria-label="Hourly forecast">
        {upcoming.map((h) => (
          <li key={h.forecast_valid_at} className="flex flex-col items-center gap-1 font-mono text-xs text-muted">
            <span className="sr-only">{h.precipitation_mm === null ? 'missing value' : `${h.precipitation_mm} mm`} at</span>
            <div
              className="w-[34px] rounded-sm bg-exp-3"
              style={{ height: `${h.precipitation_mm === null ? 4 : 6 + (h.precipitation_mm / maxMm) * 30}px` }}
              aria-hidden="true"
            />
            {formatTime(h.forecast_valid_at)}
          </li>
        ))}
      </ul>
      <div className="min-w-0 flex-[1_1_260px] text-[13px] text-muted">
        Source: {weather.source} forecast for one representative Mumbai point, not ward-specific.
        <br />
        <span className="font-mono">Retrieved {formatTime(weather.retrieved_at)} IST</span>
        {stale && <span className="ml-2 font-semibold text-moderate-ink">May be out of date</span>}
      </div>
      {weather.is_simulated && <SimulatedBadge label="Simulated values" />}
    </div>
  )
}
