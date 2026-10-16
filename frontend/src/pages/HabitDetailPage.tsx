import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchEntriesInRange, fetchLatestEntry } from "../api/entries";
import { fetchHabit } from "../api/habits";
import { fetchMetrics } from "../api/metrics";
import { fetchStats } from "../api/stats";
import { CalendarView } from "../components/CalendarView";
import { DayDetailModal } from "../components/DayDetailModal";
import { HeatmapView } from "../components/HeatmapView";
import { LogEntryModal } from "../components/LogEntryModal";
import { SettingsModal } from "../components/SettingsModal";
import { addDays, toISO, todayISO } from "../dates";
import type { Entry, HabitStats } from "../types/entry";
import type { Habit } from "../types/habit";
import type { Metric } from "../types/metric";

const card = { border: "1px solid #ddd", borderRadius: 8, padding: "0.75rem", minWidth: 110, flex: "1 1 110px" };

export function HabitDetailPage() {
  const id = Number(useParams().habitId);
  const now = new Date();
  const [habit, setHabit] = useState<Habit | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [stats, setStats] = useState<HabitStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [view, setView] = useState<"calendar" | "heatmap">("calendar");
  const [ym, setYm] = useState({ year: now.getFullYear(), month: now.getMonth() });
  const [monthEntries, setMonthEntries] = useState<Entry[]>([]);
  const [latestDate, setLatestDate] = useState<string | null>(null);
  const [heatEntries, setHeatEntries] = useState<Entry[]>([]);

  const [showSettings, setShowSettings] = useState(false);
  const [logDate, setLogDate] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const monthStart = toISO(new Date(ym.year, ym.month, 1));
    const monthEnd = toISO(new Date(ym.year, ym.month + 1, 0));
    const [s, me, latest] = await Promise.all([
      fetchStats(id),
      fetchEntriesInRange(id, monthStart, monthEnd),
      fetchLatestEntry(id),
    ]);
    setStats(s);
    setMonthEntries(me);
    setLatestDate(latest?.date ?? null);
    setHeatEntries(latest ? await fetchEntriesInRange(id, addDays(latest.date, -29), latest.date) : []);
  }, [id, ym]);

  const refreshMetrics = useCallback(async () => setMetrics(await fetchMetrics(id)), [id]);

  useEffect(() => {
    if (!Number.isFinite(id)) return;
    Promise.all([fetchHabit(id), refreshMetrics(), refresh()])
      .then(([h]) => setHabit(h))
      .catch((err) => {
        setError("Failed to load habit. Check that it exists and the backend is reachable.");
        console.error(err);
      });
  }, [id, refreshMetrics, refresh]);

  const pct = (n: number) => `${Math.round(n * 100)}%`;
  const findEntry = (d: string) =>
    monthEntries.find((e) => e.date === d) ?? heatEntries.find((e) => e.date === d);
  const showHeatmap = view === "heatmap" && latestDate !== null;

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", fontFamily: "sans-serif", padding: "0 1rem" }}>
      <p><Link to="/habits">← All habits</Link></p>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
        <h1 style={{ margin: 0 }}>{habit?.name ?? "Habit"}</h1>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button onClick={() => setLogDate(todayISO())}>Log entry</button>
          <button onClick={() => setShowSettings(true)}>⚙ Settings</button>
        </div>
      </div>
      {habit?.description && <p>{habit.description}</p>}

      {error && <p style={{ color: "crimson", background: "#fff0f0", padding: "0.75rem", borderRadius: 8 }}>{error}</p>}

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
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2>Dates</h2>
          {latestDate && (
            <button onClick={() => setView(view === "calendar" ? "heatmap" : "calendar")}>
              {view === "calendar" ? "Show heatmap" : "Show calendar"}
            </button>
          )}
        </div>
        {showHeatmap ? (
          <HeatmapView end={latestDate} entries={heatEntries} metrics={metrics} onSelect={setSelectedDate} />
        ) : (
          <CalendarView
            year={ym.year}
            month={ym.month}
            entries={monthEntries}
            onChangeMonth={(year, month) => setYm({ year, month })}
            onSelect={setSelectedDate}
          />
        )}
        {!latestDate && <p><small>No entries yet. Log one to unlock the heatmap.</small></p>}
      </section>

      {showSettings && (
        <SettingsModal
          habitId={id}
          metrics={metrics}
          onClose={() => setShowSettings(false)}
          onChanged={async () => { await Promise.all([refreshMetrics(), refresh()]); }}
        />
      )}
      {logDate && (
        <LogEntryModal
          habitId={id}
          metrics={metrics}
          initialDate={logDate}
          onClose={() => setLogDate(null)}
          onSaved={refresh}
        />
      )}
      {selectedDate && !logDate && (
        <DayDetailModal
          date={selectedDate}
          entry={findEntry(selectedDate)}
          metrics={metrics}
          onClose={() => setSelectedDate(null)}
          onEdit={() => { setLogDate(selectedDate); setSelectedDate(null); }}
        />
      )}
    </main>
  );
}
