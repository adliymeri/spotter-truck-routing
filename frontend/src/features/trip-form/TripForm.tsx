import {
  Alert,
  Box,
  Button,
  InputAdornment,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { type FormEvent, useState } from "react";

import type { IntervalMiles, Place, PlanRequest } from "../../api/types";
import { localInputToIso, nextFullHourLocal } from "../../utils/format";
import PlaceAutocomplete from "./PlaceAutocomplete";

const INTERVALS: IntervalMiles[] = [10, 25, 50];
const DEFAULT_WEIGHT_LB = 40_000;
const MAX_WEIGHT_LB = 200_000;

interface Props {
  onSubmit: (request: PlanRequest) => void;
  isLoading: boolean;
}

export default function TripForm({ onSubmit, isLoading }: Props) {
  const [origin, setOrigin] = useState<Place | null>(null);
  const [destination, setDestination] = useState<Place | null>(null);
  const [departure, setDeparture] = useState(nextFullHourLocal);
  const [weight, setWeight] = useState(String(DEFAULT_WEIGHT_LB));
  const [intervalMiles, setIntervalMiles] = useState<IntervalMiles>(25);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!origin || !destination) {
      setError("Choose an origin and a destination from the list.");
      return;
    }
    const weightLb = Number(weight);
    if (!Number.isFinite(weightLb) || weightLb <= 0 || weightLb > MAX_WEIGHT_LB) {
      setError(`Enter a load weight between 1 and ${MAX_WEIGHT_LB.toLocaleString()} lb.`);
      return;
    }
    if (!departure) {
      setError("Choose a departure time.");
      return;
    }
    setError(null);
    onSubmit({
      origin: { lat: origin.lat, lng: origin.lng },
      destination: { lat: destination.lat, lng: destination.lng },
      departure: localInputToIso(departure),
      weight_lb: weightLb,
      interval_miles: intervalMiles,
    });
  }

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      <Stack spacing={2}>
        <PlaceAutocomplete label="Origin" value={origin} onChange={setOrigin} />
        <PlaceAutocomplete label="Destination" value={destination} onChange={setDestination} />

        <TextField
          label="Departure"
          type="datetime-local"
          value={departure}
          onChange={(e) => setDeparture(e.target.value)}
          slotProps={{ inputLabel: { shrink: true } }}
        />

        <TextField
          label="Load weight"
          type="number"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          slotProps={{
            input: { endAdornment: <InputAdornment position="end">lb</InputAdornment> },
            htmlInput: { min: 1, max: MAX_WEIGHT_LB, step: 1000 },
          }}
        />

        <Box>
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 0.5 }}>
            Check weather every
          </Typography>
          <ToggleButtonGroup
            exclusive
            fullWidth
            size="small"
            value={intervalMiles}
            onChange={(_, value: IntervalMiles | null) => value && setIntervalMiles(value)}
          >
            {INTERVALS.map((miles) => (
              <ToggleButton key={miles} value={miles}>
                {miles} mi
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        {error && <Alert severity="warning">{error}</Alert>}

        <Button type="submit" variant="contained" size="large" disabled={isLoading}>
          {isLoading ? "Planning…" : "Plan route"}
        </Button>
      </Stack>
    </Box>
  );
}