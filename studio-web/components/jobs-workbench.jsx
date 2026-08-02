"use client";

import { useState } from "react";
import { jobs as initialJobs } from "@/lib/data";
import { PageHeading, Panel, StatusChip } from "@/components/ui";

export function JobsWorkbench() {
  const [jobs, setJobs] = useState(initialJobs);
  const [selectedId, setSelectedId] = useState(initialJobs[0].id);
  const selected = jobs.find((job) => job.id === selectedId) || jobs[0];

  function retry(id) {
    setJobs((current) => current.map((job) => job.id === id ? { ...job, state: "排队", elapsed: "-", output: "等待资源" } : job));
    setSelectedId(id);
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
          <div className="table-wrap">
            <table>
              <thead><tr><th>任务</th><th>类型</th><th>状态</th><th>资源</th><th>耗时</th><th>产物</th><th>成本</th></tr></thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id}>
                    <td><button className="button-quiet mono" type="button" aria-pressed={job.id === selectedId} onClick={() => setSelectedId(job.id)}>{job.id}</button></td>
                    <td>{job.kind}</td>
                    <td><StatusChip state={job.state} /></td>
                    <td>{job.resource}</td>
                    <td className="mono">{job.elapsed}</td>
                    <td>{job.output}</td>
                    <td className="numeric mono">{job.cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
              <button className="button" type="button" onClick={() => retry(selected.id)}>按原配置重试</button>
            </div>
          ) : null}
          <p className="notice" style={{ marginTop: 14 }}><strong>边界：</strong> 研究任务只计算与保存研究产物，不拥有账户、订单或交易所权限。</p>
        </Panel>
      </div>
    </>
  );
}
