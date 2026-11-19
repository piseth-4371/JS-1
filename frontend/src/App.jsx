import { useCallback, useEffect, useRef, useState } from "react";
import { getJSON } from "./api.js";
import Header from "./components/Header.jsx";
import SimpleView from "./components/SimpleView.jsx";
import { autoMarket, signalCard } from "./simpleView.js";

const POLL_MS = 5000; // closed-bar analysis and dashboard panels
const PREVIEW_POLL_MS = 2000; // display-only quote preview
const FEEDS = {
  nas100: "/api/market/analysis?hours=12",
  btc: "/api/market/analysis?hours=12&source=binance&symbol=BTCUSDT",
  gold: "/api/market/analysis?hours=12&symbol=XAUUSD", // scanner-only market, no paper book
};
const PREVIEW_MARKETS = ["nas100", "btc"]; // the quote preview exists only for the paper books

export default function App() {
  const [ov, setOv] = useState(null);
  const [market, setMarket] = useState(null);
  const [preview, setPreview] = useState(null);
  const [signals, setSignals] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [scan, setScan] = useState(null);
  const [error, setError] = useState(null);
  const [backendDown, setBackendDown] = useState(false);
  const [marketError, setMarketError] = useState(null);
  const [previewError, setPreviewError] = useState(null);
  // No market picker: the chart follows the signal (or practice setup, or open market) automatically.
  const view = autoMarket(signalCard({ scan: backendDown ? null : scan, ov: backendDown ? null : ov, signals, now: Date.now() / 1000 }), scan, ov);
  const viewRef = useRef(view);
  viewRef.current = view;
  const analysisSequence = useRef(0);
  const previewSequence = useRef(0);
  const analysisRequest = useRef(null);
  const previewRequest = useRef(null);
  const panelsRequest = useRef(false);

  const refreshPanels = useCallback(async () => {
    if (panelsRequest.current) return;
    panelsRequest.current = true;
    try {
      const [o, s, mt, sc] = await Promise.allSettled([
        getJSON("/api/overview"),
        getJSON("/api/signals?limit=100"),
        getJSON("/api/journal/metrics"),
        getJSON("/api/scanner"),
      ]);
      if (o.status === "fulfilled") { setOv(o.value); setBackendDown(false); }
      else setBackendDown(true);
      if (s.status === "fulfilled") setSignals(s.value);
      if (mt.status === "fulfilled") setMetrics(mt.value);
      if (sc.status === "fulfilled") setScan(sc.value);
    } finally {
      panelsRequest.current = false;
    }
  }, []);

  const refreshMarket = useCallback(async () => {
    const requestedView = viewRef.current;
    if (analysisRequest.current?.view === requestedView) return;
    const request = { view: requestedView, sequence: ++analysisSequence.current };
    analysisRequest.current = request;
    try {
      const data = await getJSON(FEEDS[requestedView]);
      if (request.sequence !== analysisSequence.current || requestedView !== viewRef.current) return;
      setMarket({ ...data, view: requestedView });
      setMarketError(null);
    } catch (error) {
      if (request.sequence !== analysisSequence.current || requestedView !== viewRef.current) return;
      setMarketError(error.message);
    } finally {
      if (analysisRequest.current === request) analysisRequest.current = null;
    }
  }, []);

  const refreshPreview = useCallback(async () => {
    const requestedView = viewRef.current;
    if (!PREVIEW_MARKETS.includes(requestedView)) return;
    if (previewRequest.current?.view === requestedView) return;
    const request = { view: requestedView, sequence: ++previewSequence.current };
    previewRequest.current = request;
    try {
      const data = await getJSON(`/api/market/preview?market=${requestedView}`, { timeoutMs: 6000 });
      if (request.sequence !== previewSequence.current || requestedView !== viewRef.current) return;
      setPreview({ ...data, view: requestedView });
      setPreviewError(null);
    } catch (error) {
      if (request.sequence !== previewSequence.current || requestedView !== viewRef.current) return;
      setPreviewError(error.message);
    } finally {
      if (previewRequest.current === request) previewRequest.current = null;
    }
  }, []);

  const refresh = useCallback(() => {
    refreshPanels();
    refreshMarket();
    refreshPreview();
  }, [refreshPanels, refreshMarket, refreshPreview]);

  useEffect(() => {
    refreshPanels();
    const t = setInterval(refreshPanels, POLL_MS);
    return () => clearInterval(t);
  }, [refreshPanels]);

  useEffect(() => {
    // Old requests must not overwrite a newly selected market.
    analysisSequence.current += 1;
    previewSequence.current += 1;
    // An older in-flight request is now outdated (its answer will be ignored), so it must not
    // block the new one - otherwise the chart waits for the next 5 s poll ("Loading" bug).
    analysisRequest.current = null;
    previewRequest.current = null;
    setMarket(null);
    setPreview(null);
    setMarketError(null);
    setPreviewError(null);
    refreshMarket();
    refreshPreview();
    const analysisTimer = setInterval(refreshMarket, POLL_MS);
    const previewTimer = setInterval(refreshPreview, PREVIEW_POLL_MS);
    return () => { clearInterval(analysisTimer); clearInterval(previewTimer); };
  }, [view, refreshMarket, refreshPreview]);

  const bookInfo = ov?.markets?.find((m) => m.key === view);

  return (
    <div className="min-h-screen">
      <Header ov={ov} market={market} preview={preview} marketError={marketError} previewError={previewError}
        refresh={refresh} setError={setError} view={view} bookInfo={bookInfo} />
      <main className="mx-auto flex max-w-[1600px] flex-col gap-4 p-4">
        {backendDown && (
          <div className="rounded-lg bg-red-600/20 p-3 text-red-200 ring-1 ring-red-500/40">
            Cannot reach the backend. Start it with: <code>.\.venv\Scripts\python -m uvicorn app.main:app --port 8000</code>.
            Values below may be out of date.
          </div>
        )}
        {marketError && (
          <div className="rounded-lg bg-amber-500/15 p-3 text-amber-200 ring-1 ring-amber-500/40">
            Chart history could not refresh. The displayed candles may be out of date.
          </div>
        )}
        {error && (
          <div className="rounded-lg bg-amber-500/15 p-3 text-amber-200 ring-1 ring-amber-500/40">{error}</div>
        )}
        {ov?.kill_switch && (
          <div className="rounded-lg bg-red-600/25 p-3 font-semibold text-red-100 ring-1 ring-red-500">
            KILL SWITCH IS ON: all trading is blocked. Orders were cancelled and positions closed.
          </div>
        )}
        <SimpleView scan={scan} ov={ov} signals={signals} metrics={metrics} backendDown={backendDown}
          market={market?.view === view ? market : null} preview={preview} previewError={previewError}
          marketError={marketError} view={view} />
        <footer className="pb-4 text-center text-xs text-slate-500">
          Paper trading only · simulated signals and fills · NAS100, BTC and gold checked automatically · times in New York time (chart clock also shows your local time)
        </footer>
      </main>
    </div>
  );
}
