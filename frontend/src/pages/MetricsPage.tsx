import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import {
  getWorkspaceMetricCatalog,
  getWorkspaceMetricValues,
  getWorkspaceSnapshot,
} from "../api/workspace";
import { DataTable, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";
import { formatDate, formatDateTime, getStatementRows } from "../lib/finance";

type MetricsPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
};

export function MetricsPage({ selectedCode, selectedStock }: MetricsPageProps) {
  const snapshotQuery = useQuery({
    queryKey: ["workspace-snapshot", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceSnapshot(selectedCode),
  });

  const catalogQuery = useQuery({
    queryKey: ["workspace-metric-catalog", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceMetricCatalog(selectedCode),
  });

  const metricsQuery = useQuery({
    queryKey: ["workspace-metric-values", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceMetricValues(selectedCode),
  });

  const summaryItems = useMemo(
    () => [
      {
        label: "Company",
        value: selectedStock?.stock_name ?? snapshotQuery.data?.stock.stock_name ?? "Awaiting selection",
        note: selectedStock?.stock_code ?? (selectedCode || "Choose a stock from the rail"),
      },
      {
        label: "Market",
        value: selectedStock?.market ?? snapshotQuery.data?.stock.market ?? "Unknown",
        note: selectedStock?.industry ?? "Industry unavailable",
      },
      {
        label: "Listed",
        value: formatDate(selectedStock?.list_date),
        note: "Listing date from the stock registry",
      },
      {
        label: "Archive refresh",
        value: formatDateTime(snapshotQuery.data?.updated_at),
        note: snapshotQuery.data?.source ?? "Baidu archive feed",
      },
    ],
    [selectedCode, selectedStock, snapshotQuery.data],
  );

  const categorySummary = useMemo(() => {
    const categories = metricsQuery.data?.categories ?? {};
    return [
      {
        label: "Catalog size",
        value: String(catalogQuery.data?.total ?? 0),
        note: "Registered metrics in the workspace catalog",
      },
      {
        label: "Profitability",
        value: String(categories.profitability?.length ?? 0),
        note: "Profitability metrics currently exposed",
      },
      {
        label: "Cashflow",
        value: String(categories.cashflow?.length ?? 0),
        note: "Cash-based evidence block",
      },
      {
        label: "Trend",
        value: String(categories.trend?.length ?? 0),
        note: "Growth and directional metrics",
      },
    ];
  }, [catalogQuery.data?.total, metricsQuery.data?.categories]);

  if (!selectedCode) {
    return (
      <SectionCard title="Metrics page" eyebrow="No stock selected">
        <StateBlock
          title="Pick a company to begin"
          description="Use the left rail to choose a stock code or search a company name."
        />
      </SectionCard>
    );
  }

  if (snapshotQuery.isError || catalogQuery.isError || metricsQuery.isError) {
    const message =
      (snapshotQuery.error as Error | undefined)?.message ??
      (catalogQuery.error as Error | undefined)?.message ??
      (metricsQuery.error as Error | undefined)?.message ??
      "Unable to load the workspace metrics view.";

    return (
      <SectionCard title="Metrics page" eyebrow="Data unavailable">
        <StateBlock tone="danger" title="Unable to load metrics" description={message} />
      </SectionCard>
    );
  }

  const balanceRows = getStatementRows(snapshotQuery.data, "balance_sheet");
  const incomeRows = getStatementRows(snapshotQuery.data, "income_statement");
  const cashflowRows = getStatementRows(snapshotQuery.data, "cashflow_statement");

  return (
    <div className="page-stack">
      <SectionCard
        title={selectedStock?.stock_name ?? snapshotQuery.data?.stock.stock_name ?? selectedCode}
        eyebrow="Metrics workspace"
        action={<span className="section-meta">Code {selectedCode}</span>}
      >
        <div className="hero-copy">
          <p>
            Archive-first financial statements and the first wave of reusable metrics now live in
            one workspace. This page is the dense, evidence-first view for raw statements and
            grouped indicators.
          </p>
        </div>

        <MetricGrid items={summaryItems} />
      </SectionCard>

      <div className="two-up">
        <SectionCard
          title="Balance sheet"
          eyebrow="Archive snapshot"
          action={<span className="section-meta">{balanceRows.length} fields</span>}
        >
          {snapshotQuery.isLoading ? (
            <LoadingSkeleton lines={5} />
          ) : (
            <DataTable rows={balanceRows} emptyLabel="No balance sheet rows were returned yet." />
          )}
        </SectionCard>

        <SectionCard
          title="Income statement"
          eyebrow="Archive snapshot"
          action={<span className="section-meta">{incomeRows.length} fields</span>}
        >
          {snapshotQuery.isLoading ? (
            <LoadingSkeleton lines={5} />
          ) : (
            <DataTable rows={incomeRows} emptyLabel="No income statement rows were returned yet." />
          )}
        </SectionCard>
      </div>

      <SectionCard
        title="Cash flow statement"
        eyebrow="Archive snapshot"
        action={<span className="section-meta">{cashflowRows.length} fields</span>}
      >
        {snapshotQuery.isLoading ? (
          <LoadingSkeleton lines={6} />
        ) : (
          <DataTable rows={cashflowRows} emptyLabel="No cash flow rows were returned yet." />
        )}
      </SectionCard>

      <div className="two-up">
        <SectionCard title="Metric catalog" eyebrow="Workspace registry">
          {catalogQuery.isLoading ? (
            <LoadingSkeleton lines={4} />
          ) : (
            <MetricGrid items={categorySummary} />
          )}
        </SectionCard>

        <SectionCard title="Metric digest" eyebrow="Narrative lead">
          {metricsQuery.isLoading ? (
            <LoadingSkeleton lines={4} />
          ) : (
            <div className="copy-block">
              <p>{metricsQuery.data?.summary ?? "No metric summary returned yet."}</p>
              <p>
                Available periods: {(snapshotQuery.data?.available_periods ?? []).slice(0, 3).join(", ") || "No periods available"}.
              </p>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
