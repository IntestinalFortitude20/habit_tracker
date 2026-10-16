import { api } from "./client";
import type { Entry, EntryPayload } from "../types/entry";

const base = (habitId: number) => `/api/habits/${habitId}/entries`;

export async function fetchEntries(habitId: number, limit = 14): Promise<Entry[]> {
  return (await api.get<Entry[]>(base(habitId), { params: { limit, order: "desc" } })).data;
}

export async function fetchEntriesInRange(habitId: number, start: string, end: string): Promise<Entry[]> {
  return (await api.get<Entry[]>(base(habitId), { params: { start, end, order: "asc" } })).data;
}

export async function fetchLatestEntry(habitId: number): Promise<Entry | null> {
  const r = (await api.get<Entry[]>(base(habitId), { params: { limit: 1, order: "desc" } })).data;
  return r[0] ?? null;
}

// POST upserts: logging an existing date replaces that day's entry.
export async function saveEntry(habitId: number, payload: EntryPayload): Promise<Entry> {
  return (await api.post<Entry>(base(habitId), payload)).data;
}

export async function deleteEntry(habitId: number, entryId: number): Promise<void> {
  await api.delete(`${base(habitId)}/${entryId}`);
}
