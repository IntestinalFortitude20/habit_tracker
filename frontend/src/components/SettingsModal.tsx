import { useEffect, useRef, useState } from "react";
import { deleteHabit } from "../api/habits";
import { createMetric, deleteMetric, updateMetric } from "../api/metrics";
import type { Metric, MetricType } from "../types/metric";
import { Button } from "./Button";
import { GoalSection } from "./GoalSection";
import { Modal } from "./Modal";

const METRIC_TYPES: MetricType[] = ["boolean", "count", "duration", "rating"];

type Props = {
  habitId: number;
  habitName?: string;
  metrics: Metric[];
  onClose: () => void;
  onChanged: () => Promise<void>;
  onHabitDeleted: () => void;
};

export function SettingsModal({ habitId, habitName, metrics, onClose, onChanged, onHabitDeleted }: Props) {
  const [name, setName] = useState("");
  const [type, setType] = useState<MetricType>("count");
  const [unit, setUnit] = useState("");
  const [editing, setEditing] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editUnit, setEditUnit] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!confirmingDelete) return;
    // Modal focuses its container on mount; focus Cancel afterwards so it is the default.
    const t = window.setTimeout(() => cancelRef.current?.focus(), 0);
    return () => window.clearTimeout(t);
  }, [confirmingDelete]);

  async function confirmDeleteHabit() {
    setDeleting(true);
    setError(null);
    try {
      await deleteHabit(habitId);
      onHabitDeleted();
    } catch (err) {
      setError("Failed to delete habit.");
      setConfirmingDelete(false);
      console.error(err);
    } finally {
      setDeleting(false);
    }
  }

  async function run(action: () => Promise<void>, failMsg: string, okMsg: string) {
    setError(null);
    setSuccess(null);
    try {
      await action();
      await onChanged();
      setSuccess(okMsg);
    } catch (err) {
      setError(failMsg);
      console.error(err);
    }
  }

  function onAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    void run(async () => {
      await createMetric(habitId, { name: name.trim(), type, unit: unit.trim() || null });
      setName("");
      setUnit("");
    }, "Failed to add metric.", "Metric added.");
  }

  function startEdit(m: Metric) {
    setEditing(m.id);
    setEditName(m.name);
    setEditUnit(m.unit ?? "");
  }

  function saveEdit(m: Metric) {
    if (!editName.trim()) return;
    void run(async () => {
      await updateMetric(habitId, m.id, { name: editName.trim(), unit: editUnit.trim() || null });
      setEditing(null);
    }, "Failed to update metric.", "Metric updated.");
  }

  function onDelete(m: Metric) {
    if (!window.confirm(`Delete metric "${m.name}" and its logged values?`)) return;
    void run(() => deleteMetric(habitId, m.id), "Failed to delete metric.", "Metric deleted.");
  }

  if (confirmingDelete) {
    const label = habitName ? `"${habitName}"` : "this habit";
    return (
      <Modal title="Delete habit?" onClose={() => setConfirmingDelete(false)}>
        <p>
          Are you sure you want to delete {label}? The habit and all of its entries cannot be recovered.
        </p>
        <div className="actions">
          <button ref={cancelRef} type="button" className="btn btn--secondary" onClick={() => setConfirmingDelete(false)} disabled={deleting}>
            Cancel
          </button>
          <Button variant="danger" loading={deleting} onClick={() => void confirmDeleteHabit()}>Delete habit</Button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal title="Settings" onClose={onClose}>
      {error && <p className="alert alert--error" role="alert">{error}</p>}
      {success && <p className="alert alert--success" role="status">{success}</p>}
      <GoalSection habitId={habitId} metrics={metrics} onChanged={onChanged} />
      <h3>Metrics</h3>
      {metrics.length === 0 ? <p className="empty">No metrics yet.</p> : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: "0.75rem" }}>
          {metrics.map((m) => (
            <li key={m.id} className="card">
              {editing === m.id ? (
                <div className="form-row">
                  <input className="input" aria-label="Metric name" value={editName} onChange={(e) => setEditName(e.target.value)} />
                  <input className="input" aria-label="Unit" placeholder="Unit" value={editUnit} onChange={(e) => setEditUnit(e.target.value)} />
                  <Button variant="primary" onClick={() => saveEdit(m)}>Save</Button>
                  <Button onClick={() => setEditing(null)}>Cancel</Button>
                </div>
              ) : (
                <div className="row">
                  <span><strong>{m.name}</strong> <small>({m.type}{m.unit ? `, ${m.unit}` : ""})</small></span>
                  <span className="actions">
                    <Button onClick={() => startEdit(m)}>Edit</Button>
                    <Button variant="danger" onClick={() => onDelete(m)}>Delete</Button>
                  </span>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      <h3>Add metric</h3>
      <form onSubmit={onAdd} className="form-row">
        <input className="input" aria-label="Metric name" placeholder="Name (e.g. Reps)" value={name} onChange={(e) => setName(e.target.value)} />
        <select className="input" aria-label="Metric type" value={type} onChange={(e) => setType(e.target.value as MetricType)}>
          {METRIC_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <input className="input" aria-label="Unit" placeholder="Unit (optional)" value={unit} onChange={(e) => setUnit(e.target.value)} />
        <Button variant="primary" type="submit">Add metric</Button>
      </form>
      <h3>Danger zone</h3>
      <Button variant="danger" onClick={() => setConfirmingDelete(true)}>Delete habit</Button>
    </Modal>
  );
}
