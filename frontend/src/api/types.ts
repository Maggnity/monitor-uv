/** Tipos espelhando os schemas da API (backend/app/api/schemas.py). */
import type { UvLevelKey } from '../theme/uvScale'

export interface Level {
  key: UvLevelKey
  label: string
  recommendation: string
}

export interface City {
  id: number
  name: string
  state: string
  lat: number
  lng: number
  timezone: string
  station_code: string
}

export interface Peak {
  date: string
  uv_max: number
  start: string | null
  end: string | null
}

export type CurrentStatus = 'ok' | 'stale' | 'night' | 'no_data'
export type ValueKind = 'measured' | 'estimated'

export interface Current {
  city: City
  status: CurrentStatus
  display_uv: number | null
  display_kind: ValueKind | null
  /** Valor de demonstração (provedor simulado ou seed) */
  display_synthetic: boolean
  measured_uv: number | null
  measured_at: string | null
  estimated_uv: number | null
  level: Level | null
  next_peak: Peak | null
  minutes_to_burn?: number | null
}

export interface HourlyPoint {
  time: string
  uv: number
  level_key: UvLevelKey
}

export interface Today {
  date: string
  hourly: HourlyPoint[]
  peak: { start: string; end: string; uv_max: number } | null
  best_windows: { start: string; end: string }[]
  hours_above_8: number
  kind: 'forecast'
}

export interface ForecastDay {
  date: string
  uv_max: number
  level: Level
  weather_code: number | null
}

export type Period = '7d' | '30d' | '12m'

export interface HistoryDay {
  date: string
  uv_max: number
  level_key: UvLevelKey
  origin: 'real' | 'sintetico' | 'forecast'
}

export interface History {
  period: Period
  contains_synthetic: boolean
  days: HistoryDay[]
}

export type Trend = 'up' | 'down' | 'stable'

export interface CompareRow {
  city: City
  current_uv: number | null
  current_kind: ValueKind | null
  current_synthetic: boolean
  peak_today: number | null
  hours_above_8: number
  trend: Trend
  sparkline: number[]
  vulnerability?: number | null
  vulnerability_illustrative?: boolean
}

export interface Compare {
  date: string
  contains_synthetic: boolean
  rows: CompareRow[]
  series: { city_id: number; points: { time: string; uv: number }[] }[]
}

export type MapWhen = 'now' | 'peak_today' | 'tomorrow'

export interface MapPoint {
  city_id: number
  name: string
  lat: number
  lng: number
  uv: number | null
  level: Level | null
  kind: ValueKind | 'forecast' | null
  synthetic: boolean
}

export interface Alert {
  id: number
  city: City
  threshold: number
  active: boolean
  created_at: string
  last_triggered_at: string | null
}

export interface AlertTrigger {
  alert_id: number
  city_id: number
  city_name: string
  threshold: number
  uv: number
  triggered_at: string
}

export interface Phototype {
  code: string
  description: string
  med_j_m2: number
  source: string
}

export interface Health {
  status: string
  database: string
  uv_provider: 'openuv' | 'simulado'
}
