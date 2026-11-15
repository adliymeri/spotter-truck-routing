import type { FeatureCollection, Point } from "geojson";
import type { ExpressionSpecification } from "maplibre-gl";
import { useMemo } from "react";
import { Layer, Source } from "react-map-gl/maplibre";

import type { Heatmap } from "../../api/types";
import { RISK_COLORS } from "../../theme/riskColors";

const METERS_PER_MILE = 1609.34;
const METERS_PER_PIXEL_AT_ZOOM_0 = 156543.03;
const MAX_ZOOM = 20;
const COVERAGE = 1.6;

interface Props {
  heatmap: Heatmap;
  hour: number;
  beforeId: string;
}

export default function WeatherHeatmap({ heatmap, hour, beforeId }: Props) {
  const data = useMemo<FeatureCollection<Point>>(
    () => ({
      type: "FeatureCollection",
      features: heatmap.points.map((coord, i) => ({
        type: "Feature",
        properties: Object.fromEntries(heatmap.frames.map((frame, h) => [`h${h}`, frame[i]])),
        geometry: { type: "Point", coordinates: coord },
      })),
    }),
    [heatmap],
  );

  const radius = useMemo(() => {
    const meanLat = heatmap.points.reduce((sum, [, lat]) => sum + lat, 0) / (heatmap.points.length || 1);
    const metersPerPixel = METERS_PER_PIXEL_AT_ZOOM_0 * Math.cos((meanLat * Math.PI) / 180);
    const r0 = (heatmap.spacing_miles * METERS_PER_MILE * COVERAGE) / metersPerPixel;
    return [
      "interpolate",
      ["exponential", 2],
      ["zoom"],
      0,
      r0,
      MAX_ZOOM,
      r0 * 2 ** MAX_ZOOM,
    ] as ExpressionSpecification;
  }, [heatmap]);

  const color = [
    "match",
    ["get", `h${hour}`],
    0,
    RISK_COLORS.LOW,
    1,
    RISK_COLORS.MODERATE,
    2,
    RISK_COLORS.HIGH,
    3,
    RISK_COLORS.SEVERE,
    4,
    RISK_COLORS.NO_TRAVEL,
    "#9e9e9e",
  ] as ExpressionSpecification;

  return (
    <Source id="weather-heatmap" type="geojson" data={data}>
      <Layer
        id="weather-heatmap"
        type="circle"
        beforeId={beforeId}
        paint={{
          "circle-radius": radius,
          "circle-color": color,
          "circle-opacity": 0.35,
          "circle-blur": 1,
        }}
      />
    </Source>
  );
}
