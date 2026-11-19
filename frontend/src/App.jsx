import { useCallback, useEffect, useRef, useState } from "react";
import { getJSON } from "./api.js";
import Chart from "./components/Chart.jsx";
import Header from "./components/Header.jsx";
import Journal from "./components/Journal.jsx";
import Overview from "./components/Overview.jsx";
import ScannerPanel from "./components/ScannerPanel.jsx";
import SignalPanel from "./components/SignalPanel.jsx";
import SessionPanel from "./components/SessionPanel.jsx";
import WhyWaitPanel from "./components/WhyWaitPanel.jsx";

const POLL_MS = 5000; // closed-bar analysis and dashboard panels
const PREVIEW_POLL_MS = 2000; // display-only quote preview
const FEEDS = {
  nas100: "/api/market/analysis?hours=12",
  btc: "/api/market/analysis?hours=12&source=binance&symbol=BTCUSDT",
};

export default function App() {
  const [ov, setOv] = useState(null);
  const [market, setMarket] = useState(null);
  const [preview, setPreview] = useState(null);
  const [signals, setSignals] = useState([]);
  const [orders, setOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [scan, setScan] = useState(null);
  const [error, setError] = useState(null);
  const [backendDown, setBackendDown] = useState(false);
  const [marketError, setMarketError] = useState(null);
  const [previewError, setPreviewError] = useState(null);
  const [book, setBook] = useState(null); // null = follow the book that is trading now
  const view = book ?? ov?.trading_now ?? "nas100";
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
      const [o, s, ord, p, e, mt, sc] = await Promise.allSettled([
        getJSON("/api/overview"),
        getJSON("/api/signals?limit=100"),
        getJSON("/api/orders?limit=100"),
        getJSON("/api/positions?limit=200"),
        getJSON("/api/events?limit=200"),
        getJSON("/api/journal/metrics"),
        getJSON("/api/scanner"),
      ]);
      if (o.status === "fulfilled") { setOv(o.value); setBackendDown(false); }
      else setBackendDown(true);
      if (s.status === "fulfilled") setSignals(s.value);
      if (ord.status === "fulfilled") setOrders(ord.value);
      if (p.status === "fulfilled") setPositions(p.value);
      if (e.status === "fulfilled") setEvents(e.value);
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
  const strategy = bookInfo?.active_strategy ?? ov?.active_strategy;
  const latest = signals.find((s) => s.strategy === strategy);

  return (
    <div className="min-h-screen">
      <Header ov={ov} market={market} preview={preview} marketError={marketError} previewError={previewError}
        refresh={refresh} setError={setError}
        view={view} book={book} setBook={setBook} bookInfo={bookInfo} />
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
        <SessionPanel scan={scan} backendDown={backendDown} view={view} />
        <WhyWaitPanel scan={scan} ov={ov} signals={signals} backendDown={backendDown} />
        <ScannerPanel scan={scan} />
        <Overview ov={ov} />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2"><Chart market={market} preview={preview} previewError={previewError} marketError={marketError} view={view} /></div>
          <SignalPanel signal={latest} market={market?.view === view ? market : null} ov={ov} strategy={strategy} />
        </div>
        <Journal positions={positions} orders={orders} signals={signals} events={events} metrics={metrics} />
        <footer className="pb-4 text-center text-xs text-slate-500">
          Paper trading only · simulated orders and fills · prices from {bookInfo?.source ?? ov?.data_source ?? "-"} · NAS100 trades weekdays, BTC weekends · times in New York time (chart clock also shows your local time)
        </footer>
      </main>
    </div>
  );
}
