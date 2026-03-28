import { apiClient } from "./client";
import type { Client } from "openapi-fetch";
import type { paths as ApiPaths } from "./generated/schema";

type ApiError = { detail?: string } | unknown;

type WorkspaceJsonResponse<T> = {
  headers: Record<string, unknown>;
  content: {
    "application/json": T;
  };
};

type WorkspaceValidationResponse = {
  headers: Record<string, unknown>;
  content: {
    "application/json": unknown;
  };
};

type WorkspaceGetPath<Body> = {
  parameters: {
    query?: never;
    header?: never;
    path?: never;
    cookie?: never;
  };
  get: {
    parameters: {
      query?: Record<string, unknown>;
      header?: never;
      path: { code: string };
      cookie?: never;
    };
    responses: {
      200: WorkspaceJsonResponse<Body>;
      422: WorkspaceValidationResponse;
    };
  };
};

type WorkspacePaths = ApiPaths & {
  "/api/v2/workspaces": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get: {
      parameters: {
        query?: {
          limit?: number;
        };
        header?: never;
        path?: never;
        cookie?: never;
      };
      responses: {
        200: WorkspaceJsonResponse<WorkspaceSummary[]>;
        422: WorkspaceValidationResponse;
      };
    };
  };
  "/api/v2/workspace/{code}/snapshot": WorkspaceGetPath<WorkspaceSnapshotResponse>;
  "/api/v2/workspace/{code}/metrics/catalog": WorkspaceGetPath<WorkspaceMetricCatalogResponse>;
  "/api/v2/workspace/{code}/metrics": WorkspaceGetPath<WorkspaceMetricValuesResponse>;
  "/api/v2/workspace/{code}/models": WorkspaceGetPath<WorkspaceModelResultsResponse>;
  "/api/v2/workspace/{code}/insights/context": WorkspaceGetPath<WorkspaceAiInsightsContextResponse>;
};

type WorkspaceClient = Client<WorkspacePaths>;

const workspaceClient = apiClient as unknown as WorkspaceClient;

function toMessage(method: string, path: string, error: ApiError): string {
  if (error && typeof error === "object" && "detail" in error) {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.length > 0) {
      return `${method} ${path} failed: ${detail}`;
    }
  }
  return `${method} ${path} failed`;
}

function unwrapData<T>(method: string, path: string, result: { data?: T; error?: ApiError }): T {
  if (!result.data || result.error) {
    throw new Error(toMessage(method, path, result.error));
  }
  return result.data;
}

export type WorkspaceStatementRows = Array<Record<string, unknown>>;

export interface WorkspaceSnapshotResponse {
  stock: {
    stock_code: string;
    stock_name: string;
    market: string;
  };
  available_periods: string[];
  statements: {
    balance_sheet: WorkspaceStatementRows;
    income_statement: WorkspaceStatementRows;
    cashflow_statement: WorkspaceStatementRows;
  };
  source: string;
  updated_at?: string;
}

export interface WorkspaceMetricCatalogItem {
  key: string;
  label: string;
  group: string;
  description: string;
  unit?: string;
  source?: string;
}

export interface WorkspaceMetricCatalogResponse {
  stock_code: string;
  stock_name: string;
  report_date: string;
  total: number;
  items: WorkspaceMetricCatalogItem[];
}

export interface WorkspaceMetricValue {
  key: string;
  label: string;
  group: string;
  value: string;
  period?: string | null;
  source?: string;
  note?: string | null;
}

export interface WorkspaceMetricValuesResponse {
  stock_code: string;
  stock_name: string;
  report_date: string;
  categories: Record<string, WorkspaceMetricValue[]>;
  summary: string;
}

export interface WorkspaceModelResult {
  key: string;
  label: string;
  verdict: string;
  summary: string;
  score?: string | null;
  evidence_keys: string[];
}

export interface WorkspaceModelResultsResponse {
  stock_code: string;
  stock_name: string;
  report_date: string;
  items: WorkspaceModelResult[];
}

export interface WorkspaceAiInsightsContextResponse {
  stock_code: string;
  stock_name: string;
  report_date: string;
  profile: {
    key: string;
    name: string;
    output_contract: string[];
  };
  injection_bundle: {
    system_prompt: string;
    company_context: string;
    risk_overlay: string;
    model_summary: string;
    metric_digest: string;
  };
}

export interface WorkspaceArchiveItem {
  stock_code: string;
  stock_name: string;
  market: string;
  dataset: string;
  fetched_at: string;
  raw_path: string;
  csv_path: string;
  manifest_path: string;
  row_count: number;
  status: string;
  report_date?: string | null;
}

export interface WorkspaceSummary {
  stock_code: string;
  stock_name: string;
  market: string;
  latest_report_date?: string | null;
  dataset_count: number;
  archives: WorkspaceArchiveItem[];
}

export async function listWorkspaces(limit = 20): Promise<WorkspaceSummary[]> {
  const result = await workspaceClient.GET("/api/v2/workspaces", {
    params: { query: { limit } },
  });
  return unwrapData("GET", "/api/v2/workspaces", result);
}

export async function getWorkspaceSnapshot(code: string): Promise<WorkspaceSnapshotResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/snapshot", {
    params: { path: { code } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/snapshot", result);
}

export async function getWorkspaceMetricCatalog(code: string): Promise<WorkspaceMetricCatalogResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/metrics/catalog", {
    params: { path: { code } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/metrics/catalog", result);
}

export async function getWorkspaceMetricValues(code: string): Promise<WorkspaceMetricValuesResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/metrics", {
    params: { path: { code } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/metrics", result);
}

export async function getWorkspaceModelResults(code: string): Promise<WorkspaceModelResultsResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/models", {
    params: { path: { code } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/models", result);
}

export async function getWorkspaceAiInsightsContext(code: string): Promise<WorkspaceAiInsightsContextResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/insights/context", {
    params: { path: { code } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/insights/context", result);
}
