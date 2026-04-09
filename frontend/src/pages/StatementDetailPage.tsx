import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import {
  buildWorkspaceStatementExportUrl,
  buildWorkspaceStatementHistoryExportUrl,
  getWorkspaceStatements,
} from "../api/workspace";
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
    return "这个页面更适合按报表和报告期连续阅读，建议结合总览页的关键指标与模型页的判断一起交叉验证。";
  }
  return "This view is optimized for report reading. Cross-check it with the overview metrics and the model page for interpretation.";
}

function statementActionLabel(lang: Lang, kind: "open" | "downloadCurrent" | "downloadHistory"): string {
  if (lang === "zh") {
    if (kind === "open") return "新标签打开";
    if (kind === "downloadCurrent") return "下载当前表";
    return "下载历年报表";
  }

  if (kind === "open") return "Open in new tab";
  if (kind === "downloadCurrent") return "Download current";
  return "Download history";
}

function isStatementKey(value: string | null): value is StatementKey {
  return value === "overview" || value === "balance_sheet" || value === "income_statement" || value === "cashflow_statement";
}

function readStoredStatementTab(stockCode: string): StatementKey {
  if (typeof window === "undefined" || !stockCode) {
    return "overview";
  }

  const stored = window.localStorage.getItem(`workspace-statement-tab:${stockCode}`);
  return isStatementKey(stored) ? stored : "overview";
}

function readStoredStatementPeriod(stockCode: string): string | undefined {
  if (typeof window === "undefined" || !stockCode) {
    return undefined;
  }

  return window.localStorage.getItem(`workspace-statement-period:${stockCode}`) ?? undefined;
}

export function StatementDetailPage({
  selectedCode,
  selectedStock,
  lang,
  onBackToOverview,
}: StatementDetailPageProps) {
  const copy = getWorkspaceCopy(lang);
  const locale = getBrowserLocale(lang);
  const [activeTab, setActiveTab] = useState<StatementKey>(() => readStoredStatementTab(selectedCode));
  const [selectedPeriod, setSelectedPeriod] = useState<string | undefined>(() => readStoredStatementPeriod(selectedCode));

  const statementsQuery = useQuery({
    queryKey: ["workspace-statements-view", selectedCode, lang, selectedPeriod],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceStatements(selectedCode, lang, selectedPeriod),
    staleTime: 60_000,
  });

  const statementData = statementsQuery.data;

  useEffect(() => {
    if (!statementData?.available_periods?.length) {
      return;
    }

    if (!selectedPeriod || !statementData.available_periods.includes(selectedPeriod)) {
      setSelectedPeriod(statementData.available_periods[0]);
    }
  }, [selectedPeriod, statementData?.available_periods]);

  useEffect(() => {
    setActiveTab(readStoredStatementTab(selectedCode));
    setSelectedPeriod(readStoredStatementPeriod(selectedCode));
  }, [selectedCode]);

  useEffect(() => {
    if (typeof window === "undefined" || !selectedCode) {
      return;
    }

    window.localStorage.setItem(`workspace-statement-tab:${selectedCode}`, activeTab);
  }, [activeTab, selectedCode]);

  useEffect(() => {
    if (typeof window === "undefined" || !selectedCode || !selectedPeriod) {
      return;
    }

    window.localStorage.setItem(`workspace-statement-period:${selectedCode}`, selectedPeriod);
  }, [selectedCode, selectedPeriod]);

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

  const activeTitle = statementLabel(copy, activeTab);
  const activeRows =
    activeTab === "balance_sheet"
      ? balanceTab?.rows ?? []
      : activeTab === "income_statement"
        ? incomeTab?.rows ?? []
        : cashflowTab?.rows ?? [];

  const currentExportUrl = useMemo(() => {
    if (!selectedCode || !selectedPeriod || activeTab === "overview") {
      return undefined;
    }

    return buildWorkspaceStatementExportUrl(selectedCode, activeTab, selectedPeriod, "csv", lang);
  }, [activeTab, lang, selectedCode, selectedPeriod]);

  const historyExportUrl = useMemo(() => {
    if (!selectedCode) {
      return undefined;
    }

    return buildWorkspaceStatementHistoryExportUrl(selectedCode, "xlsx", lang);
  }, [lang, selectedCode]);

  const handleOpenInNewTab = () => {
    if (typeof window === "undefined") {
      return;
    }

    window.open("/metrics/statements", "_blank", "noopener,noreferrer");
  };

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
            <div className="statement-action-group">
              <button type="button" className="ghost-button" onClick={handleOpenInNewTab}>
                {statementActionLabel(lang, "open")}
              </button>
              {currentExportUrl ? (
                <a className="ghost-button" href={currentExportUrl}>
                  {statementActionLabel(lang, "downloadCurrent")}
                </a>
              ) : null}
              {historyExportUrl ? (
                <a className="ghost-button" href={historyExportUrl}>
                  {statementActionLabel(lang, "downloadHistory")}
                </a>
              ) : null}
              <button type="button" className="ghost-button" onClick={onBackToOverview}>
                {copy.statements.backToOverview}
              </button>
            </div>
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
