import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import { getWorkspaceAiInsightsContext } from "../api/workspace";
import { BulletList, CopyBlock, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";

type InsightsPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
};

export function InsightsPage({ selectedCode, selectedStock }: InsightsPageProps) {
  const contextQuery = useQuery({
    queryKey: ["workspace-insights-context", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceAiInsightsContext(selectedCode),
    staleTime: 30 * 60_000,
  });

  const summaryItems = useMemo(
    () => [
      {
        label: "Profile",
        value: contextQuery.data?.profile.name ?? "Awaiting context",
        note: contextQuery.data?.profile.key ?? "Prompt profile",
      },
      {
        label: "Report date",
        value: contextQuery.data?.report_date ?? "Awaiting context",
        note: "Financial period referenced by the insight bundle",
      },
      {
        label: "Stock",
        value: selectedStock?.stock_name ?? contextQuery.data?.stock_name ?? selectedCode,
        note: selectedStock?.stock_code ?? selectedCode,
      },
    ],
    [contextQuery.data, selectedCode, selectedStock],
  );

  if (!selectedCode) {
    return (
      <SectionCard title="Insights page" eyebrow="No stock selected">
        <StateBlock
          title="Pick a company to unlock the narrative"
          description="The insights workspace becomes active once a company is selected."
        />
      </SectionCard>
    );
  }

  if (contextQuery.isError) {
    const message = (contextQuery.error as Error | undefined)?.message ?? "Unable to load the insight context.";
    return (
      <SectionCard title="Insights page" eyebrow="Narrative unavailable">
        <StateBlock tone="danger" title="Unable to load the AI context" description={message} />
      </SectionCard>
    );
  }

  if (contextQuery.isLoading) {
    return (
      <SectionCard title="Insights page" eyebrow="Preparing AI context">
        <StateBlock
          title="Assembling prompt injections"
          description="The workspace is building a controlled prompt bundle from archive-backed evidence."
          action={<LoadingSkeleton lines={4} />}
        />
      </SectionCard>
    );
  }

  if (!contextQuery.data) {
    return (
      <SectionCard title="Insights page" eyebrow="No context yet">
        <StateBlock
          title="No insight context returned"
          description="The backend did not return a prompt bundle for the selected stock."
        />
      </SectionCard>
    );
  }

  const context = contextQuery.data;

  return (
    <div className="page-stack">
      <SectionCard
        title={context.stock_name}
        eyebrow="AI conclusion workspace"
        action={<span className="section-meta">{context.profile.name}</span>}
      >
        <MetricGrid items={summaryItems} />
      </SectionCard>

      <SectionCard title="System prompt" eyebrow="Injected block">
        <CopyBlock>
          <p>{context.injection_bundle.system_prompt}</p>
        </CopyBlock>
      </SectionCard>

      <div className="two-up">
        <SectionCard title="Company context" eyebrow="Injected block">
          <CopyBlock>
            <p>{context.injection_bundle.company_context}</p>
          </CopyBlock>
        </SectionCard>

        <SectionCard title="Risk overlay" eyebrow="Injected block">
          <CopyBlock>
            <p>{context.injection_bundle.risk_overlay}</p>
          </CopyBlock>
        </SectionCard>
      </div>

      <div className="two-up">
        <SectionCard title="Metric digest" eyebrow="Injected block">
          <CopyBlock>
            <p>{context.injection_bundle.metric_digest}</p>
          </CopyBlock>
        </SectionCard>

        <SectionCard title="Model summary" eyebrow="Injected block">
          <CopyBlock>
            <p>{context.injection_bundle.model_summary}</p>
          </CopyBlock>
        </SectionCard>
      </div>

      <SectionCard title="Output contract" eyebrow="LLM structure">
        <BulletList
          items={context.profile.output_contract}
          emptyLabel="No output contract returned yet."
          tone="positive"
        />
      </SectionCard>
    </div>
  );
}
