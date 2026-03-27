import type { ReactNode } from "react";
import { formatValue, toTitle } from "../lib/finance";

export function SectionCard(props: {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card panel ${props.className ?? ""}`.trim()}>
      <div className="card-head">
        <div>
          {props.eyebrow ? <p className="card-eyebrow">{props.eyebrow}</p> : null}
          <h2>{props.title}</h2>
        </div>
        {props.action ? <div className="card-action">{props.action}</div> : null}
      </div>
      <div className="card-body">{props.children}</div>
    </section>
  );
}

export function StateBlock(props: {
  tone?: "neutral" | "warning" | "danger";
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className={`state-block state-${props.tone ?? "neutral"}`}>
      <div>
        <h3>{props.title}</h3>
        <p>{props.description}</p>
      </div>
      {props.action ? <div className="state-action">{props.action}</div> : null}
    </div>
  );
}

export function LoadingSkeleton(props: { lines?: number; compact?: boolean }) {
  const lines = props.lines ?? 3;
  return (
    <div className={`skeleton-stack ${props.compact ? "skeleton-stack-compact" : ""}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <span key={index} className="skeleton-line" />
      ))}
    </div>
  );
}

export function MetricGrid(props: {
  items: Array<{ label: string; value: ReactNode; note?: string }>;
}) {
  return (
    <div className="metric-grid">
      {props.items.map((item) => (
        <article key={item.label} className="metric-tile">
          <span className="metric-label">{item.label}</span>
          <strong className="metric-value">{item.value}</strong>
          {item.note ? <p className="metric-note">{item.note}</p> : null}
        </article>
      ))}
    </div>
  );
}

export function DataTable(props: {
  rows: Array<[string, unknown]>;
  emptyLabel: string;
}) {
  if (props.rows.length === 0) {
    return <StateBlock title="Nothing to show yet" description={props.emptyLabel} />;
  }

  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <tbody>
          {props.rows.map(([key, value]) => (
            <tr key={key}>
              <th>{toTitle(key)}</th>
              <td>{formatValue(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function BulletList(props: {
  items?: string[];
  emptyLabel: string;
  tone?: "neutral" | "positive" | "warning";
}) {
  const items = props.items ?? [];
  if (items.length === 0) {
    return <StateBlock title="No entries yet" description={props.emptyLabel} />;
  }

  return (
    <ul className={`bullet-list bullet-${props.tone ?? "neutral"}`}>
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

export function CopyBlock(props: { children: ReactNode }) {
  return <div className="copy-block">{props.children}</div>;
}
