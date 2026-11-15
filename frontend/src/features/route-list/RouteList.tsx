import { Stack, Typography } from "@mui/material";

import type { TripPlan } from "../../api/types";
import RouteCard from "./RouteCard";

interface Props {
  plan: TripPlan;
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
}

export default function RouteList({ plan, selectedRouteId, onSelectRoute }: Props) {
  const byId = new Map(plan.routes.map((r) => [r.id, r]));
  const ranked = plan.ranking.map((id) => byId.get(id)).filter((r) => r !== undefined);

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2" sx={{ color: "text.secondary" }}>
        Routes, safest first
      </Typography>
      {ranked.map((route) => (
        <RouteCard
          key={route.id}
          route={route}
          recommended={route.id === plan.recommended_route_id}
          selected={route.id === selectedRouteId}
          onSelect={() => onSelectRoute(route.id)}
        />
      ))}
    </Stack>
  );
}
