import type { ReactNode } from "react";

type FabProps = {
  label: string;
  onClick: () => void;
  children?: ReactNode;
  variant?: "primary" | "chat";
  stacked?: boolean;
};

export function Fab({ label, onClick, children = "+", variant = "primary", stacked = false }: FabProps) {
  const cls = ["fab", variant === "chat" && "fab--chat", stacked && "fab--stacked"].filter(Boolean).join(" ");
  return <button type="button" className={cls} aria-label={label} title={label} onClick={onClick}>{children}</button>;
}

export function ChatFab({ onClick, stacked = false }: { onClick: () => void; stacked?: boolean }) {
  return (
    <Fab label="Open AI coach chat" variant="chat" stacked={stacked} onClick={onClick}>
      <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
        <path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2zM7 9h10v2H7V9zm6 5H7v-2h6v2zm4-6H7V6h10v2z" />
      </svg>
    </Fab>
  );
}
