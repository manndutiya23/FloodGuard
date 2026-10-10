import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import MapLegend from '../components/MapLegend'
import MapView, { type MapLayer } from '../components/MapView'
import ReportList from '../components/ReportList'
import { EmptyState, ErrorState, Loading } from '../components/StatusStates'
import WardDetails from '../components/WardDetails'
import WeatherStrip from '../components/WeatherStrip'
import { useAsync } from '../hooks/useAsync'
import { loadWardBoundaries } from '../lib/geo'
import { getReports, getRisk, getWards, getWeather } from '../services/api'
import type { RiskAssessment, Ward } from '../types'

const REFRESH_MS = 10 * 60 * 1000

const LAYERS: { id: MapLayer; label: string }[] = [
  { id: 'exposure', label: 'Historical exposure' },
  { id: 'risk', label: 'Estimated risk' },
  { id: 'reports', label: 'Reports' },
]

export default function Dashboard() {
  // ?ward=F/N&layer=risk deep-links a view (useful for demos).
  const [params, setParams] = useSearchParams()
  const layerParam = params.get('layer')
  const layer: MapLayer = LAYERS.some((l) => l.id === layerParam) ? (layerParam as MapLayer) : 'exposure'
  const selectedWard = params.get('ward')
  const [showReports, setShowReports] = useState(true)

  const setParam = (key: string, value: string | null) =>
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (value) next.set(key, value)
        else next.delete(key)
        return next
      },
      { replace: true },
    )
  const setLayer = (value: MapLayer) => setParam('layer', value === 'exposure' ? null : value)
  const setSelectedWard = (code: string) => setParam('ward', code)

  const boundaries = useAsync(loadWardBoundaries)
  const wards = useAsync(getWards)
  const risk = useAsync(() => getRisk())
  const weather = useAsync(getWeather)
  const reports = useAsync(() => getReports({ limit: 100 }))

  const { reload: reloadRisk } = risk
  const { reload: reloadWeather } = weather
  const { reload: reloadReports } = reports
  useEffect(() => {
    const id = setInterval(() => {
      reloadRisk()
      reloadWeather()
      reloadReports()
    }, REFRESH_MS)
    return () => clearInterval(id)
  }, [reloadRisk, reloadWeather, reloadReports])

  const wardMap = useMemo(
    () => new Map<string, Ward>((wards.data?.data ?? []).map((w) => [w.ward_code, w])),
    [wards.data],
  )
  const riskMap = useMemo(
    () => new Map<string, RiskAssessment>((risk.data?.data ?? []).map((r) => [r.ward_code, r])),
    [risk.data],
  )
  const wardCodes = useMemo(() => [...wardMap.keys()].sort(), [wardMap])

  return (
    <main className="mx-auto flex max-w-[1360px] flex-wrap items-start gap-6 p-4 sm:p-6">
      <section aria-label="Map" className="flex min-w-0 flex-[999_1_560px] flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div role="group" aria-label="Map layer" className="inline-flex flex-wrap gap-1 rounded-lg border border-line bg-white p-1">
            {LAYERS.map((l) => (
              <button
                key={l.id}
                type="button"
                aria-pressed={layer === l.id}
                onClick={() => setLayer(l.id)}
                className={`min-h-10 rounded-md px-3.5 ${layer === l.id ? 'bg-accent font-semibold text-white' : 'text-ink hover:bg-ground'}`}
              >
                {l.label}
              </button>
            ))}
          </div>
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showReports}
              onChange={(e) => setShowReports(e.target.checked)}
              className="h-[18px] w-[18px] accent-accent"
            />
            Show citizen reports on map
          </label>
        </div>

        {weather.data ? (
          <WeatherStrip weather={weather.data} now={weather.loadedAt ?? 0} />
        ) : weather.error ? (
          <ErrorState what="the rainfall forecast" error={weather.error} onRetry={weather.reload} />
        ) : (
          <Loading label="Loading rainfall forecast…" />
        )}

        {layer === 'risk' && risk.error && <ErrorState what="risk estimates" error={risk.error} onRetry={risk.reload} />}
        {layer !== 'exposure' && reports.error && (
          <ErrorState what="incident reports" error={reports.error} onRetry={reports.reload} />
        )}

        <div className="overflow-hidden rounded-[10px] border border-line bg-white">
          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line-soft px-4 py-3.5">
            <h2 className="m-0 text-[17px]">
              {layer === 'exposure' && 'Share of ward population potentially exposed to flooding'}
              {layer === 'risk' && 'Estimated current risk by ward'}
              {layer === 'reports' && 'Open citizen reports'}
            </h2>
            <div className="text-[13px] text-muted">
              {layer === 'exposure' && 'Historical baseline · Census 2011 population · not live conditions'}
              {layer === 'risk' && `Heuristic index · ${risk.data?.meta.data_mode.replaceAll('_', ' ') ?? 'loading'}`}
              {layer === 'reports' && 'Citizen reports · unverified until reviewed'}
            </div>
          </div>
          {boundaries.error ? (
            <div className="p-4">
              <ErrorState what="ward boundaries" error={boundaries.error} onRetry={boundaries.reload} />
            </div>
          ) : boundaries.data ? (
            <MapView
              boundaries={boundaries.data}
              wards={wardMap}
              risk={riskMap}
              reports={reports.data ?? []}
              layer={layer}
              showReports={showReports}
              selectedWard={selectedWard}
              onSelectWard={setSelectedWard}
            />
          ) : (
            <div className="flex h-[560px] items-center justify-center bg-sea">
              <Loading label="Loading map…" />
            </div>
          )}
          <MapLegend layer={layer} showReports={showReports} />
        </div>
      </section>

      <aside aria-label="Selected ward" className="flex min-w-0 flex-[1_1_380px] flex-col gap-4">
        {wards.error ? (
          <ErrorState what="ward data" error={wards.error} onRetry={wards.reload} />
        ) : wards.loading && !wards.data ? (
          <Loading label="Loading wards…" />
        ) : wardCodes.length === 0 ? (
          <EmptyState>No ward data available.</EmptyState>
        ) : (
          <WardDetails
            wardCodes={wardCodes}
            selectedWard={selectedWard}
            onSelectWard={setSelectedWard}
            ward={selectedWard ? wardMap.get(selectedWard) : undefined}
            assessment={selectedWard ? riskMap.get(selectedWard) : undefined}
            riskError={Boolean(risk.error)}
          />
        )}
        {reports.data && <ReportList reports={reports.data} wardCode={selectedWard} />}
        {reports.loading && !reports.data && <Loading label="Loading reports…" />}
      </aside>
    </main>
  )
}
