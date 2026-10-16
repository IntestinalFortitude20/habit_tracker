import { useState } from "react";
import { createHabit } from "../api/habits";
import { Button } from "./Button";
import { Modal } from "./Modal";

type Props = { onClose: () => void; onCreated: () => Promise<void> };

export function CreateHabitModal({ onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Habit name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await createHabit({ user_id: 1, name: name.trim(), description: description.trim() || undefined });
    } catch (err) {
      setError("Failed to create habit. Ensure backend is reachable at port 8000 from this device.");
      console.error(err);
      setSaving(false);
      return;
    }
    try {
      await onCreated();
    } finally {
      onClose();
    }
  }

  return (
    <Modal
      title="Create habit"
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="submit" form="create-habit-form" loading={saving}>
            {saving ? "Creating..." : "Create"}
          </Button>
        </>
      }
    >
      {error && <p className="alert alert--error" role="alert">{error}</p>}
      <form id="create-habit-form" onSubmit={onSubmit} noValidate>
        <label className="field">
          Name
          <input className="input" placeholder="e.g. Air squats" value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className="field">
          Description (optional)
          <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
      </form>
    </Modal>
  );
}
