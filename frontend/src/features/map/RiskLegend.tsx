import { Box, Paper, Stack, Typography } from "@mui/material";

import { RISK_COLORS, RISK_LABELS, RISK_LEVELS } from "../../theme/riskColors";

export default function RiskLegend() {
  return (
    <Paper elevation={2} sx={{ position: "absolute", left: 12, bottom: 28, px: 1.5, py: 1 }}>
      <Typography variant="caption" sx={{ fontWeight: 700 }}>
        Weather risk
      </Typography>
      <Stack spacing={0.25} sx={{ mt: 0.5 }}>
        {RISK_LEVELS.map((level) => (
          <Stack key={level} direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Box sx={{ width: 14, height: 6, borderRadius: 1, bgcolor: RISK_COLORS[level] }} />
            <Typography variant="caption">{RISK_LABELS[level]}</Typography>
          </Stack>
        ))}
      </Stack>
    </Paper>
  );
}
