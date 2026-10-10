import { useMemo } from 'react'
import { CircleMarker, GeoJSON, MapContainer, TileLayer, Tooltip } from 'react-leaflet'
import { geoJSON, type Layer, type PathOptions } from 'leaflet'
import type { WardFeature } from '../lib/geo'
import { exposureBand, RISK_FILLS } from '../lib/exposure'
import { categoryLabel, formatAge } from '../lib/format'
import type { Report, RiskAssessment, Ward } from '../types'

export type MapLayer = 'exposure' | 'risk' | 'reports'

interface Props {
  boundaries: WardFeature[]
  wards: Map<string, Ward>
  risk: Map<string, RiskAssessment>
  reports: Report[]
  layer: MapLayer
  showReports: boolean
  selectedWard: string | null
  onSelectWard: (code: string) => void
}

export default function MapView({ boundaries, wards, risk, reports, layer, showReports, selectedWard, onSelectWard }: Props) {
  const collection = useMemo(() => ({ type: 'FeatureCollection' as const, features: boundaries }), [boundaries])
  const bounds = useMemo(() => geoJSON(collection).getBounds().pad(0.02), [collection])

  const style = (feature?: WardFeature): PathOptions => {
    const code = feature?.properties.ward_code ?? ''
    const selected = code === selectedWard
    let fillColor = '#e3edf8'
    if (layer === 'exposure') {
      const ward = wards.get(code)
      fillColor = ward ? exposureBand(ward.percentage_of_ward_population_potentially_exposed_percent).fill : '#ffffff'
    } else if (layer === 'risk') {
      fillColor = RISK_FILLS[risk.get(code)?.risk_level ?? 'unknown']
    } else {
      fillColor = '#ffffff'
    }
    return {
      fillColor,
      fillOpacity: layer === 'reports' ? 0.35 : 0.75,
      color: selected ? '#b86b00' : '#0e1a2b',
      weight: selected ? 4 : 1,
      opacity: selected ? 1 : 0.5,
    }
  }

  const onEachFeature = (feature: WardFeature, leafletLayer: Layer) => {
    const code = feature.properties.ward_code
    const ward = wards.get(code)
    const assessment = risk.get(code)
    let label = `Ward ${code}`
    if (layer === 'exposure' && ward) label += ` · ${ward.percentage_of_ward_population_potentially_exposed_percent}% exposed (historical)`
    if (layer === 'risk' && assessment)
      label += ` · ${assessment.risk_score ?? '–'} ${assessment.risk_level}${assessment.is_simulated ? ' (simulated)' : ''}`
    leafletLayer.bindTooltip(label, { sticky: true })
    leafletLayer.on('click', () => onSelectWard(code))
  }

  const visibleReports = showReports || layer === 'reports' ? reports.filter((r) => r.status !== 'resolved') : []

  return (
    <MapContainer bounds={bounds} zoomSnap={0.5} minZoom={10} maxZoom={17} scrollWheelZoom className="h-[560px] w-full">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <GeoJSON
        key={`${layer}-${selectedWard}-${wards.size}-${risk.size}`}
        data={collection}
        style={(f) => style(f as WardFeature)}
        onEachFeature={(f, l) => onEachFeature(f as WardFeature, l)}
      />
      {visibleReports.map((report) => (
        <CircleMarker
          key={report.report_id}
          center={[report.latitude, report.longitude]}
          radius={8}
          pathOptions={{
            color: '#ffffff',
            weight: 2,
            fillColor: report.verification_status === 'verified' ? '#b23a0e' : '#e8a33d',
            fillOpacity: 1,
          }}
        >
          <Tooltip>
            {categoryLabel(report.category)} · {formatAge(report.reported_at)} · {report.verification_status}
            {report.is_simulated ? ' · simulated' : ''}
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
