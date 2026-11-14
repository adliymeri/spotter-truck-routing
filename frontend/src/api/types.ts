export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "SEVERE" | "NO_TRAVEL";

export interface LatLng {
  lat: number;
  lng: number;
}

export interface Place extends LatLng {
  label: string;
}

export interface Checkpoint {
  index: number;
  lat: number;
  lng: number;
  mile_marker: number;
  segment_miles: number;
  eta: string;
  wind_mph: number;
  rain_in_per_hr: number;
  snow_in_per_hr: number;
  risk_level: RiskLevel;
  risk_drivers: string[];
}

export interface RouteSummary {
  miles_by_level: Record<RiskLevel, number>;
  avg_risk: number;
  worst_level: RiskLevel;
}

export interface RoutePlan {
  id: string;
  distance_miles: number;
  duration_hours: number;
  arrival: string;
  geometry: [number, number][];
  summary: RouteSummary;
  checkpoints: Checkpoint[];
}

export interface TripPlan {
  recommended_route_id: string;
  ranking: string[];
  routes: RoutePlan[];
}

export type IntervalMiles = 10 | 25 | 50;

export interface PlanRequest {
  origin: LatLng;
  destination: LatLng;
  departure: string;
  weight_lb: number;
  interval_miles: IntervalMiles;
}

export interface HeatmapRequest {
  corridor: LatLng[];
  start: string;
  hours: number;
  weight_lb: number;
}

export interface Heatmap {
  start: string;
  hours: number;
  spacing_miles: number;
  points: [number, number][];
  frames: number[][];
}