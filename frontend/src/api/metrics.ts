import { api } from "./client";
import type { Metric, MetricPayload } from "../types/metric";

const base = (habitId: number) => `/api/habits/${habitId}/metrics`;

export async function fetchMetrics(habitId: number): Promise<Metric[]> {
  return (await api.get<Metric[]>(base(habitId))).data;
}

export async function createMetric(habitId: number, payload: MetricPayload): Promise<Metric> {
  return (await api.post<Metric>(base(habitId), payload)).data;
}

export async function updateMetric(
  habitId: number,
  metricId: number,
  payload: Partial<MetricPayload>
): Promise<Metric> {
  return (await api.put<Metric>(`${base(habitId)}/${metricId}`, payload)).data;
}

export async function deleteMetric(habitId: number, metricId: number): Promise<void> {
  await api.delete(`${base(habitId)}/${metricId}`);
}
