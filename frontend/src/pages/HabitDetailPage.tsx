import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { fetchEntriesInRange, fetchLatestEntry } from "../api/entries";
import { fetchHabit } from "../api/habits";
import { fetchMetrics } from "../api/metrics";
import { fetchStats } from "../api/stats";
import { Button } from "../components/Button";
import { ChatFab } from "../components/Fab";
import { ChatModal } from "../components/ChatModal";
import { Card } from "../components/Card";
import { CalendarView } from "../components/CalendarView";
import { DayDetailModal } from "../components/DayDetailModal";
import { HeatmapView } from "../components/HeatmapView";
import { LogEntryModal } from "../components/LogEntryModal";
import { SettingsModal } from "../components/SettingsModal";
import { addDays, toISO, todayISO } from "../dates";
import type { Entry, HabitStats } from "../types/entry";
import type { Habit } from "../types/habit";
import type { Metric } from "../types/metric";

export function HabitDetailPage() {
  const id = Number(useParams().habitId);
  const navigate = useNavigate();
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
  const [showChat, setShowChat] = useState(false);
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
    <main className="page stack">
      <div>
        <Link to="/habits" className="back-link">← All habits</Link>
        <h1>{habit?.name ?? "Habit"}</h1>
        {habit?.description && <p className="muted">{habit.description}</p>}
      </div>

      {error && <p className="alert alert--error" role="alert">{error}</p>}

      <div className="row">
        <div className="actions">
          <Button variant="primary" onClick={() => setLogDate(todayISO())}>Log entry</Button>
          <Button onClick={() => setShowSettings(true)}>⚙ Settings</Button>
        </div>
        {latestDate && (
          <Button onClick={() => setView(view === "calendar" ? "heatmap" : "calendar")}>
            {view === "calendar" ? "Show heatmap" : "Show calendar"}
          </Button>
        )}
      </div>

      <section>
        <h2>Stats</h2>
        <div className="stat-grid">
          <Card className="stat"><small>Current streak</small><p className="stat__value">{stats?.current_streak ?? "–"}</p></Card>
          <Card className="stat"><small>Longest streak</small><p className="stat__value">{stats?.longest_streak ?? "–"}</p></Card>
          <Card className="stat"><small>Last 7 days</small><p className="stat__value">{stats ? pct(stats.completion_rate_7d) : "–"}</p></Card>
          <Card className="stat"><small>Last 30 days</small><p className="stat__value">{stats ? pct(stats.completion_rate_30d) : "–"}</p></Card>
        </div>
      </section>

      <section>
        <h2>Dates</h2>
        <Card>
          {showHeatmap ? (
            <HeatmapView end={latestDate} entries={heatEntries} metrics={metrics} selected={selectedDate} onSelect={setSelectedDate} />
          ) : (
            <CalendarView
              year={ym.year}
              month={ym.month}
              entries={monthEntries}
              selected={selectedDate}
              onChangeMonth={(year, month) => setYm({ year, month })}
              onSelect={setSelectedDate}
            />
          )}
          {!latestDate && <p className="empty" style={{ marginTop: "1rem" }}>No entries yet. Log one to unlock the heatmap.</p>}
        </Card>
      </section>

      {!showChat && !showSettings && !logDate && !selectedDate && <ChatFab onClick={() => setShowChat(true)} />}
      {showChat && <ChatModal habitId={id} habitName={habit?.name} onClose={() => setShowChat(false)} />}
      {showSettings && (
        <SettingsModal
          habitId={id}
          habitName={habit?.name}
          metrics={metrics}
          onClose={() => setShowSettings(false)}
          onHabitDeleted={() => navigate("/habits", { replace: true })}
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
