import { useState } from "react";
import { money, num, nyTime, sideText } from "../api.js";

function Table({ cols, rows, empty }) {
  if (!rows?.length) return <p className="p-4 text-sm text-slate-400">{empty}</p>;
  return (
    <div className="max-h-80 overflow-auto">
      <table className="w-full text-left text-sm">
        <thead className="sticky top-0 bg-slate-900 text-xs uppercase text-slate-400">
          <tr>{cols.map((c) => <th key={c[0]} className="px-2 py-2 font-medium">{c[0]}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id ?? i} className="border-t border-slate-800 align-top">
              {cols.map((c) => <td key={c[0]} className="px-2 py-1.5">{c[1](r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const rTone = (r) => (r == null ? "" : r > 0 ? "text-emerald-300" : "text-red-300");

function Metrics({ m }) {
  if (!m) return <p className="p-4 text-sm text-slate-400">Loading...</p>;
  const cell = (k, v) => (
    <div key={k} className="rounded-lg bg-slate-800/60 p-3">
      <div className="label">{k}</div>
      <div className="mt-1 font-mono text-lg">{v}</div>
    </div>
  );
  return (
    <div className="p-2">
      <div className={`mb-3 rounded-lg p-3 text-sm ${m.enough_data ? "bg-sky-500/10 text-sky-200" : "bg-amber-500/10 text-amber-200"}`}>
        {m.verdict}
      </div>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
        {cell("Closed trades", m.closed_trades)}
        {cell("Win rate", `${m.win_rate.toFixed(1)}%`)}
        {cell("Expectancy", `${m.expectancy_r.toFixed(2)} R`)}
        {cell("Profit factor", m.profit_factor == null ? "-" : m.profit_factor.toFixed(2))}
        {cell("Total", `${m.total_r.toFixed(2)} R (${money(m.pnl_usd)})`)}
        {cell("Avg win / loss", `${m.avg_win_r.toFixed(2)} / ${m.avg_loss_r.toFixed(2)} R`)}
        {cell("Max drawdown", `${m.max_drawdown_pct.toFixed(1)}%`)}
        {cell("Losing streak", m.longest_losing_streak)}
        {cell("Signals (actionable)", `${m.signals_total} (${m.signals_actionable})`)}
        {cell("Rejected by risk", m.signals_rejected)}
      </div>
      {Object.keys(m.rejection_reasons).length > 0 && (
        <div className="mt-3 text-sm">
          <div className="label mb-1">Why signals were rejected</div>
          {Object.entries(m.rejection_reasons).map(([k, v]) => (
            <div key={k} className="text-slate-300">{v} × {k}</div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Journal({ positions, orders, signals, events, metrics }) {
  const [tab, setTab] = useState("positions");
  const closed = positions.filter((p) => p.status === "closed");
  const wins = closed.filter((p) => p.r > 0).length;
  const totalR = closed.reduce((a, p) => a + p.r, 0);
  const rejected = signals.filter((s) => s.action !== "WAIT" && s.risk_approved === false);

  const tabs = {
    positions: ["Trades", (
      <>
        <div className="flex gap-6 px-2 pb-2 text-sm text-slate-300">
          <span>Closed trades: <b>{closed.length}</b></span>
          <span>Win rate: <b>{closed.length ? ((wins / closed.length) * 100).toFixed(0) : "-"}%</b></span>
          <span>Total: <b className={rTone(totalR)}>{totalR.toFixed(2)} R</b></span>
          {closed.length < 30 && <span className="text-amber-300">Too few trades to judge the strategy (need 30+)</span>}
        </div>
        <Table empty="No paper trades yet." rows={positions} cols={[
          ["Opened (NY)", (p) => nyTime(p.opened_ts)],
          ["Strategy", (p) => p.strategy],
          ["Side", (p) => sideText(p.side)],
          ["Lots", (p) => num(p.qty, 2)],
          ["Entry", (p) => num(p.entry)],
          ["SL / TP", (p) => `${num(p.stop)} / ${num(p.target)}`],
          ["Status", (p) => p.status],
          ["Exit", (p) => (p.exit_price != null ? `${num(p.exit_price)} (${p.exit_reason})` : "-")],
          ["R", (p) => <span className={rTone(p.r)}>{p.r != null ? p.r.toFixed(2) : "-"}</span>],
          ["P&L", (p) => <span className={rTone(p.pnl_usd)}>{money(p.pnl_usd)}</span>],
        ]} />
      </>
    )],
    metrics: ["Metrics", <Metrics m={metrics} />],
    orders: ["Orders", (
      <Table empty="No orders yet." rows={orders} cols={[
        ["Created (NY)", (o) => nyTime(o.created_ts)],
        ["Id", (o) => <span className="font-mono text-xs">{o.client_order_id}</span>],
        ["Side", (o) => sideText(o.side)],
        ["Type", (o) => o.kind],
        ["Lots", (o) => num(o.qty, 2)],
        ["Entry", (o) => num(o.entry)],
        ["Status", (o) => o.status],
        ["Note", (o) => o.status_reason || (o.fill_price ? `filled ${num(o.fill_price)}` : "")],
      ]} />
    )],
    signals: [`Signals (${rejected.length} rejected)`, (
      <Table empty="No signals yet." rows={signals} cols={[
        ["Bar close (NY)", (s) => nyTime(s.bar_close_ts)],
        ["Strategy", (s) => s.strategy],
        ["Action", (s) => s.action],
        ["Entry / SL / TP", (s) => (s.action === "WAIT" ? "-" : `${num(s.entry)} / ${num(s.stop)} / ${num(s.target)}`)],
        ["Risk Manager", (s) => (s.risk_approved == null ? "-" : s.risk_approved ? "approved" :
          <span className="text-red-300">{s.risk_reasons.join("; ")}</span>)],
      ]} />
    )],
    events: ["Event log", (
      <Table empty="No events yet." rows={events} cols={[
        ["Time (NY)", (e) => nyTime(e.ts)],
        ["Level", (e) => <span className={e.level === "ERROR" ? "text-red-300" : e.level === "WARN" ? "text-amber-300" : ""}>{e.level}</span>],
        ["Type", (e) => e.type],
        ["Message", (e) => e.message],
      ]} />
    )],
  };

  return (
    <section className="card p-0">
      <div className="flex gap-1 border-b border-slate-800 px-2 pt-2">
        {Object.entries(tabs).map(([k, [title]]) => (
          <button key={k} onClick={() => setTab(k)}
            className={`rounded-t-md px-3 py-1.5 text-sm ${tab === k ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"}`}>
            {title}
          </button>
        ))}
      </div>
      <div className="p-2">{tabs[tab][1]}</div>
    </section>
  );
}
