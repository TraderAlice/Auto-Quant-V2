"use client";

import { useState } from "react";
import { useStudio } from "@/components/studio-context";
import { Button, EmptyState, FormField, Panel, StatusChip } from "@/components/ui";

export function ClaimVerificationForm({ projectId, runId }) {
  const { retryCore } = useStudio();
  const [state, setState] = useState({ status: "idle", message: "", verdict: null });

  async function submit(event) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setState({ status: "running", message: "Core 正在生成不可变裁决…", verdict: null });
    try {
      const response = await fetch("/api/studio/verify-factor", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          projectId,
          runId,
          statement: values.get("statement"),
          minimumEffect: Number(values.get("minimumEffect")),
          minimumSampleSize: Number(values.get("minimumSampleSize")),
          requireHoldout: values.get("requireHoldout") === "on",
          requireSelection: values.get("requireSelection") === "on",
        }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error?.message || "裁决失败");
      const assessment = payload.verification.assessment;
      setState({ status: "succeeded", message: assessment.id, verdict: assessment.verdict });
      retryCore();
    } catch (error) {
      setState({ status: "failed", message: error instanceof Error ? error.message : "裁决失败", verdict: null });
    }
  }

  return (
    <Panel title="验证外部声明" meta="明确阈值 → 当前不可变 Factor Run → 四态裁决">
      {runId ? (
        <form className="stack" onSubmit={submit}>
          <FormField label="待验证声明" htmlFor="claim-statement">
            <input id="claim-statement" name="statement" type="text" maxLength={500} defaultValue="该指标在样本外相对零基线具有稳定的正向 Rank IC。" required />
          </FormField>
          <div className="form-grid">
            <FormField label="最低 Rank IC 改善" htmlFor="claim-effect"><input id="claim-effect" name="minimumEffect" type="number" min="0" step="0.001" defaultValue="0.01" required /></FormField>
            <FormField label="最低观测数" htmlFor="claim-samples"><input id="claim-samples" name="minimumSampleSize" type="number" min="1" max="1000000" defaultValue="30" required /></FormField>
          </div>
          <div className="check-grid">
            <label><input name="requireHoldout" type="checkbox" defaultChecked />要求独立 holdout</label>
            <label><input name="requireSelection" type="checkbox" defaultChecked />要求多重选择校正</label>
          </div>
          <div className="button-row">
            <Button type="submit" loading={state.status === "running"}>{state.status === "running" ? "裁决中…" : "生成不可变裁决"}</Button>
            {state.verdict ? <StatusChip state={state.verdict === "supported" ? "known" : state.verdict === "contradicted" ? "missing" : "partial"}>{state.verdict}</StatusChip> : null}
            {state.message ? <span className="muted mono" role="status">{state.message}</span> : null}
          </div>
        </form>
      ) : <EmptyState title="尚无 Factor Run" detail="先在因子实验室执行研究，再验证外部声明。" />}
    </Panel>
  );
}
