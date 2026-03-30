import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import { getWorkspaceMetricCatalog, getWorkspaceMetricValues, getWorkspaceSnapshot } from "../api/workspace";
import { DataTable, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";
import { formatDate, formatDateTime, getStatementRows } from "../lib/finance";
import { getBrowserLocale, getWorkspaceCopy, type Lang } from "../lib/i18n";

type MetricsPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
  lang: Lang;
  onOpenStatementDetail: () => void;
};

export function MetricsPage({ selectedCode, selectedStock, lang, onOpenStatementDetail }: MetricsPageProps) {
  const copy = getWorkspaceCopy(lang);
  const locale = getBrowserLocale(lang);

  const snapshotQuery = useQuery({
    queryKey: ["workspace-snapshot", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceSnapshot(selectedCode, lang),
    staleTime: 60_000,
  });

  const catalogQuery = useQuery({
    queryKey: ["workspace-metric-catalog", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceMetricCatalog(selectedCode, lang),
  });

  const metricsQuery = useQuery({
    queryKey: ["workspace-metric-values", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceMetricValues(selectedCode, lang),
  });

  const summaryItems = useMemo(
    () => [
      {
        label: copy.shell.selectedCompany,
        value: selectedStock?.stock_name ?? snapshotQuery.data?.stock.stock_name ?? copy.shared.chooseStock,
        note: selectedStock?.stock_code ?? (selectedCode || copy.shared.chooseStock),
      },
      {
        label: copy.shell.market,
        value: selectedStock?.market ?? snapshotQuery.data?.stock.market ?? copy.shared.unavailable,
        note: selectedStock?.industry ?? copy.shared.unavailable,
      },
      {
        label: copy.shared.registryListing,
        value: formatDate(selectedStock?.list_date, locale),
        note: selectedStock?.list_date ? copy.shared.registryListing : copy.shared.unavailable,
      },
      {
        label: copy.metrics.archiveRefresh,
        value: formatDateTime(snapshotQuery.data?.updated_at, locale),
        note: snapshotQuery.data?.source ?? copy.metrics.snapshotSource,
      },
    ],
    [copy, locale, selectedCode, selectedStock, snapshotQuery.data],
  );

  const categorySummary = useMemo(() => {
    const categories = metricsQuery.data?.categories ?? {};
    return [
      {
        label: copy.metrics.catalogSize,
        value: String(catalogQuery.data?.total ?? 0),
        note: copy.metrics.metricCatalogTitle,
      },
      {
        label: copy.metrics.profitability,
        value: String(categories.profitability?.length ?? 0),
        note: copy.metrics.metricDigestTitle,
      },
      {
        label: copy.metrics.cashflow,
        value: String(categories.cashflow?.length ?? 0),
        note: copy.metrics.statementPreviewHint,
      },
      {
        label: copy.metrics.trend,
        value: String(categories.trend?.length ?? 0),
        note: copy.metrics.description,
      },
    ];
  }, [catalogQuery.data?.total, copy, metricsQuery.data?.categories]);

  const balanceRows = getStatementRows(snapshotQuery.data, "balance_sheet");
  const incomeRows = getStatementRows(snapshotQuery.data, "income_statement");
  const cashflowRows = getStatementRows(snapshotQuery.data, "cashflow_statement");

  if (!selectedCode) {
    return (
      <SectionCard title={copy.metrics.title} eyebrow={copy.metrics.eyebrow}>
        <StateBlock title={copy.metrics.noStock} description={copy.shell.selectedCompanyHint} />
      </SectionCard>
    );
  }

  if (snapshotQuery.isError || catalogQuery.isError || metricsQuery.isError) {
    const message =
      (snapshotQuery.error as Error | undefined)?.message ??
      (catalogQuery.error as Error | undefined)?.message ??
      (metricsQuery.error as Error | undefined)?.message ??
      copy.metrics.dataUnavailable;

    return (
      <SectionCard title={copy.metrics.title} eyebrow={copy.metrics.eyebrow}>
        <StateBlock tone="danger" title={copy.metrics.dataUnavailable} description={message} />
      </SectionCard>
    );
  }

  return (
    <div className="page-stack">
      <SectionCard
        title={selectedStock?.stock_name ?? snapshotQuery.data?.stock.stock_name ?? selectedCode}
        eyebrow={copy.metrics.eyebrow}
        action={<button type="button" className="ghost-button" onClick={onOpenStatementDetail}>{copy.metrics.openDetail}</button>}
      >
        <div className="hero-copy">
          <p>{copy.metrics.description}</p>
        </div>

        <MetricGrid items={summaryItems} />
      </SectionCard>

      <div className="two-up">
        <SectionCard
          title={copy.metrics.statementPreviewTitle}
          eyebrow={copy.metrics.overviewTitle}
          action={<span className="section-meta">{copy.metrics.statementPreviewHint}</span>}
        >
          {snapshotQuery.isLoading ? (
            <LoadingSkeleton lines={5} />
          ) : (
            <div className="statement-preview-stack">
              <DataTable rows={balanceRows.slice(0, 6)} emptyLabel={copy.metrics.noData} />
              <DataTable rows={incomeRows.slice(0, 6)} emptyLabel={copy.metrics.noData} />
              <DataTable rows={cashflowRows.slice(0, 6)} emptyLabel={copy.metrics.noData} />
            </div>
          )}
        </SectionCard>

        <SectionCard title={copy.metrics.metricCatalogTitle} eyebrow={copy.metrics.overviewTitle}>
          {catalogQuery.isLoading ? (
            <LoadingSkeleton lines={4} />
          ) : (
            <MetricGrid items={categorySummary} />
          )}
        </SectionCard>
      </div>

      <SectionCard title={copy.metrics.metricDigestTitle} eyebrow={copy.metrics.overviewTitle}>
        {metricsQuery.isLoading ? (
          <LoadingSkeleton lines={4} />
        ) : (
          <div className="copy-block">
            <p>{metricsQuery.data?.summary ?? copy.metrics.noData}</p>
            <p>
              {copy.metrics.availablePeriods}:{" "}
              {(snapshotQuery.data?.available_periods ?? []).slice(0, 3).join(", ") || copy.metrics.noData}.
            </p>
          </div>
        )}
      </SectionCard>
    </div>
  );
}

