import type { Entry } from "../types/entry";
import { toISO, todayISO } from "../dates";

type Props = {
  year: number;
  month: number; // 0-based
  entries: Entry[];
  onChangeMonth: (year: number, month: number) => void;
  onSelect: (date: string) => void;
};

const WEEKDAYS = ["S", "M", "T", "W", "T", "F", "S"];

export function CalendarView({ year, month, entries, onChangeMonth, onSelect }: Props) {
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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button onClick={() => go(-1)} aria-label="Previous month">‹</button>
        <strong>{first.toLocaleString(undefined, { month: "long", year: "numeric" })}</strong>
        <button onClick={() => go(1)} aria-label="Next month">›</button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, minmax(0, 1fr))", gap: 4, marginTop: 8 }}>
        {WEEKDAYS.map((w, i) => <div key={i} style={{ textAlign: "center", fontSize: 12, color: "#666" }}>{w}</div>)}
        {cells.map((d, i) => {
          if (!d) return <div key={i} />;
          const en = byDate.get(d);
          return (
            <button
              key={d}
              onClick={() => onSelect(d)}
              aria-label={d}
              style={{
                aspectRatio: "1", padding: 0, fontSize: 14, borderRadius: 6, cursor: "pointer",
                border: d === today ? "2px solid #333" : "1px solid #ddd",
                background: en ? (en.completed ? "#9be9a8" : "#ffd6d6") : "#fff",
              }}
            >
              {Number(d.slice(8))}
            </button>
          );
        })}
      </div>
      <p style={{ fontSize: 12, color: "#666" }}>Green = completed, red = logged but not completed.</p>
    </div>
  );
}
