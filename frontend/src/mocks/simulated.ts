// Simulated data for frontend development before the API is deployed.
// Every value here is invented for demonstration and is labelled is_simulated.
// Timestamps are generated relative to "now" so the mock never looks stale.
// Ward exposure figures come from wards.json (the real reference CSV).

import type { Report, RiskAssessment, RiskResponse, Weather } from '../types'
import wardsJson from './wards.json'

const HOUR_MS = 60 * 60 * 1000
const MIN_MS = 60 * 1000

// Mirrors backend/risk_engine.py defaults so mock scores look like real ones.
const MAX_RAINFALL_POINTS = 70
const MAX_EXPOSURE_POINTS = 20
const RAINFALL_NORMALIZATION_MM = 30

// Simulates one ward whose forecast window could not be assembled, to exercise the "unknown" state.
const WARD_WITH_INCOMPLETE_FORECAST = 'T'

const SIMULATED_HOURLY_MM = [4.0, 5.0, 3.0, 1.5, 0.5, 0.0]

function iso(ms: number): string {
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z')
}

function nextWholeHour(now: number): number {
  return Math.ceil(now / HOUR_MS) * HOUR_MS
}

function level(score: number): RiskAssessment['risk_level'] {
  if (score < 30) return 'low'
  if (score < 60) return 'moderate'
  return 'high'
}

export function mockWeather(now = Date.now()): Weather {
  const start = nextWholeHour(now)
  return {
    source: 'Open-Meteo',
    source_type: 'weather_model_forecast',
    status: 'simulated',
    is_simulated: true,
    requested_location: { latitude: 19.076, longitude: 72.8777 },
    provider_location: { latitude: 19.0625, longitude: 72.875, elevation_m: 10 },
    precipitation_unit: 'mm',
    retrieved_at: iso(now - 5 * MIN_MS),
    hours: SIMULATED_HOURLY_MM.map((mm, i) => ({
      forecast_valid_at: iso(start + i * HOUR_MS),
      precipitation_mm: mm,
    })),
    location_scope: 'Representative Mumbai point only; this weather signal is not ward-specific.',
  }
}

export function mockRisk(now = Date.now()): RiskResponse {
  const weather = mockWeather(now)
  const window = weather.hours.slice(0, 3)
  const windowMm = window.reduce((sum, h) => sum + (h.precipitation_mm ?? 0), 0)
  const rainfallPoints = Math.min(MAX_RAINFALL_POINTS, (windowMm / RAINFALL_NORMALIZATION_MM) * MAX_RAINFALL_POINTS)
  const windowStart = window[0].forecast_valid_at
  const windowEnd = iso(Date.parse(window[2].forecast_valid_at) + HOUR_MS)

  const data: RiskAssessment[] = wardsJson.data.map((ward) => {
    const exposurePct = ward.percentage_of_ward_population_potentially_exposed_percent
    const exposurePoints = (exposurePct / 100) * MAX_EXPOSURE_POINTS

    if (ward.ward_code === WARD_WITH_INCOMPLETE_FORECAST) {
      return {
        ward_code: ward.ward_code,
        risk_score: null,
        risk_level: 'unknown',
        reasons: [
          'A complete three-hour forecast window was not available, so a new risk score was not calculated.',
          'Latest usable forecast context is shown separately and is not a newly calculated score.',
        ],
        data_status: { rainfall: 'unavailable', historical_baseline: 'available', reports: 'unavailable' },
        calculated_at: iso(now),
        is_simulated: true,
        method: 'heuristic-v0.2',
        score_components: {
          rainfall_points: null,
          historical_exposure_points: 0,
          citizen_report_points: 0,
          maximum_total_points: 100,
        },
        latest_available_info: {
          kind: 'forecast',
          precipitation_mm: weather.hours[0].precipitation_mm ?? 0,
          unit: 'mm',
          forecast_valid_at: weather.hours[0].forecast_valid_at,
          retrieved_at: weather.retrieved_at,
          source: 'Open-Meteo',
          is_simulated: true,
        },
      }
    }

    const score = Math.round(rainfallPoints + exposurePoints)
    return {
      ward_code: ward.ward_code,
      risk_score: score,
      risk_level: level(score),
      reasons: [
        `Forecast precipitation input: ${windowMm.toFixed(1)} mm over 180 minutes (${windowStart} to ${windowEnd}).`,
        `Historical ward exposure (${exposurePct}% of ward population) contributes background context.`,
        'Citizen reports are not yet included in live scoring.',
      ],
      data_status: { rainfall: 'simulated', historical_baseline: 'available', reports: 'unavailable' },
      calculated_at: iso(now),
      is_simulated: true,
      method: 'heuristic-v0.2',
      score_components: {
        rainfall_points: Math.round(rainfallPoints * 100) / 100,
        historical_exposure_points: Math.round(exposurePoints * 100) / 100,
        citizen_report_points: 0,
        maximum_total_points: 100,
      },
      latest_available_info: null,
    }
  })

  return {
    data,
    meta: {
      risk_method: 'heuristic-v0.2',
      data_mode: 'simulation',
      location_scope: 'Representative Mumbai point only; not ward-specific weather.',
      important_limit: 'Simulated frontend mock data. Not a flood prediction or emergency warning.',
    },
  }
}

export function mockReports(now = Date.now()): Report[] {
  return [
    {
      report_id: 'sim-001',
      ward_code: 'F/N',
      latitude: 19.0335,
      longitude: 72.8545,
      category: 'waterlogging',
      description: 'Water accumulating near Gate 2',
      status: 'new',
      verification_status: 'unverified',
      reported_at: iso(now - 2 * MIN_MS),
      is_simulated: true,
    },
    {
      report_id: 'sim-002',
      ward_code: 'F/N',
      latitude: 19.0343,
      longitude: 72.8551,
      category: 'waterlogging',
      description: 'Road outside the bus depot under water',
      status: 'new',
      verification_status: 'unverified',
      reported_at: iso(now - 14 * MIN_MS),
      is_simulated: true,
    },
    {
      report_id: 'sim-003',
      ward_code: 'H/E',
      latitude: 19.0728,
      longitude: 72.8526,
      category: 'flooded_passage',
      description: 'Railway subway closed, water above ankle',
      status: 'new',
      verification_status: 'unverified',
      reported_at: iso(now - 11 * MIN_MS),
      is_simulated: true,
    },
    {
      report_id: 'sim-004',
      ward_code: 'F/N',
      latitude: 19.0262,
      longitude: 72.8569,
      category: 'flooded_passage',
      description: 'Subway underpass knee-deep',
      status: 'reviewed',
      verification_status: 'verified',
      reported_at: iso(now - 52 * MIN_MS),
      is_simulated: true,
    },
    {
      report_id: 'sim-005',
      ward_code: null,
      latitude: 19.0596,
      longitude: 72.8295,
      category: 'waterlogging',
      description: 'Lane flooded outside market',
      status: 'reviewed',
      verification_status: 'unverified',
      reported_at: iso(now - 100 * MIN_MS),
      is_simulated: true,
    },
    {
      report_id: 'sim-006',
      ward_code: 'K/W',
      latitude: 19.1197,
      longitude: 72.8464,
      category: 'waterlogging',
      description: 'Water cleared from junction',
      status: 'resolved',
      verification_status: 'verified',
      reported_at: iso(now - 3 * HOUR_MS),
      is_simulated: true,
    },
  ]
}
