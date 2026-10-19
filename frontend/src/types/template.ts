import type { MetricPayload } from "./metric";

export type HabitTemplate = {
  id: string;
  name: string;
  description: string;
  cadence: string;
  cue: string;
  tiny_version: string;
  metrics: MetricPayload[];
};
