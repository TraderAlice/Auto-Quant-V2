"use client";

import Link from "next/link";
import { useEffect, useMemo } from "react";
import { EvidenceChart } from "@/components/charts";
import { useStudio } from "@/components/studio-context";
import { Panel, StatusChip } from "@/components/ui";
import { formatPercent, formatTime, hiddenEventSummary, visibleEvents } from "@/lib/research";

const trackByAdapter = {
  "A股公告": "25%",
  "财经新闻": "51%",
  "加密事件": "76%",
};

function markerCell(event, steps) {
  const target = Date.parse(event.availableAt);
  const index = steps.findIndex((step) => Date.parse(step) >= target);
  return index < 0 ? steps.length - 1 : index;
}

function CohortTray({ events, cohortA, cohortB, removeFromCohort }) {
  const renderColumn = (label, ids) => (
    <div className="cohort-column">
      <h3>事件组 {label} · {ids.length} 条</h3>
      {ids.length ? ids.map((id) => {
        const event = events.find((item) => item.id === id);
        if (!event) return null;
        return (
          <div className="cohort-member" key={id}>
            <span>{event.title}</span>
            <button type="button" onClick={() => removeFromCohort(id)} aria-label={`从事件组移除 ${event.title}`}>移除</button>
          </div>
        );
      }) : <span className="field-value">尚未添加事件</span>}
    </div>
  );

  return <div className="cohort-tray">{renderColumn("A", cohortA)}{renderColumn("B", cohortB)}</div>;
}

export function ReplayWorkbench() {
  const {
    events,
    replaySteps,
    asOf,
    asOfIndex,
    selectedEvent,
    selectedEventId,
    cohortA,
    cohortB,
    setAsOfIndex,
    setSelectedEventId,
    stepBackward,
    stepForward,
    assignToCohort,
    removeFromCohort,
  } = useStudio();

  const visible = useMemo(() => visibleEvents(events, asOf), [events, asOf]);
  const hidden = useMemo(() => hiddenEventSummary(events, asOf), [events, asOf]);
  const selectedVisible = visible.some((event) => event.id === selectedEventId);
  const inspectorEvent = selectedVisible ? selectedEvent : visible.at(-1) || null;
  const cursorRatio = asOfIndex / (replaySteps.length - 1);

  useEffect(() => {
    const handleKey = (event) => {
      if (event.key === "[") stepBackward();
      if (event.key === "]") stepForward();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [stepBackward, stepForward]);

  return (
    <div className="replay-layout">
      <div className="stack">
        <div className="trust-strip" aria-label="回放可信状态">
          <div className="trust-item"><span>可见时点 T</span><strong className="mono">{formatTime(asOf)} CST</strong></div>
          <div className="trust-item"><span>已见证据</span><strong>{visible.length} / {events.length} 条</strong></div>
          <div className="trust-item"><span>市场快照</span><strong>5m · CN + Crypto</strong></div>
          <div className="trust-item warning"><span>暂不可见</span><strong>{hidden.total} 条 · 内容未泄露</strong></div>
        </div>

        <Panel
          title="共享证据时间轴"
          meta="K 线、因子信号、市场快照和事件轨道使用同一 visible-at 边界"
          action={
            <div className="transport" aria-label="回放控制">
              <button type="button" onClick={stepBackward} disabled={asOfIndex === 0}>上一刻</button>
              <time dateTime={asOf}>{formatTime(asOf)}</time>
              <button type="button" onClick={stepForward} disabled={asOfIndex === replaySteps.length - 1}>下一刻</button>
            </div>
          }
        >
          <EvidenceChart cursorRatio={cursorRatio} />
          <div className="table-wrap" style={{ marginTop: 10 }}>
            <div className="timeline" aria-label="事件时间轴">
              {replaySteps.map((step, index) => (
                <div className="timeline-cell" key={step}>
                  <span className="timeline-tick">{formatTime(step).split(" ").at(-1)}</span>
                  {visible.filter((event) => markerCell(event, replaySteps) === index).map((event) => {
                    const cohortClass = cohortA.includes(event.id) ? "cohort-a" : cohortB.includes(event.id) ? "cohort-b" : "";
                    return (
                      <button
                        type="button"
                        key={event.id}
                        className={`event-marker ${selectedEventId === event.id ? "selected" : ""} ${cohortClass}`}
                        style={{ "--track": trackByAdapter[event.adapter] }}
                        aria-label={`${event.adapter}: ${event.title}`}
                        aria-pressed={selectedEventId === event.id}
                        title={`${event.adapter}: ${event.title}`}
                        onClick={() => setSelectedEventId(event.id)}
                      />
                    );
                  })}
                </div>
              ))}
              <div className="future-curtain" style={{ "--cursor": `${cursorRatio * 100}%` }} />
            </div>
          </div>
          <div className="dense-list" style={{ marginTop: 8 }}>
            {visible.map((event) => (
              <button
                type="button"
                className="dense-row"
                key={event.id}
                aria-pressed={selectedEventId === event.id}
                onClick={() => setSelectedEventId(event.id)}
                style={{ width: "100%", background: selectedEventId === event.id ? "#162a36" : "transparent", color: "inherit", cursor: "pointer", textAlign: "left" }}
              >
                <div><strong>{event.title}</strong><small>{event.adapter} · available {formatTime(event.availableAt)}</small></div>
                <StatusChip state={event.evidence} />
              </button>
            ))}
          </div>
        </Panel>

        <Panel
          title="事件组"
          meta="成员快照保持不变，后续数据修订不会静默改写旧实验"
          action={<Link className="button-quiet" href="/events">比较两组</Link>}
        >
          <CohortTray events={events} cohortA={cohortA} cohortB={cohortB} removeFromCohort={removeFromCohort} />
        </Panel>
      </div>

      <aside className="evidence-inspector" aria-label="证据检查器">
        <Panel title="证据检查器" meta={inspectorEvent ? inspectorEvent.id : "当前时点没有可见事件"}>
          {inspectorEvent ? (
            <div className="stack">
              <div>
                <StatusChip state={inspectorEvent.evidence} />
                <h2 className="event-title" style={{ marginTop: 9 }}>{inspectorEvent.title}</h2>
                <p className="event-summary">{inspectorEvent.summary}</p>
              </div>
              <div className="field-grid">
                <div><span className="field-label">事件时间</span><span className="field-value">{formatTime(inspectorEvent.eventTime)}</span></div>
                <div><span className="field-label">发布时间</span><span className="field-value">{formatTime(inspectorEvent.publishedAt)}</span></div>
                <div><span className="field-label">观测时间</span><span className="field-value">{formatTime(inspectorEvent.observedAt)}</span></div>
                <div><span className="field-label">可用时间</span><span className="field-value">{formatTime(inspectorEvent.availableAt)}</span></div>
                <div><span className="field-label">修订时间</span><span className="field-value">{inspectorEvent.revisedAt ? formatTime(inspectorEvent.revisedAt) : "无"}</span></div>
                <div><span className="field-label">价格反应</span><span className="field-value">{formatPercent(inspectorEvent.reaction)}</span></div>
                <div><span className="field-label">来源</span><span className="field-value">{inspectorEvent.source}</span></div>
                <div><span className="field-label">许可</span><span className="field-value">{inspectorEvent.rights}</span></div>
                <div><span className="field-label">实体</span><span className="field-value">{inspectorEvent.entity}</span></div>
                <div><span className="field-label">内容哈希</span><span className="field-value">{inspectorEvent.hash}</span></div>
              </div>
              <div className="tag-list">{inspectorEvent.tags.map((tag) => <span className="tag" key={tag}>{tag}</span>)}</div>
              <div className="button-row">
                <button
                  type="button"
                  className={`cohort-action ${cohortA.includes(inspectorEvent.id) ? "active-a" : ""}`}
                  aria-pressed={cohortA.includes(inspectorEvent.id)}
                  onClick={() => assignToCohort(inspectorEvent.id, "A")}
                >
                  加入事件组 A
                </button>
                <button
                  type="button"
                  className={`cohort-action ${cohortB.includes(inspectorEvent.id) ? "active-b" : ""}`}
                  aria-pressed={cohortB.includes(inspectorEvent.id)}
                  onClick={() => assignToCohort(inspectorEvent.id, "B")}
                >
                  加入事件组 B
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-state"><strong>时点 T 尚无可见事件</strong><span>向后推进回放以观察证据如何进入可用集。</span></div>
          )}
        </Panel>
        <div className="notice" style={{ marginTop: 10 }}>
          <strong>Point-in-time：</strong> {hidden.total} 条未来证据只计数，不显示标题或内容。按 <span className="mono">[</span> / <span className="mono">]</span> 单步回放。
        </div>
      </aside>
    </div>
  );
}
