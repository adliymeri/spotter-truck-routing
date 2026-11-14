import Map, { AttributionControl, NavigationControl } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import maplibregl from "./maplibre";

const MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const INITIAL_VIEW = { longitude: -96, latitude: 39, zoom: 3.6 };
const WEATHER_ATTRIBUTION = 'Weather data by <a href="https://open-meteo.com/" target="_blank">Open-Meteo</a>';

export default function TripMap() {
  return (
    <Map
      mapLib={maplibregl}
      initialViewState={INITIAL_VIEW}
      mapStyle={MAP_STYLE}
      style={{ width: "100%", height: "100%" }}
      attributionControl={false}
    >
      <NavigationControl position="top-right" />
      <AttributionControl customAttribution={WEATHER_ATTRIBUTION} compact />
    </Map>
  );
}