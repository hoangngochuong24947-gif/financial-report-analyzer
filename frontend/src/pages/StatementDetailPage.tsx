import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import { getWorkspaceStatements } from "../api/workspace";
import { FinancialStatementTable } from "../components/FinancialStatementTable";
import { DataTable, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";
import { formatDateTime } from "../lib/finance";
import { getBrowserLocale, getWorkspaceCopy, type Lang } from "../lib/i18n";

type StatementKey = "overview" | "balance_sheet" | "income_statement" | "cashflow_statement";

type StatementDetailPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
  lang: Lang;
  onBackToOverview: () => void;
};

function statementLabel(copy: ReturnType<typeof getWorkspaceCopy>, key: StatementKey): string {
  if (key === "balance_sheet") return copy.statements.balanceSheet;
  if (key === "income_statement") return copy.statements.incomeStatement;
  if (key === "cashflow_statement") return copy.statements.cashflowStatement;
  return copy.statements.overview;
}

function statementReadingHint(lang: Lang): string {
  if (lang === "zh") {
    return "当前页面以报表阅读为主，建议结合总览页的关键指标矩阵和模型页的结构判断交叉验证。";
  }
  return "This view is optimized for report reading. Cross-check it with the overview metrics and the model page for interpretation.";
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
  const [selectedPeriod, setSelectedPeriod] = useState<string | undefined>();

  const statementsQuery = useQuery({
    queryKey: ["workspace-statements-view", selectedCode, lang, selectedPeriod],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceStatements(selectedCode, lang, selectedPeriod),
    staleTime: 60_000,
  });

  const statementData = statementsQuery.data;

  useEffect(() => {
    if (!selectedPeriod && statementData?.available_periods?.length) {
      setSelectedPeriod(statementData.available_periods[0]);
    }
  }, [selectedPeriod, statementData?.available_periods]);

  const stockIdentity = statementData?.stock ?? {
    stock_code: selectedCode,
    stock_name: selectedStock?.stock_name ?? selectedCode,
    market: selectedStock?.market ?? "Unknown",
  };

  const statementTabs = statementData?.tabs ?? [];
  const balanceTab = statementTabs.find((tab) => tab.key === "balance_sheet");
  const incomeTab = statementTabs.find((tab) => tab.key === "income_statement");
  const cashflowTab = statementTabs.find((tab) => tab.key === "cashflow_statement");

  const metaItems = useMemo(
    () => [
      {
        label: copy.statements.reportDate,
        value: statementData?.selected_period ?? selectedPeriod ?? copy.shared.unavailable,
        note: statementData?.updated_at ? formatDateTime(statementData.updated_at, locale) : copy.statements.source,
      },
      {
        label: copy.statements.availablePeriods,
        value: statementData?.available_periods?.length ? String(statementData.available_periods.length) : "0",
        note: statementData?.available_periods?.slice(0, 4).join(" / ") ?? copy.statements.noStatements,
      },
      {
        label: copy.shell.selectedCompany,
        value: stockIdentity.stock_name,
        note: selectedStock?.stock_code ?? selectedCode,
      },
      {
        label: copy.shell.archiveWorkspaces,
        value: statementData?.source ?? copy.shared.unavailable,
        note: statementData ? copy.shared.archiveSummary : copy.statements.noArchive,
      },
    ],
    [copy, locale, selectedCode, selectedPeriod, selectedStock, statementData, stockIdentity.stock_name],
  );

  if (!selectedCode) {
    return (
      <SectionCard title={copy.statements.title} eyebrow={copy.statements.eyebrow}>
        <StateBlock title={copy.shared.chooseStock} description={copy.statements.description} />
      </SectionCard>
    );
  }

  if (statementsQuery.isError && !statementData) {
    const message = (statementsQuery.error as Error | undefined)?.message ?? copy.statements.loadError;
    return (
      <SectionCard title={copy.statements.title} eyebrow={copy.statements.eyebrow}>
        <StateBlock tone="danger" title={copy.statements.loadError} description={message} />
      </SectionCard>
    );
  }

  const activeTitle = statementLabel(copy, activeTab);
  const activeRows =
    activeTab === "balance_sheet"
      ? balanceTab?.rows ?? []
      : activeTab === "income_statement"
        ? incomeTab?.rows ?? []
        : cashflowTab?.rows ?? [];

  return (
    <div className="page-stack">
      <SectionCard
        title={stockIdentity.stock_name}
        eyebrow={copy.statements.title}
        action={
          <div className="statement-header-actions">
            <label className="field field-inline">
              <span>{copy.statements.reportDate}</span>
              <select
                value={selectedPeriod ?? statementData?.selected_period ?? ""}
                onChange={(event) => setSelectedPeriod(event.target.value)}
              >
                {(statementData?.available_periods ?? []).map((period) => (
                  <option key={period} value={period}>
                    {period}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="ghost-button" onClick={onBackToOverview}>
              {copy.statements.backToOverview}
            </button>
          </div>
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
              <span>{tab === "overview" ? copy.metrics.statementPreviewHint : copy.statements.availablePeriods}</span>
            </button>
          ))}
        </div>
      </SectionCard>

      {activeTab === "overview" ? (
        <div className="statement-panel-grid">
          <SectionCard title={copy.statements.balanceSheet} eyebrow={copy.statements.overview}>
            {statementsQuery.isLoading && !statementData ? (
              <LoadingSkeleton lines={5} />
            ) : (
              <FinancialStatementTable
                statementKey="balance_sheet"
                rows={(balanceTab?.rows ?? []).slice(0, 8)}
                lang={lang}
                locale={locale}
                emptyLabel={copy.statements.tableEmpty}
              />
            )}
          </SectionCard>

          <SectionCard title={copy.statements.incomeStatement} eyebrow={copy.statements.overview}>
            {statementsQuery.isLoading && !statementData ? (
              <LoadingSkeleton lines={5} />
            ) : (
              <FinancialStatementTable
                statementKey="income_statement"
                rows={(incomeTab?.rows ?? []).slice(0, 8)}
                lang={lang}
                locale={locale}
                emptyLabel={copy.statements.tableEmpty}
              />
            )}
          </SectionCard>

          <SectionCard title={copy.statements.cashflowStatement} eyebrow={copy.statements.overview}>
            {statementsQuery.isLoading && !statementData ? (
              <LoadingSkeleton lines={5} />
            ) : (
              <FinancialStatementTable
                statementKey="cashflow_statement"
                rows={(cashflowTab?.rows ?? []).slice(0, 8)}
                lang={lang}
                locale={locale}
                emptyLabel={copy.statements.tableEmpty}
              />
            )}
          </SectionCard>
        </div>
      ) : (
        <div className="statement-detail-layout">
          <SectionCard title={activeTitle} eyebrow={copy.statements.description} className="statement-main-panel">
            {statementsQuery.isLoading && !statementData ? (
              <LoadingSkeleton lines={10} />
            ) : (
              <FinancialStatementTable
                statementKey={activeTab as Exclude<StatementKey, "overview">}
                rows={activeRows}
                lang={lang}
                locale={locale}
                emptyLabel={copy.statements.tableEmpty}
              />
            )}
          </SectionCard>

          <SectionCard
            title={copy.metrics.metricDigestTitle}
            eyebrow={copy.shell.routeContext}
            className="statement-side-panel"
          >
            {statementData ? (
              <div className="copy-block">
                <p>{statementReadingHint(lang)}</p>
                <DataTable
                  rows={[
                    [copy.statements.reportDate, statementData.selected_period ?? "-"],
                    [copy.statements.availablePeriods, (statementData.available_periods ?? []).length],
                    [copy.statements.source, statementData.source ?? "-"],
                  ]}
                  emptyLabel={copy.statements.tableEmpty}
                  locale={locale}
                />
              </div>
            ) : (
              <StateBlock title={copy.shared.loading} description={copy.statements.tableEmpty} />
            )}
          </SectionCard>
        </div>
      )}
    </div>
  );
}
