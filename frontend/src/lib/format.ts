/** Formatação de tempo em português, sempre no fuso da cidade. */

export function relativeTime(iso: string, now: Date = new Date()): string {
  const minutes = Math.floor((now.getTime() - new Date(iso).getTime()) / 60_000)
  if (minutes < 1) return 'agora mesmo'
  if (minutes < 60) return `há ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `há ${hours} h`
  const days = Math.floor(hours / 24)
  return days === 1 ? 'há 1 dia' : `há ${days} dias`
}

function localParts(date: Date, timeZone: string) {
  const parts = new Intl.DateTimeFormat('pt-BR', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? 0)
  return { hour: get('hour'), minute: get('minute') }
}

export function hourLabel(iso: string | Date, timeZone: string): string {
  const { hour, minute } = localParts(new Date(iso), timeZone)
  return minute === 0 ? `${hour}h` : `${hour}h${String(minute).padStart(2, '0')}`
}

/** "Pico: 11 às 12h30" — valor arredondado e o meio da janela de pico. */
export function peakLabel(uv: number, startIso: string, endIso: string, timeZone: string): string {
  const middle = new Date((new Date(startIso).getTime() + new Date(endIso).getTime()) / 2)
  return `Pico: ${Math.round(uv)} às ${hourLabel(middle, timeZone)}`
}

export function weekdayLabel(isoDate: string, today: string): string {
  if (isoDate === today) return 'Hoje'
  const date = new Date(`${isoDate}T12:00:00Z`)
  const label = new Intl.DateTimeFormat('pt-BR', { weekday: 'short', timeZone: 'UTC' }).format(date)
  return label.charAt(0).toUpperCase() + label.slice(1).replace('.', '')
}

export function formatUv(uv: number): string {
  return String(Math.round(uv))
}
