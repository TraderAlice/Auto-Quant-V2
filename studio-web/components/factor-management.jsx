"use client";

import { useStudio } from "@/components/studio-context";
import {
  ButtonLink,
  DataTable,
  EmptyState,
  Metric,
  ObjectLink,
  PageHeading,
  Panel,
  StatusChip,
} from "@/components/ui";
import { projectFactorManagement } from "@/lib/factor-management";

const PHASE_LABELS = {
  "not-started": "未开始",
  "baseline-ready": "基线已就绪",
  researching: "研究中",
  reported: "已报告",
  stale: "输入过期",
  "scientific-limit": "科研边界",
  "repair-required": "需要修补",
  unspecified: "等待 Core 阶段",
  unannounced: "未声明研究 Program",
};

const PHASE_DETAILS = {
  "not-started": "尚无 Factor Run，治理面等待第一次不可变 Run。",
  "baseline-ready": "存在不可变 baseline Run，等待首次 Report。",
  researching: "当前 Session 正在生成更多候选，活跃进度与不可变证据并存。",
  reported: "当前不可变 Report 已冻结，可继续下一轮治理。",
  stale: "Study 输入已变更，旧 Run/Report 尚未重生成。",
  "scientific-limit": "固定 Study 已给出科研边界，无需继续尝试。",
  "repair-required": "最近 Run 在失败处置上需要修复或重新审视。",
};

const GATE_DETAILS = {
  passed: "因子证据已经通过，可以进入组合研究。",
  "waiting-current-evidence": "当前因子定义还没有对应的有效证据。",
  "waiting-current-report": "验证已经完成，仍需冻结成研究结论。",
  "blocked-upstream-evidence": "因子的样本外预测证据不足，先回到假设或定义继续研究。",
  "blocked-selection-adjusted-evidence": "选择校正尚未通过，不能进入组合研究。",
  "blocked-scientific-limit": "当前方法已经触及科学边界，继续搜索没有依据。",
  "blocked-failed-evidence": "最近验证失败，先修复证据问题。",
};

const GATE_LABELS = {
  passed: "可以进入组合研究",
  "waiting-current-evidence": "等待当前因子证据",
  "waiting-current-report": "等待冻结研究结论",
  "blocked-upstream-evidence": "样本外证据不足",
  "blocked-selection-adjusted-evidence": "选择校正未通过",
  "blocked-scientific-limit": "已触及科学边界",
  "blocked-failed-evidence": "最近验证失败",
};

const PROGRAM_STAGE_LABELS = {
  "factor-evidence-required": "先完成因子证据",
  "portfolio-evidence-required": "再完成组合证据",
  "optional-rl-in-progress": "正在进行可选 RL 挑战",
  "required-research-complete": "必需研究已经完成",
};

const ACTION_LABELS = {
  "session.start": "开始下一轮因子研究",
  "session.complete": "完成本轮因子研究",
  "run.execute": "生成新的验证证据",
  "run.show": "查看最新证据",
  "report.publish": "冻结研究结论",
  "report.show": "查看研究结论",
  "study.inspect": "检查因子定义",
};

function formatNumber(value, digits = 4) {
  return Number.isFinite(value) ? value.toFixed(digits) : "—";
}

function formatPercent(value, digits = 1) {
  return Number.isFinite(value) ? `${(value * 100).toFixed(digits)}%` : "—";
}

function formatDate(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toISOString().slice(0, 10);
}

function trimHash(hash, length = 12) {
  if (!hash) return "unavailable";
  return hash.length > length ? `${hash.slice(0, length)}…` : hash;
}

function datasetLabel(dataset) {
  return dataset ? `${dataset.id || "未声明"}@${dataset.version || "未声明"}` : "未声明";
}

export function FactorManagement() {
  const { source, demoEnabled, factor } = useStudio();
  const connected = source.mode === "connected" && !demoEnabled;
  const project = connected ? source.snapshot?.projects?.[0] : null;
  const view = project ? projectFactorManagement(project) : null;

  if (!connected) {
    return (
      <PageHeading
        eyebrow="Factor Research / CORE PROJECTION"
        title="因子研究"
        description="仅读取 loopback Core Studio snapshot；本视图不进入演示数据。"
      />
    );
  }

  if (!project || !view) {
    return (
      <>
        <PageHeading
          eyebrow="Factor Research / CORE PROJECTION"
          title="因子研究"
          description="等待首个连接的 Project。所有记录均来自 Core 验证，不可伪造。"
          actions={<ButtonLink href="/lab">进入因子实验室</ButtonLink>}
        />
        <EmptyState title="尚未连接 Project" detail="Core snapshot 中没有可读 Project；先创建或选择一个 Project 再返回。" />
      </>
    );
  }

  const phase = view.status.phase;
  const phaseLabel = PHASE_LABELS[phase] || phase;
  const phaseDetail = PHASE_DETAILS[phase] || "等待 Core 给出明确的 Factor 阶段投影。";
  const study = view.study;
  const dataset = study?.dataset;
  const gates = view.gates.factorToPortfolio;
  const gateLabel = "因子证据 → 组合研究";
  const sessionLabel = view.progress.laneLatestSession
    ? `${view.progress.laneLatestSession.id} · ${view.progress.laneLatestSession.status}`
    : "未声明";

  return (
    <>
      <PageHeading
        eyebrow="因子研究 / 已连接真实证据"
        title="因子研究"
        description="看清这个因子在研究什么、用了哪些数据、当前证据是否可信，以及下一步该做什么。"
        actions={
          <>
            <ButtonLink href="/lab">因子实验室</ButtonLink>
            <ButtonLink href="/results">测试结果</ButtonLink>
            <ButtonLink variant="quiet" href={`/factors/${factor.id}`}>因子护照</ButtonLink>
          </>
        }
      />

      <div className="trust-strip" aria-label="因子研究边界">
        <div className="trust-item"><span>因子版本</span><strong className="mono">{study?.id || view.factorDefinition.studyId || "未声明"}</strong></div>
        <div className="trust-item"><span>数据版本</span><strong>{datasetLabel(dataset)}</strong></div>
        <div className="trust-item"><span>研究计划</span><strong>{view.programAvailable ? "已连接" : "未声明"}</strong></div>
        <div className={`trust-item ${view.status.tone === "known" ? "" : "warning"}`}><span>当前进度</span><strong>{phaseLabel}</strong></div>
      </div>

      <div className="metric-row" aria-label="因子证据概览">
        <Metric label="研究进度" value={phaseLabel} detail={phaseDetail} tone={view.status.tone === "known" ? "positive" : "warning"} />
        <Metric
          label="样本外相关性"
          value={formatNumber(view.evidence.validationMeanIc, 6)}
          detail={`${view.evidence.primaryMetric || "Core 未声明指标"} · run ${view.evidence.runId || "无"}`}
        />
        <Metric
          label="覆盖与可用"
          value={formatPercent(view.evidence.meanCoverage)}
          detail={Number.isFinite(view.evidence.observationCoverage) ? `observation ${formatPercent(view.evidence.observationCoverage)}` : "Core 未提供 availability"}
        />
        <Metric
          label="最新证据"
          value={view.status.currentRun ? "OK" : view.evidence.runStatus || "—"}
          detail={view.evidence.runId ? trimHash(view.evidence.runId, 16) : "无不可变 Factor Run"}
        />
        <Metric
          label="研究记录"
          value={view.status.currentReportId ? trimHash(view.status.currentReportId, 12) : "—"}
          detail={`Sessions ${view.progress.activeSessions} active · ${view.progress.completedSessions} closed`}
        />
      </div>

      <div className="result-grid">
        <div className="stack">
          <Panel title="这个因子在研究什么" meta={study ? "定义、数据与验证目标" : "等待研究定义"}>
            {study ? (
              <div className="field-grid">
                <div><span className="field-label">因子版本</span><span className="field-value mono">{study.id}</span></div>
                <div><span className="field-label">研究类型</span><span className="field-value">{view.factorDefinition.subjectKind}</span></div>
                <div><span className="field-label">研究假设</span><span className="field-value">{view.factorDefinition.description || "尚未写明"}</span></div>
                <div><span className="field-label">判定指标</span><span className="field-value">{study.objective ? `${study.objective.metric || "—"} · ${study.objective.direction || "—"}` : "尚未写明"}</span></div>
                <div><span className="field-label">最低改进门槛</span><span className="field-value">{Number.isFinite(study.objective?.minimumImprovement) ? study.objective.minimumImprovement : "尚未写明"}</span></div>
                <div><span className="field-label">数据版本</span><span className="field-value">{datasetLabel(dataset)}</span></div>
                <div><span className="field-label">历史区间</span><span className="field-value">{study.datasetTimeRange ? `${study.datasetTimeRange.start || "—"} → ${study.datasetTimeRange.end || "—"}` : "尚未写明"}</span></div>
                <div><span className="field-label">资产类型</span><span className="field-value">{dataset?.assetClass || "未声明"}</span></div>
                <div><span className="field-label">研究标的</span><span className="field-value">{dataset?.universe?.length || 0} · {dataset?.universe?.slice(0, 6).join(", ") || "未声明"}</span></div>
                <details className="dense-row">
                  <summary><strong>技术细节</strong></summary>
                  <div className="field-grid" style={{ marginTop: 8 }}>
                    <div><span className="field-label">Study inputHash</span><span className="field-value mono">{trimHash(study.inputHash)}</span></div>
                    <div><span className="field-label">Source hash</span><span className="field-value mono">{trimHash(study.sourceHash)}</span></div>
                    <div><span className="field-label">Dependency hash</span><span className="field-value mono">{trimHash(study.dependencyHash)}</span></div>
                    <div><span className="field-label">Dataset hash</span><span className="field-value mono">{trimHash(study.datasetHash)}</span></div>
                    <div><span className="field-label">可编辑路径</span><span className="field-value">{view.dependencies.editableCount}</span></div>
                    <div><span className="field-label">依赖路径</span><span className="field-value">{view.dependencies.dependencyCount}</span></div>
                  </div>
                </details>
              </div>
            ) : (
              <EmptyState title="Factor lane 未在 Research Program 中声明" detail="研究 Program 没有 id=“factor” 的 lane；管理面不依赖 Studio 临时计算。" />
            )}
          </Panel>

          <Panel title="为什么停在这里" meta={GATE_LABELS[gates?.status] || "等待验证状态"}>
            <div className="dense-list">
              <div className="dense-row">
                <div>
                  <strong>整条研究链的进度</strong>
                  <p>{PROGRAM_STAGE_LABELS[view.program?.stage] || "等待系统给出研究顺序"}</p>
                  {view.program?.stage || view.program?.method ? (
                    <details><summary className="muted">技术细节</summary><p>{view.program?.stage || "未声明"} · {view.program?.method || "尚未声明验证方法"}</p></details>
                  ) : null}
                </div>
                <StatusChip state={view.program?.stage ? "partial" : "missing"}>{PROGRAM_STAGE_LABELS[view.program?.stage] || "等待研究计划"}</StatusChip>
              </div>
              <div className="dense-row">
                <div>
                  <strong>{gateLabel}</strong>
                  <p>{GATE_DETAILS[gates?.status] || "等待系统给出明确的验证状态。"}</p>
                  {gates?.explanation ? (
                    <details><summary className="muted">技术细节</summary><p>{gates.explanation}</p></details>
                  ) : null}
                </div>
                <StatusChip state={gates?.status ? "partial" : "missing"}>{GATE_LABELS[gates?.status] || "等待验证"}</StatusChip>
              </div>
              <div className="dense-row">
                <div>
                  <strong>建议下一步</strong>
                  <p>{ACTION_LABELS[view.recommendedAction?.id] || "当前没有待执行动作"}</p>
                  {view.recommendedAction?.description ? (
                    <details><summary className="muted">技术操作</summary><p>{view.recommendedAction.description}</p></details>
                  ) : null}
                </div>
                <StatusChip state={view.recommendedAction?.id ? "partial" : "missing"}>{view.recommendedAction?.id ? "可执行" : "无待办"}</StatusChip>
              </div>
            </div>
            {view.warnings.length ? (
              <details className="notice" style={{ marginTop: 10 }}><summary><strong>研究约束与技术告警</strong></summary><p>{view.warnings.join(" · ")}</p></details>
            ) : null}
            <div style={{ marginTop: 12 }} className="button-row">
              {view.recommendedAction?.id ? <ButtonLink href="/lab">在因子实验室中执行</ButtonLink> : null}
              <ButtonLink variant="quiet" href="/results">查看结果</ButtonLink>
            </div>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="研究证据" meta={view.evidence.runId ? "每次结果都可追溯、不可改写" : "等待第一份因子证据"}>
            {view.evidence.runId ? (
              <div className="provenance-card">
                <StatusChip state={view.status.currentRun ? "known" : "delayed"}>{view.status.currentRun ? "current" : "历史"}</StatusChip>
                <strong className="mono">{view.evidence.runId}</strong>
                <span className="field-value">validation mean IC {formatNumber(view.evidence.validationMeanIc, 6)} · ICIR {formatNumber(view.evidence.validationIcir)} · HAC t {formatNumber(view.evidence.validationHacT, 3)}</span>
                <span className="field-value">coverage {formatPercent(view.evidence.meanCoverage)} · turnover {formatNumber(view.evidence.meanRankTurnover, 3)}</span>
                <span className="field-value mono">input:{trimHash(study?.inputHash)} · source:{trimHash(study?.sourceHash)}</span>
                {view.status.currentReportId ? (
                  <span className="field-value mono">Report: {view.status.currentReportId}</span>
                ) : (
                  <span className="field-value">当前没有冻结当前 Run 的不可变 Report</span>
                )}
              </div>
            ) : (
              <EmptyState title="尚无不可变 Factor Run" detail="在 factor lane 出现第一个 Run 之前，evidence 覆盖与统计裁决都不可信。" />
            )}
          </Panel>

          <Panel title="Session / Campaign 进度" meta="区分不可变证据与可变活动">
            <div className="dense-list">
              <div className="dense-row">
                <div><strong>当前 Session</strong><p>{sessionLabel}</p></div>
                <StatusChip state={view.progress.laneLatestSessionActive ? "delayed" : "partial"}>
                  {view.progress.laneLatestSessionActive ? "活跃" : "无活跃 Session"}
                </StatusChip>
              </div>
              <div className="dense-row">
                <div><strong>实验历史 / 活跃 Campaign</strong><p>实验是不可变历史；Campaign 只统计当前活跃 Session 的进度。</p></div>
                <StatusChip state={view.progress.experimentCount || view.progress.activeCampaigns ? "delayed" : "partial"}>
                  {view.progress.experimentCount} exp · {view.progress.activeCampaigns} active camp
                </StatusChip>
              </div>
              <div className="dense-row">
                <div><strong>已关闭 Session</strong><p>其他 lane 的活动被过滤；factor lane 仅保留与 Study 对齐的 Session。</p></div>
                <StatusChip state="partial">{view.progress.completedSessions} closed</StatusChip>
              </div>
            </div>
            {view.immutableReports.length ? (
              <DataTable minWidth={420}>
                <thead>
                  <tr><th>不可变 Report</th><th>Study</th><th>Leader Run</th><th>发布</th></tr>
                </thead>
                <tbody>
                  {view.immutableReports.slice(0, 6).map((report) => (
                    <tr key={`${report.source}-${report.id || report.publishedAt}`}>
                      <td className="mono">{report.id || "—"}</td>
                      <td className="mono">{report.studyId || "—"}</td>
                      <td className="mono">{report.leaderRunId || "—"}</td>
                      <td>{formatDate(report.publishedAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </DataTable>
            ) : (
              <p className="muted" style={{ marginTop: 8 }}>研究 Program 暂未声明任何 Report。</p>
            )}
          </Panel>

          <Panel title="适用范围与可信度" meta="哪些标的参与预测，以及当前证据是否够资格">
            <div className="dense-list">
              <div className="dense-row">
                <div>
                  <strong>预测资产 / 上下文资产</strong>
                  <p>{view.cohorts?.available ? `${view.cohorts.predictionAssets.length} pred · ${view.cohorts.contextAssets.length} ctx · mode ${view.cohorts.evaluationMode || "—"}` : "Cohort 待 Core 投影"}</p>
                </div>
                <StatusChip state={view.cohorts?.available ? "known" : "missing"}>{view.cohorts?.available ? "available" : "no-cohort"}</StatusChip>
              </div>
              <div className="dense-row">
                <div><strong>Qualification 阶段</strong><p>{view.evidence.qualificationStage || "未声明"} · {view.evidence.qualificationExplanation || "待 Core 给出资格裁决"}</p></div>
                <StatusChip state={view.evidence.qualificationAvailable ? "known" : "missing"}>{view.evidence.qualificationAvailable ? "qualification available" : "no-qualification"}</StatusChip>
              </div>
              <div className="dense-row">
                <div>
                  <strong>Validation 最弱 fold</strong>
                  <p>candidate {view.evidence.weakestCandidateFoldId || "—"} = {formatNumber(view.evidence.weakestCandidateFoldIc)} · style-neutral {view.evidence.weakestStyleNeutralFoldId || "—"} = {formatNumber(view.evidence.weakestStyleNeutralFoldIc)}</p>
                </div>
                <StatusChip state="partial">chronological</StatusChip>
              </div>
            </div>
            {view.evidence.warning ? (
              <div className="notice" style={{ marginTop: 10 }}><strong>选择边界：</strong> {view.evidence.warning}</div>
            ) : null}
          </Panel>
        </div>
      </div>

      <Panel title="继续查看" meta="从管理页进入实验、结果、护照与复现证据">
        <ObjectLink href="/lab" label="FactorLab" id={factor.id} />
        <ObjectLink href="/results" label="Run/Report" id={view.status.currentReportId || "autoquant-research-report"} />
        <ObjectLink href={`/factors/${factor.id}`} label="FactorPassport" id={factor.id} />
        <ObjectLink href="/audit" label="Audit" id="harness" />
      </Panel>
    </>
  );
}
