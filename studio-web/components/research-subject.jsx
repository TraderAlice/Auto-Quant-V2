import { Panel, StatusChip } from "@/components/ui";

function join(values, fallback = "Core 未声明") {
  return values?.length ? values.join(", ") : fallback;
}

export function ResearchSubject({ subject }) {
  if (!subject) return null;
  const clock = [subject.market.clock, subject.market.calendar, subject.market.timezone].filter(Boolean).join(" · ");
  return (
    <Panel title="研究标的" meta={`${subject.sourceStudyId} · Core projection`}>
      <div className="field-grid">
        <div><span className="field-label">研究模板</span><span className="field-value">{subject.label}</span></div>
        <div><span className="field-label">经济类别</span><span className="field-value">{subject.assetClass}</span></div>
        <div><span className="field-label">标的池</span><span className="field-value">{subject.universe.length} · {join(subject.universe.slice(0, 6))}</span></div>
        <div><span className="field-label">市场时钟</span><span className="field-value">{clock || "Core 未声明"}</span></div>
        <div><span className="field-label">场所 / 币种</span><span className="field-value">{join(subject.venues)} / {join(subject.currencies)}</span></div>
        <div><span className="field-label">基础频率</span><span className="field-value">{subject.interval || "Core 未声明"}</span></div>
      </div>
      <div className="tag-list" style={{ marginTop: 12 }}>
        {subject.adapters.map((adapter) => <span className="tag" key={adapter}>{adapter}</span>)}
        <StatusChip state={subject.unresolved.length ? "partial" : "known"}>
          {subject.unresolved.length ? `${subject.unresolved.length} 项未解析` : "标的语义完整"}
        </StatusChip>
      </div>
      {subject.unresolved.length ? <p className="notice" style={{ marginTop: 12 }}><strong>待补齐：</strong> {subject.unresolved.join("、")}。在 Core 声明前不生成市场特定结论。</p> : null}
    </Panel>
  );
}
