import { api } from "./client";
import type { HabitTemplate } from "../types/template";

export async function fetchTemplates(): Promise<HabitTemplate[]> {
  return (await api.get<HabitTemplate[]>("/api/templates")).data;
}
