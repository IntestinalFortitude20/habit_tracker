import { useEffect, useState } from "react";
import { cancelGoal, createGoal, fetchGoal, fetchGoalTypes, fetchProgress, goalErrorMessage, regenerateGoal } from "../api/goals";
import type { ExperienceLevel, Goal, GoalProgress, GoalType, GoalTypeInfo } from "../types/goal";
import { Button } from "./Button";

type Props = { habitId: number; onChanged: () => Promise<void> };

export function GoalSection({ habitId, onChanged }: Props) {
  const [types, setTypes] = useState<GoalTypeInfo[]>([]);
  const [disclaimer, setDisclaimer] = useState("");
  const [goal, setGoal] = useState<Goal | null>(null);
  const [progress, setProgress] = useState<GoalProgress | null>(null);
  const [goalType, setGoalType] = useState<GoalType>("marathon");
  const [level, setLevel] = useState<ExperienceLevel>("beginner");
  const [unit, setUnit] = useState<"mi" | "km">("mi");
  const [targetDate, setTargetDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const g = await fetchGoal(habitId);
    setGoal(g);
    setProgress(g ? await fetchProgress(habitId) : null);
  }

  useEffect(() => {
    fetchGoalTypes().then((r) => { setTypes(r.goal_types); setDisclaimer(r.disclaimer); }).catch(console.error);
    load().catch(console.error);
  }, [habitId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function run(action: () => Promise<void>) {
    setError(null);
    try {
      await action();
      await load();
      await onChanged();
    } catch (err) {
      setError(goalErrorMessage(err));
    }
  }

  const label = (id: string) => types.find((t) => t.id === id)?.label ?? id;

  return (
    <section>
      <h3>Training goal</h3>
      {error && <p className="alert alert--error" role="alert">{error}</p>}
      {goal ? (
        <div className="card">
          <p>
            <strong>{label(goal.goal_type)}</strong> on {goal.target_date} ({goal.experience_level})
            {progress && <> — {progress.weeks_remaining} week(s) left, <strong>{progress.status_label}</strong></>}
          </p>
          {progress?.suggest_regenerate && <p className="alert alert--error">You're well behind plan. Regenerate the remaining plan?</p>}
          <div className="actions">
            <Button onClick={() => void run(() => regenerateGoal(habitId))}>Regenerate remaining plan</Button>
            <Button variant="danger" onClick={() => void run(() => cancelGoal(habitId))}>Remove goal</Button>
          </div>
        </div>
      ) : (
        <form
          className="form-row"
          onSubmit={(e) => { e.preventDefault(); void run(() => createGoal(habitId, { goal_type: goalType, target_date: targetDate, experience_level: level, unit })); }}
        >
          <select className="input" aria-label="Goal" value={goalType} onChange={(e) => setGoalType(e.target.value as GoalType)}>
            {types.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
          <select className="input" aria-label="Experience level" value={level} onChange={(e) => setLevel(e.target.value as ExperienceLevel)}>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          <select className="input" aria-label="Units" value={unit} onChange={(e) => setUnit(e.target.value as "mi" | "km")}>
            <option value="mi">miles</option>
            <option value="km">km</option>
          </select>
          <input className="input" type="date" aria-label="Target date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} required />
          <Button variant="primary" type="submit">Create plan</Button>
        </form>
      )}
      {disclaimer && <p className="muted"><small>{disclaimer}</small></p>}
    </section>
  );
}
