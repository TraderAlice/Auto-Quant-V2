"use client";

import { useState } from "react";
import { factor } from "@/lib/data";
import { useStudio } from "@/components/studio-context";
import { ResearchSubject } from "@/components/research-subject";
import { RunStudyButton } from "@/components/run-study-button";
import { Button, ButtonLink, EmptyState, FormField, PageHeading, Panel, StatusChip } from "@/components/ui";

const initialConfig = {
  universe: "沪深全市场，逐日可交易标的",
  horizon: "20 个交易日",
  lag: "1",
  winsorize: true,
  neutralize: true,
  costs: true,
  revisionGuard: true,
};

export function FactorLab() {
  const { source, subject, demoEnabled, factor: activeFactor } = useStudio();
  const [config, setConfig] = useState(initialConfig);
  const [runId, setRunId] = useState("");

  const update = (key, value) => {
    setConfig((current) => ({ ...current, [key]: value }));
    setRunId("");
  };

  function submit(event) {
    event.preventDefault();
    setRunId("EXP-240801-18");
  }

  if (source.mode === "connected" && !demoEnabled) {
    const project = source.snapshot.projects[0];
    const study = project?.studies?.find((item) => item.subjectKind === "factor") || project?.studies?.[0];
    const explorer = project?.factorExplorer;
    return (
      <>
        <PageHeading
          eyebrow="Factor Lab / CORE PROJECTION"
          title="因子实验室"
          description="从已验证的 Study 创建不可变研究 Run；配置、数据快照、Judge 与结果均由 Core 锁定。"
          actions={<ButtonLink href="/results">查看结果状态</ButtonLink>}
        />
        <ResearchSubject subject={subject} />
        <div className="lab-grid" style={{ marginTop: 10 }}>
          <Panel title="实验输入" meta="当前 Core Study 契约">
            <div className="field-grid">
              <div><span className="field-label">Study</span><span className="field-value mono">{study?.id || "未声明"}</span></div>
              <div><span className="field-label">Factor</span><span className="field-value">{activeFactor.name}</span></div>
              <div><span className="field-label">Dataset</span><span className="field-value">{activeFactor.dataset}</span></div>
              <div><span className="field-label">Objective</span><span className="field-value">{study?.primaryMetric || "未声明"} · {study?.direction || "未声明"}</span></div>
              <div><span className="field-label">ResearchFrame</span><span className="field-value mono">{activeFactor.frameId}</span></div>
              <div><span className="field-label">执行边界</span><span className="field-value">离线研究，无交易权限</span></div>
            </div>
            <div style={{ marginTop: 14 }}><RunStudyButton projectId={project?.id} studyId={study?.id}>创建并执行研究 Run</RunStudyButton></div>
          </Panel>
          <Panel title="运行摘要" meta="最新 Core immutable evidence">
            {explorer?.run ? (
              <div className="run-summary">
                <div className="field"><span>Run</span><strong className="mono">{explorer.run.id}</strong></div>
                <div className="field"><span>Status</span><strong>{explorer.run.status}</strong></div>
                <div className="field"><span>Objective</span><strong>{explorer.run.objective?.metric}</strong></div>
                <div className="field"><span>Validation Rank IC</span><strong>{explorer.summary?.validation?.meanRankIc?.toFixed(6)}</strong></div>
                <div className="field"><span>Input hash</span><strong className="mono">{explorer.run.inputHash}</strong></div>
                <div className="field"><span>执行边界</span><strong>离线研究，无交易权限</strong></div>
              </div>
            ) : (
              <EmptyState title="尚无有效 Run" detail="执行后由 Core 写入不可变证据。" />
            )}
          </Panel>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeading
        eyebrow="Factor Lab / TEST CONFIGURATION"
        title="因子实验室"
        description="把候选定义、时间边界、样本池和测试假设收束为一份可复现实验。"
        actions={<ButtonLink href="/results">查看最近结果</ButtonLink>}
      />

      <div className="trust-strip" aria-label="实验信任上下文">
        <div className="trust-item"><span>FactorDefinition</span><strong>{factor.id} {factor.version}</strong></div>
        <div className="trust-item"><span>ResearchFrame</span><strong>{factor.frameId}</strong></div>
        <div className="trust-item"><span>Dataset</span><strong>{factor.dataset}</strong></div>
        <div className="trust-item"><span>执行模式</span><strong>研究沙盒，不连接实盘</strong></div>
      </div>

      <form className="lab-grid" onSubmit={submit}>
        <Panel title="测试配置" meta="配置变化会生成新的实验定义">
          <div className="form-grid">
            <FormField label="研究标的池" htmlFor="universe">
              <select id="universe" name="universe" autoComplete="off" value={config.universe} onChange={(event) => update("universe", event.target.value)}>
                <option>沪深全市场，逐日可交易标的</option>
                <option>中证 800，逐日成分</option>
                <option>事件 cohort 关联标的</option>
              </select>
            </FormField>
            <FormField label="持有期" htmlFor="horizon">
              <select id="horizon" name="horizon" autoComplete="off" value={config.horizon} onChange={(event) => update("horizon", event.target.value)}>
                <option>5 个交易日</option>
                <option>20 个交易日</option>
                <option>60 个交易日</option>
              </select>
            </FormField>
            <FormField label="信号延迟（交易日）" htmlFor="lag">
              <input id="lag" name="lag" autoComplete="off" type="number" min="1" max="10" inputMode="numeric" value={config.lag} onChange={(event) => update("lag", event.target.value)} />
            </FormField>
            <FormField label="测试引擎" htmlFor="engine">
              <select id="engine" name="engine" autoComplete="off" defaultValue="截面排序 0.12.4">
                <option>截面排序 0.12.4</option>
                <option>事件研究 0.9.7</option>
              </select>
            </FormField>
          </div>

          <fieldset style={{ marginTop: 14 }}>
            <legend>研究护栏</legend>
            <div className="check-grid">
              <label><input name="winsorize" type="checkbox" checked={config.winsorize} onChange={(event) => update("winsorize", event.target.checked)} />1% / 99% 缩尾</label>
              <label><input name="neutralize" type="checkbox" checked={config.neutralize} onChange={(event) => update("neutralize", event.target.checked)} />行业与规模中性</label>
              <label><input name="costs" type="checkbox" checked={config.costs} onChange={(event) => update("costs", event.target.checked)} />计入换手成本</label>
              <label><input name="revisionGuard" type="checkbox" checked={config.revisionGuard} onChange={(event) => update("revisionGuard", event.target.checked)} />锁定事件修订版本</label>
            </div>
          </fieldset>

          <div className="button-row" style={{ marginTop: 14 }}>
            <Button type="submit">创建研究实验</Button>
            <Button variant="quiet" type="button" onClick={() => { setConfig(initialConfig); setRunId(""); }}>恢复默认</Button>
          </div>
        </Panel>

        <div className="stack">
          <Panel title="运行摘要" meta="提交前的确定性快照">
            <div className="run-summary">
              <div className="field"><span>标的池</span><strong>{config.universe}</strong></div>
              <div className="field"><span>持有期</span><strong>{config.horizon}</strong></div>
              <div className="field"><span>可见性延迟</span><strong>T + {config.lag}</strong></div>
              <div className="field"><span>point-in-time</span><strong>available_at 强制约束</strong></div>
              <div className="field"><span>预计资源</span><strong>GPU A10 1x · 约 19 分钟</strong></div>
              <div className="field"><span>预算上限</span><strong>¥10.00</strong></div>
            </div>
          </Panel>

          {runId ? (
            <Panel title="实验已创建">
              <div className="provenance-card" role="status">
                <StatusChip state="排队">等待研究资源</StatusChip>
                <strong className="mono">{runId}</strong>
                <span className="muted">已锁定当前配置、数据集版本与 ResearchFrame。此动作不会发送订单或连接交易账户。</span>
                <ButtonLink href="/jobs">查看研究任务</ButtonLink>
              </div>
            </Panel>
          ) : (
            <div className="notice"><strong>研究范围：</strong> 这里仅创建离线因子测试，不包含实盘模拟、账户或订单。</div>
          )}
        </div>
      </form>
    </>
  );
}
