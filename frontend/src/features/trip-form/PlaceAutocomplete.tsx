import { Autocomplete, TextField } from "@mui/material";
import { useState } from "react";

import { usePlaceSearch } from "../../api/hooks";
import type { Place } from "../../api/types";
import { useDebouncedValue } from "../../utils/useDebouncedValue";

interface Props {
  label: string;
  value: Place | null;
  onChange: (place: Place | null) => void;
}

const samePlace = (a: Place, b: Place) => a.label === b.label && a.lat === b.lat && a.lng === b.lng;

export default function PlaceAutocomplete({ label, value, onChange }: Props) {
  const [input, setInput] = useState("");
  const debounced = useDebouncedValue(input, 300);
  const { data = [], isFetching } = usePlaceSearch(debounced);

  const options = value && !data.some((p) => samePlace(p, value)) ? [value, ...data] : data;

  return (
    <Autocomplete
      value={value}
      onChange={(_, place) => onChange(place)}
      inputValue={input}
      onInputChange={(_, text) => setInput(text)}
      options={options}
      filterOptions={(x) => x}
      getOptionLabel={(p) => p.label}
      isOptionEqualToValue={samePlace}
      loading={isFetching}
      noOptionsText={input.trim().length < 2 ? "Type at least 2 characters" : "No places found"}
      renderInput={(params) => <TextField {...params} label={label} />}
    />
  );
}