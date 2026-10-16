import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
  loading?: boolean;
  icon?: boolean;
};

export function Button({ variant = "secondary", loading = false, icon = false, className = "", disabled, type = "button", ...rest }: Props) {
  const cls = ["btn", `btn--${variant}`, icon && "btn--icon", loading && "btn--loading", className].filter(Boolean).join(" ");
  return <button {...rest} type={type} className={cls} disabled={disabled || loading} aria-busy={loading || undefined} />;
}
