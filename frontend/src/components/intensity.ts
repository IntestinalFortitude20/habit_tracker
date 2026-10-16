import type { Entry } from "../types/entry";
import type { Metric } from "../types/metric";

export const GRAY = "#ebedf0";
export const LEVEL_COLORS = [GRAY, "#9be9a8", "#40c463", "#216e39"];

// 0 = no contribution; 1..3 = light/medium/dark. Uses the first count metric when present,
// otherwise the completed flag.
export function intensityLevel(entry: Entry | undefined, metrics: Metric[], maxCount: number): number {
  if (!entry) return 0;
  const countMetric = metrics.find((m) => m.type === "count");
  if (countMetric) {
    const v = entry.metric_values.find((x) => x.metric_id === countMetric.id)?.value ?? 0;
    if (v <= 0 || maxCount <= 0) return entry.completed ? 1 : 0;
    return Math.min(3, Math.max(1, Math.ceil((v / maxCount) * 3)));
  }
  return entry.completed ? 3 : 0;
}

export function maxCountValue(entries: Entry[], metrics: Metric[]): number {
  const countMetric = metrics.find((m) => m.type === "count");
  if (!countMetric) return 0;
  return Math.max(0, ...entries.flatMap((e) => e.metric_values.filter((v) => v.metric_id === countMetric.id).map((v) => v.value)));
}
