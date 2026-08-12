"use client";

import { auditChain, factor } from "@/lib/data";
import { useStudio } from "@/components/studio-context";
import { EmptyState, PageHeading, Panel, StatusChip } from "@/components/ui";
import { factorVerificationFrom } from "@/lib/verification";

const checks = [
  ["因子定义已锁定", "fdef:92ae4170"],
  ["ResearchFrame 可寻址", factor.frameId],
  ["数据集校验和一致", "ds:0bf7c9d2"],
  ["回放包保留可见性原因", factor.bundleId],
  ["运行环境镜像可获得", "image-86f1"],
  ["随机种子与参数已保存", "seed: 240801"],
];

export default function AuditPage() {
  const { source, demoEnabled } = useStudio();

  if (source.mode === "connected" && !demoEnabled) {
    const snapshot = source.snapshot;
    const project = snapshot.projects[0];
    const coreDiagnostics = [...snapshot.diagnostics, ...(project?.diagnostics || [])];
    const explorer = project?.factorExplorer;
    const verification = factorVerificationFrom(project, snapshot.diagnostics);
    const reproduce = (project?.commands || []).find((item) => item.id === "run.factor" && item.effect === "read-only");
    return (
      <>
        <PageHeading eyebrow="Audit / CORE PROJECTION" title="审计与复现" description="保留可验证的 Core 来源链；没有有效 ExperimentRun 时不生成虚假的复现闭包或命令。" />
        <div className="audit-grid">
          <Panel title="来源链" meta="当前 Studio snapshot 的可信对象">
            <div className="audit-chain">
              {[
                ["Harness", `AQ ${snapshot.harness.version}`, snapshot.harness.commit.slice(0, 12)],
                ["StudioSnapshot", `schema v${snapshot.schemaVersion}`, snapshot.generatedAt],
                ["Project", project?.id || "no-project", project?.valid ? "verified" : "diagnostics"],
                ...(explorer?.run ? [["ExperimentRun", explorer.run.id, explorer.run.inputHash?.slice(0, 12) || "no input hash"], ["Dataset", explorer.dataset?.id || "unknown", explorer.dataset?.hash?.slice(0, 12) || "no dataset hash"]] : []),
                ...((project?.studies || []).map((study) => ["Study", study.id, study.datasetHash?.slice(0, 12) || "no dataset hash"])),
              ].map((node, index) => <div className="audit-node" key={`${node[0]}-${node[1]}`}><span className="audit-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{node[0]}</strong><span className="mono">{node[1]} · {node[2]}</span></div><StatusChip state={project?.valid ? "known" : "partial"}>{project?.valid ? "verified" : "可寻址"}</StatusChip></div>)}
            </div>
          </Panel>
          <div className="stack">
            <Panel title="复现门禁" meta={`${coreDiagnostics.length} 条 Core diagnostics`}>
              {coreDiagnostics.length ? <div className="dense-list">{coreDiagnostics.map((item, index) => <div className="dense-row" key={`${item.code}-${index}`}><div><strong>{item.code}</strong><p>{item.message}</p></div><StatusChip state="missing">{item.category}</StatusChip></div>)}</div> : <EmptyState title="没有诊断项" detail={explorer?.run ? `${explorer.run.id} 已形成可寻址的结果来源链。` : "仍需 ExperimentRun 才能形成结果复现闭包。"} />}
            </Panel>
            <Panel title="研究证据门禁" meta="资格、选择偏差、稳健性与独立 holdout">
              <div className="dense-list">
                <div className="dense-row"><div><strong>Deterministic verdict</strong><p>{verification.verdict.detail}</p></div><StatusChip state={verification.verdict.state}>{verification.verdict.id}</StatusChip></div>
                <div className="dense-row"><div><strong>Selection adjustment</strong><p>{verification.selection.available ? verification.selection.method : "missing — 不声明已校正显著性"}</p></div><StatusChip state={verification.selection.passes === true ? "known" : verification.selection.passes === false ? "missing" : "partial"}>{verification.selection.passes === true ? "passes" : verification.selection.passes === false ? "fails" : "inconclusive"}</StatusChip></div>
                <div className="dense-row"><div><strong>External holdout</strong><p>{verification.holdout.available ? verification.holdout.state : "missing — 当前 test 不能冒充新 holdout"}</p></div><StatusChip state={verification.holdout.state === "assessed" ? "known" : "partial"}>{verification.holdout.state}</StatusChip></div>
                <div className="dense-row"><div><strong>Trading authority</strong><p>研究与审计专用</p></div><StatusChip state={verification.authority.tradingAuthority === "none" ? "known" : "restricted"}>{verification.authority.tradingAuthority || "missing"}</StatusChip></div>
              </div>
            </Panel>
            <Panel title="复现指令">{reproduce ? <div className="provenance-card"><span className="field-label">Research CLI · read-only</span><code className="field-value mono">{reproduce.argv.join(" ")}</code><span className="muted">只读取并验证不可变研究证据；tradingAuthority=none。</span></div> : <EmptyState title="命令不可用" detail="当前没有通过校验的 ExperimentRun；不生成指向无效证据的命令。" />}</Panel>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeading
        eyebrow="Audit / PROVENANCE GRAPH"
        title="审计与复现"
        description="从因子定义到实验产物逐层验证版本、哈希和 point-in-time 边界。"
      />
      <div className="audit-grid">
        <Panel title="来源链" meta="EXP-240801-17 的最小可复现闭包">
          <div className="audit-chain">
            {auditChain.map((node, index) => (
              <div className="audit-node" key={node.id}>
                <span className="audit-index">{String(index + 1).padStart(2, "0")}</span>
                <div><strong>{node.kind}</strong><span className="mono">{node.id} · {node.version} · {node.hash}</span></div>
                <StatusChip state={node.state === "产物完整" ? "成功" : "known"}>{node.state}</StatusChip>
              </div>
            ))}
          </div>
        </Panel>

        <div className="stack">
          <Panel title="复现门禁" meta="6 / 6 已满足">
            <div className="dense-list">
              {checks.map(([label, value]) => (
                <div className="dense-row" key={label}>
                  <div><strong>{label}</strong><small className="mono">{value}</small></div>
                  <StatusChip state="通过" />
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="复现指令">
            <div className="provenance-card">
              <span className="field-label">Research CLI</span>
              <code className="field-value mono">aq research reproduce EXP-240801-17 --frame {factor.frameId}</code>
              <span className="muted">指令只重建研究环境与产物，不连接账户或交易服务。</span>
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}
