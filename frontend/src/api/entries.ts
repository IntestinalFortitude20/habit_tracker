import { api } from "./client";
import type { Entry, EntryPayload } from "../types/entry";

const base = (habitId: number) => `/api/habits/${habitId}/entries`;

export async function fetchEntries(habitId: number, limit = 14): Promise<Entry[]> {
  return (await api.get<Entry[]>(base(habitId), { params: { limit, order: "desc" } })).data;
}

// POST upserts: logging an existing date replaces that day's entry.
export async function saveEntry(habitId: number, payload: EntryPayload): Promise<Entry> {
  return (await api.post<Entry>(base(habitId), payload)).data;
}

export async function deleteEntry(habitId: number, entryId: number): Promise<void> {
  await api.delete(`${base(habitId)}/${entryId}`);
}
