import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { deleteEntry, fetchEntries, saveEntry } from "../api/entries";
import { fetchHabit } from "../api/habits";
import { createMetric, deleteMetric, fetchMetrics, updateMetric } from "../api/metrics";
import { fetchStats } from "../api/stats";
import type { Entry, HabitStats } from "../types/entry";
import type { Habit } from "../types/habit";
import type { Metric, MetricType } from "../types/metric";

const METRIC_TYPES: MetricType[] = ["boolean", "count", "duration", "rating"];
const today = () => {
  const n = new Date();
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}-${String(n.getDate()).padStart(2, "0")}`;
};
const card = { border: "1px solid #ddd", borderRadius: 8, padding: "0.75rem", minWidth: 110 };

export function HabitDetailPage() {
  const id = Number(useParams().habitId);
  const [habit, setHabit] = useState<Habit | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [stats, setStats] = useState<HabitStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [mName, setMName] = useState("");
  const [mType, setMType] = useState<MetricType>("count");
  const [mUnit, setMUnit] = useState("");

  const [date, setDate] = useState(today());
  const [completed, setCompleted] = useState(true);
  const [values, setValues] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);

  const refreshEntries = useCallback(async () => {
    const [e, s] = await Promise.all([fetchEntries(id), fetchStats(id)]);
    setEntries(e);
    setStats(s);
  }, [id]);

  const refreshMetrics = useCallback(async () => setMetrics(await fetchMetrics(id)), [id]);

  useEffect(() => {
    if (!Number.isFinite(id)) return;
    Promise.all([fetchHabit(id), refreshMetrics(), refreshEntries()])
      .then(([h]) => setHabit(h))
      .catch((err) => {
        setError("Failed to load habit. Check that it exists and the backend is reachable.");
        console.error(err);
      });
  }, [id, refreshMetrics, refreshEntries]);

  async function run(action: () => Promise<void>, failMsg: string, okMsg?: string) {
    setError(null);
    setSuccess(null);
    try {
      await action();
      if (okMsg) setSuccess(okMsg);
    } catch (err) {
      setError(failMsg);
      console.error(err);
    }
  }

  function onAddMetric(e: React.FormEvent) {
    e.preventDefault();
    if (!mName.trim()) return;
    void run(async () => {
      await createMetric(id, { name: mName.trim(), type: mType, unit: mUnit.trim() || null });
      setMName("");
      setMUnit("");
      await refreshMetrics();
    }, "Failed to add metric.", "Metric added.");
  }

  function onEditMetric(m: Metric) {
    const name = window.prompt("Metric name", m.name);
    if (name === null || !name.trim()) return;
    const unit = window.prompt("Unit (optional)", m.unit ?? "");
    if (unit === null) return;
    void run(async () => {
      await updateMetric(id, m.id, { name: name.trim(), unit: unit.trim() || null });
      await refreshMetrics();
    }, "Failed to update metric.", "Metric updated.");
  }

  function onDeleteMetric(m: Metric) {
    if (!window.confirm(`Delete metric "${m.name}" and its logged values?`)) return;
    void run(async () => {
      await deleteMetric(id, m.id);
      await Promise.all([refreshMetrics(), refreshEntries()]);
    }, "Failed to delete metric.", "Metric deleted.");
  }

  async function onLog(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    await run(async () => {
      const metric_values = metrics
        .filter((m) => values[m.id] !== undefined && values[m.id] !== "")
        .map((m) => ({ metric_id: m.id, value: Number(values[m.id]) }))
        .filter((v) => Number.isFinite(v.value));
      await saveEntry(id, { date, completed, metric_values });
      await refreshEntries();
    }, "Failed to save entry.", `Entry saved for ${date}.`);
    setSaving(false);
  }

  function onDeleteEntry(entry: Entry) {
    void run(async () => {
      await deleteEntry(id, entry.id);
      await refreshEntries();
    }, "Failed to delete entry.", "Entry deleted.");
  }

  const metricName = (mid: number) => metrics.find((m) => m.id === mid)?.name ?? `#${mid}`;
  const pct = (n: number) => `${Math.round(n * 100)}%`;

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", fontFamily: "sans-serif", padding: "0 1rem" }}>
      <p><Link to="/habits">← All habits</Link></p>
      <h1>{habit?.name ?? "Habit"}</h1>
      {habit?.description && <p>{habit.description}</p>}

      {error && <p style={{ color: "crimson", background: "#fff0f0", padding: "0.75rem", borderRadius: 8 }}>{error}</p>}
      {success && <p style={{ color: "#146c2e", background: "#effaf1", padding: "0.75rem", borderRadius: 8 }}>{success}</p>}

      <section>
        <h2>Stats</h2>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <div style={card}><small>Current streak</small><h3>{stats?.current_streak ?? "–"}</h3></div>
          <div style={card}><small>Longest streak</small><h3>{stats?.longest_streak ?? "–"}</h3></div>
          <div style={card}><small>Last 7 days</small><h3>{stats ? pct(stats.completion_rate_7d) : "–"}</h3></div>
          <div style={card}><small>Last 30 days</small><h3>{stats ? pct(stats.completion_rate_30d) : "–"}</h3></div>
        </div>
      </section>

      <section>
        <h2>Metrics</h2>
        <form onSubmit={onAddMetric} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <input placeholder="Name (e.g. Reps)" value={mName} onChange={(e) => setMName(e.target.value)} />
          <select value={mType} onChange={(e) => setMType(e.target.value as MetricType)}>
            {METRIC_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <input placeholder="Unit (optional)" value={mUnit} onChange={(e) => setMUnit(e.target.value)} />
          <button type="submit">Add metric</button>
        </form>
        {metrics.length === 0 ? <p>No metrics yet.</p> : (
          <ul>
            {metrics.map((m) => (
              <li key={m.id}>
                <strong>{m.name}</strong> ({m.type}{m.unit ? `, ${m.unit}` : ""}){" "}
                <button onClick={() => onEditMetric(m)}>Edit</button>{" "}
                <button onClick={() => onDeleteMetric(m)}>Delete</button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Log entry</h2>
        <form onSubmit={onLog} style={{ display: "grid", gap: "0.5rem", maxWidth: 420 }}>
          <label>Date <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></label>
          <label><input type="checkbox" checked={completed} onChange={(e) => setCompleted(e.target.checked)} /> Completed</label>
          {metrics.map((m) => (
            <label key={m.id}>
              {m.name}{m.unit ? ` (${m.unit})` : ""}{" "}
              {m.type === "boolean" ? (
                <select value={values[m.id] ?? ""} onChange={(e) => setValues({ ...values, [m.id]: e.target.value })}>
                  <option value="">–</option>
                  <option value="1">Yes</option>
                  <option value="0">No</option>
                </select>
              ) : (
                <input
                  type="number"
                  step="any"
                  min={m.type === "rating" ? 1 : 0}
                  max={m.type === "rating" ? 5 : undefined}
                  value={values[m.id] ?? ""}
                  onChange={(e) => setValues({ ...values, [m.id]: e.target.value })}
                />
              )}
            </label>
          ))}
          <button disabled={saving} type="submit">{saving ? "Saving..." : "Save entry"}</button>
        </form>
        <p><small>Saving a date that already has an entry replaces it.</small></p>
      </section>

      <section>
        <h2>Recent entries</h2>
        {entries.length === 0 ? <p>No entries yet.</p> : (
          <ul>
            {entries.map((en) => (
              <li key={en.id}>
                {en.date} — {en.completed ? "✅ done" : "❌ not done"}
                {en.metric_values.map((v) => `, ${metricName(v.metric_id)}: ${v.value}`).join("")}{" "}
                <button onClick={() => onDeleteEntry(en)}>Delete</button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
