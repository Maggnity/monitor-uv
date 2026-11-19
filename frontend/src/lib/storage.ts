/** Preferências guardadas no navegador. */
const CITY = 'monitor-uv:city-id'
const ASKED_LOCATION = 'monitor-uv:asked-location'
const PHOTOTYPE = 'monitor-uv:phototype'

export const DEFAULT_CITY_ID = 1 // São Paulo

export function getCityId(): number | null {
  const value = Number(localStorage.getItem(CITY))
  return Number.isInteger(value) && value > 0 ? value : null
}

export function setCityId(id: number): void {
  localStorage.setItem(CITY, String(id))
}

export function hasAskedLocation(): boolean {
  return localStorage.getItem(ASKED_LOCATION) === '1'
}

export function markAskedLocation(): void {
  localStorage.setItem(ASKED_LOCATION, '1')
}

export function getPhototype(): string | null {
  return localStorage.getItem(PHOTOTYPE)
}

export function setPhototype(code: string | null): void {
  if (code) localStorage.setItem(PHOTOTYPE, code)
  else localStorage.removeItem(PHOTOTYPE)
}
