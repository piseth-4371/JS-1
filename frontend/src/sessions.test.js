import test from "node:test";
import assert from "node:assert/strict";
import { isScanFresh } from "./sessions.js";
import { getJSON } from "./api.js";

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
