import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import { getWorkspaceModelResults } from "../api/workspace";
import { BulletList, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";

type ModelsPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
};

export function ModelsPage({ selectedCode, selectedStock }: ModelsPageProps) {
  const modelsQuery = useQuery({
    queryKey: ["workspace-models", selectedCode],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceModelResults(selectedCode),
  });

  const headlineItems = useMemo(() => {
    return (modelsQuery.data?.items ?? []).slice(0, 4).map((item) => ({
      label: item.label,
      value: item.verdict.toUpperCase(),
      note: item.score ? `Score ${item.score}` : "Model card",
    }));
  }, [modelsQuery.data?.items]);

  if (!selectedCode) {
    return (
      <SectionCard title="Models page" eyebrow="No stock selected">
        <StateBlock
          title="Pick a company to begin"
          description="The model view becomes active once the left rail selection is set."
        />
      </SectionCard>
    );
  }

  if (modelsQuery.isError) {
    const message = (modelsQuery.error as Error | undefined)?.message ?? "Unable to load the model cards.";
    return (
      <SectionCard title="Models page" eyebrow="Data unavailable">
        <StateBlock tone="danger" title="Unable to load model data" description={message} />
      </SectionCard>
    );
  }

  return (
    <div className="page-stack">
      <SectionCard
        title="Analysis models"
        eyebrow={selectedStock?.stock_name ?? modelsQuery.data?.stock_name ?? selectedCode}
        action={<span className="section-meta">Five fixed finance lenses</span>}
      >
        {modelsQuery.isLoading ? (
          <LoadingSkeleton lines={4} />
        ) : (
          <MetricGrid items={headlineItems} />
        )}
      </SectionCard>

      {(modelsQuery.data?.items ?? []).map((item) => (
        <SectionCard
          key={item.key}
          title={item.label}
          eyebrow={item.key}
          action={<span className="section-meta">{item.verdict}</span>}
        >
          {modelsQuery.isLoading ? (
            <LoadingSkeleton lines={4} />
          ) : (
            <div className="copy-block">
              <p>{item.summary}</p>
              <BulletList
                items={item.evidence_keys.map((evidenceKey) => `Evidence: ${evidenceKey}`)}
                emptyLabel="No evidence keys attached yet."
                tone={item.verdict === "weak" || item.verdict === "high" ? "warning" : "neutral"}
              />
            </div>
          )}
        </SectionCard>
      ))}
    </div>
  );
}
