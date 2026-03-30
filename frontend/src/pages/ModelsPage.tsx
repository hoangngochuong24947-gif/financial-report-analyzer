import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { StockInfo } from "../api/sdk";
import { getWorkspaceModelResults } from "../api/workspace";
import { BulletList, LoadingSkeleton, MetricGrid, SectionCard, StateBlock } from "../components/DataBlocks";
import { getWorkspaceCopy, type Lang } from "../lib/i18n";

type ModelsPageProps = {
  selectedCode: string;
  selectedStock?: StockInfo;
  lang: Lang;
};

export function ModelsPage({ selectedCode, selectedStock, lang }: ModelsPageProps) {
  const copy = getWorkspaceCopy(lang);

  const modelsQuery = useQuery({
    queryKey: ["workspace-models", selectedCode, lang],
    enabled: Boolean(selectedCode),
    queryFn: () => getWorkspaceModelResults(selectedCode, lang),
  });

  const headlineItems = useMemo(() => {
    return (modelsQuery.data?.items ?? []).slice(0, 4).map((item) => ({
      label: item.label,
      value: item.verdict.toUpperCase(),
      note: item.score ? `Score ${item.score}` : copy.models.lenses,
    }));
  }, [copy.models.lenses, modelsQuery.data?.items]);

  if (!selectedCode) {
    return (
      <SectionCard title={copy.models.title} eyebrow={copy.models.eyebrow}>
        <StateBlock title={copy.models.noStock} description={copy.models.description} />
      </SectionCard>
    );
  }

  if (modelsQuery.isError) {
    const message = (modelsQuery.error as Error | undefined)?.message ?? copy.models.dataUnavailable;
    return (
      <SectionCard title={copy.models.title} eyebrow={copy.models.eyebrow}>
        <StateBlock tone="danger" title={copy.models.dataUnavailable} description={message} />
      </SectionCard>
    );
  }

  return (
    <div className="page-stack">
      <SectionCard
        title={selectedStock?.stock_name ?? modelsQuery.data?.stock_name ?? selectedCode}
        eyebrow={copy.models.eyebrow}
        action={<span className="section-meta">{copy.models.lenses}</span>}
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
                emptyLabel={copy.models.dataUnavailable}
                tone={item.verdict === "weak" || item.verdict === "high" ? "warning" : "neutral"}
              />
            </div>
          )}
        </SectionCard>
      ))}
    </div>
  );
}

