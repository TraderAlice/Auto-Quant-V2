"use client";

import { useState } from "react";
import { useStudio } from "@/components/studio-context";
import { ResearchSubject } from "@/components/research-subject";
import { Button, ButtonLink, DataTable, EmptyState, Panel, StatusChip } from "@/components/ui";
import { compareCohorts, formatPercent, formatTime } from "@/lib/research";

export function EventWorkbench() {
  const { events, cohortA, cohortB, assignToCohort, removeFromCohort, setSelectedEventId, source, subject, demoEnabled } = useStudio();
  const comparison = compareCohorts(events, cohortA, cohortB);
  const [draftSaved, setDraftSaved] = useState(false);

  if (source.mode === "connected" && !demoEnabled) {
    return (
      <div className="stack">
        <ResearchSubject subject={subject} />
        <Panel title="事件样本" meta="等待 Core EventBundle 与 point-in-time 可见性投影">
          <EmptyState title="尚无验证事件" detail="A 股公告、加密事件和财经新闻适配器仍是批准范围，但当前 snapshot 没有可用事件记录。" />
        </Panel>
        <Panel title="两组事件比较" meta="成员规则、事件窗与来源版本必须来自同一 ReplayBundle">
          <div className="comparison-grid">
            <div className="comparison-side"><h3>事件组 A</h3><EmptyState title="0 条" detail="等待验证事件成员。" /></div>
            <div className="comparison-delta"><span>反应差</span><strong>—</strong><small>A - B</small></div>
            <div className="comparison-side"><h3>事件组 B</h3><EmptyState title="0 条" detail="等待验证对照成员。" /></div>
          </div>
          <div className="button-row" style={{ marginTop: 12 }}><Button type="button" disabled>生成候选因子</Button></div>
        </Panel>
      </div>
    );
  }

  return (
    <div className="stack">
      <Panel title="事件样本" meta="成员和筛选规则将作为不可变快照进入候选因子">
        <DataTable>
            <thead><tr><th>事件</th><th>适配器</th><th>可用时间</th><th>状态</th><th className="numeric">价格反应</th><th>事件组</th></tr></thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>
                    <Button type="button" variant="quiet" onClick={() => setSelectedEventId(event.id)}>{event.title}</Button>
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
                      {(cohortA.includes(event.id) || cohortB.includes(event.id)) ? <Button type="button" variant="quiet" onClick={() => removeFromCohort(event.id)}>清除</Button> : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
        </DataTable>
      </Panel>

      <Panel
        title="两组事件比较"
        meta="同一视图比较样本、实体、标签和后续价格反应"
        action={comparison.ready ? <Button type="button" onClick={() => setDraftSaved(true)}>{draftSaved ? "候选因子已保存" : "生成候选因子"}</Button> : null}
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
                <ButtonLink href="/lab">进入因子实验室</ButtonLink>
              </div>
            ) : null}
          </>
        ) : (
          <EmptyState title="每个事件组至少需要一条事件" detail="在上表为事件分配 A 或 B，然后返回比较。" />
        )}
      </Panel>
    </div>
  );
}
