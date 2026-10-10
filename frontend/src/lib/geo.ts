// Loads data/reference/mumbai_ward_boundaries.geojson without modifying the source file.
// That file stores positions as [latitude, longitude]; GeoJSON (and Leaflet's GeoJSON layer)
// expects [longitude, latitude]. We detect and swap the order here at load time.

import type { Feature, FeatureCollection, MultiPolygon, Polygon, Position } from 'geojson'
import boundariesUrl from '../../../data/reference/mumbai_ward_boundaries.geojson?url'

export type WardFeature = Feature<Polygon | MultiPolygon, { ward_code: string }>

// Mumbai sits around latitude 18.9-19.3 and longitude 72.7-73.0.
function looksLatFirst(position: Position): boolean {
  const [a, b] = position
  return a >= 18 && a <= 20 && b >= 72 && b <= 74
}

function normalizeCode(value: unknown): string {
  return String(value ?? '').replace(/\s+/g, '').toUpperCase()
}

function mapRings(rings: Position[][], swap: boolean): Position[][] {
  return rings.map((ring) => ring.map((p) => (swap ? [p[1], p[0]] : [p[0], p[1]])))
}

function firstPosition(geometry: Polygon | MultiPolygon): Position {
  return geometry.type === 'Polygon' ? geometry.coordinates[0][0] : geometry.coordinates[0][0][0]
}

export async function loadWardBoundaries(): Promise<WardFeature[]> {
  const response = await fetch(boundariesUrl)
  if (!response.ok) throw new Error('Ward boundaries could not be loaded.')
  const collection = (await response.json()) as FeatureCollection<Polygon | MultiPolygon>

  return collection.features.map((feature) => {
    const geometry = feature.geometry
    const swap = looksLatFirst(firstPosition(geometry))
    const fixed: Polygon | MultiPolygon =
      geometry.type === 'Polygon'
        ? { type: 'Polygon', coordinates: mapRings(geometry.coordinates, swap) }
        : { type: 'MultiPolygon', coordinates: geometry.coordinates.map((poly) => mapRings(poly, swap)) }
    const props = feature.properties ?? {}
    return {
      type: 'Feature',
      geometry: fixed,
      properties: { ward_code: normalizeCode(props.NAME2 ?? props.Name) },
    }
  })
}

function pointInRing(lng: number, lat: number, ring: Position[]): boolean {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i]
    const [xj, yj] = ring[j]
    if (yi > lat !== yj > lat && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside
  }
  return inside
}

function pointInPolygon(lng: number, lat: number, rings: Position[][]): boolean {
  if (!pointInRing(lng, lat, rings[0])) return false
  return !rings.slice(1).some((hole) => pointInRing(lng, lat, hole))
}

// Returns the ward containing the point, or null. Never guesses a nearest ward.
export function findWard(features: WardFeature[], lat: number, lng: number): string | null {
  for (const feature of features) {
    const g = feature.geometry
    const polygons = g.type === 'Polygon' ? [g.coordinates] : g.coordinates
    if (polygons.some((rings) => pointInPolygon(lng, lat, rings))) return feature.properties.ward_code
  }
  return null
}
