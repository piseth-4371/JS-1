import { money, pct } from "../api.js";

function Tile({ label, value, sub, tone }) {
  const color = tone === "good" ? "text-emerald-300" : tone === "bad" ? "text-red-300" : "text-slate-100";
  return (
    <div className="card min-w-[140px] flex-1">
      <div className="label">{label}</div>
      <div className={`mt-1 text-xl font-semibold ${color}`}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

const tone = (x) => (x > 0 ? "good" : x < 0 ? "bad" : undefined);

export default function Overview({ ov }) {
  if (!ov) return null;
  const rs = ov.risk_settings;
  const dayLossUsed = Math.max(0, -ov.day_pnl_pct) / rs.daily_loss_pct * 100;
  return (
    <section className="flex flex-wrap gap-3">
      <Tile label="Virtual balance" value={money(ov.equity)} sub={`started at ${money(ov.starting_balance)} (${(ov.starting_balance * 100).toFixed(0)} USC)`} />
      <Tile label="Today P&L" value={money(ov.day_pnl)} sub={pct(ov.day_pnl_pct)} tone={tone(ov.day_pnl)} />
      <Tile label="Week P&L" value={money(ov.week_pnl)} sub={pct(ov.week_pnl_pct)} tone={tone(ov.week_pnl)} />
      <Tile label="Trades today" value={`${ov.trades_today} / ${ov.max_trades_per_day}`}
        sub={`${ov.consecutive_losses_today} loss(es) in a row (stop at ${rs.max_consecutive_losses})`} />
      <div className="card min-w-[180px] flex-1">
        <div className="label">Daily loss limit used</div>
        <div className="mt-2 h-2 w-full rounded bg-slate-800">
          <div className={`h-2 rounded ${dayLossUsed >= 100 ? "bg-red-500" : "bg-amber-400"}`}
            style={{ width: `${Math.min(100, dayLossUsed)}%` }} />
        </div>
        <div className="mt-1 text-xs text-slate-400">
          {dayLossUsed.toFixed(0)}% of {rs.daily_loss_pct}% · risk/trade {rs.risk_pct}% · weekly limit {rs.weekly_loss_pct}%
        </div>
      </div>
      <Tile label="Open positions" value={ov.open_positions.length} sub={`${ov.pending_orders.length} pending order(s)`} />
    </section>
  );
}
