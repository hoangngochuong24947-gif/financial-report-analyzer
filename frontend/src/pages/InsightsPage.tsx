import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import {
  generateWorkspaceInsights,
  getWorkspaceAiInsightsContext,
  getWorkspaceSavedInsightReport,
  type WorkspaceInsightReportResponse,
} from "../api/workspace";
import { BulletList, CopyBlock, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";
import { formatDateTime } from "../lib/finance";
import { getBrowserLocale, getWorkspaceCopy, type Lang } from "../lib/i18n";

type InsightsPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
  lang: Lang;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function normalizeReport(data: unknown): WorkspaceInsightReportResponse | undefined {
  if (!isRecord(data)) {
    return undefined;
  }

  if (isRecord(data.report)) {
    return data.report as WorkspaceInsightReportResponse;
  }

  if (isRecord(data.data)) {
    return data.data as WorkspaceInsightReportResponse;
  }

  return data as WorkspaceInsightReportResponse;
}

function renderTextBlock(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    return value.filter((item) => typeof item === "string").join("\n");
  }

  return "";
}

export function InsightsPage({ selectedCode, selectedStock, lang }: InsightsPageProps) {
  const copy = getWorkspaceCopy(lang);
  const locale = getBrowserLocale(lang);
  const queryClient = useQueryClient();

  const contextQuery = useQuery({
    queryKey: ["workspace-insights-context", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceAiInsightsContext(selectedCode, lang),
    staleTime: 30 * 60_000,
  });

  const savedReportQuery = useQuery({
    queryKey: ["workspace-insights-report", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceSavedInsightReport(selectedCode, lang),
    staleTime: 60_000,
    retry: false,
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      const result = await generateWorkspaceInsights(selectedCode, lang);
      return normalizeReport(result);
    },
    onSuccess: (report) => {
      if (report) {
        queryClient.setQueryData(["workspace-insights-report", selectedCode, lang], report);
        void queryClient.invalidateQueries({ queryKey: ["workspace-insights-context", selectedCode, lang] });
      }
    },
  });

  const summaryItems = useMemo(
    () => [
      {
        label: copy.insights.title,
        value: contextQuery.data?.profile.name ?? copy.insights.noContext,
        note: contextQuery.data?.profile.key ?? copy.insights.eyebrow,
      },
      {
        label: copy.insights.reportDate,
        value: contextQuery.data?.report_date ?? copy.shared.unavailable,
        note: contextQuery.data?.stock_name ?? selectedStock?.stock_name ?? selectedCode,
      },
      {
        label: copy.shell.selectedCompany,
        value: selectedStock?.stock_name ?? contextQuery.data?.stock_name ?? selectedCode,
        note: selectedStock?.stock_code ?? selectedCode,
      },
    ],
    [copy, contextQuery.data, selectedCode, selectedStock],
  );

  const report = savedReportQuery.data ?? undefined;
  const reportSections = useMemo(
    () =>
      report
        ? [
            {
              title: copy.insights.executiveSummary,
              body: renderTextBlock(report.executive_summary),
            },
            {
              title: "Profitability",
              body: renderTextBlock(report.profitability_analysis),
            },
            {
              title: "Solvency",
              body: renderTextBlock(report.solvency_analysis),
            },
            {
              title: "Efficiency",
              body: renderTextBlock(report.efficiency_analysis),
            },
            {
              title: "Cash flow",
              body: renderTextBlock(report.cashflow_analysis),
            },
            {
              title: "Trend",
              body: renderTextBlock(report.trend_analysis),
            },
          ].filter((section) => section.body.length > 0)
        : [],
    [copy.insights.executiveSummary, report],
  );

  if (!selectedCode) {
    return (
      <SectionCard title={copy.insights.title} eyebrow={copy.insights.eyebrow}>
        <StateBlock title={copy.insights.noStock} description={copy.insights.description} />
      </SectionCard>
    );
  }

  const contextError = (contextQuery.error as Error | undefined)?.message;

  return (
    <div className="page-stack">
      <SectionCard
        title={selectedStock?.stock_name ?? contextQuery.data?.stock_name ?? selectedCode}
        eyebrow={copy.insights.eyebrow}
        action={
          <button
            type="button"
            className="ghost-button"
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
          >
            {generateMutation.isPending ? copy.insights.generating : copy.insights.generate}
          </button>
        }
      >
        <div className="hero-copy">
          <p>{copy.insights.description}</p>
        </div>

        <MetricGrid items={summaryItems} />
      </SectionCard>

      <div className="two-up">
        <SectionCard title={copy.insights.promptBundle} eyebrow={copy.insights.eyebrow}>
          {contextQuery.isLoading ? (
            <LoadingSkeleton lines={5} />
          ) : contextQuery.isError && !contextQuery.data ? (
            <StateBlock tone="danger" title={copy.insights.contextUnavailable} description={contextError ?? copy.insights.contextUnavailable} />
          ) : contextQuery.data ? (
            <div className="copy-block">
              <p>{contextQuery.data.injection_bundle.system_prompt}</p>
              <p>{contextQuery.data.injection_bundle.company_context}</p>
              <p>{contextQuery.data.injection_bundle.risk_overlay}</p>
            </div>
          ) : (
            <StateBlock title={copy.insights.noContext} description={copy.insights.description} />
          )}
        </SectionCard>

        <SectionCard title={copy.insights.output} eyebrow={copy.insights.eyebrow}>
          {generateMutation.isPending ? (
            <StateBlock
              title={copy.insights.generating}
              description="The backend is assembling a new AI report from the workspace evidence."
            />
          ) : savedReportQuery.isLoading ? (
            <LoadingSkeleton lines={4} />
          ) : report ? (
            <div className="copy-block">
              <p>
                <strong>{copy.insights.executiveSummary}</strong>
              </p>
              <p>{renderTextBlock(report.executive_summary ?? report.summary) || copy.insights.reportUnavailable}</p>
              <p>
                {copy.insights.generatedAt}: {formatDateTime(report.generated_at, locale)}
              </p>
              <p>
                {copy.insights.reportDate}: {report.report_date ?? contextQuery.data?.report_date ?? copy.shared.unavailable}
              </p>
              <p>{lang === "zh" ? "该报告已存储在后端，切换页面后仍可继续查看。" : "This report is stored on the backend and remains available after navigation."}</p>
            </div>
          ) : (
            <StateBlock title={copy.insights.reportUnavailable} description={copy.insights.description} />
          )}
        </SectionCard>
      </div>

      {reportSections.length > 0 ? (
        <div className="two-up">
          {reportSections.map((section) => (
            <SectionCard key={section.title} title={section.title} eyebrow={copy.insights.output}>
              <CopyBlock>
                <p>{section.body}</p>
              </CopyBlock>
            </SectionCard>
          ))}
        </div>
      ) : null}

      {report?.strengths?.length || report?.weaknesses?.length || report?.recommendations?.length || report?.risk_warnings?.length ? (
        <div className="two-up">
          <SectionCard title={copy.insights.strengths} eyebrow={copy.insights.output}>
            <BulletList items={report?.strengths} emptyLabel={copy.insights.reportUnavailable} tone="positive" />
          </SectionCard>
          <SectionCard title={copy.insights.weaknesses} eyebrow={copy.insights.output}>
            <BulletList items={report?.weaknesses} emptyLabel={copy.insights.reportUnavailable} tone="warning" />
          </SectionCard>
          <SectionCard title={copy.insights.recommendations} eyebrow={copy.insights.output}>
            <BulletList items={report?.recommendations} emptyLabel={copy.insights.reportUnavailable} tone="neutral" />
          </SectionCard>
          <SectionCard title={copy.insights.riskWarnings} eyebrow={copy.insights.output}>
            <BulletList items={report?.risk_warnings} emptyLabel={copy.insights.reportUnavailable} tone="warning" />
          </SectionCard>
        </div>
      ) : null}

      {contextQuery.data ? (
        <SectionCard title={copy.shared.archiveSummary} eyebrow={copy.insights.eyebrow}>
          <BulletList
            items={contextQuery.data.profile.output_contract}
            emptyLabel={copy.insights.noContext}
            tone="positive"
          />
        </SectionCard>
      ) : null}
    </div>
  );
}
