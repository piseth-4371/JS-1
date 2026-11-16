import test from "node:test";
import assert from "node:assert/strict";
import { isScanFresh, nextWindow, sessionState } from "./sessions.js";
import { getJSON } from "./api.js";

test("session clocks follow London and New York DST independently", () => {
  for (const instant of ["2026-11-16T08:05:00Z", "2026-03-16T08:05:00Z", "2026-07-13T07:05:00Z"]) {
    assert.equal(sessionState(new Date(instant)).london, true);
  }
  assert.equal(sessionState(new Date("2026-11-16T14:34:00Z")).ny, false);
  assert.equal(sessionState(new Date("2026-11-16T14:35:00Z")).ny, true);
  assert.equal(sessionState(new Date("2026-11-14T08:05:00Z")).london, false);
  assert.equal(sessionState(new Date("2026-11-16T01:00:00Z")).asia, true);
  assert.equal(nextWindow(new Date("2026-11-14T12:00:00Z"), "london").toISOString(), "2026-11-16T08:05:00.000Z");
});

test("freshness rejects missing, stale and future scans", () => {
  for (const timestamp of [null, undefined, NaN, 0, 939, 1001]) assert.equal(isScanFresh(timestamp, 1000), false);
  assert.equal(isScanFresh(940, 1000), true);
  assert.equal(isScanFresh(1000, 1000), true);
});

test("request timeout covers a stalled response body", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (_, { signal }) => ({ ok: true, json: () => new Promise((resolve, reject) => {
    signal.addEventListener("abort", () => reject(new Error("aborted body")), { once: true });
  }) });
  try {
    await assert.rejects(getJSON("/test", { timeoutMs: 20 }), /aborted body/);
  } finally {
    globalThis.fetch = original;
  }
});
