"use client";

import { useState } from "react";
import { jobs as initialJobs } from "@/lib/data";
import { ResearchSubject } from "@/components/research-subject";
import { useStudio } from "@/components/studio-context";
import { Button, DataTable, EmptyState, PageHeading, Panel, StatusChip } from "@/components/ui";

export function JobsWorkbench() {
  const { source, subject, demoEnabled } = useStudio();
  const [jobs, setJobs] = useState(initialJobs);
  const [selectedId, setSelectedId] = useState(initialJobs[0].id);
  const selected = jobs.find((job) => job.id === selectedId) || jobs[0];

  function retry(id) {
    setJobs((current) => current.map((job) => job.id === id ? { ...job, state: "排队", elapsed: "-", output: "等待资源" } : job));
    setSelectedId(id);
  }

  if (source.mode === "connected" && !demoEnabled) {
    const project = source.snapshot?.projects?.[0];
    const executions = project?.computeJobs || [];
    const executors = project?.computeExecutors || [];
    return (
      <>
        <PageHeading
          eyebrow="Research Compute / Core projection"
          title="研究任务"
          description="每次研究执行都有不可变 ComputeJob 收据；公开构建内置 CPU，GPU/MOSS provider 保留在非开源边界。"
        />
        <ResearchSubject subject={subject} />
        <div className="grid-2" style={{ marginTop: 14 }}>
          <Panel title="Core 研究执行" meta={`${executions.length} 份不可变收据`}>
            {executions.length ? (
              <div className="dense-list">
                {executions.map((item) => (
                  <div className="dense-row" key={item.id}>
                    <div><strong className="mono">{item.id}</strong><small>{item.executor.kind} · {item.study.id} · Run {item.runRef?.id || "无"} · attempt {item.retry.attempt}</small></div>
                    <StatusChip state={item.status}>{item.status}</StatusChip>
                  </div>
                ))}
              </div>
            ) : <EmptyState title="尚无 ComputeJob" detail="从因子实验室执行 Study 后会生成 CPU 收据，不使用演示队列。" />}
          </Panel>
          <Panel title="计算执行器" meta="开放收据契约，私有 provider 实现">
            <div className="dense-list">
              {executors.map((executor) => (
                <div className="dense-row" key={executor.kind}><div><strong>{executor.kind.toUpperCase()}</strong><small>{executor.provider} · {executor.reason || "本地可用"}</small></div><StatusChip state={executor.available ? "known" : "partial"}>{executor.available ? "available" : "unavailable"}</StatusChip></div>
              ))}
            </div>
            <p className="notice" style={{ marginTop: 14 }}><strong>边界：</strong> 这里展示研究任务证据，不暴露 provider 凭据、私有插件协议，也不拥有交易权限。</p>
          </Panel>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeading
        eyebrow="Research Compute / LOCAL WORKSPACE"
        title="研究任务"
        description="GPU、MOSS 与批量计算只是研究执行资源，任务产物会回链到实验和因子。"
      />
      <div className="grid-2">
        <Panel title="任务队列" meta="本地演示数据 · 资源状态不会触发外部执行">
          <DataTable>
              <thead><tr><th>任务</th><th>类型</th><th>状态</th><th>资源</th><th>耗时</th><th>产物</th><th>成本</th></tr></thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td><Button className="mono" variant="quiet" type="button" aria-pressed={job.id === selectedId} onClick={() => setSelectedId(job.id)}>{job.id}</Button></td>
                    <td>{job.kind}</td>
                    <td><StatusChip state={job.state} /></td>
                    <td>{job.resource}</td>
                    <td className="mono">{job.elapsed}</td>
                    <td>{job.output}</td>
                    <td className="numeric mono">{job.cost}</td>
                  </tr>
                ))}
              </tbody>
          </DataTable>
        </Panel>

        <Panel title={selected.id} meta="ComputeJob 详情">
          <div className="run-summary">
            <div className="field"><span>任务类型</span><strong>{selected.kind}</strong></div>
            <div className="field"><span>当前状态</span><StatusChip state={selected.state} /></div>
            <div className="field"><span>资源请求</span><strong>{selected.resource}</strong></div>
            <div className="field"><span>运行环境</span><strong className="mono">image-86f1 · Python 3.13</strong></div>
            <div className="field"><span>绑定实验</span><strong className="mono">EXP-240801-17</strong></div>
            <div className="field"><span>产物</span><strong>{selected.output}</strong></div>
          </div>
          {selected.state === "失败" ? (
            <div className="button-row" style={{ marginTop: 14 }}>
              <Button type="button" onClick={() => retry(selected.id)}>按原配置重试</Button>
            </div>
          ) : null}
          <p className="notice" style={{ marginTop: 14 }}><strong>边界：</strong> 研究任务只计算与保存研究产物，不拥有账户、订单或交易所权限。</p>
        </Panel>
      </div>
    </>
  );
}
