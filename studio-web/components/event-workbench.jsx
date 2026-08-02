"use client";

import Link from "next/link";
import { useState } from "react";
import { useStudio } from "@/components/studio-context";
import { Panel, StatusChip } from "@/components/ui";
import { compareCohorts, formatPercent, formatTime } from "@/lib/research";

export function EventWorkbench() {
  const { events, cohortA, cohortB, assignToCohort, removeFromCohort, setSelectedEventId } = useStudio();
  const comparison = compareCohorts(events, cohortA, cohortB);
  const [draftSaved, setDraftSaved] = useState(false);

  return (
    <div className="stack">
      <Panel title="事件样本" meta="成员和筛选规则将作为不可变快照进入候选因子">
        <div className="table-wrap">
          <table>
            <thead><tr><th>事件</th><th>适配器</th><th>可用时间</th><th>状态</th><th className="numeric">价格反应</th><th>事件组</th></tr></thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>
                    <button type="button" className="button-quiet" onClick={() => setSelectedEventId(event.id)}>{event.title}</button>
                    <span className="field-value" style={{ marginTop: 4 }}>{event.entity}</span>
                  </td>
                  <td>{event.adapter}</td>
                  <td className="mono">{formatTime(event.availableAt)}</td>
                  <td><StatusChip state={event.evidence} /></td>
                  <td className="numeric">{formatPercent(event.reaction)}</td>
                  <td>
                    <div className="button-row">
                      <button type="button" aria-label={`${event.title} 加入事件组 A`} aria-pressed={cohortA.includes(event.id)} className={`cohort-action ${cohortA.includes(event.id) ? "active-a" : ""}`} onClick={() => assignToCohort(event.id, "A")}>A</button>
                      <button type="button" aria-label={`${event.title} 加入事件组 B`} aria-pressed={cohortB.includes(event.id)} className={`cohort-action ${cohortB.includes(event.id) ? "active-b" : ""}`} onClick={() => assignToCohort(event.id, "B")}>B</button>
                      {(cohortA.includes(event.id) || cohortB.includes(event.id)) ? <button type="button" className="button-quiet" onClick={() => removeFromCohort(event.id)}>清除</button> : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel
        title="两组事件比较"
        meta="同一视图比较样本、实体、标签和后续价格反应"
        action={comparison.ready ? <button type="button" className="button" onClick={() => setDraftSaved(true)}>{draftSaved ? "候选因子已保存" : "生成候选因子"}</button> : null}
      >
        {comparison.ready ? (
          <>
            <div className="comparison-grid">
              <div className="comparison-side">
                <h3>事件组 A · 正向确认</h3>
                <div className="field-grid">
                  <div><span className="field-label">样本</span><span className="field-value">{comparison.left.count} 条</span></div>
                  <div><span className="field-label">平均反应</span><span className="field-value">{formatPercent(comparison.left.meanReaction)}</span></div>
                </div>
                <div className="tag-list" style={{ marginTop: 12 }}>{comparison.left.tags.map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div>
              </div>
              <div className="comparison-delta"><span>反应差</span><strong>{formatPercent(comparison.reactionSpread)}</strong><small>A - B</small></div>
              <div className="comparison-side">
                <h3>事件组 B · 对照样本</h3>
                <div className="field-grid">
                  <div><span className="field-label">样本</span><span className="field-value">{comparison.right.count} 条</span></div>
                  <div><span className="field-label">平均反应</span><span className="field-value">{formatPercent(comparison.right.meanReaction)}</span></div>
                </div>
                <div className="tag-list" style={{ marginTop: 12 }}>{comparison.right.tags.map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div>
              </div>
            </div>
            {draftSaved ? (
              <div className="provenance-card" style={{ marginTop: 12 }} role="status">
                <strong>候选因子草案 CF-240801-06 已保存</strong>
                <span className="field-value">成员、筛选条件、事件窗和 ReplayBundle RB-6F19A2 已锁定。</span>
                <Link className="button-secondary" href="/lab">进入因子实验室</Link>
              </div>
            ) : null}
          </>
        ) : (
          <div className="empty-state"><strong>每个事件组至少需要一条事件</strong><span>在上表为事件分配 A 或 B，然后返回比较。</span></div>
        )}
      </Panel>
    </div>
  );
}
