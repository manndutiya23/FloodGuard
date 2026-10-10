import { EXPOSURE_BANDS, RISK_FILLS } from '../lib/exposure'
import type { MapLayer } from './MapView'

function Swatch({ color, label, dashed }: { color: string; label: string; dashed?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`h-3.5 w-[18px] rounded-sm ${dashed ? 'border border-dashed border-muted' : 'border border-black/10'}`}
        style={{ background: color }}
        aria-hidden="true"
      />
      {label}
    </span>
  )
}

export default function MapLegend({ layer, showReports }: { layer: MapLayer; showReports: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2.5 border-t border-line-soft px-4 py-3 text-[13px]">
      {layer === 'exposure' && (
        <>
          <span className="font-semibold">Population potentially exposed (historical, Census 2011)</span>
          {EXPOSURE_BANDS.map((b) => (
            <Swatch key={b.label} color={b.fill} label={b.label} />
          ))}
        </>
      )}
      {layer === 'risk' && (
        <>
          <span className="font-semibold">Estimated risk index (heuristic)</span>
          <Swatch color={RISK_FILLS.low} label="Low (0–29)" />
          <Swatch color={RISK_FILLS.moderate} label="Moderate (30–59)" />
          <Swatch color={RISK_FILLS.high} label="High (60–100)" />
          <Swatch color={RISK_FILLS.unknown} label="Unknown (not enough data)" dashed />
        </>
      )}
      {(showReports || layer === 'reports') && (
        <>
          <span className="font-semibold">Open reports</span>
          <Swatch color="#e8a33d" label="Unverified" />
          <Swatch color="#b23a0e" label="Verified" />
        </>
      )}
    </div>
  )
}
