import type { RiskLevel } from "../api/types";

export const RISK_LEVELS: RiskLevel[] = ["LOW", "MODERATE", "HIGH", "SEVERE", "NO_TRAVEL"];

export const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: "#2e7d32",
  MODERATE: "#f9a825",
  HIGH: "#ef6c00",
  SEVERE: "#c62828",
  NO_TRAVEL: "#6a1b9a",
};

export const RISK_LABELS: Record<RiskLevel, string> = {
  LOW: "Low",
  MODERATE: "Moderate",
  HIGH: "High",
  SEVERE: "Severe",
  NO_TRAVEL: "No Travel",
};
