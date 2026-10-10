// Display helpers. API timestamps are UTC ISO strings; the UI shows Mumbai time (IST).

const IST = 'Asia/Kolkata'

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-IN', { timeZone: IST, hour: '2-digit', minute: '2-digit', hour12: false })
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-IN', {
    timeZone: IST,
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function formatAge(iso: string, now = Date.now()): string {
  const minutes = Math.max(0, Math.round((now - Date.parse(iso)) / 60000))
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (hours < 24) return rest ? `${hours} h ${rest} min ago` : `${hours} h ago`
  return formatDateTime(iso)
}

export function minutesSince(iso: string, now = Date.now()): number {
  return (now - Date.parse(iso)) / 60000
}

export const CATEGORY_LABELS: Record<string, string> = {
  waterlogging: 'Waterlogging',
  flooded_passage: 'Flooded passage',
}

export function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category
}

export function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}
