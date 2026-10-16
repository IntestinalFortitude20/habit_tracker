import { api } from "./client";

export type ChatRole = "user" | "assistant";
export type ChatMessage = { role: ChatRole; content: string };
export type ChatRequest = { message: string; habit_id: number | null; history: ChatMessage[] };
export type ChatResponse = { reply: string };

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  return (await api.post<ChatResponse>("/api/chat", payload)).data;
}
