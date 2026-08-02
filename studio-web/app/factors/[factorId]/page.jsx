import Link from "next/link";
import { PerformanceChart } from "@/components/charts";
import { Metric, ObjectLink, PageHeading, Panel, StatusChip } from "@/components/ui";
import { factor, metrics } from "@/lib/data";

export default function FactorPassport() {
  return (
    <>
      <PageHeading
        eyebrow="Factor passport"
        title={factor.name}
        description={factor.description}
        actions={
          <>
            <Link className="button-secondary" href="/lab">打开实验室</Link>
            <Link className="button" href="/replay">进入关键区间</Link>
          </>
        }
      />

      <div className="trust-strip" aria-label="因子护照状态">
        <div className="trust-item"><span>因子 ID / 版本</span><strong className="mono">{factor.id} · {factor.version}</strong></div>
        <div className="trust-item"><span>当前研究帧</span><strong className="mono">{factor.frameId}</strong></div>
        <div className="trust-item"><span>最近实验</span><strong className="mono">EXP-240801-17 · 成功</strong></div>
        <div className="trust-item warning"><span>可信状态</span><strong>2 项需要复核</strong></div>
      </div>

      <div className="metric-row">
        {metrics.map((metric) => <Metric key={metric.label} {...metric} detail={metric.delta} />)}
      </div>

      <div className="passport-grid" style={{ marginTop: 14 }}>
        <div className="passport-main stack">
          <Panel title="证据与表现" meta="示例数据，所有结果受当前可见性策略约束">
            <PerformanceChart />
          </Panel>
          <Panel title="因子定义" meta="版本化规则与研究证据">
            <div className="field-grid">
              <div><span className="field-label">定义</span><span className="field-value">zscore(event_surprise × diffusion_strength)</span></div>
              <div><span className="field-label">频率</span><span className="field-value">日频 · 事件后 1 个交易日生效</span></div>
              <div><span className="field-label">标的池</span><span className="field-value">A 股全市场 · ST/停牌过滤</span></div>
              <div><span className="field-label">可见性</span><span className="field-value">available_at &lt;= ResearchFrame.as_of</span></div>
              <div><span className="field-label">处理中立化</span><span className="field-value">行业 + 对数市值</span></div>
              <div><span className="field-label">作者证据</span><span className="field-value">Cohort A/B compare@RB-6F19A2</span></div>
            </div>
          </Panel>
        </div>

        <div className="passport-side stack">
          <Panel title="可信状态" meta="结果分数不替代诊断">
            <div className="dense-list">
              <div className="dense-row"><div><strong>时间一致性</strong><small>未来事件排除</small></div><StatusChip state="known">通过</StatusChip></div>
              <div className="dense-row"><div><strong>数据覆盖</strong><small>91.7% 样本</small></div><StatusChip state="partial">部分</StatusChip></div>
              <div className="dense-row"><div><strong>许可状态</strong><small>新闻正文受限</small></div><StatusChip state="restricted">受限</StatusChip></div>
              <div className="dense-row"><div><strong>修订风险</strong><small>1 条附件修订</small></div><StatusChip state="revised">已修订</StatusChip></div>
            </div>
          </Panel>

          <Panel title="关联对象" meta="双向跳转保持上下文">
            <ObjectLink href="/replay" label="ReplayBundle" id={factor.bundleId} />
            <ObjectLink href="/events" label="EventCohorts" id="COH-A / COH-B" />
            <ObjectLink href="/results" label="ExperimentRun" id="EXP-240801-17" />
            <ObjectLink href="/jobs" label="ComputeJob" id="JOB-91F2" />
            <ObjectLink href="/audit" label="AuditChain" id="AUD-31B7" />
          </Panel>

          <Panel title="版本" meta="研究证据保持不可变">
            <div className="dense-list">
              <div className="dense-row"><div><strong>v1.7</strong><small>加入修订敏感性约束</small></div><StatusChip state="known">当前</StatusChip></div>
              <div className="dense-row"><div><strong>v1.6</strong><small>扩大事件后窗口</small></div><span className="mono">2026-07-18</span></div>
              <div className="dense-row"><div><strong>v1.5</strong><small>加入新闻适配器</small></div><span className="mono">2026-06-29</span></div>
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}
