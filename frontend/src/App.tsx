import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createCrawlerJob,
  getCrawlerJobStatus,
  listStocks,
  type StockInfo,
} from "./api/sdk";
import {
  getWorkspaceAiInsightsContext,
  getWorkspaceMetricCatalog,
  getWorkspaceMetricValues,
  getWorkspaceModelResults,
  getWorkspaceSnapshot,
} from "./api/workspace";
import { SectionCard, StateBlock } from "./components/DataBlocks";
import { WorkspaceChrome } from "./components/WorkspaceChrome";
import { WorkspaceSummary } from "./components/WorkspaceSummary";
import { InsightsPage } from "./pages/InsightsPage";
import { MetricsPage } from "./pages/MetricsPage";
import { ModelsPage } from "./pages/ModelsPage";
import { formatDate, formatDateTime } from "./lib/finance";
import {
  WORKSPACE_ROUTE_META,
  WORKSPACE_TABS,
  type WorkspaceRoute,
  useWorkspaceRoute,
} from "./lib/routing";

type JobState = "idle" | "queued" | "started" | "finished" | "failed";

function getJobStatus(data: unknown): string {
  if (data && typeof data === "object" && "status" in data) {
    return String((data as { status?: unknown }).status ?? "");
  }

  return "";
}

function routeTone(route: WorkspaceRoute): "neutral" | "positive" | "warning" {
  if (route === "insights") {
    return "positive";
  }

  if (route === "models") {
    return "warning";
  }

  return "neutral";
}

function jobTone(jobState: JobState): "neutral" | "positive" | "warning" | "danger" {
  if (jobState === "finished") return "positive";
  if (jobState === "queued" || jobState === "started") return "warning";
  if (jobState === "failed") return "danger";
  return "neutral";
}

export default function App() {
  const queryClient = useQueryClient();
  const { route, navigate } = useWorkspaceRoute();
  const [search, setSearch] = useState("");
  const [market, setMarket] = useState("ALL");
  const [selectedCode, setSelectedCode] = useState("");
  const [manualCode, setManualCode] = useState("");
  const [jobId, setJobId] = useState("");

  const deferredSearch = useDeferredValue(search);

  const stocksQuery = useQuery({
    queryKey: ["stocks", market],
    queryFn: () =>
      listStocks({
        market: market === "ALL" ? undefined : market,
      }),
  });

  useEffect(() => {
    if (!selectedCode && stocksQuery.data && stocksQuery.data.length > 0) {
      setSelectedCode(stocksQuery.data[0].stock_code);
    }
  }, [selectedCode, stocksQuery.data]);

  const markets = useMemo(() => {
    const values = new Set<string>();
    (stocksQuery.data ?? []).forEach((item) => {
      if (item.market) {
        values.add(item.market);
      }
    });
    return ["ALL", ...Array.from(values)];
  }, [stocksQuery.data]);

  const visibleStocks = useMemo(() => {
    const source = stocksQuery.data ?? [];
    const keyword = deferredSearch.trim().toLowerCase();
    if (!keyword) {
      return source;
    }

    return source.filter((item) => {
      return (
        item.stock_code.toLowerCase().includes(keyword) ||
        item.stock_name.toLowerCase().includes(keyword) ||
        (item.industry ?? "").toLowerCase().includes(keyword)
      );
    });
  }, [deferredSearch, stocksQuery.data]);

  const selectedStock: StockInfo | undefined = useMemo(() => {
    return (stocksQuery.data ?? []).find((item) => item.stock_code === selectedCode);
  }, [selectedCode, stocksQuery.data]);

  const refreshStockMutation = useMutation({
    mutationFn: async () => {
      if (!selectedCode) {
        throw new Error("Select one stock before refreshing.");
      }
      return createCrawlerJob(selectedCode);
    },
    onSuccess: (result) => {
      if (result.status === "queued") {
        setJobId(result.job_id);
        return;
      }

      setJobId("");
      if (selectedCode) {
        queryClient.invalidateQueries({ queryKey: ["workspace-snapshot", selectedCode] });
        queryClient.invalidateQueries({ queryKey: ["workspace-metric-catalog", selectedCode] });
        queryClient.invalidateQueries({ queryKey: ["workspace-metric-values", selectedCode] });
        queryClient.invalidateQueries({ queryKey: ["workspace-models", selectedCode] });
        queryClient.invalidateQueries({ queryKey: ["workspace-insights-context", selectedCode] });
      }
    },
  });

  const refreshStocksMutation = useMutation({
    mutationFn: async () =>
      listStocks({
        market: market === "ALL" ? undefined : market,
        refresh: true,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["stocks", market], data);
      if (!selectedCode && data.length > 0) {
        setSelectedCode(data[0].stock_code);
      }
    },
  });

  const jobQuery = useQuery({
    queryKey: ["job", jobId],
    enabled: Boolean(jobId),
    queryFn: () => getCrawlerJobStatus(jobId),
    refetchInterval: (query) => {
      const state = getJobStatus(query.state.data);
      if (state === "finished" || state === "failed") {
        return false;
      }
      return 2_000;
    },
  });

  useEffect(() => {
    const status = getJobStatus(jobQuery.data);
    if (status === "finished" && selectedCode) {
      queryClient.invalidateQueries({ queryKey: ["workspace-snapshot", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["workspace-metric-catalog", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["workspace-metric-values", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["workspace-models", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["workspace-insights-context", selectedCode] });
    }
  }, [jobQuery.data, queryClient, selectedCode]);

  useEffect(() => {
    if (!selectedCode) {
      return;
    }

    void Promise.all([
      queryClient.prefetchQuery({
        queryKey: ["workspace-snapshot", selectedCode],
        queryFn: () => getWorkspaceSnapshot(selectedCode),
      }),
      queryClient.prefetchQuery({
        queryKey: ["workspace-metric-catalog", selectedCode],
        queryFn: () => getWorkspaceMetricCatalog(selectedCode),
      }),
      queryClient.prefetchQuery({
        queryKey: ["workspace-metric-values", selectedCode],
        queryFn: () => getWorkspaceMetricValues(selectedCode),
      }),
      queryClient.prefetchQuery({
        queryKey: ["workspace-models", selectedCode],
        queryFn: () => getWorkspaceModelResults(selectedCode),
      }),
      queryClient.prefetchQuery({
        queryKey: ["workspace-insights-context", selectedCode],
        queryFn: () => getWorkspaceAiInsightsContext(selectedCode),
      }),
    ]);
  }, [queryClient, selectedCode]);

  const jobState = (getJobStatus(jobQuery.data) || (jobId ? "queued" : "idle")) as JobState;
  const activeRouteMeta = WORKSPACE_ROUTE_META[route];

  const leftRail = (
    <div className="rail-stack">
      <SectionCard title="Stock explorer" eyebrow="Registry">
        <div className="control-stack">
          <label className="field">
            <span>Market</span>
            <select
              value={market}
              onChange={(event) => {
                setMarket(event.target.value);
                setSelectedCode("");
              }}
            >
              {markets.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Search</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Code, company, or industry"
            />
          </label>

          <label className="field">
            <span>Manual code</span>
            <div className="inline-action">
              <input
                value={manualCode}
                onChange={(event) => setManualCode(event.target.value.trim())}
                placeholder="e.g. 600519"
              />
              <button
                type="button"
                className="ghost-button"
                onClick={() => {
                  if (!manualCode) {
                    return;
                  }
                  setSelectedCode(manualCode);
                  setSearch("");
                }}
              >
                Load
              </button>
            </div>
          </label>

          <div className="inline-action">
            <button
              type="button"
              className="ghost-button"
              onClick={() => refreshStocksMutation.mutate()}
              disabled={refreshStocksMutation.isPending}
            >
              {refreshStocksMutation.isPending ? "Refreshing list..." : "Refresh registry"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => refreshStockMutation.mutate()}
              disabled={refreshStockMutation.isPending || !selectedCode}
            >
              {refreshStockMutation.isPending ? "Refreshing feed..." : "Refresh selected"}
            </button>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="Workspace pages"
        eyebrow="Navigation"
        action={<span className="section-meta">{activeRouteMeta.title}</span>}
      >
        <div className="route-rail">
          {WORKSPACE_TABS.map((tab) => (
            <button
              key={tab.route}
              type="button"
              className={`rail-tab ${route === tab.route ? "rail-tab-active" : ""}`}
              onClick={() => navigate(tab.route)}
            >
              <strong>{tab.label}</strong>
              <span>{tab.note}</span>
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Selected stocks" eyebrow="Live feed">
        {stocksQuery.isLoading ? (
          <StateBlock title="Loading registry" description="Fetching the latest stock list." />
        ) : stocksQuery.isError ? (
          <StateBlock
            tone="danger"
            title="Registry unavailable"
            description={(stocksQuery.error as Error).message}
          />
        ) : (
          <div className="stock-list">
            {visibleStocks.length === 0 ? (
              <StateBlock
                title="No matches"
                description="Try a different search term or clear the filters."
              />
            ) : (
              visibleStocks.map((stock) => (
                <button
                  key={stock.stock_code}
                  type="button"
                  className={`stock-item ${selectedCode === stock.stock_code ? "stock-item-active" : ""}`}
                  onClick={() => setSelectedCode(stock.stock_code)}
                >
                  <strong>{stock.stock_name}</strong>
                  <span>{stock.stock_code}</span>
                  <em>{stock.market ?? "Unknown market"}</em>
                </button>
              ))
            )}
          </div>
        )}
      </SectionCard>
    </div>
  );

  const rightRail = (
    <div className="rail-stack">
      <SectionCard title="Selected company" eyebrow="Context">
        <div className="summary-stack">
          <WorkspaceSummary
            label="Company"
            value={(selectedStock?.stock_name ?? selectedCode) || "Nothing selected"}
            note={selectedStock?.stock_code ?? "Choose a company from the list"}
          />
          <WorkspaceSummary label="Market" value={selectedStock?.market ?? "Unknown"} note={selectedStock?.industry ?? "Industry unavailable"} />
          <WorkspaceSummary label="Listed" value={formatDate(selectedStock?.list_date)} note="Registry listing date" />
        </div>
      </SectionCard>

      <SectionCard title="Route context" eyebrow="Current page">
        <WorkspaceSummary label="Page" value={activeRouteMeta.title} note={activeRouteMeta.description} />
        <WorkspaceSummary
          label="Tone"
          value={routeTone(route).toUpperCase()}
          note="The shell adjusts density by page"
        />
      </SectionCard>

      <SectionCard title="Crawler job" eyebrow="Async state">
        <div className="summary-stack">
          <WorkspaceSummary
            label="Status"
            value={jobState.toUpperCase()}
            note={jobId || "No active job"}
          />
          <WorkspaceSummary
            label="Timestamp"
            value={formatDateTime(jobQuery.data && typeof jobQuery.data === "object" && "updated_at" in jobQuery.data ? String((jobQuery.data as Record<string, unknown>).updated_at ?? "") : undefined)}
            note="Latest poll time from the crawler API"
          />
        </div>
      </SectionCard>

      <SectionCard title="Workspace notes" eyebrow="Operational">
        <StateBlock
          tone={jobTone(jobState) === "danger" ? "danger" : jobTone(jobState) === "warning" ? "warning" : "neutral"}
          title="Feed refresh"
          description="Use the refresh buttons to update the stock registry or request a fresh crawler run for the selected company."
        />
      </SectionCard>
    </div>
  );

  return (
    <WorkspaceChrome
      title="Financial Report Analyzer"
      subtitle="A calm editorial workspace for metrics, models, and AI-written insight."
      tabs={WORKSPACE_TABS}
      activeRoute={route}
      onNavigate={navigate}
      leftRail={leftRail}
      rightRail={rightRail}
    >
      <div className="workspace-header">
        <div>
          <span className="eyebrow">Selected stock</span>
          <h2>{selectedStock?.stock_name ?? selectedCode ?? "Choose a company"}</h2>
          <p>
            {selectedStock?.stock_code ?? "—"} {selectedStock?.market ? ` / ${selectedStock.market}` : ""}
            {selectedStock?.industry ? ` / ${selectedStock.industry}` : ""}
          </p>
        </div>
        <div className="header-status">
          <span>Active page</span>
          <strong>{activeRouteMeta.title}</strong>
        </div>
      </div>

      {route === "metrics" ? (
        <MetricsPage selectedCode={selectedCode} selectedStock={selectedStock} />
      ) : route === "models" ? (
        <ModelsPage selectedCode={selectedCode} selectedStock={selectedStock} />
      ) : (
        <InsightsPage selectedCode={selectedCode} selectedStock={selectedStock} />
      )}
    </WorkspaceChrome>
  );
}
