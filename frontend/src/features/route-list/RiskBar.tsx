import { Box, Tooltip } from "@mui/material";

import type { RiskLevel } from "../../api/types";
import { RISK_COLORS, RISK_LABELS, RISK_LEVELS } from "../../theme/riskColors";
import { formatMiles } from "../../utils/format";

export default function RiskBar({ milesByLevel }: { milesByLevel: Record<RiskLevel, number> }) {
  const total = RISK_LEVELS.reduce((sum, level) => sum + milesByLevel[level], 0) || 1;

  return (
    <Box sx={{ display: "flex", height: 8, borderRadius: 1, overflow: "hidden", bgcolor: "grey.200" }}>
      {RISK_LEVELS.filter((level) => milesByLevel[level] > 0).map((level) => (
        <Tooltip key={level} title={`${RISK_LABELS[level]}: ${formatMiles(milesByLevel[level])}`}>
          <Box sx={{ width: `${(milesByLevel[level] / total) * 100}%`, bgcolor: RISK_COLORS[level] }} />
        </Tooltip>
      ))}
    </Box>
  );
}