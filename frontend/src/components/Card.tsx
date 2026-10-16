import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`card ${className}`.trim()}>{children}</div>;
}

export function LinkCard({ to, children }: { to: string; children: ReactNode }) {
  return <Link to={to} className="card card--link">{children}</Link>;
}
