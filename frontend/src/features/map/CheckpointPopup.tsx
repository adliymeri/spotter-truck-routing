import { Stack, Typography } from "@mui/material";

import type { Checkpoint } from "../../api/types";
import RiskChip from "../../components/RiskChip";
import { formatDateTime } from "../../utils/format";

export default function CheckpointPopup({ checkpoint: cp }: { checkpoint: Checkpoint }) {
  return (
    <Stack spacing={0.5} sx={{ minWidth: 210 }}>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
          Mile {Math.round(cp.mile_marker)}
        </Typography>
        <RiskChip level={cp.risk_level} />
      </Stack>
      <Typography variant="body2" sx={{ color: "text.secondary" }}>
        ETA {formatDateTime(cp.eta)}
      </Typography>
      <Typography variant="body2">Wind {cp.wind_mph} mph</Typography>
      <Typography variant="body2">Rain {cp.rain_in_per_hr} in/hr</Typography>
      <Typography variant="body2">Snow {cp.snow_in_per_hr} in/hr</Typography>
      {cp.risk_drivers.length > 0 && (
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          Caused by: {cp.risk_drivers.join(", ")}
        </Typography>
      )}
    </Stack>
  );
}
