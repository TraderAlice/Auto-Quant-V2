"use client";

import { useStudio } from "@/components/studio-context";
import { ButtonLink, Metric, ObjectLink, PageHeading, Panel, StatusChip } from "@/components/ui";
import { RunStudyButton } from "@/components/run-study-button";

const lanes = {
  portfolio: {
    studyId: "ohlcv-portfolio-quality",
    eyebrow: "Portfolio research / CORE PROJECTION",
    title: "组合研究",
    description: "把候选因子翻译为有约束、有成本、有风险证据的研究组合。",
    primaryLabel: "Primary metric",
    fallbackMetric: "validation_net_sharpe",
    metricName: "Net Sharpe",
    checks: [
      ["Factor population", "与因子研究共享、独立锁定", "known"],
      ["Portfolio mandate", "方向、现金、上限与基准由 mandate 拥有", "known"],
      ["Cost / capacity", "沿实际调仓路径评估", "partial"],
      ["Frozen holdout", "不得用于选择，只用于最终证据", "known"],
    ],
    nextHref: "/rl",
    nextLabel: "进入治理式 RL",
  },
  rl: {
    studyId: "ohlcv-rl-factor-policy",
    eyebrow: "Governed RL / CORE PROJECTION",
    title: "治理式 RL",
    description: "锁定候选因子和组合 mandate，在固定环境、fold 与 seed 下评估有限动作策略。",
    primaryLabel: "Primary metric",
    fallbackMetric: "validation_mean_net_sharpe",
    metricName: "Mean net Sharpe",
    checks: [
      ["Candidate factor", "只读内容锁；因子变更会使 RL 证据过期", "known"],
      ["Observation / action", "状态编码和动作 sleeve 必须显式", "known"],
      ["Reward / baseline", "必须相对固定与上下文基线证明增量", "partial"],
      ["Seeds / holdout", "逐 fold、逐 seed 保存，冻结样本不选模", "known"],
    ],
    nextHref: "/audit",
    nextLabel: "查看审计证据",
  },
};

function datasetLabel(dataset) {
  return dataset ? `${dataset.id}@${dataset.version}` : "未绑定";
}

export function ResearchLane({ kind }) {
  const config = lanes[kind];
  const { source, subject, demoEnabled, factor } = useStudio();
  const project = source.snapshot?.projects?.[0];
  const study = project?.studies?.find((item) => item.id === config.studyId);
  const explorer = kind === "portfolio" ? project?.portfolioExplorer : project?.rlExplorer;
  const modelRuntime = project?.modelRuntime;
  const latestModelRun = project?.modelRuns?.at(-1);
  const verifiedRuns = (project?.runs || []).filter((run) => run.studyId === config.studyId).length;
  const primaryMetric = explorer?.run?.primaryMetric || explorer?.run?.objective?.metric || study?.primaryMetric || config.fallbackMetric;
  const primaryValue = explorer?.run?.primaryValue ?? explorer?.summary?.validation?.mean;
  const rlValueAdded = explorer?.summary?.rlAddedValidationValue;
  const checks = config.checks.map(([label, detail, state]) => {
    if (kind === "portfolio" && label === "Cost / capacity" && explorer?.liquidityCapacity) {
      return [label, "成本、换手、流动性与容量已沿实际调仓路径评估", "known", "已评估"];
    }
    if (kind === "rl" && label === "Reward / baseline" && typeof rlValueAdded === "boolean") {
      return [
        label,
        `相对最佳固定基线的 validation 平均优势 ${explorer.summary.meanValidationAdvantageVsBestBaseline.toFixed(6)}`,
        rlValueAdded ? "known" : "missing",
        rlValueAdded ? "通过" : "未证明增量",
      ];
    }
    return [label, detail, state, state === "known" ? "已定义" : "待验证"];
  });
  const coreConnected = source.mode === "connected" && !demoEnabled;
  const evidenceState = verifiedRuns ? "known" : "missing";

  return (
    <>
      <PageHeading
        eyebrow={config.eyebrow}
        title={study?.name || config.title}
        description={study?.description || config.description}
        actions={
          <>
            <RunStudyButton projectId={project?.id} studyId={study?.id}>重新执行 Study</RunStudyButton>
            <ButtonLink href={config.nextHref}>{config.nextLabel}</ButtonLink>
          </>
        }
      />

      <div className="trust-strip" aria-label={`${config.title}研究边界`}>
        <div className="trust-item"><span>Study</span><strong className="mono">{study?.id || config.studyId}</strong></div>
        <div className="trust-item"><span>Dataset</span><strong>{datasetLabel(study?.dataset)}</strong></div>
        <div className={`trust-item ${subject?.unresolved.length ? "warning" : ""}`}><span>Subject</span><strong>{subject ? `${subject.label} · ${subject.universe.length}` : "未解析"}</strong></div>
        <div className="trust-item"><span>Core evidence</span><strong>{verifiedRuns} verified run</strong></div>
        <div className="trust-item"><span>研究模式</span><strong>验证与复现</strong></div>
      </div>

      <div className="metric-row">
        <Metric label={config.primaryLabel} value={Number.isFinite(primaryValue) ? primaryValue.toFixed(6) : "—"} detail={`${primaryMetric} · ${study?.direction || "maximize"}`} tone={!Number.isFinite(primaryValue) || primaryValue < 0 || rlValueAdded === false ? "warning" : "positive"} />
        <Metric label="Verified runs" value={String(verifiedRuns)} detail={verifiedRuns ? "Core immutable evidence" : "尚无有效 Explorer 投影"} tone={verifiedRuns ? "positive" : "warning"} />
        <Metric label="Universe" value={String(study?.dataset?.universe?.length || 0)} detail={study?.dataset?.asset_class || "等待 Core"} />
        <Metric label="Dataset hash" value={study?.datasetHash?.slice(0, 10) || "unavailable"} detail="Core-owned" />
        <Metric label="Evidence mode" value="CORE" detail="不可变研究证据" />
      </div>

      <div className="result-grid">
        <div className="stack">
          <Panel title="固定研究契约" meta={coreConnected ? "直接读取 Core Studio snapshot" : "当前为隔离演示视图"}>
            <div className="field-grid">
              <div><span className="field-label">Study kind</span><span className="field-value">{kind === "portfolio" ? "portfolio" : study?.subjectKind || "model"}</span></div>
              <div><span className="field-label">Objective</span><span className="field-value">{study?.primaryMetric || config.fallbackMetric} · {study?.direction || "maximize"}</span></div>
              <div><span className="field-label">Time range</span><span className="field-value">{study?.dataset?.time_range ? `${study.dataset.time_range.start} → ${study.dataset.time_range.end}` : "等待 Core"}</span></div>
              <div><span className="field-label">Universe</span><span className="field-value">{study?.dataset?.universe?.join(", ") || "等待 Core"}</span></div>
              <div><span className="field-label">Dataset hash</span><span className="field-value mono">{study?.datasetHash || "等待 Core"}</span></div>
              <div><span className="field-label">Research frame</span><span className="field-value mono">{factor.frameId}</span></div>
              <div><span className="field-label">Market clock</span><span className="field-value">{subject ? [subject.market.clock, subject.market.calendar, subject.market.timezone].filter(Boolean).join(" · ") || "Core 未声明" : "等待 Core"}</span></div>
              <div><span className="field-label">Interval / venue</span><span className="field-value">{subject ? `${subject.interval || "未声明"} · ${subject.venues.join(", ") || "未声明"}` : "等待 Core"}</span></div>
            </div>
          </Panel>

          <Panel title={kind === "portfolio" ? "组合门禁" : "RL 治理门禁"} meta="高分不能绕过固定证据边界">
            <div className="dense-list">
              {checks.map(([label, detail, state, status]) => (
                <div className="dense-row" key={label}>
                  <div><strong>{label}</strong><p>{detail}</p></div>
                  <StatusChip state={state}>{status}</StatusChip>
                </div>
              ))}
              {(subject?.guardrails || []).map((detail, index) => (
                <div className="dense-row" key={detail}>
                  <div><strong>{subject.label} · {index + 1}</strong><p>{detail}</p></div>
                  <StatusChip state={subject.unresolved.length ? "partial" : "known"}>{subject.unresolved.length ? "待补语义" : "标的约束"}</StatusChip>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Core 证据状态" meta="不使用前端假结果填补缺失 Run">
            <div className="provenance-card">
              <StatusChip state={evidenceState}>{verifiedRuns ? "可检查" : "尚无有效 Run"}</StatusChip>
              <strong className="mono">{explorer?.run?.id || "Explorer 当前为空"}</strong>
              <span className="field-value">
                {verifiedRuns
                  ? `${primaryMetric} = ${Number.isFinite(primaryValue) ? primaryValue.toFixed(6) : "unavailable"} · ${explorer?.run?.status}`
                  : "当前 sample 的不可变 Run 未通过 Core 校验，页面保留 Study 契约但不伪造指标。"}
              </span>
              {kind === "rl" && typeof rlValueAdded === "boolean" ? (
                <StatusChip state={rlValueAdded ? "known" : "missing"}>{rlValueAdded ? "RL 证明增量" : "RL 未证明基线增量"}</StatusChip>
              ) : null}
            </div>
          </Panel>

          <Panel title="研究对象链" meta="Factor → Portfolio → governed RL">
            <ObjectLink href="/" label="FactorStudy" id={factor.id} />
            <ObjectLink href="/portfolio" label="PortfolioStudy" id="ohlcv-portfolio-quality" />
            <ObjectLink href="/rl" label="RLPolicyStudy" id="ohlcv-rl-factor-policy" />
            <ObjectLink href="/jobs" label="ComputeJob" id="Core task contract" />
            <ObjectLink href="/audit" label="Audit" id={factor.frameId} />
          </Panel>

          {kind === "rl" ? (
            <Panel title="监督式 ML 运行时" meta="Core 能力声明，不伪造模型结果">
              <div className="provenance-card">
                <StatusChip state={modelRuntime?.available ? "known" : "missing"}>{modelRuntime?.available ? "可用" : "未连接"}</StatusChip>
                <strong>{latestModelRun?.result?.selectedModel || modelRuntime?.models?.join(" / ") || "等待 Core"}</strong>
                <span className="field-value">point-in-time 特征 · validation-only 选模 · test 仅终局审计</span>
                <span className="mono">{modelRuntime?.entrypoint || "Core 未声明入口"}</span>
                {latestModelRun ? <span className="mono">{latestModelRun.id}</span> : null}
              </div>
            </Panel>
          ) : null}

          <div className="notice"><strong>研究产物：</strong> 目标权重、历史动作和策略工件共同构成可复现证据链。</div>
        </div>
      </div>
    </>
  );
}
