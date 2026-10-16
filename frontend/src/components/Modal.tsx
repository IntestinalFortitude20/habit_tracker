import { useEffect, useId, useRef } from "react";
import type { ReactNode } from "react";
import { Button } from "./Button";

type Props = { title: string; onClose: () => void; children: ReactNode; footer?: ReactNode };

export function Modal({ title, onClose, children, footer }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const node = ref.current;
    const focusable = () =>
      Array.from(node?.querySelectorAll<HTMLElement>('input, select, textarea, button, [href], [tabindex]:not([tabindex="-1"])') ?? [])
        .filter((el) => !(el as HTMLButtonElement).disabled);
    // Focus the dialog itself (not a field) so touch devices don't pop the keyboard open.
    node?.focus();
    const onFocusIn = (e: FocusEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && t !== node && t.matches("input, select, textarea")) {
        window.setTimeout(() => t.scrollIntoView({ block: "center", behavior: "smooth" }), 300);
      }
    };
    node?.addEventListener("focusin", onFocusIn);
    const vv = window.visualViewport;
    const onViewport = () => {
      if (!vv) return;
      document.documentElement.style.setProperty("--vvh", `${vv.height}px`);
      const active = document.activeElement as HTMLElement | null;
      if (active && node?.contains(active) && active.matches("input, select, textarea")) {
        active.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    };
    onViewport();
    vv?.addEventListener("resize", onViewport);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { closeRef.current(); return; }
      if (e.key !== "Tab") return;
      const els = focusable();
      if (els.length === 0) return;
      const first = els[0], last = els[els.length - 1];
      if (e.shiftKey && (document.activeElement === first || document.activeElement === node)) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      node?.removeEventListener("focusin", onFocusIn);
      vv?.removeEventListener("resize", onViewport);
      document.documentElement.style.removeProperty("--vvh");
      previous?.focus?.();
    };
  }, []);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        ref={ref}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal__header">
          <h2 className="modal__title" id={titleId}>{title}</h2>
          <Button icon onClick={onClose} aria-label="Close">✕</Button>
        </div>
        <div className="modal__body">{children}</div>
        {footer && <div className="modal__footer">{footer}</div>}
      </div>
    </div>
  );
}
