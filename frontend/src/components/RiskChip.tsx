import { Chip } from "@mui/material";

import type { RiskLevel } from "../api/types";
import { RISK_COLORS, RISK_LABELS } from "../theme/riskColors";

export default function RiskChip({ level }: { level: RiskLevel }) {
  return (
    <Chip
      size="small"
      label={RISK_LABELS[level]}
      sx={{
        bgcolor: RISK_COLORS[level],
        color: level === "MODERATE" ? "rgba(0,0,0,0.87)" : "#fff",
        fontWeight: 600,
      }}
    />
  );
}
