import { Box, Paper, Typography } from "@mui/material";

import TripMap from "./features/map/TripMap";

export default function App() {
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
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          Compare routes by weather risk, load and travel time.
        </Typography>
      </Paper>

      <Box sx={{ flex: 1, position: "relative" }}>
        <TripMap />
      </Box>
    </Box>
  );
}