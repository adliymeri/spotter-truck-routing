import { Alert, Box, Divider, Paper, Typography } from "@mui/material";

import { usePlanTrip } from "./api/hooks";
import TripMap from "./features/map/TripMap";
import TripForm from "./features/trip-form/TripForm";

export default function App() {
  const planTrip = usePlanTrip();

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <Paper
        square
        elevation={3}
        sx={{ width: 400, flexShrink: 0, p: 2.5, overflowY: "auto", zIndex: 1 }}
      >
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          Weather-Aware Truck Routing
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
          Compare routes by weather risk, load and travel time.
        </Typography>

        <TripForm onSubmit={(request) => planTrip.mutate(request)} isLoading={planTrip.isPending} />

        <Divider sx={{ my: 2.5 }} />

        {planTrip.isError && <Alert severity="error">{planTrip.error.message}</Alert>}

        {planTrip.data && (
          <Typography variant="body2">
            Got {planTrip.data.routes.length} routes. Recommended: {planTrip.data.recommended_route_id}
          </Typography>
        )}
      </Paper>

      <Box sx={{ flex: 1, position: "relative" }}>
        <TripMap />
      </Box>
    </Box>
  );
}