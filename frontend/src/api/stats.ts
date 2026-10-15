import { api } from "./client";
import type { HabitStats } from "../types/entry";

export async function fetchStats(habitId: number): Promise<HabitStats> {
  return (await api.get<HabitStats>(`/api/habits/${habitId}/stats`)).data;
}
