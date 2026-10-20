import type { Entry } from "../types/entry";
import type { Metric } from "../types/metric";
import type { PlanDayEdit, Workout } from "../types/goal";
import { confirmationMessage, goalErrorMessage } from "../api/goals";
import { useState } from "react";
import { Button } from "./Button";
import { Modal } from "./Modal";

type Props = {
  date: string;
  entry?: Entry;
  metrics: Metric[];
  workout?: Workout;
  hasPlan?: boolean;
  onPlanChange?: (edit: PlanDayEdit) => Promise<void>;
  onClose: () => void;
  onEdit: () => void;
};

export function DayDetailModal({ date, entry, metrics, workout, hasPlan = false, onPlanChange, onClose, onEdit }: Props) {
  const [target, setTarget] = useState(String(workout?.target_value ?? workout?.target_distance ?? ""));
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Applies a plan edit; a past-day or logged-day change asks the user to confirm first.
  const applyEdit = async (edit: PlanDayEdit) => {
    if (!onPlanChange) return;
    setError(null);
    try {
      await onPlanChange(edit);
    } catch (err) {
      const warning = confirmationMessage(err);
      if (warning === null) { setError(goalErrorMessage(err)); return; }
      if (!window.confirm(warning)) return;
      try { await onPlanChange({ ...edit, confirm: true }); } catch (e) { setError(goalErrorMessage(e)); }
    }
  };

  const isRest = workout?.workout_type === "rest";
  const metricFor = (id: number) => metrics.find((m) => m.id === id);
  return (
    <Modal
      title={date}
      onClose={onClose}
      footer={<Button variant="primary" onClick={onEdit}>{entry ? "Edit entry" : "Log entry"}</Button>}
    >
      {hasPlan && (
        <section className="day-plan" aria-label="Planned workout">
          <h4>Plan {workout?.edited && <small className="tag" data-testid="edited-tag">edited</small>}</h4>
          {!workout || isRest ? (
            <p>Rest day{workout?.notes ? ` — ${workout.notes}` : ""}</p>
          ) : (
            <p>
              {workout.workout_type}: {workout.target_value ?? workout.target_distance ?? "–"}
              {workout.target_duration_min ? ` (${workout.target_duration_min} min)` : ""}
            </p>
          )}
          {workout && onPlanChange && (
            <div className="actions">
              {!isRest && (
                <>
                  <input className="input" type="number" min="0" step="0.1" aria-label="Target" value={target} onChange={(e) => setTarget(e.target.value)} />
                  <Button disabled={target === "" || Number(target) < 0} onClick={() => void applyEdit({ target_value: Number(target) })}>Save target</Button>
                  <input className="input" maxLength={200} aria-label="Rest day note" placeholder="Why rest? (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
                  <Button onClick={() => void applyEdit({ workout_type: "rest", notes: note.trim() || null })}>Make rest day</Button>
                </>
              )}
              {isRest && <Button onClick={() => void applyEdit({ workout_type: "workout" })}>Make workout day</Button>}
            </div>
          )}
          {error && <p className="alert alert--error">{error}</p>}
        </section>
      )}
      {!entry ? <p className="empty">No entry for this day.</p> : (
        <>
          <p>{entry.completed ? "✅ Completed" : "❌ Not completed"}</p>
          {entry.metric_values.length > 0 && (
            <ul>
              {entry.metric_values.map((v) => {
                const m = metricFor(v.metric_id);
                return <li key={v.id}>{m?.name ?? `#${v.metric_id}`}: {v.value}{m?.unit ? ` ${m.unit}` : ""}</li>;
              })}
            </ul>
          )}
        </>
      )}
    </Modal>
  );
}
