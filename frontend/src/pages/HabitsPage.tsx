import { useEffect, useState } from "react";
import { createHabit, fetchHabits } from "../api/habits";
import type { Habit } from "../types/habit";

export function HabitsPage() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    const data = await fetchHabits();
    setHabits(data);
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      await createHabit({
        user_id: 1,
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setName("");
      setDescription("");
      await load();
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 800, margin: "2rem auto", fontFamily: "sans-serif", padding: "0 1rem" }}>
      <h1>Habit Tracker</h1>
      <p>Track your habits, streaks, and custom metrics.</p>

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
