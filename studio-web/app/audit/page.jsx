import { auditChain, factor } from "@/lib/data";
import { PageHeading, Panel, StatusChip } from "@/components/ui";

const checks = [
  ["因子定义已锁定", "fdef:92ae4170"],
  ["ResearchFrame 可寻址", factor.frameId],
  ["数据集校验和一致", "ds:0bf7c9d2"],
  ["回放包保留可见性原因", factor.bundleId],
  ["运行环境镜像可获得", "image-86f1"],
  ["随机种子与参数已保存", "seed: 240801"],
];

export default function AuditPage() {
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
