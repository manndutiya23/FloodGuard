// Types mirror docs/API_CONTRACT.md. Keep field names and enum values in sync with it.

export type RiskLevel = 'low' | 'moderate' | 'high' | 'unknown'
export type DataStatus = 'available' | 'unavailable' | 'stale' | 'simulated'
export type ReportStatus = 'new' | 'reviewed' | 'resolved'
export type VerificationStatus = 'unverified' | 'verified'
export type ReportCategory = 'waterlogging' | 'flooded_passage'

export interface Ward {
  ward_code: string
  population_potentially_exposed_within_250m_buffer: number
  percentage_of_ward_population_potentially_exposed_percent: number
  underlying_population_data_year: number
  source?: string
  source_table?: string
  source_page?: number
  data_type: string
}

export interface WardsResponse {
  data: Ward[]
  meta: {
    source: string
    source_page: number
    data_type?: string
    underlying_population_data_year?: number
  }
}

export interface ForecastHour {
  forecast_valid_at: string
  precipitation_mm: number | null
}

export interface Weather {
  source: string
  source_type?: string
  status: DataStatus
  is_simulated: boolean
  requested_location?: { latitude: number; longitude: number }
  provider_location?: { latitude: number | null; longitude: number | null; elevation_m?: number | null }
  precipitation_unit?: string
  retrieved_at: string
  hours: ForecastHour[]
  location_scope?: string
  message?: string
  error_code?: string
}

export interface LatestAvailableInfo {
  kind: 'forecast' | 'observation'
  precipitation_mm: number
  unit: string
  forecast_valid_at?: string
  observed_at?: string
  retrieved_at: string
  source: string
  is_simulated: boolean
}

export interface ScoreComponents {
  rainfall_points: number | null
  historical_exposure_points: number
  citizen_report_points: number
  maximum_total_points: number
}

export interface RiskAssessment {
  ward_code: string
  risk_score: number | null
  risk_level: RiskLevel
  reasons: string[]
  data_status: {
    rainfall: DataStatus
    historical_baseline: DataStatus
    reports: DataStatus
  }
  calculated_at: string
  is_simulated: boolean
  method: string
  score_components?: ScoreComponents | null
  latest_available_info?: LatestAvailableInfo | null
  location_scope?: string
  weather_source?: string
}

export interface RiskResponse {
  data: RiskAssessment[]
  meta: {
    risk_method: string
    data_mode: string
    location_scope: string
    important_limit?: string
  }
}

export interface Report {
  report_id: string
  ward_code: string | null
  latitude: number
  longitude: number
  category: ReportCategory
  description?: string | null
  status: ReportStatus
  verification_status: VerificationStatus
  reported_at: string
  is_simulated: boolean
}

export interface NewReport {
  latitude: number
  longitude: number
  category: ReportCategory
  description?: string
  ward_code?: string | null
  is_simulated?: boolean
}

export interface CreatedReport {
  report_id: string
  status: ReportStatus
  verification_status: VerificationStatus
  reported_at: string
  is_simulated: boolean
}

export interface ReportFilters {
  status?: ReportStatus
  ward_code?: string
  limit?: number
}
