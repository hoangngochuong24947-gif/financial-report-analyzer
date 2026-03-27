import type { components } from "./generated/schema";
import { apiClient } from "./client";

type ApiError = { detail?: string } | unknown;

function toMessage(method: string, path: string, error: ApiError): string {
  if (error && typeof error === "object" && "detail" in error) {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.length > 0) {
      return `${method} ${path} failed: ${detail}`;
    }
  }
  return `${method} ${path} failed`;
}

export type StockInfo = components["schemas"]["StockInfo"];
export type CrawlJobResponse = components["schemas"]["CrawlJobResponse"];
export type DuPontResult = components["schemas"]["DuPontResult"];
export type CashFlowResult = components["schemas"]["CashFlowResult"];

export type SnapshotPayload = {
  stock_code: string;
  fetched_at?: string;
  statements?: {
    balance_sheet?: Array<Record<string, unknown>>;
    income_statement?: Array<Record<string, unknown>>;
    cashflow_statement?: Array<Record<string, unknown>>;
  };
};

export type FinancialRatios = {
  stock_code: string;
  report_date: string;
  profitability: Record<string, unknown>;
  solvency: Record<string, unknown>;
  efficiency: Record<string, unknown>;
};

export type TrendResult = {
  metric_name?: string;
  current?: number;
  previous?: number;
  change?: number;
  change_rate?: number;
  trend?: string;
  [key: string]: unknown;
};

export async function listStocks(params?: { market?: string; refresh?: boolean }): Promise<StockInfo[]> {
  const { data, error } = await apiClient.GET("/api/v2/stocks", {
    params: { query: { market: params?.market, refresh: params?.refresh } },
  });

  if (error) {
    throw new Error(toMessage("GET", "/api/v2/stocks", error));
  }
  return data ?? [];
}

export async function getSnapshot(params: {
  code: string;
  latestOnly?: boolean;
  refresh?: boolean;
}): Promise<SnapshotPayload> {
  const { data, error } = await apiClient.GET("/api/v2/stocks/{code}/snapshot", {
    params: {
      path: { code: params.code },
      query: {
        latest_only: params.latestOnly ?? true,
        refresh: params.refresh ?? false,
      },
    },
  });

  if (error) {
    throw new Error(toMessage("GET", "/api/v2/stocks/{code}/snapshot", error));
  }
  return (data ?? { stock_code: params.code }) as SnapshotPayload;
}

export async function createCrawlerJob(stockCode: string): Promise<CrawlJobResponse> {
  const { data, error } = await apiClient.POST("/api/v2/crawler/jobs", {
    body: { stock_code: stockCode },
  });

  if (error || !data) {
    throw new Error(toMessage("POST", "/api/v2/crawler/jobs", error));
  }
  return data;
}

export async function getCrawlerJobStatus(jobId: string): Promise<unknown> {
  const { data, error } = await apiClient.GET("/api/v2/crawler/jobs/{job_id}", {
    params: { path: { job_id: jobId } },
  });

  if (error) {
    throw new Error(toMessage("GET", "/api/v2/crawler/jobs/{job_id}", error));
  }
  return data as Record<string, unknown>;
}

export async function getFinancialRatios(code: string): Promise<FinancialRatios> {
  const { data, error } = await apiClient.GET("/api/stocks/{code}/ratios", {
    params: { path: { code } },
  });

  if (error || !data) {
    throw new Error(toMessage("GET", "/api/stocks/{code}/ratios", error));
  }
  return data as FinancialRatios;
}

export async function getDuPont(code: string): Promise<DuPontResult> {
  const { data, error } = await apiClient.GET("/api/stocks/{code}/dupont", {
    params: { path: { code } },
  });

  if (error || !data) {
    throw new Error(toMessage("GET", "/api/stocks/{code}/dupont", error));
  }
  return data;
}

export async function getCashflowAnalysis(code: string): Promise<CashFlowResult> {
  const { data, error } = await apiClient.GET("/api/stocks/{code}/cashflow", {
    params: { path: { code } },
  });

  if (error || !data) {
    throw new Error(toMessage("GET", "/api/stocks/{code}/cashflow", error));
  }
  return data;
}

export async function getTrendAnalysis(
  code: string,
  metric = "net_income",
): Promise<TrendResult> {
  const { data, error } = await apiClient.GET("/api/stocks/{code}/trend", {
    params: {
      path: { code },
      query: { metric },
    },
  });

  if (error || !data) {
    throw new Error(toMessage("GET", "/api/stocks/{code}/trend", error));
  }
  return data as TrendResult;
}

export * from "./workspace";
