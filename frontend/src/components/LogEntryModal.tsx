import { useEffect, useState } from "react";
import { fetchEntriesInRange, saveEntry } from "../api/entries";
import { fetchGoal, fetchPlan } from "../api/goals";
import type { Goal, Workout } from "../types/goal";
import type { Metric } from "../types/metric";
import { Button } from "./Button";
import { Modal } from "./Modal";

type Props = {
  habitId: number;
  metrics: Metric[];
  initialDate: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
};

export function LogEntryModal({ habitId, metrics, initialDate, onClose, onSaved }: Props) {
  const [date, setDate] = useState(initialDate);
  const [completed, setCompleted] = useState(true);
  const [values, setValues] = useState<Record<number, string>>({});
  const [existing, setExisting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [goal, setGoal] = useState<Goal | null>(null);
  const [workout, setWorkout] = useState<Workout | null>(null);

  useEffect(() => { fetchGoal(habitId).then(setGoal).catch(console.error); }, [habitId]);

  // Prefill when the selected date already has an entry.
  useEffect(() => {
    if (!date) return;
    let cancelled = false;
    fetchEntriesInRange(habitId, date, date)
      .then(([en]) => {
        if (cancelled) return;
        setExisting(!!en);
        setCompleted(en ? en.completed : true);
        const entered = en ? Object.fromEntries(en.metric_values.map((v) => [v.metric_id, String(v.value)])) : {};
        setValues(entered);
        if (!goal) { setWorkout(null); return; }
        // Show the day's planned target and pre-fill the distance metric for new entries.
        return fetchPlan(habitId, date, date).then(([w]) => {
          if (cancelled) return;
          setWorkout(w ?? null);
          if (!en && w?.target_distance && goal.metric_id) setValues({ [goal.metric_id]: String(w.target_distance) });
          if (!en && w?.workout_type === "rest") setCompleted(true);
        });
      })
      .catch((err) => {
        if (!cancelled) setError("Failed to load existing entry.");
        console.error(err);
      });
    return () => { cancelled = true; };
  }, [habitId, date, goal]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const metric_values = metrics
        .filter((m) => values[m.id] !== undefined && values[m.id] !== "")
        .map((m) => ({ metric_id: m.id, value: Number(values[m.id]) }))
        .filter((v) => Number.isFinite(v.value));
      await saveEntry(habitId, { date, completed, metric_values });
      setExisting(true);
      await onSaved();
      setSuccess(`Entry saved for ${date}.`);
    } catch (err) {
      setError("Failed to save entry.");
      console.error(err);
    }
    setSaving(false);
  }

  return (
    <Modal
      title="Log entry"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Close</Button>
          <Button variant="primary" type="submit" form="log-entry-form" loading={saving}>
            {saving ? "Saving..." : existing ? "Update entry" : "Save entry"}
          </Button>
        </>
      }
    >
      {error && <p className="alert alert--error" role="alert">{error}</p>}
      {success && <p className="alert alert--success" role="status">{success}</p>}
      <form id="log-entry-form" onSubmit={onSubmit}>
        {workout && (
          <p className="alert alert--success" role="status">
            Target: <strong>{workout.workout_type.replace("_", " ")}</strong>
            {workout.target_distance ? ` ${workout.target_distance} ${goal?.unit ?? ""}` : ""}
            {workout.target_duration_min ? ` ${workout.target_duration_min} min` : ""}
            {workout.percent_of_target !== null && workout.difference !== null &&
              ` — logged ${workout.percent_of_target}% of target (${workout.difference >= 0 ? "+" : ""}${workout.difference} ${goal?.unit ?? ""})`}
          </p>
        )}
        <label className="field">Date <input className="input" type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></label>
        <label className="field field--check"><input type="checkbox" checked={completed} onChange={(e) => setCompleted(e.target.checked)} /> Completed</label>
        {metrics.map((m) => (
          <label key={m.id} className="field">
            {m.name}{m.unit ? ` (${m.unit})` : ""}
            {m.type === "boolean" ? (
              <select className="input" value={values[m.id] ?? ""} onChange={(e) => setValues({ ...values, [m.id]: e.target.value })}>
                <option value="">–</option>
                <option value="1">Yes</option>
                <option value="0">No</option>
              </select>
            ) : (
              <input
                className="input"
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
      </form>
      {existing && <p className="muted"><small>This date already has an entry; saving replaces it.</small></p>}
    </Modal>
  );
}
