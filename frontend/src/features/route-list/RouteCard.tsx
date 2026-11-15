import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { Card, CardActionArea, Chip, Stack, Typography } from "@mui/material";

import type { RoutePlan } from "../../api/types";
import RiskChip from "../../components/RiskChip";
import { formatDateTime, formatDuration, formatMiles } from "../../utils/format";
import RiskBar from "./RiskBar";

interface Props {
  route: RoutePlan;
  recommended: boolean;
  selected: boolean;
  onSelect: () => void;
}

export default function RouteCard({ route, recommended, selected, onSelect }: Props) {
  const { miles_by_level: miles } = route.summary;

  return (
    <Card
      variant="outlined"
      sx={{ borderColor: selected ? "primary.main" : "divider", borderWidth: selected ? 2 : 1 }}
    >
      <CardActionArea onClick={onSelect} sx={{ p: 1.5 }}>
        <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
          <Typography sx={{ fontWeight: 700 }}>Route {route.id.replace("route-", "")}</Typography>
          {recommended && (
            <Chip size="small" color="success" icon={<CheckCircleIcon />} label="Recommended" />
          )}
        </Stack>

        <Typography variant="body2">
          {formatMiles(route.distance_miles)} · {formatDuration(route.duration_hours)}
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 1 }}>
          Arrives {formatDateTime(route.arrival)}
        </Typography>

        <RiskBar milesByLevel={miles} />

        <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center", flexWrap: "wrap" }}>
          <RiskChip level={route.summary.worst_level} />
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            Severe {formatMiles(miles.SEVERE + miles.NO_TRAVEL)} · High {formatMiles(miles.HIGH)} · Avg risk{" "}
            {route.summary.avg_risk.toFixed(2)}
          </Typography>
        </Stack>
      </CardActionArea>
    </Card>
  );
}
