function pad(n: number): string {
  return String(n).padStart(2, "0");
}

export function nextFullHourLocal(): string {
  const d = new Date();
  d.setMinutes(0, 0, 0);
  d.setHours(d.getHours() + 1);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`;
}

export function localInputToIso(value: string): string {
  return new Date(value).toISOString();
}