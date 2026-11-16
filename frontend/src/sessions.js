const clocks = Object.fromEntries(["America/New_York", "Europe/London"].map(zone => [zone,
  new Intl.DateTimeFormat("en-GB", { timeZone: zone, weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" })]));

function clock(date, zone) {
  const parts = Object.fromEntries(clocks[zone].formatToParts(date).map(p => [p.type, p.value]));
  return { minute: Number(parts.hour) * 60 + Number(parts.minute), day: parts.weekday,
    label: `${parts.hour}:${parts.minute}` };
}

export function sessionState(date) {
  const ny = clock(date, "America/New_York");
  const london = clock(date, "Europe/London");
  const weekday = !["Sat", "Sun"].includes(ny.day);
  const asia = (ny.minute >= 1080 && ["Sun", "Mon", "Tue", "Wed", "Thu"].includes(ny.day))
    || (weekday && ny.minute < 720 && london.minute < 480);
  return { asia, london: weekday && london.minute >= 485 && london.minute <= 600,
    ny: weekday && ny.minute >= 575 && ny.minute <= 900,
    nyClock: ny.label, londonClock: london.label };
}

export function nextWindow(date, key) {
  const start = Math.floor(date.getTime() / 60000) * 60000;
  for (let offset = 1; offset <= 8 * 24 * 60; offset++) {
    const candidate = new Date(start + offset * 60000);
    if (sessionState(candidate)[key]) return candidate;
  }
  return null;
}

export function isScanFresh(timestamp, nowSeconds) {
  const age = nowSeconds - timestamp;
  return Number.isFinite(timestamp) && timestamp > 0 && age >= 0 && age <= 60;
}
