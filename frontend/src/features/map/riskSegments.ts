import type { FeatureCollection, LineString } from "geojson";

import type { RiskLevel, RoutePlan } from "../../api/types";
import { RISK_COLORS } from "../../theme/riskColors";
import { cumulativeMiles } from "../../utils/geo";

export type SegmentProps = { color: string; level: RiskLevel };

export function riskSegments(route: RoutePlan): FeatureCollection<LineString, SegmentProps> {
  const coords = route.geometry;
  const raw = cumulativeMiles(coords);
  const scale = raw[raw.length - 1] > 0 ? route.distance_miles / raw[raw.length - 1] : 1;
  const miles = raw.map((m) => m * scale);
  const cps = route.checkpoints;

  const features = cps.flatMap((cp, i) => {
    const start = i === 0 ? 0 : (cps[i - 1].mile_marker + cp.mile_marker) / 2;
    const end = i === cps.length - 1 ? Infinity : (cp.mile_marker + cps[i + 1].mile_marker) / 2;

    let from = miles.findIndex((m) => m >= start);
    if (from < 0) from = coords.length - 1;
    let to = from;
    while (to + 1 < coords.length && miles[to + 1] <= end) to++;

    const slice = coords.slice(Math.max(0, from - 1), Math.min(coords.length, to + 2));
    if (slice.length < 2) return [];

    return [
      {
        type: "Feature" as const,
        properties: { color: RISK_COLORS[cp.risk_level], level: cp.risk_level },
        geometry: { type: "LineString" as const, coordinates: slice },
      },
    ];
  });

  return { type: "FeatureCollection", features };
}