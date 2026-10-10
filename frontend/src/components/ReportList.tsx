import { Link } from 'react-router-dom'
import type { Report } from '../types'
import { capitalize, categoryLabel, formatAge } from '../lib/format'
import { EmptyState } from './StatusStates'

export default function ReportList({ reports, wardCode }: { reports: Report[]; wardCode: string | null }) {
  const shown = reports.filter((r) => r.status !== 'resolved' && (!wardCode || r.ward_code === wardCode)).slice(0, 5)
  return (
    <section aria-labelledby="recent-reports" className="flex flex-col gap-3 rounded-[10px] border border-line bg-white p-[18px]">
      <div className="flex items-center justify-between">
        <h3 id="recent-reports" className="m-0 text-[15px]">
          Open reports {wardCode ? `in ${wardCode}` : 'across Mumbai'}
        </h3>
        <Link to="/report" className="text-sm font-semibold text-accent">
          Report flooding
        </Link>
      </div>
      {shown.length === 0 ? (
        <EmptyState>No open reports {wardCode ? 'matched to this ward' : 'right now'}.</EmptyState>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
          {shown.map((r) => (
            <li key={r.report_id} className="flex items-start gap-2.5">
              <span className="w-[76px] shrink-0 pt-0.5 font-mono text-xs text-muted">{formatAge(r.reported_at)}</span>
              <div className="flex-1 text-sm">
                <strong>{categoryLabel(r.category)}</strong>
                {r.description && ` · ${r.description}`}
                <div className="mt-0.5 text-xs text-muted">
                  {capitalize(r.verification_status)} · {capitalize(r.status)}
                  {r.is_simulated && ' · Simulated'}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
