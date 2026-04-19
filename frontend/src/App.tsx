import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createCrawlerJob, getCrawlerJobStatus, listStocks, type StockInfo } from "./api/sdk";
import { listWorkspaces, type WorkspaceSummary } from "./api/workspace";
import { SectionCard, StateBlock, WorkspaceSummaryList } from "./components/DataBlocks";
import { WorkspaceChrome } from "./components/WorkspaceChrome";
import { InsightsPage } from "./pages/InsightsPage";
import { MetricsPage } from "./pages/MetricsPage";
import { ModelsPage } from "./pages/ModelsPage";
import { StatementDetailPage } from "./pages/StatementDetailPage";
import { getWorkspaceCopy, SUPPORTED_LANGS, type Lang } from "./lib/i18n";
import { routeToPath, useWorkspaceRoute } from "./lib/routing";

type CrawlJobState = {
  job_id?: string;
  status?: string;
  error?: string | null;
  created_at?: string;
  result?: unknown;
};

const WORKSPACE_ARCHIVE_LIMIT = 5000;

function getArchiveStatusLabel(lang: Lang, archived: boolean): string {
  if (archived) {
    return lang === "zh" ? "已归档" : "Archived";
  }
  return lang === "zh" ? "待归档" : "Pending archive";
}

function getStoredLang(): Lang {
  if (typeof window === "undefined") {
    return "zh";
  }

  const stored = window.localStorage.getItem("workspace-lang");
  return stored === "en" ? "en" : "zh";
}

function getStoredCode(): string {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem("workspace-selected-code") ?? "";
}

function getArchiveStatusLabelSafe(lang: Lang, archived: boolean): string {
  return archived
    ? lang === "zh"
      ? "已归档"
      : "Archived"
    : lang === "zh"
      ? "待归档"
      : "Pending archive";
}

function summarizeJobState(copy: ReturnType<typeof getWorkspaceCopy>, state: CrawlJobState | undefined): string {
  if (!state?.status) {
    return copy.shared.unavailable;
  }

  const normalized = state.status.toLowerCase();
  if (normalized === "queued") return copy.shell.crawlerJob;
  if (normalized === "started" || normalized === "running") return copy.shared.loading;
  if (normalized === "finished") return copy.shared.archiveSummary;
  if (normalized === "failed") return copy.shell.archiveUnavailable;
  return state.status;
}

function workspaceToStockInfo(workspace: WorkspaceSummary): StockInfo {
  return {
    stock_code: workspace.stock_code,
    stock_name: workspace.stock_name,
    market: workspace.market,
    industry: undefined,
    list_date: undefined,
  };
}

function mergeStockOptions(primary: StockInfo[], fallback: StockInfo[]): StockInfo[] {
  if (primary.length === 0) {
    return fallback;
  }

  const merged = new Map(primary.map((item) => [item.stock_code, item]));
  for (const item of fallback) {
    if (!merged.has(item.stock_code)) {
      merged.set(item.stock_code, item);
    }
  }
  return Array.from(merged.values());
}

export default function App() {
  const queryClient = useQueryClient();
  const [lang, setLang] = useState<Lang>(getStoredLang);
  const [selectedCode, setSelectedCode] = useState<string>(getStoredCode);
  const [search, setSearch] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [crawlTarget, setCrawlTarget] = useState<string | null>(null);
  const [crawlJobId, setCrawlJobId] = useState<string | null>(null);
  const [stockRefreshVersion, setStockRefreshVersion] = useState(0);
  const { route, metricsView, navigate, navigateMetricsView } = useWorkspaceRoute();
  const copy = getWorkspaceCopy(lang);

  const stocksQuery = useQuery({
    queryKey: ["stocks", stockRefreshVersion],
    queryFn: () => listStocks({ refresh: stockRefreshVersion > 0 }),
    staleTime: 10 * 60_000,
  });

  const workspacesQuery = useQuery({
    queryKey: ["workspaces"],
    queryFn: () => listWorkspaces(WORKSPACE_ARCHIVE_LIMIT, lang),
    staleTime: 60_000,
  });

  const workspaces = workspacesQuery.data ?? [];
  const workspaceStockOptions = useMemo(() => workspaces.map(workspaceToStockInfo), [workspaces]);
  const stockOptions = useMemo(
    () => mergeStockOptions(stocksQuery.data ?? [], workspaceStockOptions),
    [stocksQuery.data, workspaceStockOptions],
  );
  const workspaceCodes = useMemo(() => new Set(workspaces.map((item) => item.stock_code)), [workspaces]);

  const createCrawlerMutation = useMutation({
    mutationFn: async (stockCode: string) => createCrawlerJob(stockCode),
    onSuccess: (job, stockCode) => {
      setCrawlTarget(stockCode);
      setCrawlJobId(job.job_id);
    },
  });

  const crawlStatusQuery = useQuery({
    queryKey: ["crawler-job", crawlJobId],
    enabled: Boolean(crawlJobId),
    queryFn: () => getCrawlerJobStatus(crawlJobId!),
    refetchInterval: (query) => {
      const status = String((query.state.data as CrawlJobState | undefined)?.status ?? "").toLowerCase();
      if (!status || status === "queued" || status === "started" || status === "running") {
        return 4000;
      }
      return false;
    },
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    window.localStorage.setItem("workspace-lang", lang);
  }, [lang]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (selectedCode) {
      window.localStorage.setItem("workspace-selected-code", selectedCode);
    }
  }, [selectedCode]);

  useEffect(() => {
    if (!selectedCode) {
      const initialCode = workspaces[0]?.stock_code ?? stockOptions[0]?.stock_code;
      if (initialCode) {
        setSelectedCode(initialCode);
      }
    }
  }, [selectedCode, stockOptions, workspaces]);

  useEffect(() => {
    if (!selectedCode || workspacesQuery.isLoading || createCrawlerMutation.isPending) {
      return;
    }

    if (workspaceCodes.has(selectedCode)) {
      if (crawlTarget === selectedCode) {
        setCrawlTarget(null);
        setCrawlJobId(null);
      }
      return;
    }

    if (crawlTarget !== selectedCode && !crawlJobId) {
      createCrawlerMutation.mutate(selectedCode);
    }
  }, [
    crawlJobId,
    crawlTarget,
    createCrawlerMutation,
    selectedCode,
    workspaceCodes,
    workspacesQuery.isLoading,
  ]);

  useEffect(() => {
    const status = String((crawlStatusQuery.data as CrawlJobState | undefined)?.status ?? "").toLowerCase();
    if (!status || !crawlTarget) {
      return;
    }

    if (status === "finished") {
      void queryClient.invalidateQueries({ queryKey: ["stocks"] });
      void queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-snapshot", crawlTarget] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-statements", crawlTarget] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-statements-view", crawlTarget] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-metric-catalog", crawlTarget] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-metric-values", crawlTarget] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-models", crawlTarget] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-insights-context", crawlTarget] });
      setCrawlJobId(null);
    }
  }, [crawlStatusQuery.data, crawlTarget, queryClient]);

  const selectedStock = useMemo(() => {
    return stockOptions.find((item) => item.stock_code === selectedCode);
  }, [selectedCode, stockOptions]);

  const filteredStocks = useMemo(() => {
    const source = stockOptions;
    const keyword = search.trim().toLowerCase();
    const filtered = keyword
      ? source.filter((item) => {
          const name = item.stock_name?.toLowerCase() ?? "";
          const code = item.stock_code?.toLowerCase() ?? "";
          return name.includes(keyword) || code.includes(keyword);
        })
      : source;

    return [...filtered]
      .sort((left, right) => Number(workspaceCodes.has(right.stock_code)) - Number(workspaceCodes.has(left.stock_code)))
      .slice(0, 200);
  }, [search, stockOptions, workspaceCodes]);

  const selectedHasWorkspace = selectedCode ? workspaceCodes.has(selectedCode) : false;
  const currentJobState = crawlStatusQuery.data as CrawlJobState | undefined;
  const activeRoutePath = routeToPath(route, metricsView);

  const handleSelectStock = (stock: StockInfo) => {
    setSelectedCode(stock.stock_code);
  };

  const handleManualLoad = () => {
    const nextCode = manualCode.trim();
    if (!nextCode) {
      return;
    }
    setSelectedCode(nextCode);
    setSearch("");
  };

  const handleRefreshSelected = () => {
    if (!selectedCode) {
      return;
    }
    setCrawlTarget(selectedCode);
    setCrawlJobId(null);
    createCrawlerMutation.mutate(selectedCode);
  };

  const leftRail = (
    <>
      <SectionCard title={copy.shell.selectedStocks} eyebrow={copy.shell.archiveWorkspaces}>
        <div className="control-stack">
          <label className="field">
            <span>{copy.shell.search}</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={copy.shell.search}
            />
          </label>

          <div className="stock-list">
            {stocksQuery.isLoading && workspaceStockOptions.length === 0 ? (
              <StateBlock title={copy.shared.loading} description={copy.shell.loadingArchive} />
            ) : filteredStocks.length > 0 ? (
              filteredStocks.map((stock) => (
                <button
                  key={stock.stock_code}
                  type="button"
                  className={`stock-item ${stock.stock_code === selectedCode ? "stock-item-active" : ""}`}
                  onClick={() => handleSelectStock(stock)}
                >
                  <strong>{stock.stock_name}</strong>
                  <span>{stock.stock_code}</span>
                  <em>
                    {stock.market ?? copy.shared.unavailable} ·{" "}
                    {getArchiveStatusLabelSafe(lang, workspaceCodes.has(stock.stock_code))}
                  </em>
                </button>
              ))
            ) : (
              <StateBlock title={copy.shell.noMatches} description={copy.shell.selectedCompanyHint} />
            )}
          </div>
        </div>
      </SectionCard>
    </>
  );

  const rightRail = (
    <div className="rail-stack">
      <SectionCard title={copy.shell.selectedCompany} eyebrow={copy.shell.routeContext}>
        <WorkspaceSummaryList
          items={[
            {
              label: copy.shell.selectedCompany,
              value: selectedStock?.stock_name || selectedCode || copy.shell.noSelection,
              note: selectedStock?.stock_code ?? copy.shared.unavailable,
            },
            {
              label: copy.shell.market,
              value: selectedStock?.market ?? copy.shared.unavailable,
              note: selectedHasWorkspace ? copy.shared.latestArchiveReport : copy.shell.archiveUnavailable,
            },
            {
              label: copy.shell.activePage,
              value: copy.routeTabs[route].label,
              note: activeRoutePath,
            },
          ]}
        />
      </SectionCard>

      <SectionCard title={copy.shell.crawlerJob} eyebrow={copy.shell.workspaceNotes}>
        {!selectedCode ? (
          <StateBlock title={copy.shell.noSelection} description={copy.shell.selectedCompanyHint} />
        ) : selectedHasWorkspace ? (
          <StateBlock
            title={copy.shared.archiveSummary}
            description={copy.shell.openStatements}
            action={
              <button type="button" className="ghost-button" onClick={handleRefreshSelected}>
                {copy.shell.refreshSelected}
              </button>
            }
          />
        ) : (
          <StateBlock
            title={createCrawlerMutation.isPending ? copy.shell.loadingArchive : summarizeJobState(copy, currentJobState)}
            description={
              (currentJobState?.error as string | undefined) ??
              (createCrawlerMutation.isPending ? copy.shell.autoCrawlStarted : copy.shell.missingArchive)
            }
            action={
              <button type="button" className="ghost-button" onClick={handleRefreshSelected}>
                {copy.shell.refreshSelected}
              </button>
            }
          />
        )}
      </SectionCard>
    </div>
  );

  const controls = (
    <div className="workspace-toolbar">
      <div className="toolbar-cluster">
        <label className="field field-inline">
          <span>{copy.shell.manualCode}</span>
          <div className="inline-action">
            <input
              value={manualCode}
              onChange={(event) => setManualCode(event.target.value)}
              placeholder="600519"
            />
            <button type="button" className="ghost-button" onClick={handleManualLoad}>
              {copy.shell.load}
            </button>
          </div>
        </label>
      </div>

      <div className="toolbar-cluster toolbar-cluster-right">
        <label className="field field-inline">
          <span>{copy.language.label}</span>
          <select value={lang} onChange={(event) => setLang(event.target.value as Lang)}>
            {SUPPORTED_LANGS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="ghost-button"
          onClick={() => setStockRefreshVersion((current) => current + 1)}
        >
          {copy.shell.refreshRegistry}
        </button>
      </div>
    </div>
  );

  const tabs = [
    { route: "metrics" as const, label: copy.routeTabs.metrics.label, note: copy.routeTabs.metrics.note },
    { route: "models" as const, label: copy.routeTabs.models.label, note: copy.routeTabs.models.note },
    { route: "insights" as const, label: copy.routeTabs.insights.label, note: copy.routeTabs.insights.note },
  ];

  const archivePendingTitle =
    createCrawlerMutation.isPending || ["queued", "started", "running"].includes(String(currentJobState?.status ?? "").toLowerCase())
      ? copy.shell.crawlerJob
      : getArchiveStatusLabelSafe(lang, false);
  const archivePendingDescription =
    (currentJobState?.error as string | undefined) ??
    (createCrawlerMutation.isPending ? copy.shell.autoCrawlStarted : copy.shell.missingArchive);

  return (
    <WorkspaceChrome
      title={copy.app.title}
      subtitle={copy.app.subtitle}
      eyebrow={copy.metrics.eyebrow}
      tabs={tabs}
      activeRoute={route}
      onNavigate={navigate}
      tabsLabel={copy.shell.workspacePages}
      controls={controls}
      leftRail={leftRail}
      rightRail={rightRail}
    >
      {selectedCode && !selectedHasWorkspace ? (
        <SectionCard title={copy.shell.crawlerJob} eyebrow={copy.shell.workspaceNotes}>
          <StateBlock
            title={archivePendingTitle}
            description={archivePendingDescription}
            action={
              <button type="button" className="ghost-button" onClick={handleRefreshSelected}>
                {copy.shell.refreshSelected}
              </button>
            }
          />
        </SectionCard>
      ) : null}

      {selectedCode && !selectedHasWorkspace ? null : route === "metrics" && metricsView === "overview" ? (
        <MetricsPage
          selectedCode={selectedCode}
          selectedStock={selectedStock}
          lang={lang}
          onOpenStatementDetail={() => navigateMetricsView("statements")}
        />
      ) : null}

      {selectedCode && !selectedHasWorkspace ? null : route === "metrics" && metricsView === "statements" ? (
        <StatementDetailPage
          selectedCode={selectedCode}
          selectedStock={selectedStock}
          lang={lang}
          onBackToOverview={() => navigateMetricsView("overview")}
        />
      ) : null}

      {selectedCode && !selectedHasWorkspace
        ? null
        : route === "models"
          ? <ModelsPage selectedCode={selectedCode} selectedStock={selectedStock} lang={lang} />
          : null}
      {selectedCode && !selectedHasWorkspace
        ? null
        : route === "insights"
          ? <InsightsPage selectedCode={selectedCode} selectedStock={selectedStock} lang={lang} />
          : null}
    </WorkspaceChrome>
  );
}
