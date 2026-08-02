"use client";

import Link from "next/link";
import { useStudio } from "@/components/studio-context";
import { Metric, ObjectLink, PageHeading, Panel, StatusChip } from "@/components/ui";

const lanes = {
  portfolio: {
    studyId: "ohlcv-portfolio-quality",
    eyebrow: "Portfolio research / CORE PROJECTION",
    title: "组合研究",
    description: "把候选因子翻译为有约束、有成本、有风险证据的研究组合；不连接账户或订单。",
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
  const { source, demoEnabled, factor } = useStudio();
  const project = source.snapshot?.projects?.[0];
  const study = project?.studies?.find((item) => item.id === config.studyId);
  const explorer = kind === "portfolio" ? project?.portfolioExplorer : project?.rlExplorer;
  const runs = explorer?.runs || [];
  const verifiedRuns = runs.length;
  const coreConnected = source.mode === "connected" && !demoEnabled;
  const evidenceState = verifiedRuns ? "known" : "missing";

  return (
    <>
      <PageHeading
        eyebrow={config.eyebrow}
        title={study?.name || config.title}
        description={study?.description || config.description}
        actions={<Link className="button" href={config.nextHref}>{config.nextLabel}</Link>}
      />

      <div className="trust-strip" aria-label={`${config.title}研究边界`}>
        <div className="trust-item"><span>Study</span><strong className="mono">{study?.id || config.studyId}</strong></div>
        <div className="trust-item"><span>Dataset</span><strong>{datasetLabel(study?.dataset)}</strong></div>
        <div className="trust-item"><span>Core evidence</span><strong>{verifiedRuns} verified run</strong></div>
        <div className="trust-item warning"><span>执行边界</span><strong>研究环境，无实盘权限</strong></div>
      </div>

      <div className="metric-row">
        <Metric label={config.primaryLabel} value={config.metricName} detail={`${study?.primaryMetric || config.fallbackMetric} · ${study?.direction || "maximize"}`} />
        <Metric label="Verified runs" value={String(verifiedRuns)} detail={verifiedRuns ? "Core immutable evidence" : "尚无有效 Explorer 投影"} tone={verifiedRuns ? "positive" : "warning"} />
        <Metric label="Universe" value={String(study?.dataset?.universe?.length || 0)} detail={study?.dataset?.asset_class || "等待 Core"} />
        <Metric label="Dataset hash" value={study?.datasetHash?.slice(0, 10) || "unavailable"} detail="Core-owned" />
        <Metric label="Trading authority" value="NONE" detail="不会生成或发送订单" />
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
            </div>
          </Panel>

          <Panel title={kind === "portfolio" ? "组合门禁" : "RL 治理门禁"} meta="高分不能绕过固定证据边界">
            <div className="dense-list">
              {config.checks.map(([label, detail, state]) => (
                <div className="dense-row" key={label}>
                  <div><strong>{label}</strong><p>{detail}</p></div>
                  <StatusChip state={state}>{state === "known" ? "已定义" : "待验证"}</StatusChip>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Core 证据状态" meta="不使用前端假结果填补缺失 Run">
            <div className="provenance-card">
              <StatusChip state={evidenceState}>{verifiedRuns ? "可检查" : "尚无有效 Run"}</StatusChip>
              <strong>{verifiedRuns ? `${verifiedRuns} 个不可变结果` : "Explorer 当前为空"}</strong>
              <span className="field-value">
                {verifiedRuns
                  ? "结果来自 Core snapshot，可回到对应 Run 与审计对象。"
                  : "当前 sample 的不可变 Run 未通过 Core 校验，页面保留 Study 契约但不伪造指标。"}
              </span>
            </div>
          </Panel>

          <Panel title="研究对象链" meta="Factor → Portfolio → governed RL">
            <ObjectLink href="/" label="FactorStudy" id={factor.id} />
            <ObjectLink href="/portfolio" label="PortfolioStudy" id="ohlcv-portfolio-quality" />
            <ObjectLink href="/rl" label="RLPolicyStudy" id="ohlcv-rl-factor-policy" />
            <ObjectLink href="/jobs" label="ComputeJob" id="Core task contract" />
            <ObjectLink href="/audit" label="Audit" id={factor.frameId} />
          </Panel>

          <div className="notice"><strong>明确边界：</strong> 目标权重、历史动作和策略工件都是研究证据，不是券商订单、账户状态或交易许可。</div>
        </div>
      </div>
    </>
  );
}
