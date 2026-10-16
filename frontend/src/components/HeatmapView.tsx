import type { Entry } from "../types/entry";
import type { Metric } from "../types/metric";
import { addDays } from "../dates";
import { intensityLevel, LEVEL_COLORS, maxCountValue } from "./intensity";

type Props = { end: string; selected?: string | null; entries: Entry[]; metrics: Metric[]; onSelect: (date: string) => void };

// Fixed 30-day window (inclusive) ending at `end`; days without entries render gray.
export function HeatmapView({ end, entries, metrics, selected, onSelect }: Props) {
  const start = addDays(end, -29);
  const byDate = new Map(entries.map((e) => [e.date, e]));
  const max = maxCountValue(entries, metrics);
  const days = Array.from({ length: 30 }, (_, i) => addDays(start, i));

  return (
    <div>
      <p style={{ margin: "0 0 0.5rem" }}><small>{start} → {end}</small></p>
      <div className="heat-grid">
        {days.map((d) => {
          const en = byDate.get(d);
          return (
            <button
              key={d}
              type="button"
              onClick={() => onSelect(d)}
              title={d}
              aria-label={d}
              aria-pressed={d === selected}
              className={`heat-cell${d === selected ? " heat-cell--selected" : ""}`}
              style={{ background: LEVEL_COLORS[intensityLevel(en, metrics, max)] }}
            />
          );
        })}
      </div>
      <p className="legend">
        Less
        {LEVEL_COLORS.map((c, i) => <span key={i} className="swatch" style={{ background: c }} />)}
        More
      </p>
    </div>
  );
}
