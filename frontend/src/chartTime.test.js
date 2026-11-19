import test from "node:test";
import assert from "node:assert/strict";
import { formatCountdown, liveConnects, mergeLiveCandle, secondsToClose } from "./chartTime.js";

test("countdown to the candle close", () => {
  const hour = 1_800_000_000 - (1_800_000_000 % 3600);
  assert.equal(secondsToClose(hour + 125, 5), 175);
  assert.equal(secondsToClose(hour + 125, 1), 55);
  assert.equal(secondsToClose(hour + 125, 60), 3475);
  assert.equal(secondsToClose(hour, 15), 900);
  assert.equal(formatCountdown(135), "02:15");
  assert.equal(formatCountdown(3725), "1:02:05");
  assert.equal(formatCountdown(-3), "00:00");
});

test("live 5m candle folds into a longer candle without losing its history", () => {
  const h = 1_800_000_000 - (1_800_000_000 % 3600);
  const base = { time: h, open: 100, high: 110, low: 95, close: 105 };
  const live = { time: h + 1200, open: 105, high: 112, low: 101, close: 108 };
  assert.deepEqual(mergeLiveCandle(base, live, 60), { time: h, open: 100, high: 112, low: 95, close: 108 });
  // A new hour starts: the live candle opens a new one.
  assert.deepEqual(mergeLiveCandle(base, { ...live, time: h + 3600 }, 60), { time: h + 3600, open: 105, high: 112, low: 101, close: 108 });
  // 5m: same as showing the preview candle itself.
  assert.deepEqual(mergeLiveCandle({ ...base, time: h + 900 }, live, 5), live);
});

test("a live quote days after stale history is not glued on", () => {
  const base = { time: 1_800_000_000, open: 1, high: 1, low: 1, close: 1 };
  const live = { time: 1_800_000_000 + 4 * 86400, open: 2, high: 2, low: 2, close: 2 };
  assert.equal(liveConnects(base, live, 5), false);
  assert.equal(mergeLiveCandle(base, live, 5), null);
  assert.equal(liveConnects(base, { ...live, time: base.time + 300 }, 5), true);
});

test("no live candle on 1m or when older than history", () => {
  const live = { time: 1_800_000_000, open: 1, high: 1, low: 1, close: 1 };
  assert.equal(mergeLiveCandle(null, live, 1), null);
  assert.equal(mergeLiveCandle({ time: 1_800_000_000 + 3600, open: 1, high: 1, low: 1, close: 1 }, live, 5), null);
});
