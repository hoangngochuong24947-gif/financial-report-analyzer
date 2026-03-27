import type { ReactNode } from "react";

export function WorkspaceSummary(props: {
  label: string;
  value: ReactNode;
  note?: string;
}) {
  return (
    <article className="summary-card">
      <span>{props.label}</span>
      <strong>{props.value}</strong>
      {props.note ? <p>{props.note}</p> : null}
    </article>
  );
}
