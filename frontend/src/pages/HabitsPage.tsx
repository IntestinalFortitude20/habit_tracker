import { useEffect, useState } from "react";
import { fetchStats } from "../api/stats";
import { fetchHabits } from "../api/habits";
import { LinkCard } from "../components/Card";
import { CreateHabitModal } from "../components/CreateHabitModal";
import { ChatModal } from "../components/ChatModal";
import { ChatFab, Fab } from "../components/Fab";
import type { HabitStats } from "../types/entry";
import type { Habit } from "../types/habit";

export function HabitsPage() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [streaks, setStreaks] = useState<Record<number, HabitStats>>({});
  const [showCreate, setShowCreate] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const data = await fetchHabits();
      setHabits(data);
      const results = await Promise.allSettled(data.map((h) => fetchStats(h.id)));
      const next: Record<number, HabitStats> = {};
      results.forEach((r, i) => {
        if (r.status === "fulfilled") next[data[i].id] = r.value;
      });
      setStreaks(next);
    } catch (err) {
      setError("Failed to load habits. Check backend connection and CORS settings.");
      console.error(err);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = window.setTimeout(() => setToast(null), 3000);
    return () => window.clearTimeout(t);
  }, [toast]);

  return (
    <main className="page page--fabs stack">
      <header>
        <h1>Habit Tracker</h1>
        <p className="muted">Track your habits, streaks, and custom metrics.</p>
      </header>

      {error && <p className="alert alert--error" role="alert">{error}</p>}

      <section>
        <h2>Your habits</h2>
        {habits.length === 0 ? (
          <p className="empty">No habits yet. Tap the + button to add your first habit.</p>
        ) : (
          <div className="card-grid">
            {habits.map((habit) => (
              <LinkCard key={habit.id} to={`/habits/${habit.id}`}>
                <h3 className="card__title">{habit.name}</h3>
                {habit.description && <p className="card__desc">{habit.description}</p>}
                {streaks[habit.id] && (
                  <p className="card__meta">🔥 {streaks[habit.id].current_streak}-day streak</p>
                )}
              </LinkCard>
            ))}
          </div>
        )}
      </section>

      {!showCreate && !showChat && <ChatFab stacked onClick={() => setShowChat(true)} />}
      <Fab label="Create habit" onClick={() => setShowCreate(true)} />
      {showCreate && (
        <CreateHabitModal
          onClose={() => setShowCreate(false)}
          onCreated={async () => {
            await load();
            setToast("Habit created.");
          }}
        />
      )}
      {showChat && <ChatModal habitId={null} onClose={() => setShowChat(false)} />}
      {toast && <div className="toast" role="status">{toast}</div>}
    </main>
  );
}
