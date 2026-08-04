"use client";

import { adapters } from "@/lib/data";
import { DataIntake } from "@/components/data-intake";
import { useStudio } from "@/components/studio-context";
import { DataTable, PageHeading, Panel, StatusChip } from "@/components/ui";

const mappings = [
  ["event_time", "源事件实际发生时间", "不可由发布时间替代"],
  ["published_at", "来源首次发布时间", "保存来源时区"],
  ["observed_at", "适配器首次观察时间", "用于测量采集延迟"],
  ["available_at", "研究系统可使用时间", "point-in-time 过滤主键"],
  ["revised_at", "当前版本修订时间", "原版本仍需可寻址"],
];

const eventAdapters = [
  ["a-share-announcement", "A 股公告"],
  ["crypto-event", "加密事件"],
  ["financial-news", "财经新闻"],
];

export default function DataPage() {
  const { source, demoEnabled } = useStudio();

  if (source.mode === "connected" && !demoEnabled) {
    const snapshot = source.snapshot;
    const project = snapshot.projects[0];
    return (
      <>
        <PageHeading eyebrow="Data Catalog / CORE PROJECTION" title="数据目录" description="展示 Core 已声明的数据集与仍未接入的事件适配器；覆盖率、许可和延迟未知时保持未知。" />
        <div className="stack">
          <DataIntake />
          <Panel title="研究数据集" meta={`${project?.studies?.length || 0} 个 Core Study`}>
            <DataTable><thead><tr><th>Study</th><th>Dataset</th><th>资产类</th><th>时间范围</th><th>校验和</th></tr></thead><tbody>
              {(project?.studies || []).map((study) => <tr key={study.id}><td><strong>{study.name}</strong><span className="field-value mono">{study.id}</span></td><td className="mono">{study.dataset ? `${study.dataset.id}@${study.dataset.version}` : "未绑定"}</td><td>{study.dataset?.asset_class || "未声明"}</td><td className="mono">{study.dataset?.time_range ? `${study.dataset.time_range.start} → ${study.dataset.time_range.end}` : "未声明"}</td><td className="mono">{study.datasetHash?.slice(0, 12) || "未声明"}</td></tr>)}
            </tbody></DataTable>
          </Panel>
          <Panel title="事件适配器" meta="批准范围，不等于已连接">
            <div className="dense-list">{eventAdapters.map(([kind, name]) => {
              const packages = (project?.eventSnapshots || []).filter((item) => item.adapterKind === kind);
              const latest = packages.at(-1);
              return <div className="dense-row" key={kind}><div><strong>{name}</strong><p>{latest ? `${latest.id}@${latest.version} · ${latest.eventCount} events · ${latest.availableStart} → ${latest.availableEnd}` : "当前 Core snapshot 未声明覆盖率、延迟、许可或修订状态。"}</p></div><StatusChip state={latest ? "known" : "missing"}>{latest ? "已验证" : "未接入"}</StatusChip></div>;
            })}</div>
          </Panel>
          <Panel title="时间一致性契约" meta="所有适配器必须输出相同可见性字段">
            <DataTable><thead><tr><th>字段</th><th>含义</th><th>约束</th></tr></thead><tbody>{mappings.map((row) => <tr key={row[0]}><td className="mono">{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>)}</tbody></DataTable>
          </Panel>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeading
        eyebrow="Data Catalog / ADAPTER CONTRACTS"
        title="数据目录"
        description="覆盖率、延迟、许可、缺失与修订状态作为研究证据的一部分持续可见。"
      />
      <div className="stack">
        <Panel title="事件适配器" meta="三类已批准研究来源">
          <DataTable>
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
          </DataTable>
        </Panel>

        <div className="grid-2">
          <Panel title="时间一致性契约" meta="所有适配器输出相同可见性字段">
            <DataTable>
                <thead><tr><th>字段</th><th>含义</th><th>约束</th></tr></thead>
                <tbody>{mappings.map((row) => <tr key={row[0]}><td className="mono">{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>)}</tbody>
            </DataTable>
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
