export type Coord = [number, number]; // [lng, lat]

const EARTH_RADIUS_MILES = 3958.8;
const toRad = (deg: number) => (deg * Math.PI) / 180;

export function haversineMiles([lng1, lat1]: Coord, [lng2, lat2]: Coord): number {
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_MILES * Math.asin(Math.sqrt(h));
}

export function cumulativeMiles(coords: Coord[]): number[] {
  const totals = [0];
  for (let i = 1; i < coords.length; i++) {
    totals.push(totals[i - 1] + haversineMiles(coords[i - 1], coords[i]));
  }
  return totals;
}

export function boundsOf(coords: Coord[]): [Coord, Coord] {
  let minLng = Infinity;
  let minLat = Infinity;
  let maxLng = -Infinity;
  let maxLat = -Infinity;
  for (const [lng, lat] of coords) {
    minLng = Math.min(minLng, lng);
    minLat = Math.min(minLat, lat);
    maxLng = Math.max(maxLng, lng);
    maxLat = Math.max(maxLat, lat);
  }
  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}