import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import { getWorkspaceMetricCatalog, getWorkspaceMetricValues, getWorkspaceSnapshot } from "../api/workspace";
import { DataTable, LoadingSkeleton, MetricGrid, MetricTable, SectionCard, StateBlock } from "../components/DataBlocks";
import { formatDate, formatDateTime, getMetricDisplayLabel, getStatementRows } from "../lib/finance";
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
  const [activeGroup, setActiveGroup] = useState<string>("");

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

  const categoryEntries = useMemo(() => Object.entries(metricsQuery.data?.categories ?? {}), [metricsQuery.data?.categories]);

  useEffect(() => {
    if (!activeGroup && categoryEntries.length > 0) {
      setActiveGroup(categoryEntries[0][0]);
    }
  }, [activeGroup, categoryEntries]);

  const balanceRows = getStatementRows(snapshotQuery.data, "balance_sheet");
  const incomeRows = getStatementRows(snapshotQuery.data, "income_statement");
  const cashflowRows = getStatementRows(snapshotQuery.data, "cashflow_statement");
  const activeMetricItems = metricsQuery.data?.categories?.[activeGroup] ?? categoryEntries[0]?.[1] ?? [];

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
        action={
          <button type="button" className="ghost-button" onClick={onOpenStatementDetail}>
            {copy.metrics.openDetail}
          </button>
        }
      >
        <div className="hero-copy">
          <p>{copy.metrics.description}</p>
        </div>

        <MetricGrid items={summaryItems} />
      </SectionCard>

      <SectionCard
        title={copy.metrics.statementPreviewTitle}
        eyebrow={copy.metrics.overviewTitle}
        action={<span className="section-meta">{copy.metrics.statementPreviewHint}</span>}
      >
        {snapshotQuery.isLoading ? (
          <LoadingSkeleton lines={6} />
        ) : (
          <div className="statement-panel-grid">
            <article className="statement-preview-panel">
              <div className="statement-preview-head">
                <h3>{copy.statements.balanceSheet}</h3>
                <button type="button" className="ghost-button" onClick={onOpenStatementDetail}>
                  {copy.shell.openStatements}
                </button>
              </div>
              <DataTable rows={balanceRows.slice(0, 6)} emptyLabel={copy.metrics.noData} locale={locale} />
            </article>

            <article className="statement-preview-panel">
              <div className="statement-preview-head">
                <h3>{copy.statements.incomeStatement}</h3>
                <button type="button" className="ghost-button" onClick={onOpenStatementDetail}>
                  {copy.shell.openStatements}
                </button>
              </div>
              <DataTable rows={incomeRows.slice(0, 6)} emptyLabel={copy.metrics.noData} locale={locale} />
            </article>

            <article className="statement-preview-panel">
              <div className="statement-preview-head">
                <h3>{copy.statements.cashflowStatement}</h3>
                <button type="button" className="ghost-button" onClick={onOpenStatementDetail}>
                  {copy.shell.openStatements}
                </button>
              </div>
              <DataTable rows={cashflowRows.slice(0, 6)} emptyLabel={copy.metrics.noData} locale={locale} />
            </article>
          </div>
        )}
      </SectionCard>

      <div className="two-up">
        <SectionCard title={copy.metrics.metricCatalogTitle} eyebrow={copy.metrics.overviewTitle}>
          {catalogQuery.isLoading ? <LoadingSkeleton lines={4} /> : <MetricGrid items={categorySummary} />}
        </SectionCard>

        <SectionCard title={copy.metrics.metricDigestTitle} eyebrow={copy.metrics.overviewTitle}>
          {metricsQuery.isLoading ? (
            <LoadingSkeleton lines={4} />
          ) : (
            <div className="copy-block">
              <p>{metricsQuery.data?.summary ?? copy.metrics.noData}</p>
              <p>
                {copy.metrics.availablePeriods}:{" "}
                {(snapshotQuery.data?.available_periods ?? []).slice(0, 4).join(", ") || copy.metrics.noData}.
              </p>
            </div>
          )}
        </SectionCard>
      </div>

      <SectionCard title={copy.metrics.metricDigestTitle} eyebrow={copy.metrics.metricCatalogTitle}>
        {metricsQuery.isLoading ? (
          <LoadingSkeleton lines={5} />
        ) : categoryEntries.length > 0 ? (
          <div className="metric-detail-stack">
            <div className="metric-group-switcher">
              {categoryEntries.map(([groupKey, items]) => (
                <button
                  key={groupKey}
                  type="button"
                  className={`metric-group-chip ${groupKey === activeGroup ? "metric-group-chip-active" : ""}`}
                  onClick={() => setActiveGroup(groupKey)}
                >
                  <strong>{getMetricDisplayLabel(groupKey, groupKey, lang)}</strong>
                  <span>{items.length}</span>
                </button>
              ))}
            </div>
            <MetricTable
              items={activeMetricItems}
              emptyLabel={copy.metrics.noData}
              locale={locale}
              lang={lang}
            />
          </div>
        ) : (
          <StateBlock title={copy.metrics.noData} description={copy.metrics.dataUnavailable} />
        )}
      </SectionCard>
    </div>
  );
}
