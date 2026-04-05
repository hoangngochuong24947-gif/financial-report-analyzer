import type { StatementDetailRow } from "../api/workspace";
import { buildStatementSections, formatValue } from "../lib/finance";
import { StateBlock } from "./DataBlocks";

type StatementKey = "balance_sheet" | "income_statement" | "cashflow_statement";

export function FinancialStatementTable(props: {
  statementKey: StatementKey;
  rows: StatementDetailRow[];
  lang: "zh" | "en";
  locale: string;
  emptyLabel: string;
}) {
  const sections = buildStatementSections(props.statementKey, props.rows, props.lang);

  if (sections.length === 0) {
    return <StateBlock title="Nothing to show yet" description={props.emptyLabel} />;
  }

  return (
    <div className="statement-detail-table-wrap">
      <table className="statement-detail-table">
        <thead>
          <tr>
            <th>{props.lang === "zh" ? "科目" : "Line item"}</th>
            <th>{props.lang === "zh" ? "数值" : "Value"}</th>
            <th>{props.lang === "zh" ? "来源" : "Source"}</th>
          </tr>
        </thead>
        <tbody>
          {sections.map((section) => (
            <FragmentSection
              key={section.title}
              title={section.title}
              rows={section.rows}
              locale={props.locale}
              lang={props.lang}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FragmentSection(props: {
  title: string;
  rows: StatementDetailRow[];
  locale: string;
  lang: "zh" | "en";
}) {
  return (
    <>
      <tr className="statement-section-row">
        <th colSpan={3}>{props.title}</th>
      </tr>
      {props.rows.map((row) => {
        const renderedValue = row.display_value?.trim()
          ? row.display_value
          : formatValue(row.value, props.locale);
        return (
          <tr key={`${props.title}-${row.key}`}>
            <th>{row.label}</th>
            <td>
              <div className="statement-value-cell">
                <strong>{renderedValue}</strong>
                {row.unit ? <span>{row.unit}</span> : null}
                {row.is_estimated ? <em>{props.lang === "zh" ? "估算" : "Estimated"}</em> : null}
              </div>
            </td>
            <td>{row.source ?? "-"}</td>
          </tr>
        );
      })}
    </>
  );
}
