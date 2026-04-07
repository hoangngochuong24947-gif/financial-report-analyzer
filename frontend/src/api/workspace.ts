import { apiClient } from "./client";
import type { Client } from "openapi-fetch";
import type { paths as ApiPaths } from "./generated/schema";
import type { Lang } from "../lib/i18n";

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

type WorkspaceQuery = {
  lang?: string;
};

function toApiLang(lang?: Lang): string | undefined {
  if (!lang) {
    return undefined;
  }
  return lang === "en" ? "en-US" : "en-US";
}

type WorkspaceGetPath<Body> = {
  parameters: {
    query?: never;
    header?: never;
    path?: never;
    cookie?: never;
  };
  get: {
    parameters: {
      query?: WorkspaceQuery & Record<string, unknown>;
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

type WorkspacePostPath<Body> = {
  parameters: {
    query?: never;
    header?: never;
    path?: never;
    cookie?: never;
  };
  post: {
    parameters: {
      query?: WorkspaceQuery & Record<string, unknown>;
      header?: never;
      path: { code: string };
      cookie?: never;
    };
    requestBody?: never;
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
        query?: WorkspaceQuery & {
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
  "/api/v2/workspace/{code}/statements": WorkspaceGetPath<WorkspaceStatementsResponse>;
  "/api/v2/workspace/{code}/insights/generate": WorkspacePostPath<WorkspaceInsightReportResponse>;
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

function hasData<T>(result: { data?: T; error?: ApiError }): result is { data: T; error?: never } {
  return Boolean(result.data) && !result.error;
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

export interface WorkspaceStatementsResponse {
  stock_code?: string;
  stock_name?: string;
  report_date?: string;
  updated_at?: string;
  source?: string;
  available_periods?: string[];
  selected_period?: string;
  lang?: string;
  stock?: {
    stock_code: string;
    stock_name: string;
    market: string;
  };
  tabs?: StatementDetailTab[];
  statements?: {
    balance_sheet?: WorkspaceStatementRows;
    income_statement?: WorkspaceStatementRows;
    cashflow_statement?: WorkspaceStatementRows;
  };
  balance_sheet?: WorkspaceStatementRows;
  income_statement?: WorkspaceStatementRows;
  cashflow_statement?: WorkspaceStatementRows;
}

export interface StatementDetailRow {
  field?: string;
  key: string;
  label: string;
  section?: string | null;
  value: unknown;
  display_value?: string;
  unit?: string;
  source?: string;
  period?: string | null;
  is_estimated?: boolean;
}

export interface StatementDetailTab {
  key: string;
  title?: string;
  label?: string;
  period?: string;
  rows: StatementDetailRow[];
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

export interface WorkspaceInsightSection {
  title?: string;
  label?: string;
  content?: string;
  items?: string[];
}

export interface WorkspaceInsightReportResponse {
  stock_code?: string;
  stock_name?: string;
  report_date?: string;
  generated_at?: string;
  executive_summary?: string;
  profitability_analysis?: string;
  solvency_analysis?: string;
  efficiency_analysis?: string;
  cashflow_analysis?: string;
  trend_analysis?: string;
  strengths?: string[];
  weaknesses?: string[];
  recommendations?: string[];
  risk_warnings?: string[];
  sections?: WorkspaceInsightSection[];
  [key: string]: unknown;
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

export async function listWorkspaces(limit = 20, lang?: Lang): Promise<WorkspaceSummary[]> {
  const result = await workspaceClient.GET("/api/v2/workspaces", {
    params: { query: { limit, lang: toApiLang(lang) } },
  });
  return unwrapData("GET", "/api/v2/workspaces", result);
}

export async function getWorkspaceSnapshot(code: string, lang?: Lang): Promise<WorkspaceSnapshotResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/snapshot", {
    params: { path: { code }, query: { lang: toApiLang(lang) } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/snapshot", result);
}

export async function getWorkspaceMetricCatalog(code: string, lang?: Lang): Promise<WorkspaceMetricCatalogResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/metrics/catalog", {
    params: { path: { code }, query: { lang: toApiLang(lang) } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/metrics/catalog", result);
}

export async function getWorkspaceMetricValues(code: string, lang?: Lang): Promise<WorkspaceMetricValuesResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/metrics", {
    params: { path: { code }, query: { lang: toApiLang(lang) } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/metrics", result);
}

export async function getWorkspaceModelResults(code: string, lang?: Lang): Promise<WorkspaceModelResultsResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/models", {
    params: { path: { code }, query: { lang: toApiLang(lang) } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/models", result);
}

export async function getWorkspaceAiInsightsContext(code: string, lang?: Lang): Promise<WorkspaceAiInsightsContextResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/insights/context", {
    params: { path: { code }, query: { lang: toApiLang(lang) } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/insights/context", result);
}

export async function getWorkspaceStatements(
  code: string,
  lang?: Lang,
  period?: string,
): Promise<WorkspaceStatementsResponse> {
  const result = await workspaceClient.GET("/api/v2/workspace/{code}/statements", {
    params: { path: { code }, query: { lang: toApiLang(lang), period } },
  });
  return unwrapData("GET", "/api/v2/workspace/{code}/statements", result);
}

export async function generateWorkspaceInsights(
  code: string,
  lang?: Lang,
): Promise<WorkspaceInsightReportResponse> {
  const result = await workspaceClient.POST("/api/v2/workspace/{code}/insights/generate", {
    params: { path: { code }, query: { lang: toApiLang(lang) } },
  });
  return unwrapData("POST", "/api/v2/workspace/{code}/insights/generate", result);
}

export function hasWorkspaceStatements(data: WorkspaceStatementsResponse | undefined): boolean {
  return Boolean(
    data &&
      ((Array.isArray(data.balance_sheet) && data.balance_sheet.length > 0) ||
        (Array.isArray(data.income_statement) && data.income_statement.length > 0) ||
        (Array.isArray(data.cashflow_statement) && data.cashflow_statement.length > 0) ||
        (Array.isArray(data.statements?.balance_sheet) && data.statements.balance_sheet.length > 0) ||
        (Array.isArray(data.statements?.income_statement) && data.statements.income_statement.length > 0) ||
        (Array.isArray(data.statements?.cashflow_statement) && data.statements.cashflow_statement.length > 0)),
  );
}

export function resolveWorkspaceStatements(
  data: WorkspaceStatementsResponse | undefined,
): WorkspaceStatementsResponse | undefined {
  if (!data) {
    return undefined;
  }

  if (data.statements) {
    return data;
  }

  return {
    ...data,
    statements: {
      balance_sheet: data.balance_sheet ?? [],
      income_statement: data.income_statement ?? [],
      cashflow_statement: data.cashflow_statement ?? [],
    },
  };
}
