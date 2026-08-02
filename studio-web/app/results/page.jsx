import Link from "next/link";
import { PerformanceChart } from "@/components/charts";
import { diagnostics, factor, metrics } from "@/lib/data";
import { Metric, PageHeading, Panel, StatusChip } from "@/components/ui";

const buckets = [
  ["D1", "-7.8%", "-0.62", "19.4%"],
  ["D2", "-3.1%", "-0.24", "20.7%"],
  ["D3", "-0.7%", "-0.05", "22.1%"],
  ["D4", "+2.4%", "+0.18", "25.8%"],
  ["D5", "+10.8%", "+0.73", "29.2%"],
];

export default function ResultsPage() {
  return (
    <>
      <PageHeading
        eyebrow="Experiment / EXP-240801-17"
        title="测试结果"
        description="成本后收益、稳健性诊断与可复现来源集中呈现。"
        actions={<Link className="button-secondary" href="/lab">复制为新实验</Link>}
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
            <div className="table-wrap">
              <table>
                <thead><tr><th>分组</th><th>年化收益</th><th>平均暴露</th><th>年化换手</th></tr></thead>
                <tbody>{buckets.map((row) => <tr key={row[0]}>{row.map((cell, index) => <td key={cell} className={index > 0 ? "numeric mono" : "mono"}>{cell}</td>)}</tr>)}</tbody>
              </table>
            </div>
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
              <Link className="button-quiet" href="/audit">打开审计链</Link>
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}
