"use client";

import Link from "next/link";
import { useStudio } from "@/components/studio-context";
import { Button, ButtonLink, EmptyState, PageHeading, Panel, StatusChip } from "@/components/ui";
import { RESEARCH_STAGE_ORDER, researchSessions } from "@/lib/research-console";

function SessionCard({ item }) {
  const { project, bundle, projection } = item;
  const session = bundle.session;
  const stages = projection.ledger?.stages || [];
  return (
    <Link href={`/research/${session.id}`} className="research-session-card">
      <div><strong>{session.studyId || session.id}</strong><small className="mono">{project.id} · {session.id}</small></div>
      <div className="stage-dots" aria-label="Ledger stage states">
        {RESEARCH_STAGE_ORDER.map((id) => {
          const stage = stages.find((value) => value.id === id);
          return <span key={id} className={`stage-dot stage-dot-${stage?.state || "unavailable"}`} title={`${id}: ${stage?.state || "unavailable"}`} />;
        })}
      </div>
      <StatusChip state={projection.state === "available" ? "known" : projection.state === "partial" ? "partial" : "missing"}>{projection.state}</StatusChip>
    </Link>
  );
}

export default function ResearchPage() {
  const { source, demoEnabled, returnToCore } = useStudio();
  if (demoEnabled) {
    return <><PageHeading eyebrow="ResearchLedger / DEMO ISOLATED" title="研究控制台不可使用演示证据" description="Demo records never satisfy Connected Core evidence or mutation authority." /><EmptyState title="Review-only demo state" detail="Return to Core to inspect verified Session ledgers."><Button type="button" onClick={returnToCore}>返回 Core</Button></EmptyState></>;
  }
  if (source.mode !== "connected") return <><PageHeading eyebrow="ResearchLedger" title="研究控制台" description="等待本地 Core snapshot。" /><EmptyState title="Core unavailable" detail="Start aq studio serve or retry the connected snapshot from the shell gate." /></>;

  const items = researchSessions(source.snapshot);
  return (
    <>
      <PageHeading eyebrow="Work / ResearchLedger" title="Agent Research Console" description="Data → Question → Factor → Experiment → Campaign → Evidence → Approval → Reproduction。浏览器只投影 Core 证据，不计算 verdict。" actions={<ButtonLink href="/audit">审计与复现</ButtonLink>} />
      <div className="trust-strip" aria-label="ResearchLedger summary">
        <div className="trust-item"><span>Sessions</span><strong>{items.length}</strong></div>
        <div className="trust-item"><span>Verified ledgers</span><strong>{items.filter((item) => item.projection.state === "available").length}</strong></div>
        <div className="trust-item"><span>Partial / invalid</span><strong>{items.filter((item) => item.projection.state !== "available").length}</strong></div>
        <div className="trust-item"><span>Source</span><strong>CONNECTED CORE</strong></div>
      </div>
      <Panel title="Research Sessions" meta={`${source.snapshot.projects.length} Project(s)`}>
        {items.length ? <div className="research-session-list">{items.map((item) => <SessionCard key={`${item.project.id}:${item.bundle.session.id}`} item={item} />)}</div> : <EmptyState title="No research Sessions" detail="Core has not published a governed Session in this Workspace." />}
      </Panel>
    </>
  );
}
