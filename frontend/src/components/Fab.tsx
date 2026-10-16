export function Fab({ label, onClick }: { label: string; onClick: () => void }) {
  return <button type="button" className="fab" aria-label={label} title={label} onClick={onClick}>+</button>;
}
