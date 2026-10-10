// Sequential colour bands for historical ward exposure (share of ward population).

export const EXPOSURE_BANDS = [
  { max: 25, label: 'Under 25%', fill: '#e3edf8', text: '#0e1a2b' },
  { max: 40, label: '25–40%', fill: '#aecbea', text: '#0e1a2b' },
  { max: 55, label: '40–55%', fill: '#5b8fcb', text: '#0e1a2b' },
  { max: Infinity, label: '55% and above', fill: '#1f4e8c', text: '#ffffff' },
] as const

export function exposureBand(percent: number) {
  return EXPOSURE_BANDS.find((band) => percent < band.max) ?? EXPOSURE_BANDS[EXPOSURE_BANDS.length - 1]
}

export const RISK_FILLS: Record<string, string> = {
  low: '#aecbea',
  moderate: '#e8a33d',
  high: '#b23a0e',
  unknown: '#c9d1da',
}
