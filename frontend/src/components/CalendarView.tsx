import type { Entry } from "../types/entry";
import { Button } from "./Button";
import { toISO, todayISO } from "../dates";

type Props = {
  year: number;
  month: number; // 0-based
  entries: Entry[];
  selected?: string | null;
  onChangeMonth: (year: number, month: number) => void;
  onSelect: (date: string) => void;
};

const WEEKDAYS = ["S", "M", "T", "W", "T", "F", "S"];

export function CalendarView({ year, month, entries, selected, onChangeMonth, onSelect }: Props) {
  const byDate = new Map(entries.map((e) => [e.date, e]));
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
          const cls = [
            "cal-day",
            en && (en.completed ? "cal-day--done" : "cal-day--missed"),
            d === today && "cal-day--today",
            d === selected && "cal-day--selected",
          ].filter(Boolean).join(" ");
          return (
            <button key={d} type="button" onClick={() => onSelect(d)} aria-label={d} aria-pressed={d === selected} className={cls}>
              {Number(d.slice(8))}
            </button>
          );
        })}
      </div>
      <p className="legend">
        <span className="legend__item"><span className="swatch" style={{ background: "#b7efc3" }} /> Completed</span>
        <span className="legend__item"><span className="swatch" style={{ background: "#fbd0d0" }} /> Logged, not completed</span>
        <span className="legend__item"><span className="swatch" style={{ background: "#fff" }} /> No entry</span>
      </p>
    </div>
  );
}
