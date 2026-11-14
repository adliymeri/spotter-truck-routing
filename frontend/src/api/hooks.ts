import { keepPreviousData, useMutation, useQuery } from "@tanstack/react-query";

import { api } from "./client";
import type { PlanRequest } from "./types";

const MIN_QUERY_LENGTH = 2;

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