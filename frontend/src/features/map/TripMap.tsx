import type { FeatureCollection, LineString, Point } from "geojson";
import { useEffect, useMemo, useRef, useState } from "react";
import Map, {
  AttributionControl,
  Layer,
  type MapLayerMouseEvent,
  type MapRef,
  Marker,
  NavigationControl,
  Popup,
  Source,
} from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

import type { TripPlan } from "../../api/types";
import { RISK_COLORS } from "../../theme/riskColors";
import { boundsOf } from "../../utils/geo";
import CheckpointPopup from "./CheckpointPopup";
import maplibregl from "./maplibre";
import RiskLegend from "./RiskLegend";
import { riskSegments } from "./riskSegments";

const MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const INITIAL_VIEW = { longitude: -96, latitude: 39, zoom: 3.6 };
const WEATHER_ATTRIBUTION = 'Weather data by <a href="https://open-meteo.com/" target="_blank">Open-Meteo</a>';
const INTERACTIVE_LAYERS = ["checkpoints", "routes-hit"];
const EMPTY: FeatureCollection = { type: "FeatureCollection", features: [] };

interface Props {
  plan: TripPlan | undefined;
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
}

export default function TripMap({ plan, selectedRouteId, onSelectRoute }: Props) {
  const mapRef = useRef<MapRef>(null);
  const [popupIndex, setPopupIndex] = useState<number | null>(null);
  const [hovering, setHovering] = useState(false);

  const selected = plan?.routes.find((r) => r.id === selectedRouteId);
  const popupCheckpoint = selected?.checkpoints.find((c) => c.index === popupIndex);

  useEffect(() => {
    setPopupIndex(null);
    if (!plan) return;
    const bounds = boundsOf(plan.routes.flatMap((r) => r.geometry));
    mapRef.current?.fitBounds(bounds, { padding: 80, duration: 800 });
  }, [plan]);

  useEffect(() => setPopupIndex(null), [selectedRouteId]);

  const routesGeojson = useMemo<FeatureCollection<LineString, { id: string }>>(
    () => ({
      type: "FeatureCollection",
      features: (plan?.routes ?? []).map((r) => ({
        type: "Feature",
        properties: { id: r.id },
        geometry: { type: "LineString", coordinates: r.geometry },
      })),
    }),
    [plan],
  );

  const segmentsGeojson = useMemo(() => (selected ? riskSegments(selected) : EMPTY), [selected]);

  const checkpointsGeojson = useMemo<FeatureCollection<Point, { index: number; color: string }>>(
    () => ({
      type: "FeatureCollection",
      features: (selected?.checkpoints ?? []).map((cp) => ({
        type: "Feature",
        properties: { index: cp.index, color: RISK_COLORS[cp.risk_level] },
        geometry: { type: "Point", coordinates: [cp.lng, cp.lat] },
      })),
    }),
    [selected],
  );

  function handleClick(event: MapLayerMouseEvent) {
    const feature = event.features?.[0];
    if (!feature) {
      setPopupIndex(null);
      return;
    }
    if (feature.layer.id === "checkpoints") {
      setPopupIndex(Number(feature.properties.index));
    } else {
      onSelectRoute(String(feature.properties.id));
    }
  }

  const selectedId = selectedRouteId ?? "";
  const start = plan?.routes[0]?.geometry[0];
  const end = plan?.routes[0]?.geometry.at(-1);

  return (
    <>
      <Map
        ref={mapRef}
        mapLib={maplibregl}
        initialViewState={INITIAL_VIEW}
        mapStyle={MAP_STYLE}
        style={{ width: "100%", height: "100%" }}
        attributionControl={false}
        interactiveLayerIds={INTERACTIVE_LAYERS}
        onClick={handleClick}
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
        cursor={hovering ? "pointer" : "grab"}
      >
        <NavigationControl position="top-right" />
        <AttributionControl customAttribution={WEATHER_ATTRIBUTION} compact />

        <Source id="routes" type="geojson" data={routesGeojson}>
          <Layer
            id="routes-other"
            type="line"
            filter={["!=", ["get", "id"], selectedId]}
            layout={{ "line-cap": "round", "line-join": "round" }}
            paint={{ "line-color": "#78909c", "line-width": 4, "line-opacity": 0.7 }}
          />
          <Layer
            id="routes-hit"
            type="line"
            paint={{ "line-color": "#000", "line-width": 16, "line-opacity": 0 }}
          />
          <Layer
            id="route-selected-casing"
            type="line"
            filter={["==", ["get", "id"], selectedId]}
            layout={{ "line-cap": "round", "line-join": "round" }}
            paint={{ "line-color": "#0d1b2a", "line-width": 9 }}
          />
        </Source>

        <Source id="risk-segments" type="geojson" data={segmentsGeojson}>
          <Layer
            id="route-risk"
            type="line"
            layout={{ "line-cap": "round", "line-join": "round" }}
            paint={{ "line-color": ["get", "color"], "line-width": 5 }}
          />
        </Source>

        <Source id="checkpoints" type="geojson" data={checkpointsGeojson}>
          <Layer
            id="checkpoints"
            type="circle"
            paint={{
              "circle-radius": 5,
              "circle-color": ["get", "color"],
              "circle-stroke-color": "#fff",
              "circle-stroke-width": 1.5,
            }}
          />
        </Source>

        {start && <Marker longitude={start[0]} latitude={start[1]} color="#1565c0" />}
        {end && <Marker longitude={end[0]} latitude={end[1]} color="#c62828" />}

        {popupCheckpoint && (
          <Popup
            longitude={popupCheckpoint.lng}
            latitude={popupCheckpoint.lat}
            closeOnClick={false}
            onClose={() => setPopupIndex(null)}
            maxWidth="280px"
          >
            <CheckpointPopup checkpoint={popupCheckpoint} />
          </Popup>
        )}
      </Map>

      {plan && <RiskLegend />}
    </>
  );
}