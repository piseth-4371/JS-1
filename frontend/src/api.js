// Small helpers to talk to the FastAPI backend (proxied by Vite at /api).

export async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} -> HTTP ${r.status}`);
  return r.json();
}

export async function postJSON(path, body = {}) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `${path} -> HTTP ${r.status}`);
  return data;
}

// ---------- formatting ----------
const nyFmt = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York", month: "short", day: "2-digit",
  hour: "2-digit", minute: "2-digit", hour12: false,
});

/** Epoch seconds -> "Nov 13, 10:35" in New York time. */
export const nyTime = (ts) => (ts ? nyFmt.format(new Date(ts * 1000)) : "-");

export const money = (x, digits = 2) =>
  x == null ? "-" : `${x < 0 ? "-" : ""}$${Math.abs(x).toFixed(digits)}`;

export const pct = (x) => (x == null ? "-" : `${x >= 0 ? "+" : ""}${x.toFixed(2)}%`);

export const num = (x, d = 2) => (x == null ? "-" : Number(x).toFixed(d));

export const sideText = (s) => (s === 1 ? "LONG" : s === -1 ? "SHORT" : "-");
