// "Why WAIT?" — turns the scanner snapshot (/api/scanner), the paper account (/api/overview) and the latest paper
// signals (/api/signals) into plain-English reasons. Pure function: no fetching, no clock, easy to test.
// It only explains what the backend already decided; it never creates or ranks a signal.
import { isScanFresh } from "./sessions.js";

export const CATEGORIES = {
  data: { label: "Missing or stale data", order: 1 },
  closed: { label: "Market closed", order: 2 },
  unproven: { label: "Unproven strategy", order: 3 },
  news: { label: "News blackout", order: 4 },
  cost: { label: "Spread too expensive", order: 5 },
  risk: { label: "Risk limit", order: 6 },
  setup: { label: "No setup now", order: 7 },
};

const MAX_COST_SHARE = 0.2;          // same 20% rule as backend/app/core/scanner.py
const RECENT_SIGNAL_SECONDS = 15 * 60;
const pct = (x) => `${Math.round(x * 100)}%`;
const list = (xs) => [...new Set(xs)].join(", ");

export function whyWait({ scan, ov, signals = [], now }) {
  const reasons = [];
  const add = (category, title, detail) => reasons.push({ category, title, detail });

  if (!scan && !ov) {
    add("data", "The dashboard cannot reach the backend",
      "Without the backend there is no data, so nothing can be checked. Start it, then this panel fills in.");
    return finish("UNKNOWN", reasons);
  }

  // --- Scanner (signals-only, 3 markets) ---
  const scanFresh = scan && isScanFresh(scan.scanned_ts, now);
  const markets = scan?.markets ?? [];
  const setups = markets.flatMap((m) => m.setups ?? []);
  const signal = scan?.signal && scanFresh && now < scan.signal.expiry_ts ? scan.signal : null;

  if (!scan) {
    add("data", "Scanner results are not available", "The scanner endpoint did not answer, so no market could be checked.");
  } else if (!scanFresh) {
    const mins = scan.scanned_ts ? Math.round((now - scan.scanned_ts) / 60) : null;
    add("data", "The scanner has stopped updating",
      mins == null ? "It has not run since the backend started." : `Its last scan was ${mins} min ago, so its view is out of date.`);
  }

  const bad = markets.filter((m) => m.state === "stale" || m.state === "no data");
  for (const m of bad) add("data", `${m.label}: ${m.state === "stale" ? "price feed is stale" : "no price data"}`, m.detail);

  if (markets.length && markets.every((m) => m.state === "closed")) {
    add("closed", "All markets are outside their trading windows",
      "NAS100 and gold trade weekdays 03:00-15:55 New York time; BTC only at weekends.");
  }

  if (scan && !(scan.qualified_strategies ?? []).length) {
    const practice = setups.filter((s) => !s.qualified).length;
    add("unproven", "No strategy has passed its test",
      "Every strategy failed its pre-registered backtest (see the experiment journal), so the scanner never shows " +
      "a signal from one." + (practice ? ` ${practice} setup(s) on the latest bar are practice only.` : ""));
  } else {
    const unq = setups.filter((s) => !s.qualified);
    if (unq.length) add("unproven", `${unq.length} setup(s) come from strategies that failed their test`,
      `Practice only: ${list(unq.map((s) => s.strategy))}.`);
  }

  const blackout = ov?.news?.blackout_now;
  if (blackout) add("news", `High-impact news: ${blackout}`, "No new entries within 30 minutes of this event.");
  else if (setups.some((s) => s.news_blackout)) add("news", "A setup falls inside a news blackout", "No new entries near high-impact news.");
  if (ov?.news && ov.news.calendar_covers_now === false) {
    add("data", "The news calendar does not cover today",
      `It is only filled in until ${ov.news.calendar_until}. Without it the system cannot rule out news, so it waits.`);
  }

  const pricey = setups.filter((s) => s.cost_share > MAX_COST_SHARE);
  if (pricey.length) {
    const worst = Math.max(...pricey.map((s) => s.cost_share));
    add("cost", `${pricey.length} setup(s) would spend too much on costs`,
      `Spread and slippage would take up to ${pct(worst)} of the money at risk; the limit is ${pct(MAX_COST_SHARE)}. ` +
      "A small stop makes the fixed spread a big share of the risk.");
  }

  const openFresh = markets.filter((m) => m.state === "open");
  const noSetup = openFresh.filter((m) => !(m.setups ?? []).length);
  if (scanFresh && noSetup.length) {
    add("setup", `No setup on the latest bar: ${list(noSetup.map((m) => m.label))}`,
      "The strategies' entry rules were not met. Waiting is the normal result most of the time.");
  }

  // --- Paper engine (the simulated account) ---
  if (ov) {
    const rs = ov.risk_settings ?? {};
    if (ov.kill_switch) add("risk", "The kill switch is ON", "All trading is blocked until you reset it.");
    if (ov.engine_enabled === false) add("data", "The paper engine is not running", "ENGINE_ENABLED is off, so it records nothing.");
    if (ov.auto_trading === false && !ov.kill_switch) {
      add("risk", "Auto-trading is OFF", "The paper engine records signals but places no simulated orders.");
    }
    if (rs.max_trades_per_day != null && ov.trades_today >= rs.max_trades_per_day) {
      add("risk", `Daily trade limit reached (${ov.trades_today}/${rs.max_trades_per_day})`, "No more trades today.");
    }
    if (rs.max_consecutive_losses != null && ov.consecutive_losses_today >= rs.max_consecutive_losses) {
      add("risk", `${ov.consecutive_losses_today} losses in a row today`, "The anti-revenge rule stops trading for the rest of the day.");
    }
    if (rs.daily_loss_pct != null && ov.day_pnl_pct <= -rs.daily_loss_pct) {
      add("risk", "Daily loss limit reached", `Today is ${ov.day_pnl_pct.toFixed(2)}%; the limit is -${rs.daily_loss_pct}%.`);
    }
    if (rs.weekly_loss_pct != null && ov.week_pnl_pct <= -rs.weekly_loss_pct) {
      add("risk", "Weekly loss limit reached", `This week is ${ov.week_pnl_pct.toFixed(2)}%; the limit is -${rs.weekly_loss_pct}%.`);
    }
    for (const b of ov.markets ?? []) {
      if (b.enabled && b.open_now && b.stale) add("data", `${b.label} paper book: price feed is stale`, "The paper engine skips stale data.");
    }
    const last = signals.find((s) => s.action && s.action !== "WAIT");
    if (last && now - last.bar_close_ts <= RECENT_SIGNAL_SECONDS && !last.risk_approved && (last.risk_reasons ?? []).length) {
      add("risk", `The last paper signal was rejected (${last.strategy}, ${last.action})`, last.risk_reasons.join("; "));
    }
  }

  return finish(signal ? "SIGNAL" : "WAIT", reasons);
}

function finish(state, reasons) {
  const sorted = [...reasons].sort((a, b) => CATEGORIES[a.category].order - CATEGORIES[b.category].order);
  const headline = state === "SIGNAL"
    ? "A signal from a qualified strategy is showing. It is not a guarantee."
    : sorted.length ? `WAIT, mainly because: ${sorted[0].title.charAt(0).toLowerCase()}${sorted[0].title.slice(1)}.`
      : "WAIT: no reason was reported.";
  return { state, headline, reasons: sorted };
}
