"use client";

import Link from "next/link";
import { EvidenceChart } from "@/components/charts";
import { useStudio } from "@/components/studio-context";
import { ResearchSubject } from "@/components/research-subject";
import { Button, ButtonLink, Metric, ObjectLink, PageHeading, Panel, StatusChip } from "@/components/ui";
import { adapters, factor, jobs, metrics } from "@/lib/data";

function studyHref(study) {
  if (study.id.includes("portfolio")) return "/portfolio";
  if (study.id.includes("rl")) return "/rl";
  return `/factors/${study.id}`;
}

export default function ResearchHome() {
  const { source, subject, demoEnabled, enableDemo } = useStudio();

  if (source.mode === "connected" && !demoEnabled) {
    const snapshot = source.snapshot;
    const project = snapshot.projects[0];
    const counts = project?.counts || {};
    const coreMetrics = [
      ["Studies", counts.studies ?? 0],
      ["Runs", counts.runs ?? 0],
      ["Sessions", counts.sessions ?? 0],
      ["Reports", counts.reports ?? 0],
      ["Diagnostics", (snapshot.diagnostics.length + (project?.diagnostics?.length || 0))],
    ];
    return (
      <>
        <PageHeading
          eyebrow="Connected Core / READ ONLY"
          title={snapshot.source.workspace?.name || project?.name || "AutoQuant research workspace"}
          description="当前页面直接读取 Core 验证的 Studio snapshot；浏览器不读取项目文件，也不生成研究结论。"
          actions={<Button variant="secondary" type="button" onClick={enableDemo}>查看演示工作台</Button>}
        />
        <div className="trust-strip" aria-label="Core snapshot 状态">
          <div className="trust-item"><span>Harness</span><strong className="mono">AQ {snapshot.harness.version}@{snapshot.harness.commit.slice(0, 8)}</strong></div>
          <div className="trust-item"><span>Snapshot</span><strong className="mono">schema v{snapshot.schemaVersion}</strong></div>
          <div className="trust-item"><span>Generated</span><strong className="mono">{snapshot.generatedAt.replace("T", " ").replace("Z", " UTC")}</strong></div>
          <div className={`trust-item ${snapshot.valid ? "" : "warning"}`}><span>Verification</span><strong>{snapshot.valid ? "全部类别有效" : "存在 Core diagnostics"}</strong></div>
        </div>
        <div className="metric-row" aria-label="Core workspace counts">
          {coreMetrics.map(([label, value]) => <Metric key={label} label={label} value={String(value)} />)}
        </div>
        <div style={{ marginTop: 14 }}><ResearchSubject subject={subject} /></div>
        <div className="dashboard-grid" style={{ marginTop: 14 }}>
          <Panel title="Projects" meta={`${snapshot.projects.length} 个 Core 投影`}>
            <div className="dense-list">
              {snapshot.projects.map((item) => (
                <div className="dense-row" key={item.id}>
                  <div><strong>{item.name}</strong><p>{item.description || item.id}</p></div>
                  <StatusChip state={item.valid ? "known" : "missing"}>{item.valid ? "verified" : "diagnostics"}</StatusChip>
                </div>
              ))}
            </div>
          </Panel>
          <div className="stack">
            <Panel title="Current Project" meta={project?.id || "No Project"}>
              {project ? (
                <div className="dense-list">
                  {project.studies.map((study) => (
                    <Link className="dense-row" href={studyHref(study)} key={study.id}>
                      <div><strong>{study.name}</strong><small>{study.primaryMetric}</small></div>
                      <StatusChip state="known">{study.subjectKind}</StatusChip>
                    </Link>
                  ))}
                </div>
              ) : <p className="muted">Workspace 中没有 Project。</p>}
            </Panel>
            <Panel title="Core diagnostics" meta="未验证字节不会进入展示结论">
              {(project?.diagnostics?.length || snapshot.diagnostics.length) ? (
                <div className="dense-list">
                  {[...snapshot.diagnostics, ...(project?.diagnostics || [])].slice(0, 6).map((item, index) => (
                    <div className="dense-row" key={`${item.code}-${index}`}>
                      <div><strong>{item.code}</strong><p>{item.message}</p></div>
                      <StatusChip state="missing">{item.category}</StatusChip>
                    </div>
                  ))}
                </div>
              ) : <p className="muted">没有诊断项。</p>}
            </Panel>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeading
        eyebrow="Research home"
        title="研究工作区"
        description="恢复上一次研究帧，检查数据可信状态，并继续从证据到因子测试的同一条研究链。"
        actions={<ButtonLink variant="primary" href="/replay">继续时序回放</ButtonLink>}
      />

      <div className="trust-strip" aria-label="当前研究可信状态">
        <div className="trust-item"><span>研究帧</span><strong className="mono">{factor.frameId}</strong></div>
        <div className="trust-item"><span>回放 Bundle</span><strong className="mono">{factor.bundleId}</strong></div>
        <div className="trust-item"><span>数据覆盖</span><strong>91.7% · 3 类适配器</strong></div>
        <div className="trust-item warning"><span>已知限制</span><strong>新闻正文 12.4% 受限</strong></div>
      </div>

      <div className="metric-row" aria-label="最近一次因子测试指标">
        {metrics.map((metric) => <Metric key={metric.label} {...metric} detail={metric.delta} />)}
      </div>

      <div className="dashboard-grid" style={{ marginTop: 14 }}>
        <div className="stack">
          <Panel
            title="关键历史区间"
            meta="2024-02-23 · 事件证据、K 线与因子信号已对齐"
            action={<ButtonLink variant="quiet" href="/replay">打开回放</ButtonLink>}
          >
            <EvidenceChart compact cursorRatio={0.55} />
          </Panel>
          <Panel title="正在进行的研究" meta="所有对象沿用同一 ResearchFrame">
            <div className="dense-list">
              <div className="dense-row">
                <div><strong>{factor.name}</strong><p>候选因子已版本化，等待结果复核</p></div>
                <StatusChip state="known">{factor.version} 可测试</StatusChip>
              </div>
              <div className="dense-row">
                <div><strong>事件 cohort A / B</strong><p>正向确认 2 条，对照事件 2 条</p></div>
                <ButtonLink variant="quiet" href="/events">继续比较</ButtonLink>
              </div>
              <div className="dense-row">
                <div><strong>实验 EXP-240801-17</strong><p>成本后收益和修订敏感性已生成</p></div>
                <ButtonLink variant="quiet" href="/results">查看结果</ButtonLink>
              </div>
              <div className="dense-row">
                <div><strong>组合与治理式 RL</strong><p>沿用同一因子、数据版本、冻结样本和审计链</p></div>
                <ButtonLink variant="quiet" href="/portfolio">继续研究</ButtonLink>
              </div>
            </div>
          </Panel>
        </div>

        <div className="stack">
          <Panel title="对象链" meta="点击返回同一研究上下文">
            <ObjectLink href={`/factors/${factor.id}`} label="FactorPassport" id={factor.id} />
            <ObjectLink href="/replay" label="ResearchFrame" id={factor.frameId} />
            <ObjectLink href="/results" label="ExperimentRun" id="EXP-240801-17" />
            <ObjectLink href="/portfolio" label="PortfolioStudy" id="ohlcv-portfolio-quality" />
            <ObjectLink href="/rl" label="RLPolicyStudy" id="ohlcv-rl-factor-policy" />
            <ObjectLink href="/jobs" label="ComputeJob" id="JOB-91F2" />
          </Panel>

          <Panel title="数据健康" meta="最近观测和许可状态">
            <div className="dense-list">
              {adapters.map((adapter) => (
                <div className="dense-row" key={adapter.name}>
                  <div><strong>{adapter.name}</strong><small>最后观测 {adapter.lastSeen}</small></div>
                  <StatusChip state={adapter.state} />
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="计算队列" meta="GPU / MOSS 研究任务">
            <div className="dense-list">
              {jobs.slice(0, 3).map((job) => (
                <div className="dense-row" key={job.id}>
                  <div><strong>{job.kind}</strong><small className="mono">{job.id}</small></div>
                  <StatusChip state={job.state} />
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </>
  );
}
