import { useEffect, useState } from "react";
import { createHabit, fetchHabits } from "../api/habits";
import type { Habit } from "../types/habit";

export function HabitsPage() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const data = await fetchHabits();
      setHabits(data);
    } catch (err) {
      setError("Failed to load habits. Check backend connection and CORS settings.");
      console.error(err);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError(null);
    try {
      await createHabit({
        user_id: 1,
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setName("");
      setDescription("");
      await load();
    } catch (err) {
      setError("Failed to create habit. Ensure backend is reachable at port 8000 from this device.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", fontFamily: "sans-serif", padding: "0 1rem" }}>
      <h1>Habit Tracker</h1>
      <p>Track your habits, streaks, and custom metrics.</p>

      {error && (
        <p style={{ color: "crimson", background: "#fff0f0", padding: "0.75rem", borderRadius: 8 }}>
          {error}
        </p>
      )}

      <section style={{ marginTop: "1.5rem", marginBottom: "2rem" }}>
        <h2>Create habit</h2>
        <form onSubmit={onCreate} style={{ display: "grid", gap: "0.5rem", maxWidth: 420 }}>
          <input
            placeholder="Habit name (e.g. Air squats)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button disabled={loading} type="submit">
            {loading ? "Creating..." : "Create"}
          </button>
        </form>
      </section>

      <section>
        <h2>Your habits</h2>
        {habits.length === 0 ? (
          <p>No habits yet. Add your first habit above.</p>
        ) : (
          <ul>
            {habits.map((habit) => (
              <li key={habit.id}>
                <strong>{habit.name}</strong>
                {habit.description ? ` — ${habit.description}` : ""}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
