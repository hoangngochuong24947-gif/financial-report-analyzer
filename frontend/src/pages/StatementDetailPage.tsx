import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import {
  getWorkspaceSnapshot,
  getWorkspaceStatements,
  resolveWorkspaceStatements,
  type WorkspaceSnapshotResponse,
  type WorkspaceStatementsResponse,
} from "../api/workspace";
import { DataTable, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";
import { formatDate, formatDateTime, getStatementRows } from "../lib/finance";
import { getBrowserLocale, getWorkspaceCopy, type Lang } from "../lib/i18n";

type StatementKey = "overview" | "balance_sheet" | "income_statement" | "cashflow_statement";

type StatementDetailPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
  lang: Lang;
  onBackToOverview: () => void;
};

function toSnapshotLike(
  selectedCode: string,
  selectedStock: StockInfo | undefined,
  data: WorkspaceStatementsResponse | WorkspaceSnapshotResponse | undefined,
): WorkspaceSnapshotResponse | undefined {
  if (!data) {
    return undefined;
  }

  if ("stock" in data) {
    return data;
  }

  const stockName = data.stock_name ?? selectedStock?.stock_name ?? selectedCode;

  return {
    stock: {
      stock_code: selectedCode,
      stock_name: stockName,
      market: selectedStock?.market ?? "Unknown",
    },
    available_periods: data.available_periods ?? [],
    statements: {
      balance_sheet: data.statements?.balance_sheet ?? data.balance_sheet ?? [],
      income_statement: data.statements?.income_statement ?? data.income_statement ?? [],
      cashflow_statement: data.statements?.cashflow_statement ?? data.cashflow_statement ?? [],
    },
    source: data.source ?? "workspace",
    updated_at: data.updated_at,
  };
}

function statementLabel(copy: ReturnType<typeof getWorkspaceCopy>, key: StatementKey): string {
  if (key === "balance_sheet") return copy.statements.balanceSheet;
  if (key === "income_statement") return copy.statements.incomeStatement;
  if (key === "cashflow_statement") return copy.statements.cashflowStatement;
  return copy.statements.overview;
}

export function StatementDetailPage({
  selectedCode,
  selectedStock,
  lang,
  onBackToOverview,
}: StatementDetailPageProps) {
  const copy = getWorkspaceCopy(lang);
  const locale = getBrowserLocale(lang);
  const [activeTab, setActiveTab] = useState<StatementKey>("overview");

  const statementsQuery = useQuery({
    queryKey: ["workspace-statements", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: async () => {
      try {
        return await getWorkspaceStatements(selectedCode, lang);
      } catch {
        return null;
      }
    },
    staleTime: 60_000,
  });

  const snapshotQuery = useQuery({
    queryKey: ["workspace-statement-snapshot", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceSnapshot(selectedCode, lang),
    staleTime: 60_000,
  });

  const snapshotLike = useMemo(
    () =>
      toSnapshotLike(
        selectedCode,
        selectedStock,
        resolveWorkspaceStatements(statementsQuery.data ?? undefined) ??
          snapshotQuery.data ??
          undefined,
      ),
    [selectedCode, selectedStock, snapshotQuery.data, statementsQuery.data],
  );

  const metaItems = useMemo(
    () => [
      {
        label: copy.statements.reportDate,
        value: snapshotLike?.updated_at
          ? formatDateTime(snapshotLike.updated_at, locale)
          : snapshotLike?.available_periods?.[0] ?? copy.shared.unavailable,
        note: snapshotLike?.source ?? copy.statements.source,
      },
      {
        label: copy.statements.availablePeriods,
        value: snapshotLike?.available_periods?.length ? String(snapshotLike.available_periods.length) : "0",
        note: snapshotLike?.available_periods?.slice(0, 3).join(" / ") ?? copy.statements.noStatements,
      },
      {
        label: copy.shell.selectedCompany,
        value: selectedStock?.stock_name ?? snapshotLike?.stock.stock_name ?? selectedCode,
        note: selectedStock?.stock_code ?? selectedCode,
      },
      {
        label: copy.shell.archiveWorkspaces,
        value: snapshotLike?.source ?? copy.shared.unavailable,
        note: snapshotLike ? copy.shared.archiveSummary : copy.statements.noArchive,
      },
    ],
    [copy, locale, selectedCode, selectedStock, snapshotLike],
  );

  if (!selectedCode) {
    return (
      <SectionCard title={copy.statements.title} eyebrow={copy.statements.eyebrow}>
        <StateBlock title={copy.shared.chooseStock} description={copy.statements.description} />
      </SectionCard>
    );
  }

  if (snapshotQuery.isError && !snapshotLike) {
    const message = (snapshotQuery.error as Error | undefined)?.message ?? copy.statements.loadError;
    return (
      <SectionCard title={copy.statements.title} eyebrow={copy.statements.eyebrow}>
        <StateBlock tone="danger" title={copy.statements.loadError} description={message} />
      </SectionCard>
    );
  }

  const balanceRows = getStatementRows(snapshotLike, "balance_sheet");
  const incomeRows = getStatementRows(snapshotLike, "income_statement");
  const cashflowRows = getStatementRows(snapshotLike, "cashflow_statement");

  const renderTable = (key: Exclude<StatementKey, "overview">) => {
    const rows =
      key === "balance_sheet" ? balanceRows : key === "income_statement" ? incomeRows : cashflowRows;

    return rows.length > 0 ? (
      <DataTable rows={rows} emptyLabel={copy.statements.tableEmpty} />
    ) : (
      <StateBlock title={copy.statements.noStatements} description={copy.statements.tableEmpty} />
    );
  };

  const activeTitle = statementLabel(copy, activeTab);

  return (
    <div className="page-stack">
      <SectionCard
        title={snapshotLike?.stock.stock_name ?? selectedStock?.stock_name ?? selectedCode}
        eyebrow={copy.statements.title}
        action={
          <button type="button" className="ghost-button" onClick={onBackToOverview}>
            {copy.statements.backToOverview}
          </button>
        }
      >
        <MetricGrid items={metaItems} />
      </SectionCard>

      <SectionCard
        title={copy.statements.title}
        eyebrow={copy.statements.eyebrow}
        action={<span className="section-meta">{activeTitle}</span>}
      >
        <div className="statement-tabs" role="tablist" aria-label={copy.statements.title}>
          {(["overview", "balance_sheet", "income_statement", "cashflow_statement"] as StatementKey[]).map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={tab === activeTab}
              className={`statement-tab ${tab === activeTab ? "statement-tab-active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              <strong>{statementLabel(copy, tab)}</strong>
              <span>
                {tab === "overview" ? copy.metrics.statementPreviewHint : copy.statements.availablePeriods}
              </span>
            </button>
          ))}
        </div>
      </SectionCard>

      {activeTab === "overview" ? (
        <>
          <div className="two-up">
            <SectionCard title={copy.statements.balanceSheet} eyebrow={copy.statements.overview}>
              {snapshotQuery.isLoading && !snapshotLike ? (
                <LoadingSkeleton lines={5} />
              ) : (
                <DataTable
                  rows={balanceRows.slice(0, 8)}
                  emptyLabel={copy.statements.tableEmpty}
                />
              )}
            </SectionCard>

            <SectionCard title={copy.statements.incomeStatement} eyebrow={copy.statements.overview}>
              {snapshotQuery.isLoading && !snapshotLike ? (
                <LoadingSkeleton lines={5} />
              ) : (
                <DataTable
                  rows={incomeRows.slice(0, 8)}
                  emptyLabel={copy.statements.tableEmpty}
                />
              )}
            </SectionCard>
          </div>

          <SectionCard title={copy.statements.cashflowStatement} eyebrow={copy.statements.overview}>
            {snapshotQuery.isLoading && !snapshotLike ? (
              <LoadingSkeleton lines={5} />
            ) : (
              <DataTable
                rows={cashflowRows.slice(0, 8)}
                emptyLabel={copy.statements.tableEmpty}
              />
            )}
          </SectionCard>
        </>
      ) : (
        <SectionCard title={activeTitle} eyebrow={copy.statements.description}>
          {snapshotQuery.isLoading && !snapshotLike ? (
            <LoadingSkeleton lines={6} />
          ) : (
            renderTable(activeTab as Exclude<StatementKey, "overview">)
          )}
        </SectionCard>
      )}
    </div>
  );
}

