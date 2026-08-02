"use client";

import Link from "next/link";
import { useState } from "react";
import { factor } from "@/lib/data";
import { PageHeading, Panel, StatusChip } from "@/components/ui";

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

  return (
    <>
      <PageHeading
        eyebrow="Factor Lab / TEST CONFIGURATION"
        title="因子实验室"
        description="把候选定义、时间边界、样本池和测试假设收束为一份可复现实验。"
        actions={<Link className="button-secondary" href="/results">查看最近结果</Link>}
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
            <div className="form-field">
              <label htmlFor="universe">研究标的池</label>
              <select id="universe" name="universe" autoComplete="off" value={config.universe} onChange={(event) => update("universe", event.target.value)}>
                <option>沪深全市场，逐日可交易标的</option>
                <option>中证 800，逐日成分</option>
                <option>事件 cohort 关联标的</option>
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="horizon">持有期</label>
              <select id="horizon" name="horizon" autoComplete="off" value={config.horizon} onChange={(event) => update("horizon", event.target.value)}>
                <option>5 个交易日</option>
                <option>20 个交易日</option>
                <option>60 个交易日</option>
              </select>
            </div>
            <div className="form-field">
              <label htmlFor="lag">信号延迟（交易日）</label>
              <input id="lag" name="lag" autoComplete="off" type="number" min="1" max="10" inputMode="numeric" value={config.lag} onChange={(event) => update("lag", event.target.value)} />
            </div>
            <div className="form-field">
              <label htmlFor="engine">测试引擎</label>
              <select id="engine" name="engine" autoComplete="off" defaultValue="截面排序 0.12.4">
                <option>截面排序 0.12.4</option>
                <option>事件研究 0.9.7</option>
              </select>
            </div>
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
            <button className="button" type="submit">创建研究实验</button>
            <button className="button-quiet" type="button" onClick={() => { setConfig(initialConfig); setRunId(""); }}>恢复默认</button>
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
                <Link className="button-secondary" href="/jobs">查看研究任务</Link>
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
