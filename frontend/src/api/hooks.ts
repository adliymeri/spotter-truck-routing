import { keepPreviousData, useMutation, useQuery } from "@tanstack/react-query";

import { api } from "./client";
import type { LatLng, PlanRequest, TripPlan } from "./types";

const MIN_QUERY_LENGTH = 2;
const MAX_CORRIDOR_POINTS = 2000;
export const HEATMAP_HOURS = 48;

export function usePlaceSearch(query: string) {
  const q = query.trim();
  return useQuery({
    queryKey: ["geocode", q],
    queryFn: ({ signal }) => api.geocode(q, signal),
    enabled: q.length >= MIN_QUERY_LENGTH,
    staleTime: 5 * 60_000,
    placeholderData: keepPreviousData,
  });
}

export function usePlanTrip() {
  return useMutation({ mutationFn: (body: PlanRequest) => api.plan(body) });
}

function corridorOf(plan: TripPlan): LatLng[] {
  const seen = new Set<string>();
  const points: LatLng[] = [];
  for (const route of plan.routes) {
    for (const cp of route.checkpoints) {
      const key = `${cp.lat.toFixed(2)},${cp.lng.toFixed(2)}`;
      if (!seen.has(key)) {
        seen.add(key);
        points.push({ lat: cp.lat, lng: cp.lng });
      }
    }
  }
  return points.slice(0, MAX_CORRIDOR_POINTS);
}

export function useHeatmap(plan: TripPlan | undefined, request: PlanRequest | undefined) {
  return useQuery({
    queryKey: ["heatmap", plan?.ranking, request],
    queryFn: () =>
      api.heatmap({
        corridor: corridorOf(plan!),
        start: request!.departure,
        hours: HEATMAP_HOURS,
        weight_lb: request!.weight_lb,
      }),
    enabled: Boolean(plan && request),
    staleTime: 10 * 60_000,
  });
}