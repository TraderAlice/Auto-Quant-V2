"use client";

import { useStudio } from "@/components/studio-context";
import { ButtonLink, EmptyState, Metric, ObjectLink, PageHeading, Panel, StatusChip } from "@/components/ui";
import { strategyManagementFromProject } from "@/lib/strategy-management";

const PHASE_LABELS = {
  "not-started": { state: "missing", label: "未开始" },
  "baseline-ready": { state: "partial", label: "基线就绪" },
  researching: { state: "delayed", label: "研究中" },
  reported: { state: "known", label: "已裁决" },
  stale: { state: "delayed", label: "待更新" },
  "scientific-limit": { state: "restricted", label: "科学极限" },
  "repair-required": { state: "missing", label: "需要修复" },
};

const STAGE_LABELS = {
  "factor-evidence-required": { state: "delayed", label: "等待因子证据" },
  "portfolio-evidence-required": { state: "delayed", label: "等待组合证据" },
  "optional-rl-in-progress": { state: "partial", label: "可选 RL 进行中" },
  "required-research-complete": { state: "known", label: "必需研究完成" },
};

const GATE_LABELS = {
  passed: { state: "known", label: "通过" },
  "waiting-current-evidence": { state: "delayed", label: "等待当前证据" },
  "waiting-current-report": { state: "delayed", label: "等待当前裁决" },
  "blocked-prerequisite": { state: "restricted", label: "前置受阻" },
  "blocked-upstream-evidence": { state: "missing", label: "上游证据不足" },
  "blocked-selection-adjusted-evidence": { state: "missing", label: "选择校正未通过" },
  "blocked-legacy-evidence": { state: "restricted", label: "历史证据不重组" },
  "blocked-scientific-limit": { state: "restricted", label: "科学极限" },
  "blocked-failed-evidence": { state: "missing", label: "失败证据" },
};

const GATE_NAMES = {
  "factor-to-portfolio": "因子证据 → 组合研究",
  "portfolio-to-rl": "组合证据 → RL 挑战",
};

const GATE_DETAILS = {
  passed: "上一步已经形成当前有效证据，可以进入下一项验证。",
  "waiting-current-evidence": "当前定义还没有对应的有效证据。",
  "waiting-current-report": "验证已经完成，仍需冻结成研究结论。",
  "blocked-prerequisite": "前一步尚未通过，当前研究暂不启动。",
  "blocked-upstream-evidence": "上游证据不足，先回到因子研究解决。",
  "blocked-selection-adjusted-evidence": "选择校正尚未通过，不能继续扩大研究。",
  "blocked-legacy-evidence": "历史证据与当前定义不一致，需要重新验证。",
  "blocked-scientific-limit": "当前方法已经触及科学边界，继续搜索没有依据。",
  "blocked-failed-evidence": "最近验证失败，先修复证据问题。",
};

const LANE_LABELS = {
  factor: "因子研究",
  portfolio: "组合研究",
  rl: "RL 挑战",
};

const ACTION_LABELS = {
  "session.start": "开始下一轮研究",
  "session.complete": "完成本轮研究",
  "run.execute": "生成新的验证证据",
  "run.show": "查看最新证据",
  "report.publish": "冻结研究结论",
  "report.show": "查看研究结论",
  "study.inspect": "检查研究定义",
};

const EFFECT_LABELS = {
  "creates-artifact": "会生成新的研究证据",
  "read-only": "只查看现有证据",
};

function formatNumber(value, digits = 6) {
  return Number.isFinite(value) ? value.toFixed(digits) : "—";
}

function LanePanel({ lane, title, meta, focusLink, footer }) {
  const editablePaths = lane.editablePaths || [];
  const commands = lane.commands || [];
  const phaseMeta = PHASE_LABELS[lane.phase] || { state: "partial", label: lane.phase || "未知" };
  return (
    <Panel title={title} meta={meta}>
      <div className="field-grid">
        <div><span className="field-label">研究项</span><span className="field-value mono">{lane.studyId || "未声明"}</span></div>
        <div><span className="field-label">当前状态</span><span className="field-value"><StatusChip state={phaseMeta.state}>{phaseMeta.label}</StatusChip></span></div>
        <div><span className="field-label">本轮证据</span><span className="field-value">{lane.currentAttempt ? "与当前定义一致" : "需要更新"}</span></div>
        <div><span className="field-label">验证结果</span><span className="field-value">{lane.currentRun ? "已生成" : (lane.latestRun?.status || "无")}</span></div>
        <div><span className="field-label">证据版本</span><span className="field-value mono">{lane.latestRun?.id || "—"}</span></div>
        <div><span className="field-label">研究会话</span><span className="field-value mono">{lane.latestSession?.id || "—"}</span></div>
        <div><span className="field-label">主要结果</span><span className="field-value mono">{formatNumber(lane.primaryValue)}</span></div>
        <div><span className="field-label">报告 / 会话</span><span className="field-value">{lane.reportCount} / {lane.sessionCount ?? "—"}</span></div>
      </div>
      <div className="tag-list" style={{ marginTop: 10 }}>
        {editablePaths.map((path) => <span className="tag" key={path}>{path}</span>)}
        {lane.optional ? <StatusChip state="partial">RL 可选</StatusChip> : null}
      </div>
      {focusLink}
      {commands.length ? (
        <details className="dense-row" style={{ paddingTop: 6 }}>
          <summary><strong>技术操作</strong></summary>
          <ol className="field-value mono" style={{ paddingLeft: 18 }}>
            {commands.map((command) => <li key={`${command.id}-${command.argv?.join(" ")}`}><span className="muted">{command.id} · </span>{command.display}</li>)}
          </ol>
        </details>
      ) : null}
      {footer}
    </Panel>
  );
}

export function StrategyManagement() {
  const { source, demoEnabled } = useStudio();
  const project = source?.snapshot?.projects?.[0] || null;
  const view = strategyManagementFromProject(project);
  const coreConnected = source?.mode === "connected" && !demoEnabled;

  if (!coreConnected) {
    return (
      <EmptyState
        title="策略研究等待 Core 投影"
        detail="连接 Core 后，这里会汇总因子组合、组合规则、ML/RL 验证与可复现产物。"
      >
        <ButtonLink variant="quiet" href="/portfolio">查看组合证据</ButtonLink>
        <ButtonLink variant="quiet" href="/rl">查看 RL 证据</ButtonLink>
      </EmptyState>
    );
  }

  const portfolio = view.portfolio;
  const rl = view.rl;
  const progression = view.progression;
  const recommended = view.recommended;
  const dossier = view.dossier;
  const composition = view.composition;
  const model = view.model;
  const holdout = view.holdout;
  const stageMeta = STAGE_LABELS[progression.stage] || { state: "partial", label: progression.stage || "未声明" };
  const focusGate = progression.gates.find((gate) => gate.status !== "passed");

  return (
    <>
      <PageHeading
        eyebrow="策略研究 / 已连接真实证据"
        title="策略研究"
        description="把候选因子组合成可验证的策略方案，并分别检查组合规则、ML、RL、成本、风险和样本外证据。"
        actions={
          <>
            <ButtonLink href="/portfolio">查看组合证据</ButtonLink>
            <ButtonLink href="/rl">查看 RL 证据</ButtonLink>
          </>
        }
      />

      <div className="trust-strip" aria-label="策略研究边界">
        <div className="trust-item"><span>研究项目</span><strong className="mono">{view.projectId || "—"}</strong></div>
        <div className="trust-item"><span>验证方法</span><strong>{progression.selectionSplit ? "验证集决定，测试集只审计" : "未声明"}</strong></div>
        <div className="trust-item"><span>当前进度</span><strong><StatusChip state={stageMeta.state}>{stageMeta.label}</StatusChip></strong></div>
        <div className={`trust-item ${dossier.available ? "" : "warning"}`}><span>研究档案</span><strong>{dossier.available ? "已连接" : "未生成"}</strong></div>
        <div className={`trust-item ${holdout.available ? "" : "warning"}`}><span>独立样本</span><strong>{holdout.state || "未绑定"}</strong></div>
      </div>

      <div className="metric-row" aria-label="策略研究汇总">
        <Metric label="研究链进度" value={stageMeta.label} detail={`当前关注：${LANE_LABELS[progression.focusLaneId] || "等待决定"}`} tone={progression.stage === "required-research-complete" ? "positive" : "warning"} />
        <Metric label="组合验证" value={PHASE_LABELS[portfolio.phase]?.label || "未声明"} detail={portfolio.latestRun?.id || "尚无证据"} tone={portfolio.currentRun ? "positive" : "warning"} />
        <Metric label="RL 验证" value={PHASE_LABELS[rl.phase]?.label || "未声明"} detail={rl.latestRun?.id || (rl.optional ? "可选研究" : "尚无证据")} tone={rl.currentRun ? "positive" : "warning"} />
        <Metric label="研究工件" value={String(portfolio.artifactCount + rl.artifactCount)} detail={`${view.artifacts.reports} 份报告 · ${view.artifacts.explorations} 组深度诊断`} />
      </div>

      <div className="result-grid">
        <div className="stack">
          <Panel title="验证顺序" meta={progression.selectionSplit ? "只用验证集决定下一步" : "等待验证规则"}>
            <div className="dense-list">
              {progression.gates.length ? progression.gates.map((gate) => {
                const gateMeta = GATE_LABELS[gate.status] || { state: "partial", label: gate.status || "未声明" };
                return (
                  <div className="dense-row" key={gate.id}>
                    <div>
                      <strong>{GATE_NAMES[gate.id] || gate.id}</strong>
                      <p>{GATE_DETAILS[gate.status] || "等待系统给出明确的验证状态。"}</p>
                      <details>
                        <summary className="muted">技术细节</summary>
                        <p>{gate.explanation}</p>
                        <small className="muted">stage {gate.requiredStage} · {gate.runId ? `run ${gate.runId}` : "无 Run"} · {gate.reportId ? `report ${gate.reportId}` : "无裁决"}</small>
                      </details>
                    </div>
                    <StatusChip state={gateMeta.state}>{gateMeta.label}</StatusChip>
                  </div>
                );
              }) : <EmptyState title="门禁未声明" detail="等待 Core 投影研究程序进展。" />}
            </div>
            <div className="notice" style={{ marginTop: 10 }}><strong>当前解释：</strong> {GATE_DETAILS[focusGate?.status] || "等待系统给出明确的验证状态。"}</div>
          </Panel>

          <LanePanel
            lane={portfolio}
            title="组合研究 · 因子到组合的固定通道"
            meta={`主要指标：${portfolio.primaryMetric || "—"}`}
            focusLink={(
              <div className="button-row" style={{ marginTop: 10 }}>
                <ButtonLink href="/portfolio">打开组合证据</ButtonLink>
                <ButtonLink variant="quiet" href="/results">查看因子证据</ButtonLink>
              </div>
            )}
            footer={
              <div className="notice" style={{ marginTop: 10 }}>
                <strong>组合验证：</strong> {portfolio.liquidityCapacity ? "成本与容量证据已由 Core 投影。" : "等待实际调仓路径上的成本与容量证据。"}
              </div>
            }
          />

          <LanePanel
            lane={rl}
            title="治理式 RL · 可选的政策挑战"
            meta={`${rl.optional ? "可选" : "必选"} · ${rl.seedCount} seeds / ${rl.foldCount} folds`}
            focusLink={(
              <div className="button-row" style={{ marginTop: 10 }}>
                <ButtonLink href="/rl">打开 RL 证据</ButtonLink>
                <ButtonLink variant="quiet" href="/audit">检查 Core 诊断</ButtonLink>
              </div>
            )}
            footer={
              <div className="notice" style={{ marginTop: 10 }}>
                <strong>RL value-add：</strong>{" "}
                {typeof rl.rlValueAdded === "boolean"
                  ? (rl.rlValueAdded
                    ? `RL 在 validation 上相对最佳基线展示净优势 ${formatNumber(rl.meanValidationAdvantage)}`
                    : "RL 尚未在 validation 上证明对最佳固定基线的净优势。")
                  : "RL value-add 证据等待 Core 投影。"}
              </div>
            }
          />
        </div>

        <div className="stack">
          <Panel title="因子如何进入策略" meta="依赖关系由研究计划锁定">
            <div className="notice"><strong>固定关系：</strong>组合研究使用同一候选因子；RL 挑战继续使用同一因子与组合约束，页面不会临时改写。</div>
            <details className="dense-row" style={{ marginTop: 10 }}>
              <summary><strong>技术细节：固定依赖契约</strong></summary>
              <div className="field-grid" style={{ marginTop: 8 }}>
              <div><span className="field-label">Factor → Portfolio</span><span className="field-value mono">{composition?.factorToPortfolio || "未声明"}</span></div>
              <div><span className="field-label">Portfolio → RL</span><span className="field-value mono">{composition?.rlFactorDependency || "未声明"}</span></div>
              <div><span className="field-label">Portfolio mandate</span><span className="field-value mono">{composition?.portfolioMandate || "未声明"}</span></div>
              <div><span className="field-label">Factor prediction universe</span><span className="field-value mono">{composition?.factorPredictionUniverse || "未声明"}</span></div>
              <div><span className="field-label">Research horizon</span><span className="field-value mono">{composition?.researchHorizon || "未声明"}</span></div>
              <div><span className="field-label">Factor claim authority</span><span className="field-value mono">{composition?.factorClaim || "未声明"}</span></div>
              <div><span className="field-label">Lane selection split</span><span className="field-value mono">{progression.selectionSplit || "未声明"}</span></div>
              </div>
            </details>
            <div className="dense-list" style={{ marginTop: 10 }}>
              {view.laneBoundaries.length ? view.laneBoundaries.map((lane) => (
                <div className="dense-row" key={lane.id}>
                  <div>
                    <strong>{LANE_LABELS[lane.id] || lane.name}</strong>
                    <p>{lane.studyId}</p>
                    <small className="muted">depends: {lane.dependsOn.length ? lane.dependsOn.join(", ") : "—"} · editable: {lane.editablePaths.join(", ") || "—"}</small>
                  </div>
                  <StatusChip state={lane.optional ? "partial" : "known"}>{lane.optional ? "可选" : "必选"}</StatusChip>
                </div>
              )) : <EmptyState title="研究通道未声明" detail="等待 Core researchProgramStatus.manifest。" />}
            </div>
          </Panel>

          <Panel title="建议下一步" meta="来自验证状态，不由页面猜测">
            {recommended.available && recommended.command ? (
              <div className="provenance-card">
                <StatusChip state="known">{EFFECT_LABELS[recommended.command.effect] || "系统建议"}</StatusChip>
                <strong>{ACTION_LABELS[recommended.command.id] || "查看系统建议"}</strong>
                <small className="muted">研究环节：{LANE_LABELS[recommended.laneId] || "未声明"}</small>
                <details>
                  <summary className="muted">技术操作</summary>
                  <p className="field-value">{recommended.command.description}</p>
                  <code className="field-value mono">{recommended.command.display}</code>
                </details>
              </div>
            ) : (
              <EmptyState
                title="无推荐动作"
                detail={progression.stage === "required-research-complete" ? "必需研究已完成；可选 RL 由 Agent 决定是否启动。" : "等待 Core 投影出下一条研究动作。"}
              />
            )}
          </Panel>

          <Panel title="ML / RL 研究产物" meta="模型选择、固定 holdout 与工件清单">
            <div className="field-grid">
              <div><span className="field-label">ML 研究环境</span><span className="field-value">{model.available ? "可用" : "未投影"}</span></div>
              <div><span className="field-label">候选模型</span><span className="field-value">{model.candidates.join(" / ") || "未声明"}</span></div>
              <div><span className="field-label">选模规则</span><span className="field-value mono">{model.selectionAuthority || "未声明"}</span></div>
              <div><span className="field-label">测试集用途</span><span className="field-value mono">{model.testUse || "未声明"}</span></div>
              <div><span className="field-label">最新模型 Run</span><span className="field-value mono">{model.latestRun?.id || "—"}</span></div>
              <div><span className="field-label">已选模型</span><span className="field-value">{model.selectedModel || "—"}</span></div>
              <div><span className="field-label">独立留出样本</span><span className="field-value">{holdout.state || "未绑定"}</span></div>
              <div><span className="field-label">工件</span><span className="field-value">Portfolio {portfolio.artifactCount} · RL {rl.artifactCount}</span></div>
            </div>
          </Panel>

          <Panel title="继续查看" meta="进入因子、组合、RL 与复现证据">
            <ObjectLink href="/results" label="因子证据" id="ohlcv-factor-quality" />
            <ObjectLink href="/portfolio" label="组合证据" id={portfolio.studyId} />
            <ObjectLink href="/rl" label="RL 策略证据" id={rl.studyId} />
            <ObjectLink href="/audit" label="审计与复现" id="core-source-chain" />
          </Panel>

          <Panel title="研究档案状态" meta="可以交付和复现的证据包">
            {dossier.available ? (
              <div className="provenance-card">
                <StatusChip state={dossier.ready ? "known" : "partial"}>{dossier.ready ? "已就绪" : "未就绪"}</StatusChip>
                <strong>{dossier.latestDossier?.id || "项目研究档案"}</strong>
                <small className="muted">已包含 {dossier.includedLaneIds?.map((id) => LANE_LABELS[id] || id).join("、") || "—"} · 暂不包含 {dossier.omittedOptionalLanes?.map((item) => LANE_LABELS[item?.id || item] || item?.id || item).join("、") || "—"}</small>
                <small className="muted">{dossier.blockers.length ? `${dossier.blockers.length} 个阻塞项` : "无阻塞项"}</small>
              </div>
            ) : (
              <EmptyState title="无 Dossier 投影" detail="等待 Core 投影项目级 Dossier；本页不创建新结论。" />
            )}
          </Panel>
        </div>
      </div>
    </>
  );
}
