import { api } from "./client";

export type ChatRole = "user" | "assistant";
export type ChatMessage = { role: ChatRole; content: string };
export type ChatRequest = { message: string; habit_id: number | null; history: ChatMessage[] };
export type ChatResponse = { reply: string };

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  return (await api.post<ChatResponse>("/api/chat", payload)).data;
}

export class ChatStreamError extends Error {}

export async function streamChat(
  payload: ChatRequest,
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${api.defaults.baseURL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!resp.ok || !resp.body) {
    let detail = "Something went wrong. Please try again.";
    try {
      const body = await resp.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* keep default */
    }
    throw new ChatStreamError(detail);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let done = false;

  const handle = (block: string) => {
    let event = "message";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data += line.slice(5).trim();
    }
    if (!data) {
      if (event === "done") done = true;
      return;
    }
    const parsed = JSON.parse(data);
    if (event === "error") throw new ChatStreamError(parsed.detail ?? "The response was interrupted.");
    if (event === "done") done = true;
    else if (typeof parsed.token === "string") onToken(parsed.token);
  };

  for (;;) {
    const { value, done: eof } = await reader.read();
    buffer += decoder.decode(value, { stream: !eof }).replace(/\r\n/g, "\n");
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      handle(buffer.slice(0, idx));
      buffer = buffer.slice(idx + 2);
    }
    if (eof) break;
  }
  if (buffer.trim()) handle(buffer);
  if (!done) throw new ChatStreamError("The response was interrupted.");
}
