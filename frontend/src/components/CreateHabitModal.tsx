import { useEffect, useState } from "react";
import { createHabit } from "../api/habits";
import { createMetric } from "../api/metrics";
import { fetchTemplates } from "../api/templates";
import type { MetricPayload } from "../types/metric";
import type { HabitTemplate } from "../types/template";
import { Button } from "./Button";
import { Modal } from "./Modal";

type Props = { onClose: () => void; onCreated: () => Promise<void> };

export function CreateHabitModal({ onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [templates, setTemplates] = useState<HabitTemplate[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [metrics, setMetrics] = useState<MetricPayload[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplates().then(setTemplates).catch((err) => console.error(err));
  }, []);

  function onTemplateChange(id: string) {
    setTemplateId(id);
    const t = templates.find((x) => x.id === id);
    if (!t) {
      setMetrics([]);
      return;
    }
    setName(t.name);
    setDescription(`${t.description} Cue: ${t.cue}. Tiny version: ${t.tiny_version}.`);
    setMetrics(t.metrics);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Habit name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const habit = await createHabit({ user_id: 1, name: name.trim(), description: description.trim() || undefined });
      for (const m of metrics) {
        await createMetric(habit.id, m);
      }
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
        {templates.length > 0 && (
          <label className="field">
            Start from template (optional)
            <select className="input" value={templateId} onChange={(e) => onTemplateChange(e.target.value)}>
              <option value="">None - start from scratch</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </label>
        )}
        <label className="field">
          Name
          <input className="input" placeholder="e.g. Air squats" value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className="field">
          Description (optional)
          <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        {metrics.length > 0 && (
          <p className="field">Metrics: {metrics.map((m) => (m.unit ? `${m.name} (${m.unit})` : m.name)).join(", ")}</p>
        )}
      </form>
    </Modal>
  );
}
