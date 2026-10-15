export type MetricType = "boolean" | "count" | "duration" | "rating";

export type Metric = {
  id: number;
  habit_id: number;
  name: string;
  type: MetricType;
  unit?: string | null;
};

export type MetricPayload = {
  name: string;
  type: MetricType;
  unit?: string | null;
};
