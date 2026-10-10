import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { RiskLevelBadge, SimulatedBadge, VerificationBadge } from '../components/Badges'
import { EmptyState, ErrorState, Loading } from '../components/StatusStates'
import { useAsync } from '../hooks/useAsync'
import { capitalize, categoryLabel, formatAge, formatTime } from '../lib/format'
import { getReports, getRisk, updateReportStatus } from '../services/api'
import type { Report, ReportStatus, VerificationStatus } from '../types'

// Display-only duplicate hint, mirroring the contract's provisional thresholds.
// It does not merge or hide records.
const DUPLICATE_DISTANCE_M = 200
const DUPLICATE_MINUTES = 30

const NEXT_STATUS: Partial<Record<ReportStatus, ReportStatus>> = { new: 'reviewed', reviewed: 'resolved' }

function distanceMeters(a: Report, b: Report): number {
  const R = 6371000
  const toRad = (d: number) => (d * Math.PI) / 180
  const dLat = toRad(b.latitude - a.latitude)
  const dLng = toRad(b.longitude - a.longitude)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.latitude)) * Math.cos(toRad(b.latitude)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

function nearbyCount(report: Report, all: Report[]): number {
  return all.filter(
    (other) =>
      other.report_id !== report.report_id &&
      other.status !== 'resolved' &&
      other.category === report.category &&
      Math.abs(Date.parse(other.reported_at) - Date.parse(report.reported_at)) <= DUPLICATE_MINUTES * 60000 &&
      distanceMeters(report, other) <= DUPLICATE_DISTANCE_M,
  ).length
}

type StatusFilter = 'open' | ReportStatus | 'all'

export default function ResponderDashboard() {
  const reports = useAsync(() => getReports({ limit: 200 }))
  const risk = useAsync(() => getRisk())
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('open')
  const [wardFilter, setWardFilter] = useState('')
  const [verificationFilter, setVerificationFilter] = useState<'' | VerificationStatus>('')
  const [updating, setUpdating] = useState<string | null>(null)
  const [updateError, setUpdateError] = useState<Error | null>(null)
  const [overrides, setOverrides] = useState<Record<string, ReportStatus>>({})

  const all = useMemo(
    () => (reports.data ?? []).map((r) => (overrides[r.report_id] ? { ...r, status: overrides[r.report_id] } : r)),
    [reports.data, overrides],
  )

  const filtered = all
    .filter((r) => (statusFilter === 'all' ? true : statusFilter === 'open' ? r.status !== 'resolved' : r.status === statusFilter))
    .filter((r) => (wardFilter === '' ? true : wardFilter === 'unmatched' ? r.ward_code === null : r.ward_code === wardFilter))
    .filter((r) => (verificationFilter ? r.verification_status === verificationFilter : true))
    .sort((a, b) => b.reported_at.localeCompare(a.reported_at))

  const wardOptions = [...new Set(all.map((r) => r.ward_code).filter((c): c is string => c !== null))].sort()
  const counts = {
    new: all.filter((r) => r.status === 'new').length,
    reviewed: all.filter((r) => r.status === 'reviewed').length,
    resolved: all.filter((r) => r.status === 'resolved').length,
  }

  const rankedWards = useMemo(() => {
    const data = risk.data?.data ?? []
    return [...data].sort((a, b) => (b.risk_score ?? -1) - (a.risk_score ?? -1))
  }, [risk.data])
  const highCount = rankedWards.filter((r) => r.risk_level === 'high').length
  const unscored = rankedWards.filter((r) => r.risk_score === null)
  const anySimulated = all.some((r) => r.is_simulated) || rankedWards.some((r) => r.is_simulated)

  async function advance(report: Report) {
    const next = NEXT_STATUS[report.status]
    if (!next) return
    setUpdating(report.report_id)
    setUpdateError(null)
    try {
      const updated = await updateReportStatus(report.report_id, next)
      setOverrides((o) => ({ ...o, [report.report_id]: updated.status ?? next }))
    } catch (err) {
      setUpdateError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setUpdating(null)
    }
  }

  const selectClass = 'min-h-10 rounded-md border border-[#9aa7b6] bg-white px-2 text-sm text-ink'

  return (
    <main className="mx-auto flex max-w-[1360px] flex-col gap-5 p-4 sm:p-6">
      <div className="rounded-md border border-warn-line bg-warn-bg px-4 py-2.5 text-sm text-warn-ink">
        <strong>Prototype workflow.</strong> No sign-in yet, so this view is not secure responder access.
        {anySimulated && ' Items marked simulated are demonstration data.'}
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-3">
        {[
          { label: 'New reports', value: counts.new },
          { label: 'Reviewed', value: counts.reviewed },
          { label: 'Resolved', value: counts.resolved },
          { label: 'Wards with high estimate', value: risk.data ? highCount : '–' },
        ].map((s) => (
          <div key={s.label} className="rounded-[10px] border border-line bg-white px-4 py-3.5">
            <div className="text-[13px] text-muted">{s.label}</div>
            <div className="font-mono text-[28px] font-semibold">{reports.data || s.label.startsWith('Wards') ? s.value : '–'}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-start gap-5">
        <section aria-labelledby="reports-heading" className="min-w-0 flex-[999_1_640px] overflow-hidden rounded-[10px] border border-line bg-white">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-line-soft px-4 py-3.5">
            <div>
              <h2 id="reports-heading" className="m-0 text-[17px]">
                Citizen reports
              </h2>
              <div className="text-[13px] text-muted">Reported facts. Newest first. Unverified until reviewed.</div>
            </div>
            <div className="flex flex-wrap gap-2.5">
              <label className="flex flex-col gap-1 text-xs text-muted">
                Status
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as StatusFilter)} className={selectClass}>
                  <option value="open">New and reviewed</option>
                  <option value="new">New</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="resolved">Resolved</option>
                  <option value="all">All</option>
                </select>
              </label>
              <label className="flex flex-col gap-1 text-xs text-muted">
                Ward
                <select value={wardFilter} onChange={(e) => setWardFilter(e.target.value)} className={selectClass}>
                  <option value="">All wards</option>
                  {wardOptions.map((w) => (
                    <option key={w} value={w}>
                      {w}
                    </option>
                  ))}
                  <option value="unmatched">Unmatched</option>
                </select>
              </label>
              <label className="flex flex-col gap-1 text-xs text-muted">
                Verification
                <select
                  value={verificationFilter}
                  onChange={(e) => setVerificationFilter(e.target.value as '' | VerificationStatus)}
                  className={selectClass}
                >
                  <option value="">All</option>
                  <option value="unverified">Unverified</option>
                  <option value="verified">Verified</option>
                </select>
              </label>
              <button
                type="button"
                onClick={() => {
                  setOverrides({})
                  reports.reload()
                }}
                className="min-h-10 self-end rounded-md border border-line px-3 text-sm font-semibold hover:bg-ground"
              >
                Refresh
              </button>
            </div>
          </div>

          {updateError && (
            <div className="p-4 pb-0">
              <ErrorState what="the status update" title="Status was not updated." error={updateError} />
            </div>
          )}

          {reports.error ? (
            <div className="p-4">
              <ErrorState what="incident reports" error={reports.error} onRetry={reports.reload} />
            </div>
          ) : reports.loading && !reports.data ? (
            <Loading label="Loading reports…" />
          ) : filtered.length === 0 ? (
            <div className="p-4">
              <EmptyState>No reports match these filters.</EmptyState>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] border-collapse text-sm">
                <thead>
                  <tr className="text-left text-xs tracking-wide text-muted uppercase">
                    <th scope="col" className="px-4 py-2.5 font-semibold">Reported</th>
                    <th scope="col" className="px-2 py-2.5 font-semibold">Ward</th>
                    <th scope="col" className="px-2 py-2.5 font-semibold">Report</th>
                    <th scope="col" className="px-2 py-2.5 font-semibold">Verification</th>
                    <th scope="col" className="px-2 py-2.5 font-semibold">Workflow</th>
                    <th scope="col" className="px-4 py-2.5">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r) => {
                    const nearby = nearbyCount(r, all)
                    const next = NEXT_STATUS[r.status]
                    return (
                      <tr key={r.report_id} className={`border-t border-line-soft ${r.status === 'new' ? 'bg-[#fffaf2]' : ''}`}>
                        <td className="px-4 py-3 font-mono whitespace-nowrap">
                          {formatAge(r.reported_at)}
                          <br />
                          <span className="text-xs text-muted">{formatTime(r.reported_at)} IST</span>
                        </td>
                        <td className={`px-2 py-3 font-mono ${r.ward_code ? 'font-semibold' : 'text-muted'}`}>{r.ward_code ?? 'Unmatched'}</td>
                        <td className="px-2 py-3">
                          <strong>{categoryLabel(r.category)}</strong>
                          {r.is_simulated && (
                            <span className="ml-2 align-middle">
                              <SimulatedBadge />
                            </span>
                          )}
                          {r.description && (
                            <>
                              <br />
                              <span className="text-muted">{r.description}</span>
                            </>
                          )}
                          {nearby > 0 && r.status !== 'resolved' && (
                            <div className="mt-0.5 text-xs text-moderate-ink">
                              Possible duplicate of {nearby} nearby report{nearby > 1 ? 's' : ''} (within {DUPLICATE_DISTANCE_M} m,{' '}
                              {DUPLICATE_MINUTES} min)
                            </div>
                          )}
                        </td>
                        <td className="px-2 py-3">
                          <VerificationBadge status={r.verification_status} />
                        </td>
                        <td className={`px-2 py-3 ${r.status === 'new' ? 'font-semibold' : ''}`}>{capitalize(r.status)}</td>
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                          {next && (
                            <button
                              type="button"
                              onClick={() => advance(r)}
                              disabled={updating === r.report_id}
                              className={`min-h-10 rounded-md px-3.5 text-sm font-semibold disabled:opacity-60 ${
                                next === 'reviewed'
                                  ? 'border border-accent bg-accent text-white hover:bg-accent-dark'
                                  : 'border border-[#9aa7b6] bg-white text-ink hover:bg-ground'
                              }`}
                            >
                              {updating === r.report_id ? 'Saving…' : `Mark ${next}`}
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
          <div className="border-t border-line-soft px-4 py-2.5 text-[13px] text-muted">
            Changing workflow status does not mark a report verified. Verification is a separate review step.
          </div>
        </section>

        <aside aria-labelledby="wards-heading" className="flex min-w-0 flex-[1_1_340px] flex-col gap-3 rounded-[10px] border border-line bg-white p-4">
          <div>
            <h2 id="wards-heading" className="m-0 text-[17px]">
              Wards to check first
            </h2>
            <div className="text-[13px] text-muted">Calculated estimates ({risk.data?.meta.risk_method ?? 'heuristic'}). Not observations.</div>
          </div>
          {risk.error ? (
            <ErrorState what="risk estimates" error={risk.error} onRetry={risk.reload} />
          ) : !risk.data ? (
            <Loading label="Loading estimates…" />
          ) : rankedWards.length === 0 ? (
            <EmptyState>No estimates available.</EmptyState>
          ) : (
            <ol className="m-0 flex list-none flex-col gap-2 p-0">
              {rankedWards.slice(0, 6).map((a) => (
                <li
                  key={a.ward_code}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 ${a.risk_score === null ? 'border border-dashed border-[#9aa7b6]' : 'border border-line-soft'}`}
                >
                  <span className="w-11 font-mono font-semibold">{a.ward_code}</span>
                  <span className="font-mono text-xl font-semibold">{a.risk_score ?? '–'}</span>
                  {a.risk_score === null && <span className="text-[13px] text-unknown-ink">No current score</span>}
                  <span className="ml-auto">
                    <RiskLevelBadge level={a.risk_level} />
                  </span>
                </li>
              ))}
            </ol>
          )}
          {unscored.length > 0 && (
            <p className="m-0 rounded-md bg-unknown-bg px-3 py-2 text-[13px] text-unknown-ink">
              No current score for {unscored.map((a) => a.ward_code).join(', ')}: not enough valid data. Do not read this as low risk.
            </p>
          )}
          {risk.data && <p className="m-0 text-[13px] text-muted">{risk.data.meta.location_scope} Index from 0 to 100, not a flood probability.</p>}
          <Link to="/" className="text-sm font-semibold text-accent">
            Open on map
          </Link>
        </aside>
      </div>
    </main>
  )
}
