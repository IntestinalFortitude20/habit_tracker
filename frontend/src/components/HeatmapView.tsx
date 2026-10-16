import type { Entry } from "../types/entry";
import type { Metric } from "../types/metric";
import { addDays } from "../dates";
import { intensityLevel, LEVEL_COLORS, maxCountValue } from "./intensity";

type Props = { end: string; entries: Entry[]; metrics: Metric[]; onSelect: (date: string) => void };

// Fixed 30-day window (inclusive) ending at `end`; days without entries render gray.
export function HeatmapView({ end, entries, metrics, onSelect }: Props) {
  const start = addDays(end, -29);
  const byDate = new Map(entries.map((e) => [e.date, e]));
  const max = maxCountValue(entries, metrics);
  const days = Array.from({ length: 30 }, (_, i) => addDays(start, i));

  return (
    <div>
      <p style={{ margin: "0 0 0.5rem" }}><small>{start} → {end}</small></p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(10, minmax(0, 1fr))", gap: 4, maxWidth: 420 }}>
        {days.map((d) => {
          const en = byDate.get(d);
          return (
            <button
              key={d}
              onClick={() => onSelect(d)}
              title={d}
              aria-label={d}
              style={{
                aspectRatio: "1", padding: 0, border: "none", borderRadius: 3, cursor: "pointer",
                background: LEVEL_COLORS[intensityLevel(en, metrics, max)],
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
