import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { CircleMarker, MapContainer, TileLayer, useMapEvents } from 'react-leaflet'
import { SimulatedBadge, VerificationBadge } from '../components/Badges'
import { ErrorState } from '../components/StatusStates'
import { useAsync } from '../hooks/useAsync'
import { categoryLabel, capitalize, formatDateTime } from '../lib/format'
import { findWard, loadWardBoundaries } from '../lib/geo'
import { createReport, USE_MOCKS } from '../services/api'
import type { CreatedReport, ReportCategory } from '../types'

// Provisional client-side limit; align with the backend's validation once it is implemented.
const DESCRIPTION_MAX = 280

const CATEGORIES: { id: ReportCategory; hint: string }[] = [
  { id: 'waterlogging', hint: 'Standing water on a road or lane' },
  { id: 'flooded_passage', hint: 'Underpass, subway or walkway blocked' },
]

type Point = { lat: number; lng: number }

function PinPicker({ onPick }: { onPick: (p: Point) => void }) {
  useMapEvents({ click: (e) => onPick({ lat: e.latlng.lat, lng: e.latlng.lng }) })
  return null
}

export default function ReportPage() {
  const boundaries = useAsync(loadWardBoundaries)
  const [point, setPoint] = useState<Point | null>(null)
  const [wardChoice, setWardChoice] = useState<string>('auto')
  const [category, setCategory] = useState<ReportCategory>('waterlogging')
  const [description, setDescription] = useState('')
  const [locating, setLocating] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<Error | null>(null)
  const [created, setCreated] = useState<{ report: CreatedReport; ward: string | null; category: ReportCategory; point: Point } | null>(null)

  const matchedWard = point && boundaries.data ? findWard(boundaries.data, point.lat, point.lng) : null
  const wardCodes = boundaries.data ? boundaries.data.map((f) => f.properties.ward_code).sort() : []
  const effectiveWard = wardChoice === 'auto' ? matchedWard : wardChoice === 'unknown' ? null : wardChoice
  const tooLong = description.length > DESCRIPTION_MAX

  function useMyLocation() {
    if (!('geolocation' in navigator)) {
      setLocationError('Location is not supported by this browser. Tap the map instead.')
      return
    }
    setLocating(true)
    setLocationError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPoint({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setLocating(false)
      },
      () => {
        setLocationError('Could not get your location. Tap the map to place the pin instead.')
        setLocating(false)
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!point || tooLong || submitting) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const report = await createReport({
        latitude: Number(point.lat.toFixed(6)),
        longitude: Number(point.lng.toFixed(6)),
        category,
        description: description.trim() || undefined,
        ward_code: effectiveWard,
      })
      setCreated({ report, ward: effectiveWard, category, point })
    } catch (err) {
      setSubmitError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setSubmitting(false)
    }
  }

  function reset() {
    setCreated(null)
    setPoint(null)
    setDescription('')
    setWardChoice('auto')
    setCategory('waterlogging')
  }

  if (created) {
    const { report } = created
    return (
      <main className="mx-auto flex max-w-[560px] flex-col gap-5 p-4 sm:p-6">
        <div role="status" className="flex flex-col items-center gap-2.5 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-exp-1">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#1F5FAD" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12l5 5 9-10" />
            </svg>
          </div>
          <h1 className="m-0 text-[22px]">Report received</h1>
          <p className="m-0 text-muted">Thanks. Responders can now see it in their queue.</p>
        </div>
        <dl className="m-0 grid grid-cols-[120px_minmax(0,1fr)] gap-x-2 gap-y-2.5 rounded-[10px] border border-line bg-white p-4 text-sm">
          <dt className="text-muted">Category</dt>
          <dd className="m-0 font-semibold">{categoryLabel(created.category)}</dd>
          <dt className="text-muted">Location</dt>
          <dd className="m-0 font-mono">
            {created.point.lat.toFixed(4)}, {created.point.lng.toFixed(4)}
          </dd>
          <dt className="text-muted">Ward</dt>
          <dd className="m-0 font-mono">{created.ward ?? 'Not matched'}</dd>
          <dt className="text-muted">Reported at</dt>
          <dd className="m-0 font-mono">{formatDateTime(report.reported_at)} IST</dd>
          <dt className="text-muted">Status</dt>
          <dd className="m-0">{capitalize(report.status)}</dd>
          <dt className="text-muted">Verification</dt>
          <dd className="m-0">
            <VerificationBadge status={report.verification_status} />
          </dd>
          <dt className="text-muted">Reference</dt>
          <dd className="m-0 font-mono break-all">{report.report_id}</dd>
        </dl>
        {report.is_simulated && (
          <p className="m-0 text-sm">
            <SimulatedBadge /> This report was stored in mock mode only and disappears on reload.
          </p>
        )}
        <p className="m-0 text-[13px] text-muted">
          A report is a citizen observation, not a confirmed flood. It stays unverified until reviewed.
        </p>
        <div className="flex flex-col gap-2.5">
          <Link to="/" className="flex min-h-[50px] items-center justify-center rounded-lg bg-accent font-semibold text-white no-underline hover:bg-accent-dark">
            Back to map
          </Link>
          <button type="button" onClick={reset} className="min-h-11 font-semibold text-accent">
            Report another
          </button>
        </div>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-[560px] p-4 sm:p-6">
      <h1 className="mt-0 mb-4 text-[22px]">Report flooding</h1>
      {USE_MOCKS && (
        <p className="mt-0 mb-4 text-sm">
          <SimulatedBadge label="Mock mode" /> Reports are kept in this browser tab only.
        </p>
      )}
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
        <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
          <legend className="mb-2 p-0 font-semibold">Location</legend>
          <div className="overflow-hidden rounded-[10px] border border-line">
            <MapContainer center={[19.07, 72.88]} zoom={11} className="h-[240px] w-full" scrollWheelZoom={false}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <PinPicker onPick={setPoint} />
              {point && (
                <CircleMarker
                  center={[point.lat, point.lng]}
                  radius={10}
                  pathOptions={{ color: '#ffffff', weight: 3, fillColor: '#b86b00', fillOpacity: 1 }}
                />
              )}
            </MapContainer>
          </div>
          <p className="m-0 text-[13px] text-muted">Tap the map where you see flooding, or use your location.</p>
          <div className="font-mono text-[13px] text-muted" aria-live="polite">
            {point ? `${point.lat.toFixed(4)}, ${point.lng.toFixed(4)}` : 'No location selected'}
          </div>
          <button
            type="button"
            onClick={useMyLocation}
            disabled={locating}
            className="flex min-h-11 items-center justify-center gap-2 rounded-lg border border-accent bg-white font-semibold text-accent disabled:opacity-60"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
            </svg>
            {locating ? 'Finding your location…' : 'Use my current location'}
          </button>
          {locationError && <p role="alert" className="m-0 text-sm text-high">{locationError}</p>}
          <label className="flex flex-col gap-1.5 text-sm">
            Ward
            <select
              value={wardChoice}
              onChange={(e) => setWardChoice(e.target.value)}
              className="min-h-11 rounded-lg border border-[#9aa7b6] bg-white px-2.5 text-ink"
            >
              <option value="auto">
                {point ? (matchedWard ? `Matched from location: ${matchedWard}` : 'Location is outside known wards') : 'Match from location'}
              </option>
              <option value="unknown">Not sure</option>
              {wardCodes.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          </label>
        </fieldset>

        <fieldset className="m-0 flex flex-col gap-2.5 border-0 p-0">
          <legend className="mb-2 p-0 font-semibold">What are you seeing?</legend>
          {CATEGORIES.map((c) => (
            <label
              key={c.id}
              className={`flex min-h-[52px] items-center gap-3 rounded-lg bg-white px-3.5 py-2 ${category === c.id ? 'border-2 border-accent bg-[#eef4fb]' : 'border border-line'}`}
            >
              <input
                type="radio"
                name="category"
                value={c.id}
                checked={category === c.id}
                onChange={() => setCategory(c.id)}
                className="h-5 w-5 accent-accent"
              />
              <span>
                <strong>{categoryLabel(c.id)}</strong>
                <br />
                <span className="text-[13px] text-muted">{c.hint}</span>
              </span>
            </label>
          ))}
        </fieldset>

        <label className="flex flex-col gap-1.5 font-semibold">
          Description (optional)
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Water accumulating near Gate 2"
            aria-invalid={tooLong}
            className="resize-none rounded-lg border border-[#9aa7b6] p-2.5 font-normal"
          />
          <span className={`self-end text-xs font-normal ${tooLong ? 'text-high' : 'text-muted'}`}>
            {description.length} / {DESCRIPTION_MAX}
          </span>
        </label>

        <p className="m-0 text-[13px] text-muted">
          Your report is shown as unverified until a responder reviews it. Do not enter floodwater to take a report.
        </p>

        {submitError && <ErrorState what="report submission" title="Your report was not sent." error={submitError} />}

        <button
          type="submit"
          disabled={!point || tooLong || submitting}
          className="min-h-[50px] rounded-lg bg-accent font-semibold text-white hover:bg-accent-dark disabled:cursor-not-allowed disabled:bg-[#9aa7b6]"
        >
          {submitting ? 'Sending…' : point ? 'Submit report' : 'Choose a location to submit'}
        </button>
      </form>
    </main>
  )
}
