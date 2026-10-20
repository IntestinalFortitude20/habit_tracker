import type { Entry } from "../types/entry";
import type { Workout } from "../types/goal";
import { Button } from "./Button";
import { toISO, todayISO } from "../dates";

type Props = {
  year: number;
  month: number; // 0-based
  entries: Entry[];
  plan?: Workout[];
  selected?: string | null;
  onChangeMonth: (year: number, month: number) => void;
  onSelect: (date: string) => void;
};

const WEEKDAYS = ["S", "M", "T", "W", "T", "F", "S"];

export function CalendarView({ year, month, entries, plan = [], selected, onChangeMonth, onSelect }: Props) {
  const byDate = new Map(entries.map((e) => [e.date, e]));
  const planByDate = new Map(plan.map((w) => [w.date, w]));
  const first = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (string | null)[] = [
    ...Array<null>(first.getDay()).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => toISO(new Date(year, month, i + 1))),
  ];
  const go = (delta: number) => {
    const d = new Date(year, month + delta, 1);
    onChangeMonth(d.getFullYear(), d.getMonth());
  };
  const today = todayISO();

  return (
    <div>
      <div className="row" style={{ flexWrap: "nowrap" }}>
        <Button icon onClick={() => go(-1)} aria-label="Previous month">‹</Button>
        <strong>{first.toLocaleString(undefined, { month: "long", year: "numeric" })}</strong>
        <Button icon onClick={() => go(1)} aria-label="Next month">›</Button>
      </div>
      <div className="cal-grid">
        {WEEKDAYS.map((w, i) => <div key={i} className="cal-weekday" aria-hidden="true">{w}</div>)}
        {cells.map((d, i) => {
          if (!d) return <div key={i} />;
          const en = byDate.get(d);
          const pw = planByDate.get(d);
          const cls = [
            "cal-day",
            en && (en.completed ? "cal-day--done" : "cal-day--missed"),
            !en && pw && `cal-day--plan-${pw.status}`,
            pw && `cal-day--type-${pw.workout_type}`,
            d === today && "cal-day--today",
            d === selected && "cal-day--selected",
          ].filter(Boolean).join(" ");
          return (
            <button key={d} type="button" onClick={() => onSelect(d)} aria-label={d} aria-pressed={d === selected} className={cls}
              title={pw ? `${pw.workout_type}${pw.target_distance ? ` ${pw.target_distance}` : ""}` : undefined}>
              {Number(d.slice(8))}
              {pw && pw.workout_type !== "rest" && <small className="cal-target">{pw.target_distance ?? "•"}</small>}
            </button>
          );
        })}
      </div>
      <p className="legend">
        <span className="legend__item"><span className="swatch" style={{ background: "#b7efc3" }} /> Completed</span>
        <span className="legend__item"><span className="swatch" style={{ background: "#fbd0d0" }} /> Logged, not completed</span>
        <span className="legend__item"><span className="swatch" style={{ background: "#fff" }} /> No entry</span>
        {plan.length > 0 && <span className="legend__item"><span className="swatch" style={{ background: "#e6e6f5" }} /> Rest day (plan)</span>}
      </p>
    </div>
  );
}
