import { useCallback, useEffect, useRef, useState } from "react";
import { getJSON } from "./api.js";
import Chart from "./components/Chart.jsx";
import Header from "./components/Header.jsx";
import Journal from "./components/Journal.jsx";
import Overview from "./components/Overview.jsx";
import SignalPanel from "./components/SignalPanel.jsx";

const POLL_MS = 5000; // refresh every 5 seconds
const FEEDS = {
  nas100: "/api/market/analysis?hours=12",
  btc: "/api/market/analysis?hours=12&source=binance&symbol=BTCUSDT",
};

export default function App() {
  const [ov, setOv] = useState(null);
  const [market, setMarket] = useState(null);
  const [signals, setSignals] = useState([]);
  const [orders, setOrders] = useState([]);
  const [positions, setPositions] = useState([]);
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);
  const [backendDown, setBackendDown] = useState(false);
  const [book, setBook] = useState(null); // null = follow the book that is trading now
  const view = book ?? ov?.trading_now ?? "nas100";
  const viewRef = useRef(view);
  viewRef.current = view;

  const refresh = useCallback(async () => {
    try {
      const [o, m, s, ord, p, e, mt] = await Promise.all([
        getJSON("/api/overview"),
        getJSON(FEEDS[viewRef.current]),
        getJSON("/api/signals?limit=100"),
        getJSON("/api/orders?limit=100"),
        getJSON("/api/positions?limit=200"),
        getJSON("/api/events?limit=200"),
        getJSON("/api/journal/metrics"),
      ]);
      setOv(o); setMarket(m); setSignals(s); setOrders(ord); setPositions(p); setEvents(e); setMetrics(mt);
      setBackendDown(false);
    } catch {
      setBackendDown(true);
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, [refresh]);

  useEffect(() => { refresh(); }, [view, refresh]);

  const bookInfo = ov?.markets?.find((m) => m.key === view);
  const strategy = bookInfo?.active_strategy ?? ov?.active_strategy;
  const latest = signals.find((s) => s.strategy === strategy);

  return (
    <div className="min-h-screen">
      <Header ov={ov} market={market} refresh={refresh} setError={setError}
        view={view} book={book} setBook={setBook} bookInfo={bookInfo} />
      <main className="mx-auto flex max-w-[1600px] flex-col gap-4 p-4">
        {backendDown && (
          <div className="rounded-lg bg-red-600/20 p-3 text-red-200 ring-1 ring-red-500/40">
            Cannot reach the backend. Start it with: <code>.\.venv\Scripts\python -m uvicorn app.main:app --port 8000</code>.
            Values below may be out of date.
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
        <Overview ov={ov} />
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2"><Chart market={market} /></div>
          <SignalPanel signal={latest} market={market} ov={ov} strategy={strategy} />
        </div>
        <Journal positions={positions} orders={orders} signals={signals} events={events} metrics={metrics} />
        <footer className="pb-4 text-center text-xs text-slate-500">
          Paper trading only · simulated orders and fills · prices from {bookInfo?.source ?? ov?.data_source ?? "-"} · NAS100 trades weekdays, BTC weekends · times shown in New York time
        </footer>
      </main>
    </div>
  );
}
