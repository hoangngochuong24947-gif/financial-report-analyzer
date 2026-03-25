import { useEffect, useMemo, useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  createCrawlerJob,
  getCashflowAnalysis,
  getCrawlerJobStatus,
  getDuPont,
  getFinancialRatios,
  getSnapshot,
  getTrendAnalysis,
  listStocks,
  type FinancialRatios,
  type SnapshotPayload,
  type StockInfo,
} from "./api/sdk";

type JobState = "idle" | "queued" | "started" | "finished" | "failed";

function toTitle(rawKey: string): string {
  return rawKey
    .replaceAll("_", " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value.toLocaleString("en-US") : "-";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
}

function getStatementRows(
  snapshot: SnapshotPayload | undefined,
  key: "balance_sheet" | "income_statement" | "cashflow_statement",
): Array<[string, unknown]> {
  const source = snapshot?.statements?.[key]?.[0];
  if (!source || typeof source !== "object") {
    return [];
  }

  return Object.entries(source).filter(([field]) => {
    return !["stock_code", "stock_name"].includes(field);
  });
}

function getJobStatus(data: unknown): string {
  if (data && typeof data === "object" && "status" in data) {
    return String((data as { status?: unknown }).status ?? "");
  }
  return "";
}

function FieldGrid(props: { title: string; data: Record<string, unknown> | undefined }) {
  const items = Object.entries(props.data ?? {});
  if (items.length === 0) {
    return (
      <section className="panel">
        <header className="panel-title">{props.title}</header>
        <p className="placeholder">No data available.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <header className="panel-title">{props.title}</header>
      <div className="metrics-grid">
        {items.map(([key, value]) => (
          <article key={key} className="metric-card">
            <h4>{toTitle(key)}</h4>
            <p>{formatValue(value)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function StatementTable(props: {
  title: string;
  rows: Array<[string, unknown]>;
}) {
  return (
    <section className="panel">
      <header className="panel-title">{props.title}</header>
      {props.rows.length === 0 ? (
        <p className="placeholder">No statement rows available.</p>
      ) : (
        <div className="statement-table-wrap">
          <table className="statement-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {props.rows.map(([key, value]) => (
                <tr key={key}>
                  <td>{toTitle(key)}</td>
                  <td>{formatValue(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function App() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [market, setMarket] = useState("ALL");
  const [selectedCode, setSelectedCode] = useState<string>("");
  const [manualCode, setManualCode] = useState("");
  const [jobId, setJobId] = useState<string>("");

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
    if (!search.trim()) {
      return source;
    }
    const keyword = search.toLowerCase();
    return source.filter((item) => {
      return (
        item.stock_code.toLowerCase().includes(keyword) ||
        item.stock_name.toLowerCase().includes(keyword)
      );
    });
  }, [search, stocksQuery.data]);

  const selectedStock: StockInfo | undefined = useMemo(() => {
    return (stocksQuery.data ?? []).find((item) => item.stock_code === selectedCode);
  }, [selectedCode, stocksQuery.data]);

  const snapshotQuery = useQuery({
    queryKey: ["snapshot", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getSnapshot({ code: selectedCode, latestOnly: true }),
  });

  const ratiosQuery = useQuery({
    queryKey: ["ratios", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getFinancialRatios(selectedCode),
  });

  const dupontQuery = useQuery({
    queryKey: ["dupont", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getDuPont(selectedCode),
  });

  const cashflowQuery = useQuery({
    queryKey: ["cashflow", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getCashflowAnalysis(selectedCode),
  });

  const trendQuery = useQuery({
    queryKey: ["trend", selectedCode, "net_income"],
    enabled: Boolean(selectedCode),
    queryFn: () => getTrendAnalysis(selectedCode, "net_income"),
  });

  const refreshMutation = useMutation({
    mutationFn: async () => {
      if (!selectedCode) {
        throw new Error("Select one stock before refreshing.");
      }
      return createCrawlerJob(selectedCode);
    },
    onSuccess: (result) => {
      if (result.status === "queued") {
        setJobId(result.job_id);
      } else {
        setJobId("");
        if (selectedCode) {
          queryClient.invalidateQueries({ queryKey: ["snapshot", selectedCode] });
          queryClient.invalidateQueries({ queryKey: ["ratios", selectedCode] });
          queryClient.invalidateQueries({ queryKey: ["dupont", selectedCode] });
          queryClient.invalidateQueries({ queryKey: ["cashflow", selectedCode] });
          queryClient.invalidateQueries({ queryKey: ["trend", selectedCode, "net_income"] });
        }
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
      queryClient.invalidateQueries({ queryKey: ["snapshot", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["ratios", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["dupont", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["cashflow", selectedCode] });
      queryClient.invalidateQueries({ queryKey: ["trend", selectedCode, "net_income"] });
    }
  }, [jobQuery.data, queryClient, selectedCode]);

  const jobState = (getJobStatus(jobQuery.data) || (jobId ? "queued" : "idle")) as JobState;

  const ratioData = ratiosQuery.data as FinancialRatios | undefined;

  return (
    <div className="app-shell">
      <div className="bg-ornament bg-ornament-a" />
      <div className="bg-ornament bg-ornament-b" />

      <header className="topbar">
        <div>
          <h1>Financial Report Analyzer</h1>
          <p>v2 Snapshot + Async Crawler + v1 Analysis Dashboard</p>
        </div>
        <div className="status-box">
          <span>Job</span>
          <strong data-status={jobState}>{jobState.toUpperCase()}</strong>
        </div>
      </header>

      <main className="layout">
        <aside className="sidebar panel">
          <div className="sidebar-header">
            <h2>Stocks</h2>
            <select
              value={market}
              onChange={(e) => {
                setMarket(e.target.value);
                setSelectedCode("");
              }}
            >
              {markets.map((item) => (
                <option value={item} key={item}>
                  {item}
                </option>
              ))}
            </select>
            <button
              className="refresh-list-btn"
              onClick={() => refreshStocksMutation.mutate()}
              disabled={refreshStocksMutation.isPending}
            >
              {refreshStocksMutation.isPending ? "Refreshing..." : "Refresh List"}
            </button>
          </div>

          <input
            className="search"
            placeholder="Search by code or name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <div className="manual-code-box">
            <input
              className="search"
              placeholder="Enter stock code (e.g. 601318)"
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value.trim())}
            />
            <button
              className="load-code-btn"
              onClick={() => {
                if (!manualCode) {
                  return;
                }
                setSelectedCode(manualCode);
                setSearch("");
              }}
            >
              Load Code
            </button>
          </div>

          <div className="stock-list">
            {stocksQuery.isLoading && <p className="placeholder">Loading stock list...</p>}
            {stocksQuery.isError && (
              <p className="error-text">Failed to load stocks: {(stocksQuery.error as Error).message}</p>
            )}
            {visibleStocks.map((stock) => (
              <button
                key={stock.stock_code}
                className={`stock-item ${
                  selectedCode === stock.stock_code ? "stock-item-active" : ""
                }`}
                onClick={() => setSelectedCode(stock.stock_code)}
              >
                <strong>{stock.stock_name}</strong>
                <span>{stock.stock_code}</span>
                <em>{stock.market ?? "N/A"}</em>
              </button>
            ))}
          </div>
        </aside>

        <section className="content">
          <section className="panel hero">
            <div>
              <h2>{selectedStock?.stock_name ?? "Select a stock"}</h2>
              <p>
                {selectedStock?.stock_code ?? "-"}
                {" · "}
                {selectedStock?.market ?? "Unknown Market"}
              </p>
            </div>
            <button
              className="refresh-btn"
              onClick={() => refreshMutation.mutate()}
              disabled={refreshMutation.isPending || !selectedCode}
            >
              {refreshMutation.isPending ? "Submitting..." : "Refresh Crawler Data"}
            </button>
          </section>

          {refreshMutation.isError && (
            <p className="error-text">
              Refresh failed: {(refreshMutation.error as Error).message}
            </p>
          )}

          <div className="grid-2">
            <StatementTable
              title="Balance Sheet (Latest)"
              rows={getStatementRows(snapshotQuery.data, "balance_sheet")}
            />
            <StatementTable
              title="Income Statement (Latest)"
              rows={getStatementRows(snapshotQuery.data, "income_statement")}
            />
          </div>

          <StatementTable
            title="Cashflow Statement (Latest)"
            rows={getStatementRows(snapshotQuery.data, "cashflow_statement")}
          />

          <div className="grid-2">
            <FieldGrid title="Profitability Ratios" data={ratioData?.profitability} />
            <FieldGrid title="Solvency Ratios" data={ratioData?.solvency} />
          </div>

          <div className="grid-2">
            <FieldGrid title="Efficiency Ratios" data={ratioData?.efficiency} />
            <FieldGrid title="DuPont Analysis" data={dupontQuery.data as Record<string, unknown>} />
          </div>

          <div className="grid-2">
            <FieldGrid
              title="Cashflow Analysis"
              data={cashflowQuery.data as Record<string, unknown>}
            />
            <FieldGrid
              title="Trend Analysis (Net Income)"
              data={trendQuery.data as Record<string, unknown>}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
