import PauseIcon from "@mui/icons-material/Pause";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import {
  CircularProgress,
  FormControlLabel,
  IconButton,
  Paper,
  Slider,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";

import { formatDateTime } from "../../utils/format";

const PLAY_STEP_MS = 500;
const MARKS = [0, 12, 24, 36, 48].map((value) => ({ value, label: `${value} h` }));

interface Props {
  start: string;
  hours: number;
  hour: number;
  onHourChange: (hour: number) => void;
  visible: boolean;
  onVisibleChange: (visible: boolean) => void;
  loading: boolean;
  error?: string;
}

export default function ForecastSlider({
  start,
  hours,
  hour,
  onHourChange,
  visible,
  onVisibleChange,
  loading,
  error,
}: Props) {
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (!playing) return;
    const id = setTimeout(() => onHourChange(hour >= hours ? 0 : hour + 1), PLAY_STEP_MS);
    return () => clearTimeout(id);
  }, [playing, hour, hours, onHourChange]);

  const time = new Date(new Date(start).getTime() + hour * 3_600_000).toISOString();

  return (
    <Paper
      elevation={3}
      sx={{
        position: "absolute",
        left: "50%",
        bottom: 28,
        transform: "translateX(-50%)",
        width: "min(560px, calc(100% - 260px))",
        px: 2.5,
        py: 1.5,
      }}
    >
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", justifyContent: "space-between" }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          <IconButton
            size="small"
            onClick={() => setPlaying((p) => !p)}
            disabled={!visible || loading}
            aria-label={playing ? "Pause forecast" : "Play forecast"}
          >
            {playing ? <PauseIcon /> : <PlayArrowIcon />}
          </IconButton>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            Forecast +{hour} h
          </Typography>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            {formatDateTime(time)}
          </Typography>
          {loading && <CircularProgress size={16} />}
        </Stack>
        <FormControlLabel
          control={
            <Switch size="small" checked={visible} onChange={(e) => onVisibleChange(e.target.checked)} />
          }
          label={<Typography variant="body2">Heatmap</Typography>}
        />
      </Stack>

      {error ? (
        <Typography variant="body2" sx={{ color: "error.main", mt: 1 }}>
          {error}
        </Typography>
      ) : (
        <Slider
          size="small"
          min={0}
          max={hours}
          step={1}
          value={hour}
          marks={MARKS}
          disabled={!visible}
          onChange={(_, value) => onHourChange(value as number)}
          aria-label="Forecast hour"
          sx={{ mt: 0.5 }}
        />
      )}
    </Paper>
  );
}
