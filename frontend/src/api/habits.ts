import { api } from "./client";
import type { CreateHabitPayload, Habit } from "../types/habit";

export async function fetchHabits(): Promise<Habit[]> {
  const res = await api.get<Habit[]>("/api/habits");
  return res.data;
}

export async function createHabit(payload: CreateHabitPayload): Promise<Habit> {
  const res = await api.post<Habit>("/api/habits", payload);
  return res.data;
}

export async function fetchHabit(habitId: number): Promise<Habit> {
  const res = await api.get<Habit>(`/api/habits/${habitId}`);
  return res.data;
}
