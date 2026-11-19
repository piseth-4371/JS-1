// A scanner result counts as current only if it is at most 60 s old (and not from the future).
export function isScanFresh(timestamp, nowSeconds) {
  const age = nowSeconds - timestamp;
  return Number.isFinite(timestamp) && timestamp > 0 && age >= 0 && age <= 60;
}
