"use client";

import { FactorIcChart, PerformanceChart } from "@/components/charts";
import { useStudio } from "@/components/studio-context";
import { diagnostics, factor, metrics } from "@/lib/data";
import { ButtonLink, DataTable, EmptyState, Metric, PageHeading, Panel, StatusChip } from "@/components/ui";
import { ClaimVerificationForm } from "@/components/claim-verification-form";
import { factorVerificationFrom } from "@/lib/verification";

const buckets = [
  ["D1", "-7.8%", "-0.62", "19.4%"],
  ["D2", "-3.1%", "-0.24", "20.7%"],
  ["D3", "-0.7%", "-0.05", "22.1%"],
  ["D4", "+2.4%", "+0.18", "25.8%"],
  ["D5", "+10.8%", "+0.73", "29.2%"],
];

export default function ResultsPage() {
  const { source, demoEnabled } = useStudio();

  if (source.mode === "connected" && !demoEnabled) {
    const snapshot = source.snapshot;
    const project = snapshot.projects[0];
    const coreDiagnostics = [...snapshot.diagnostics, ...(project?.diagnostics || [])];
    const explorer = project?.factorExplorer;
    const run = explorer?.run;
    const summary = explorer?.summary;
    const verification = factorVerificationFrom(project, snapshot.diagnostics);
    const publishedVerification = project?.verificationAssessments?.at(-1) || null;
    const verifiedRuns = (project?.runs || []).filter((item) => item.studyId === run?.studyId).length;
    const quantiles = (explorer?.quantileSummary || []).filter((item) => item.role === "selection");
    const percent = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : "—";
    const decimal = (value) => Number.isFinite(value) ? value.toFixed(4) : "—";

    return (
      <>
        <PageHeading
          eyebrow="Experiment results / CORE PROJECTION"
          title="测试结果"
          description="结果工作区保持完整；只有通过 Core 校验的不可变 ExperimentRun 才能填充指标、图表与复现声明。"
          actions={<ButtonLink href="/lab">复制为新实验</ButtonLink>}
        />

        <div className="metric-row" aria-label="验证结果指标">
          <Metric label="Validation Rank IC" value={decimal(summary?.validation?.meanRankIc)} detail={`${summary?.validation?.observations || 0} observations`} tone={run ? "positive" : "warning"} />
          <Metric label="Validation ICIR" value={decimal(summary?.validation?.rankIcir)} detail={`HAC t=${decimal(summary?.validation?.hacTStatistic)}`} />
          <Metric label="Test audit Rank IC" value={decimal(summary?.testAudit?.meanRankIc)} detail="visible audit · not selection" />
          <Metric label="Coverage" value={percent(summary?.meanCoverage)} detail={`${explorer?.coverage?.length || 0} assets`} />
          <Metric label="Rank turnover" value={percent(summary?.meanRankTurnover)} detail="Core factor evidence" />
        </div>

        <div className="result-grid">
          <div className="stack">
            <Panel title="Rank IC 路径" meta={explorer?.icPath ? `${explorer.icPath.sampledRows}/${explorer.icPath.totalRows} deterministic samples` : "等待 Core Factor Explorer 投影"}>
              {explorer?.icPath ? <FactorIcChart path={explorer.icPath} /> : <EmptyState title="尚无可展示的验证结果" detail="未验证或被篡改的 Run 不会进入图表。" />}
            </Panel>
            <Panel title="Validation 分组单调性" meta="同一不可变 Run · selection split">
              {quantiles.length ? (
                <DataTable>
                    <thead><tr><th>Horizon</th><th>Low</th><th>Middle</th><th>High</th><th>H-L</th><th>Mono</th></tr></thead>
                    <tbody>{quantiles.map((row) => <tr key={row.horizon}><td className="mono">H{row.horizon}</td><td className="numeric mono">{percent(row.low)}</td><td className="numeric mono">{percent(row.middle)}</td><td className="numeric mono">{percent(row.high)}</td><td className="numeric mono">{percent(row.highMinusLow)}</td><td className="numeric mono">{decimal(row.monotonicity)}</td></tr>)}</tbody>
                </DataTable>
              ) : <EmptyState title="分组诊断不可用" detail="Core 未返回 validation quantile evidence。" />}
            </Panel>
          </div>

          <div className="stack">
            <ClaimVerificationForm projectId={project?.id} runId={run?.id} />
            {publishedVerification ? (
              <Panel title="最新外部声明裁决" meta="Core immutable VerificationAssessment">
                <div className="provenance-card">
                  <StatusChip state={publishedVerification.assessment.verdict === "supported" ? "known" : publishedVerification.assessment.verdict === "contradicted" ? "missing" : "partial"}>{publishedVerification.assessment.verdict}</StatusChip>
                  <strong>{publishedVerification.claim.statement}</strong>
                  <span className="mono">{publishedVerification.assessment.id}</span>
                  <span>{publishedVerification.assessment.limitations.length ? publishedVerification.assessment.limitations.join(" · ") : "全部声明门禁通过"}</span>
                </div>
              </Panel>
            ) : null}
            <Panel title="因子证据裁决" meta="只裁决 Core 已验证证据；缺失项不作推断">
              <div className="dense-list">
                <div className="dense-row">
                  <div><strong>{verification.verdict.label}</strong><p>{verification.verdict.detail}</p></div>
                  <StatusChip state={verification.verdict.state}>{verification.verdict.id}</StatusChip>
                </div>
                <div className="dense-row">
                  <div><strong>Factor qualification</strong><p>{verification.qualification.available ? verification.qualification.stage : "资格证据缺失"}</p></div>
                  <StatusChip state={verification.qualification.available ? "known" : "partial"}>{verification.qualification.available ? "available" : "inconclusive"}</StatusChip>
                </div>
                <div className="dense-row">
                  <div><strong>Selection adjustment</strong><p>{verification.selection.available ? `${verification.selection.method} · ${verification.selection.uniqueTrials ?? "—"} unique trials` : "当前 Core snapshot 未提供选择调整证据"}</p></div>
                  <StatusChip state={verification.selection.passes === true ? "known" : verification.selection.passes === false ? "missing" : "partial"}>{verification.selection.passes === true ? "passes" : verification.selection.passes === false ? "fails" : "missing"}</StatusChip>
                </div>
                <div className="dense-row">
                  <div><strong>Frozen holdout</strong><p>{verification.holdout.available ? `${verification.holdout.state}${verification.holdout.assessment ? ` · ${verification.holdout.assessment}` : ""}` : "未绑定独立外部 holdout"}</p></div>
                  <StatusChip state={verification.holdout.state === "assessed" ? "known" : "partial"}>{verification.holdout.state}</StatusChip>
                </div>
                <div className="dense-row">
                  <div><strong>Trading authority</strong><p>研究证据不连接账户、订单或交易执行。</p></div>
                  <StatusChip state={verification.authority.tradingAuthority === "none" ? "known" : "restricted"}>{verification.authority.tradingAuthority || "missing"}</StatusChip>
                </div>
              </div>
            </Panel>
            <Panel title="稳健性 / Holdout 状态" meta="validation 用于诊断；test 仅作可见审计">
              {verification.robustness.available ? (
                <div className="dense-list">
                  <div className="dense-row"><div><strong>最弱 candidate fold</strong><p className="mono">{verification.robustness.weakestFoldId || "—"}</p></div><StatusChip state={Number.isFinite(verification.robustness.weakestFold) && verification.robustness.weakestFold > 0 ? "known" : "missing"}>{decimal(verification.robustness.weakestFold)}</StatusChip></div>
                  <div className="dense-row"><div><strong>最弱 style-neutral fold</strong><p className="mono">{verification.robustness.weakestNeutralFoldId || "—"}</p></div><StatusChip state={Number.isFinite(verification.robustness.weakestNeutralFold) && verification.robustness.weakestNeutralFold > 0 ? "known" : "missing"}>{decimal(verification.robustness.weakestNeutralFold)}</StatusChip></div>
                  <div className="dense-row"><div><strong>Test isolation</strong><p>test 不进入 selection 或 qualification diagnosis</p></div><StatusChip state={verification.selection.testEntersSelection === false && verification.qualification.testEntersDiagnosis === false ? "known" : "partial"}>{verification.selection.testEntersSelection === false ? "isolated" : "unknown"}</StatusChip></div>
                </div>
              ) : <EmptyState title="稳健性证据缺失" detail="Core 未返回 validation chronological fold evidence。" />}
            </Panel>
            <Panel title="诊断门禁" meta={`${coreDiagnostics.length} 条当前 Core diagnostics`}>
              {coreDiagnostics.length ? (
                <div className="dense-list">
                  {coreDiagnostics.map((item, index) => (
                    <div className="dense-row" key={`${item.code}-${item.category}-${index}`}>
                      <div><strong>{item.code}</strong><p>{item.message}</p></div>
                      <StatusChip state="missing">{item.category}</StatusChip>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="Core 校验通过" detail={run ? `${verifiedRuns} 个有效 Factor Run；最新 Run 无诊断。` : "仍需有效 ExperimentRun 才能生成结果诊断。"} />
              )}
            </Panel>
            <Panel title="复现来源" meta="当前可信闭包">
              <div className="provenance-card">
                <StatusChip state={run ? "known" : "missing"}>{run ? "Core verified" : "ExperimentRun 缺失"}</StatusChip>
                <span className="field-label">ExperimentRun</span>
                <strong className="mono">{run?.id || project?.id || "no-project"}</strong>
                <span className="field-value">{run?.studyId || "no-study"} · {run?.status || "unavailable"}</span>
                <span className="field-value mono">input:{run?.inputHash || "unavailable"}</span>
                <span className="field-value mono">source:{run?.sourceHash || "unavailable"}</span>
                <span className="field-value">AQ {snapshot.harness.version}@{snapshot.harness.commit.slice(0, 8)} · {verifiedRuns} factor runs</span>
                <ButtonLink variant="quiet" href="/audit">检查 Core 诊断</ButtonLink>
              </div>
            </Panel>
            {explorer?.warning ? <div className="notice"><strong>选择边界：</strong> {explorer.warning}</div> : null}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeading
        eyebrow="Experiment / EXP-240801-17"
        title="测试结果"
        description="成本后收益、稳健性诊断与可复现来源集中呈现。"
        actions={<ButtonLink href="/lab">复制为新实验</ButtonLink>}
      />

      <div className="metric-row">
        {metrics.map((metric) => <Metric key={metric.label} label={metric.label} value={metric.value} detail={metric.delta} tone={metric.tone} />)}
      </div>

      <div className="result-grid">
        <div className="stack">
          <Panel title="成本后多空净值" meta="2019-01-01 至 2026-07-31 · 日频再平衡">
            <PerformanceChart />
          </Panel>
          <Panel title="分组单调性" meta="按因子暴露五等分，D5 为最高暴露">
            <DataTable>
                <thead><tr><th>分组</th><th>年化收益</th><th>平均暴露</th><th>年化换手</th></tr></thead>
                <tbody>{buckets.map((row) => <tr key={row[0]}>{row.map((cell, index) => <td key={cell} className={index > 0 ? "numeric mono" : "mono"}>{cell}</td>)}</tr>)}</tbody>
            </DataTable>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="诊断门禁" meta="研究结果发布前必须解释所有注意项">
            <div className="dense-list">
              {diagnostics.map((item) => (
                <div className="dense-row" key={item.label}>
                  <div><strong>{item.label}</strong><p>{item.detail}</p></div>
                  <StatusChip state={item.state} />
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="复现来源">
            <div className="provenance-card">
              <span className="field-label">ExperimentRun</span>
              <strong className="mono">EXP-240801-17</strong>
              <span className="field-value">{factor.id} {factor.version}</span>
              <span className="field-value">{factor.frameId}</span>
              <span className="field-value">{factor.dataset}</span>
              <span className="field-value mono">exp:2cc7c1a0 · engine-0.12.4</span>
              <ButtonLink variant="quiet" href="/audit">打开审计链</ButtonLink>
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}
