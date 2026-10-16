import { useState } from "react";
import { createMetric, deleteMetric, updateMetric } from "../api/metrics";
import type { Metric, MetricType } from "../types/metric";
import { Modal } from "./Modal";

const METRIC_TYPES: MetricType[] = ["boolean", "count", "duration", "rating"];

type Props = { habitId: number; metrics: Metric[]; onClose: () => void; onChanged: () => Promise<void> };

export function SettingsModal({ habitId, metrics, onClose, onChanged }: Props) {
  const [name, setName] = useState("");
  const [type, setType] = useState<MetricType>("count");
  const [unit, setUnit] = useState("");
  const [editing, setEditing] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editUnit, setEditUnit] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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

  return (
    <Modal title="Settings" onClose={onClose}>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {success && <p style={{ color: "#146c2e" }}>{success}</p>}
      <h3>Metrics</h3>
      {metrics.length === 0 ? <p>No metrics yet.</p> : (
        <ul style={{ paddingLeft: "1.25rem" }}>
          {metrics.map((m) => (
            <li key={m.id} style={{ marginBottom: "0.5rem" }}>
              {editing === m.id ? (
                <span style={{ display: "inline-flex", gap: "0.25rem", flexWrap: "wrap" }}>
                  <input value={editName} onChange={(e) => setEditName(e.target.value)} />
                  <input placeholder="Unit" value={editUnit} onChange={(e) => setEditUnit(e.target.value)} />
                  <button onClick={() => saveEdit(m)}>Save</button>
                  <button onClick={() => setEditing(null)}>Cancel</button>
                </span>
              ) : (
                <>
                  <strong>{m.name}</strong> ({m.type}{m.unit ? `, ${m.unit}` : ""}){" "}
                  <button onClick={() => startEdit(m)}>Edit</button>{" "}
                  <button onClick={() => onDelete(m)}>Delete</button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      <h3>Add metric</h3>
      <form onSubmit={onAdd} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <input placeholder="Name (e.g. Reps)" value={name} onChange={(e) => setName(e.target.value)} />
        <select value={type} onChange={(e) => setType(e.target.value as MetricType)}>
          {METRIC_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <input placeholder="Unit (optional)" value={unit} onChange={(e) => setUnit(e.target.value)} />
        <button type="submit">Add metric</button>
      </form>
    </Modal>
  );
}
