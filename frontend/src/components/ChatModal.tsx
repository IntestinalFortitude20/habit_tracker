import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import axios from "axios";
import { sendChat } from "../api/chat";
import type { ChatMessage } from "../api/chat";
import { Button } from "./Button";
import { Modal } from "./Modal";

const MAX_HISTORY = 10;
const MAX_LEN = 2000;

function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (!err.response) return "Could not reach the server. Check your connection.";
  }
  return "Something went wrong. Please try again.";
}

type Props = { habitId: number | null; habitName?: string; onClose: () => void };

export function ChatModal({ habitId, habitName, onClose }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSent, setLastSent] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, loading, error]);

  async function send(text: string, history: ChatMessage[]) {
    setLoading(true);
    setError(null);
    setLastSent(text);
    try {
      const { reply } = await sendChat({ message: text, habit_id: habitId, history: history.slice(-MAX_HISTORY) });
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
      setLastSent(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function submit() {
    const text = input.trim();
    if (!text || loading) return;
    const history = messages;
    setMessages([...history, { role: "user", content: text }]);
    setInput("");
    void send(text, history);
  }

  function retry() {
    if (!lastSent || loading) return;
    // the failed user message is the last one in state; history excludes it
    void send(lastSent, messages.slice(0, -1));
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <Modal title={habitName ? `Coach: ${habitName}` : "AI Coach"} onClose={onClose}>
      <div className="chat">
        <div className="chat__messages" aria-live="polite">
          {messages.length === 0 && (
            <p className="muted">
              {habitId === null ? "Ask for advice about your habits." : "Ask for advice about this habit."}
            </p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`chat__bubble chat__bubble--${m.role}`}>{m.content}</div>
          ))}
          {loading && <div className="chat__bubble chat__bubble--assistant" role="status">Thinking…</div>}
          {error && (
            <div className="alert alert--error" role="alert">
              {error} <Button onClick={retry} disabled={loading}>Retry</Button>
            </div>
          )}
          <div ref={endRef} />
        </div>
        <form className="chat__form" onSubmit={(e) => { e.preventDefault(); submit(); }}>
          <textarea
            rows={2}
            value={input}
            maxLength={MAX_LEN}
            placeholder="Type a message…"
            aria-label="Message"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <Button type="submit" variant="primary" disabled={loading || !input.trim()}>Send</Button>
        </form>
      </div>
    </Modal>
  );
}
