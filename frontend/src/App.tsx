import { Alert, Box, Divider, Paper, Typography } from "@mui/material";
import { useState } from "react";

import { HEATMAP_HOURS, useHeatmap, usePlanTrip } from "./api/hooks";
import type { PlanRequest } from "./api/types";
import ForecastSlider from "./features/map/ForecastSlider";
import TripMap from "./features/map/TripMap";
import RouteList from "./features/route-list/RouteList";
import TripForm from "./features/trip-form/TripForm";

export default function App() {
  const planTrip = usePlanTrip();
  const heatmap = useHeatmap(planTrip.data, planTrip.variables);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [hour, setHour] = useState(0);
  const [showHeatmap, setShowHeatmap] = useState(true);

  function handlePlan(request: PlanRequest) {
    planTrip.mutate(request, {
      onSuccess: (plan) => {
        setSelectedRouteId(plan.recommended_route_id);
        setHour(0);
      },
    });
  }

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <Paper square elevation={3} sx={{ width: 400, flexShrink: 0, p: 2.5, overflowY: "auto", zIndex: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          Weather-Aware Truck Routing
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
          Compare routes by weather risk, load and travel time.
        </Typography>

        <TripForm onSubmit={handlePlan} isLoading={planTrip.isPending} />

        <Divider sx={{ my: 2.5 }} />

        {planTrip.isError && <Alert severity="error">{planTrip.error.message}</Alert>}

        {planTrip.data && (
          <RouteList
            plan={planTrip.data}
            selectedRouteId={selectedRouteId}
            onSelectRoute={setSelectedRouteId}
          />
        )}
      </Paper>

      <Box sx={{ flex: 1, position: "relative" }}>
        <TripMap
          plan={planTrip.data}
          selectedRouteId={selectedRouteId}
          onSelectRoute={setSelectedRouteId}
          heatmap={showHeatmap ? heatmap.data : undefined}
          hour={hour}
        />

        {planTrip.data && planTrip.variables && (
          <ForecastSlider
            start={planTrip.variables.departure}
            hours={HEATMAP_HOURS}
            hour={hour}
            onHourChange={setHour}
            visible={showHeatmap}
            onVisibleChange={setShowHeatmap}
            loading={heatmap.isFetching}
            error={heatmap.error?.message}
          />
        )}
      </Box>
    </Box>
  );
}
