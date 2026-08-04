"use client";

import { use } from "react";
import { ResearchConsole } from "@/components/research-console";
import { useStudio } from "@/components/studio-context";
import { Button, ButtonLink, EmptyState, PageHeading } from "@/components/ui";
import { selectResearchSession } from "@/lib/research-console";

export default function ResearchSessionPage({ params }) {
  const { sessionId } = use(params);
  const { source, demoEnabled, returnToCore } = useStudio();
  if (demoEnabled) return <><PageHeading eyebrow="Research Session / DEMO ISOLATED" title="演示数据不能进入研究台账" description="Connected Core receipts, definitions, approval, and reproduction evidence are required." actions={<ButtonLink href="/research">返回台账</ButtonLink>} /><EmptyState title="Review-only demo state" detail="No Operator mutation is available in demo mode."><Button type="button" onClick={returnToCore}>返回 Core</Button></EmptyState></>;
  if (source.mode !== "connected") return <><PageHeading eyebrow="Research Session" title="Core unavailable" actions={<ButtonLink href="/research">返回台账</ButtonLink>} /><EmptyState title="Session unavailable" detail="The connected Core snapshot is not available." /></>;

  let selected;
  try {
    selected = selectResearchSession(source.snapshot, sessionId);
  } catch (error) {
    return <><PageHeading eyebrow="Research Session" title="Session unavailable" description={error instanceof Error ? error.message : "Session cannot be resolved."} actions={<ButtonLink href="/research">返回台账</ButtonLink>} /><EmptyState title="No verified Session" detail="The URL does not identify exactly one connected Core Session." /></>;
  }
  const { project, bundle, projection } = selected;
  return (
    <>
      <PageHeading eyebrow="Work / Agent Research Console" title={bundle.session.studyId || bundle.session.id} description={`${project.id} · ${bundle.session.id} · ${bundle.session.status}`} actions={<ButtonLink href="/research">返回台账</ButtonLink>} />
      <ResearchConsole snapshot={source.snapshot} project={project} bundle={bundle} ledger={projection.ledger} diagnostics={projection.diagnostics} />
    </>
  );
}
