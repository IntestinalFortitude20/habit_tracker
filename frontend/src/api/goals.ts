import axios from "axios";
import { api } from "./client";
import type { Goal, GoalPayload, GoalPlanDay, GoalProgress, GoalTypeInfo, Workout } from "../types/goal";

const base = (habitId: number) => `/api/habits/${habitId}/goal`;

export async function fetchGoalTypes(): Promise<{ goal_types: GoalTypeInfo[]; disclaimer: string }> {
  return (await api.get("/api/goal-types")).data;
}

export async function fetchGoal(habitId: number): Promise<Goal | null> {
  try {
    return (await api.get<Goal>(base(habitId))).data;
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) return null;
    throw err;
  }
}

export async function fetchPlan(habitId: number, start: string, end: string): Promise<Workout[]> {
  return (await api.get<Workout[]>(`${base(habitId)}/plan`, { params: { start, end } })).data;
}

export async function fetchProgress(habitId: number): Promise<GoalProgress> {
  return (await api.get<GoalProgress>(`${base(habitId)}/progress`)).data;
}

export async function createGoal(habitId: number, payload: GoalPayload): Promise<void> {
  await api.post(base(habitId), payload);
}

export async function draftGoal(habitId: number, payload: GoalPayload): Promise<{ plan: GoalPlanDay[]; disclaimer: string }> {
  return (await api.post(`${base(habitId)}/draft`, payload)).data;
}

export async function acceptGoal(habitId: number, goal: GoalPayload, plan: GoalPlanDay[]): Promise<void> {
  await api.post(`${base(habitId)}/accept`, { goal, plan });
}

export async function updatePlanDay(habitId: number, day: GoalPlanDay): Promise<void> {
  await api.put(`${base(habitId)}/plan/${day.date}`, day);
}

export async function adjustGoalPlan(habitId: number, prompt: string): Promise<void> {
  await api.post(`${base(habitId)}/adjust`, { prompt });
}

export async function regenerateGoal(habitId: number): Promise<void> {
  await api.post(`${base(habitId)}/regenerate`, {});
}

export async function cancelGoal(habitId: number): Promise<void> {
  await api.delete(base(habitId));
}

// Extracts the backend's rejection message (e.g. "too soon, earliest date ...").
export function goalErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (detail && typeof detail === "object" && typeof detail.message === "string") return detail.message;
    if (typeof detail === "string") return detail;
  }
  return "Failed to save goal.";
}
