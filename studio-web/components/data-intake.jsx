"use client";

import { useState } from "react";
import { useStudio } from "@/components/studio-context";
import { Button, FormField, Panel } from "@/components/ui";

export function DataIntake() {
  const { source, retryCore } = useStudio();
  const [state, setState] = useState({ status: "idle", message: "" });
  const [eventState, setEventState] = useState({ status: "idle", message: "" });

  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const sourceFiles = Array.from(form.elements.sources.files || []);
    const body = new FormData(form);
    body.delete("sources");
    sourceFiles.forEach((file) => {
      body.append("source", file);
      body.append("sourcePath", file.webkitRelativePath || file.name);
    });
    setState({ status: "running", message: "Core 正在校验并固化数据…" });
    try {
      const response = await fetch("/api/studio/intake", { method: "POST", body });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error?.message || "数据导入失败");
      setState({ status: "succeeded", message: `${payload.intake.projectId} · ${payload.intake.dataset}` });
      form.reset();
      retryCore();
    } catch (error) {
      setState({ status: "failed", message: error instanceof Error ? error.message : "数据导入失败" });
    }
  }

  async function submitEvents(event) {
    event.preventDefault();
    const form = event.currentTarget;
    setEventState({ status: "running", message: "Core 正在校验事件时钟与内容哈希…" });
    try {
      const response = await fetch("/api/studio/event-intake", { method: "POST", body: new FormData(form) });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error?.message || "事件导入失败");
      setEventState({ status: "succeeded", message: `${payload.eventSnapshot.id}@${payload.eventSnapshot.version} · ${payload.eventSnapshot.eventCount} events` });
      form.reset();
      retryCore();
    } catch (error) {
      setEventState({ status: "failed", message: error instanceof Error ? error.message : "事件导入失败" });
    }
  }

  return (
    <>
      <Panel title="导入价格数据" meta="本地文件 → 严格 Core intake → 可复现 DatasetSnapshot">
      <form className="stack" onSubmit={submit}>
        <div className="form-grid">
          <FormField label="新 Project ID" htmlFor="intake-project-id">
            <input id="intake-project-id" name="projectId" type="text" pattern="[a-z0-9][a-z0-9-]{0,63}" placeholder="external-strategy-audit" required />
          </FormField>
          <FormField label="项目名称（可选）" htmlFor="intake-name">
            <input id="intake-name" name="name" type="text" maxLength={120} placeholder="外部策略真实性验证" />
          </FormField>
          <FormField label="研究模板" htmlFor="intake-template">
            <select id="intake-template" name="template" defaultValue="ohlcv-research-desk">
              <option value="ohlcv-research-desk">统一研究桌：Factor → Portfolio → RL</option>
              <option value="ohlcv-factor-lab">因子实验室</option>
              <option value="ohlcv-portfolio-lab">组合实验室</option>
              <option value="ohlcv-rl-factor-lab">治理式 RL</option>
              <option value="ohlcv-event-study-lab">事件研究</option>
              <option value="ohlcv-book-risk-lab">持仓风险</option>
              <option value="ohlcv-book-path-stress-lab">路径压力测试</option>
              <option value="ohlcv-allocation-lab">资产配置</option>
            </select>
          </FormField>
          <FormField label="Research Request JSON" htmlFor="intake-request">
            <input id="intake-request" name="request" type="file" accept="application/json,.json" required />
          </FormField>
          <FormField label="Dataset package JSON" htmlFor="intake-dataset">
            <input id="intake-dataset" name="dataset" type="file" accept="application/json,.json" required />
          </FormField>
          <FormField label="Manifest 引用的数据文件" htmlFor="intake-sources">
            <input id="intake-sources" name="sources" type="file" accept=".csv,.json,.parquet,.feather" multiple required />
          </FormField>
        </div>
        <div className="notice">
          <strong>导入要求：</strong> package 必须声明来源、许可/terms、市场时钟、价格复权、资产清单；覆盖率、缺失和时间范围由 Core 从文件实测。文件只在本机临时目录校验，导入完成即清理，不接收数据商凭证。
        </div>
        <div className="button-row">
          <Button type="submit" loading={state.status === "running"}>{state.status === "running" ? "导入中…" : "校验并导入"}</Button>
          {state.message ? <span className={`muted mono ${state.status === "failed" ? "text-danger" : ""}`} role="status">{state.message}</span> : null}
        </div>
      </form>
      </Panel>
      <Panel title="导入事件数据" meta="A 股公告 / 加密事件 / 财经新闻 → point-in-time EventSnapshot">
        <form className="stack" onSubmit={submitEvents}>
          <div className="form-grid">
            <FormField label="目标 Project" htmlFor="event-project-id">
              <select id="event-project-id" name="projectId" required>
                {(source.snapshot?.projects || []).map((project) => <option key={project.id} value={project.id}>{project.name} · {project.id}</option>)}
              </select>
            </FormField>
            <FormField label="EventPackage JSON" htmlFor="event-package">
              <input id="event-package" name="package" type="file" accept="application/json,.json" required />
            </FormField>
          </div>
          <div className="notice"><strong>固定契约：</strong> 每条事件必须保留 event_time、published_at、observed_at、available_at、source、license 与内容；Core 拒绝倒置时钟、重复 ID 和篡改。</div>
          <div className="button-row">
            <Button type="submit" loading={eventState.status === "running"}>{eventState.status === "running" ? "导入中…" : "校验并导入事件"}</Button>
            {eventState.message ? <span className={`muted mono ${eventState.status === "failed" ? "text-danger" : ""}`} role="status">{eventState.message}</span> : null}
          </div>
        </form>
      </Panel>
    </>
  );
}
