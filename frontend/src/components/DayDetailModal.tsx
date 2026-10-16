import type { Entry } from "../types/entry";
import type { Metric } from "../types/metric";
import { Button } from "./Button";
import { Modal } from "./Modal";

type Props = { date: string; entry?: Entry; metrics: Metric[]; onClose: () => void; onEdit: () => void };

export function DayDetailModal({ date, entry, metrics, onClose, onEdit }: Props) {
  const metricFor = (id: number) => metrics.find((m) => m.id === id);
  return (
    <Modal
      title={date}
      onClose={onClose}
      footer={<Button variant="primary" onClick={onEdit}>{entry ? "Edit entry" : "Log entry"}</Button>}
    >
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
