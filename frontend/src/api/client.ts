import type { Heatmap, HeatmapRequest, Place, PlanRequest, TripPlan } from "./types";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function errorMessage(body: unknown): string | null {
  if (!body || typeof body !== "object") return null;
  if ("detail" in body && typeof body.detail === "string") return body.detail;
  const [first] = Object.entries(body);
  if (!first) return null;
  const [field, value] = first;
  const message = Array.isArray(value) ? value[0] : value;
  return `${field}: ${typeof message === "string" ? message : JSON.stringify(message)}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(errorMessage(body) ?? `Request failed (${response.status})`, response.status);
  }
  return body as T;
}

export const api = {
  geocode: (q: string, signal?: AbortSignal) =>
    request<{ results: Place[] }>(`/geocode/?q=${encodeURIComponent(q)}`, { signal }).then((r) => r.results),

  plan: (body: PlanRequest) =>
    request<TripPlan>("/plan/", { method: "POST", body: JSON.stringify(body) }),

  heatmap: (body: HeatmapRequest) =>
    request<Heatmap>("/heatmap/", { method: "POST", body: JSON.stringify(body) }),
};