import { adapters } from "@/lib/data";
import { PageHeading, Panel, StatusChip } from "@/components/ui";

const mappings = [
  ["event_time", "源事件实际发生时间", "不可由发布时间替代"],
  ["published_at", "来源首次发布时间", "保存来源时区"],
  ["observed_at", "适配器首次观察时间", "用于测量采集延迟"],
  ["available_at", "研究系统可使用时间", "point-in-time 过滤主键"],
  ["revised_at", "当前版本修订时间", "原版本仍需可寻址"],
];

export default function DataPage() {
  return (
    <>
      <PageHeading
        eyebrow="Data Catalog / ADAPTER CONTRACTS"
        title="数据目录"
        description="覆盖率、延迟、许可、缺失与修订状态作为研究证据的一部分持续可见。"
      />
      <div className="stack">
        <Panel title="事件适配器" meta="三类已批准研究来源">
          <div className="table-wrap">
            <table>
              <thead><tr><th>适配器</th><th>状态</th><th>历史覆盖</th><th>最近观察</th><th>延迟</th><th>许可边界</th></tr></thead>
              <tbody>
                {adapters.map((adapter) => (
                  <tr key={adapter.name}>
                    <td><strong>{adapter.name}</strong></td>
                    <td><StatusChip state={adapter.state} /></td>
                    <td className="mono">{adapter.coverage}</td>
                    <td className="mono">{adapter.lastSeen}</td>
                    <td className="mono">{adapter.latency}</td>
                    <td>{adapter.rights}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="grid-2">
          <Panel title="时间一致性契约" meta="所有适配器输出相同可见性字段">
            <div className="table-wrap">
              <table>
                <thead><tr><th>字段</th><th>含义</th><th>约束</th></tr></thead>
                <tbody>{mappings.map((row) => <tr key={row[0]}><td className="mono">{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>)}</tbody>
              </table>
            </div>
          </Panel>
          <div className="stack">
            <Panel title="当前数据版本">
              <div className="field-grid">
                <div><span className="field-label">DatasetSnapshot</span><span className="field-value mono">cn-event-snapshot@2026.08.01</span></div>
                <div><span className="field-label">Schema</span><span className="field-value mono">event-contract/v4</span></div>
                <div><span className="field-label">覆盖率</span><span className="field-value">91.7% 可用于当前测试</span></div>
                <div><span className="field-label">缺失</span><span className="field-value">2 个异常日期低于 60%</span></div>
                <div><span className="field-label">修订</span><span className="field-value">17 条事件保留多版本</span></div>
                <div><span className="field-label">校验和</span><span className="field-value mono">ds:0bf7c9d2</span></div>
              </div>
            </Panel>
            <div className="notice"><strong>许可不是脚注：</strong> 受限正文不会被复制进研究产物；产物只保留可分发元数据、引用和用户本地连接标识。</div>
          </div>
        </div>
      </div>
    </>
  );
}
