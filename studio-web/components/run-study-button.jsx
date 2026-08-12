"use client";

import { useState } from "react";
import { useStudio } from "@/components/studio-context";
import { Button } from "@/components/ui";

export function RunStudyButton({ projectId, studyId, children = "执行研究" }) {
  const { retryCore } = useStudio();
  const [state, setState] = useState({ status: "idle", message: "" });

  async function run() {
    setState({ status: "running", message: "Core 正在执行…" });
    try {
      const response = await fetch("/api/studio/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projectId, studyId }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error?.message || "研究执行失败");
      setState({ status: "succeeded", message: payload.run.id });
      retryCore();
    } catch (error) {
      setState({ status: "failed", message: error instanceof Error ? error.message : "研究执行失败" });
    }
  }

  return (
    <div className="button-row">
      <Button type="button" onClick={run} disabled={!studyId || state.status === "running"} loading={state.status === "running"}>
        {state.status === "running" ? "执行中…" : children}
      </Button>
      {state.message ? <span className={`muted mono ${state.status === "failed" ? "text-danger" : ""}`} role="status">{state.message}</span> : null}
    </div>
  );
}
