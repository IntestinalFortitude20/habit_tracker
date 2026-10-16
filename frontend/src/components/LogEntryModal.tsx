import { useEffect, useState } from "react";
import { fetchEntriesInRange, saveEntry } from "../api/entries";
import type { Metric } from "../types/metric";
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

  // Prefill when the selected date already has an entry.
  useEffect(() => {
    if (!date) return;
    let cancelled = false;
    fetchEntriesInRange(habitId, date, date)
      .then(([en]) => {
        if (cancelled) return;
        setExisting(!!en);
        setCompleted(en ? en.completed : true);
        setValues(en ? Object.fromEntries(en.metric_values.map((v) => [v.metric_id, String(v.value)])) : {});
      })
      .catch((err) => {
        if (!cancelled) setError("Failed to load existing entry.");
        console.error(err);
      });
    return () => { cancelled = true; };
  }, [habitId, date]);

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
    <Modal title="Log entry" onClose={onClose}>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {success && <p style={{ color: "#146c2e" }}>{success}</p>}
      <form onSubmit={onSubmit} style={{ display: "grid", gap: "0.5rem" }}>
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
        <button disabled={saving} type="submit">{saving ? "Saving..." : existing ? "Update entry" : "Save entry"}</button>
      </form>
      {existing && <p><small>This date already has an entry; saving replaces it.</small></p>}
    </Modal>
  );
}
