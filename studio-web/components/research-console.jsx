"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Drawer, NumberInput, Select, Tabs, Text, Textarea, TextInput } from "@mantine/core";
import { Button, DataTable, EmptyState, Panel, StatusChip } from "@/components/ui";
import {
  READ_ONLY_INTENTS,
  RESEARCH_STAGE_ORDER,
  buildArtifactReviewDraft,
  buildExperimentDefinitionDraft,
  buildFactorDefinitionDraft,
  buildOperatorRequest,
  buildReproductionRequestDraft,
  latestCampaignBudget,
  parseJsonObject,
  receiptFromEnvelope,
} from "@/lib/research-console";

const REVIEW_MUTATION_INTENTS = [
  "definition.factor.create",
  "definition.experiment.create",
  "artifact.decide",
  "reproduction.start",
];

const STATE_LABEL = { available: "Available", partial: "Partial", empty: "Empty", unavailable: "Unavailable" };
const INTENT_LABEL = {
  "research.inspect": "Inspect ledger",
  "research.explain": "Explain blockers",
  "research.compare": "Compare exact versions",
  "research.reproduction-readiness": "Check reproduction readiness",
  "definition.factor.create": "FactorDefinition editor",
  "definition.experiment.create": "ExperimentDefinition editor",
  "artifact.decide": "Artifact review decision",
  "reproduction.start": "Request reproduction",
  "campaign.stop": "Stop running Campaign",
};

function tone(state) {
  if (["available", "completed", "exact-match", "within-tolerance"].includes(state)) return "known";
  if (["unavailable", "empty", "failed", "drift", "stale"].includes(state)) return "missing";
  return "partial";
}

function ObjectRef({ value }) {
  return (
    <span className="research-object-ref">
      <span>{value.kind}</span>
      <b className="mono">{value.id}</b>
      {value.version == null ? null : <em>v{value.version}</em>}
    </span>
  );
}

export function OperationReceiptCard({ receipt }) {
  return (
    <article className="operation-receipt" aria-label={`${receipt.intent} ${receipt.status}`}>
      <header>
        <div><strong>{INTENT_LABEL[receipt.intent] || receipt.intent}</strong><small className="mono">{receipt.requestId}</small></div>
        <StatusChip state={tone(receipt.status)}>{receipt.status}</StatusChip>
      </header>
      {receipt.failedGates?.length ? <p className="receipt-warning">Failed gates: {receipt.failedGates.join(", ")}</p> : null}
      {receipt.errors?.map((error, index) => <p className="receipt-error" key={`${error.code}-${index}`}>{error.code}: {error.message}</p>)}
      {receipt.artifacts?.length ? <div className="object-list">{receipt.artifacts.map((item, index) => <ObjectRef key={`${item.kind}-${item.id}-${index}`} value={item} />)}</div> : null}
      {receipt.nextValidActions?.length ? <small>Next: {receipt.nextValidActions.join(" · ")}</small> : null}
      <time dateTime={receipt.completedAt}>{receipt.completedAt || "time unavailable"}</time>
    </article>
  );
}

function StageRail({ stages, activeId, onSelect }) {
  const stageMap = new Map(stages.map((stage) => [stage.id, stage]));
  return (
    <nav className="research-stage-rail" aria-label="ResearchLedger stages">
      {RESEARCH_STAGE_ORDER.map((id, index) => {
        const stage = stageMap.get(id);
        return (
          <button key={id} type="button" className={activeId === id ? "is-active" : ""} onClick={() => stage && onSelect(id)} disabled={!stage} aria-current={activeId === id ? "step" : undefined}>
            <span className={`research-stage-index state-${stage?.state || "unavailable"}`}>{index + 1}</span>
            <span><strong>{stage?.label || id}</strong><small>{STATE_LABEL[stage?.state] || "Unavailable"}</small></span>
          </button>
        );
      })}
    </nav>
  );
}

function BudgetBar({ budget }) {
  if (!budget) return <EmptyState title="Budget unavailable" detail="Core did not project Campaign budget evidence for this session." />;
  const metrics = [
    ["Candidates", "candidates", budget.maxCandidates],
    ["Wall", "wallSeconds", budget.maxWallSeconds],
    ["CPU", "cpuSeconds", budget.maxCpuSeconds],
    ["GPU", "gpuSeconds", budget.maxGpuSeconds],
  ];
  return (
    <div className="campaign-budget" aria-label="Campaign budget usage">
      {metrics.map(([label, key, maximum]) => {
        const used = budget.used?.[key];
        const known = Number.isFinite(used) && Number.isFinite(maximum) && maximum >= 0;
        const percent = known && maximum > 0 ? Math.min(100, (used / maximum) * 100) : 0;
        return (
          <div key={key}>
            <span><b>{label}</b><em>{known ? `${used} / ${maximum}` : "unavailable"}</em></span>
            <progress value={percent} max="100" aria-label={`${label} budget`} />
          </div>
        );
      })}
      <p>Cost: {budget.used?.cost?.known ? `${budget.used.cost.amount} ${budget.used.cost.currency || ""}` : "unknown"} · Executor: {budget.executorPolicy?.default || "unavailable"} · Holdout: {budget.holdoutPolicy?.sealed === true ? "sealed" : "unavailable"}</p>
    </div>
  );
}

function CandidateRunTable({ experiments }) {
  if (!experiments.length) return <EmptyState title="No candidate evidence" detail="Core has not published Experiment evidence for this Session." />;
  return (
    <DataTable minWidth={920}>
      <thead><tr><th>Candidate</th><th>Version</th><th>Stage</th><th>Executor</th><th>Spend</th><th>Failed gate</th><th>Best evidence</th><th>Stop / next</th></tr></thead>
      <tbody>{experiments.map((item) => (
        <tr key={item.id}>
          <td className="mono">{item.id}</td>
          <td>{item.definitionRef?.version == null ? "unavailable" : `v${item.definitionRef.version}`}</td>
          <td><StatusChip state={tone(item.verdict)}>{item.verdict || item.status || "unavailable"}</StatusChip></td>
          <td>{item.executor?.kind || "unavailable"}</td>
          <td>{item.budgetSpent?.cost?.known ? `${item.budgetSpent.cost.amount} ${item.budgetSpent.cost.currency || ""}` : "unavailable"}</td>
          <td>{item.failedGates?.join(", ") || "—"}</td>
          <td>{item.hypothesis || item.summary || "unavailable"}</td>
          <td>{item.stopReason || item.nextValidActions?.join(", ") || "—"}</td>
        </tr>
      ))}</tbody>
    </DataTable>
  );
}

function SemanticDiff({ receipts, pendingReceipt }) {
  const diff = [...(pendingReceipt ? [pendingReceipt] : receipts)].reverse().flatMap((receipt) => receipt.evidence || []).find((item) => item?.kind === "autoquant-semantic-definition-diff");
  if (!diff) {
    const detail = pendingReceipt ? "Current pending receipt has no semantic diff evidence from Core." : "Compare two exact versions to receive a Core-authored diff.";
    return <EmptyState title="No semantic diff" detail={detail} />;
  }
  return (
    <div className="semantic-diff">
      <p><b>{diff.definition?.id}</b> · v{diff.fromVersion} → v{diff.toVersion}</p>
      {(diff.changes || []).map((change) => <details key={change.field}><summary>{change.field}{diff.affectedEvidence?.includes(change.field) ? " · evidence invalidated" : ""}</summary><pre>{JSON.stringify({ before: change.before, after: change.after }, null, 2)}</pre></details>)}
    </div>
  );
}

function EvidenceReview({ stage, bundle, receipts }) {
  const budget = latestCampaignBudget(bundle);
  return (
    <Tabs defaultValue="outcome" className="evidence-review">
      <Tabs.List aria-label="Evidence review views">
        {[["outcome", "Outcome"], ["replay", "Replay"], ["cohorts", "Cohorts"], ["robustness", "Robustness"], ["costs", "Costs"], ["provenance", "Provenance"]].map(([value, label]) => <Tabs.Tab key={value} value={value}>{label}</Tabs.Tab>)}
      </Tabs.List>
      <Tabs.Panel value="outcome"><CandidateRunTable experiments={bundle.experiments || []} /></Tabs.Panel>
      <Tabs.Panel value="replay"><EmptyState title={`Replay ${stage.widgets?.replay?.state || "unavailable"}`} detail={stage.widgets?.replay?.reason || "ReplayBundle, market clock, or entity mapping is not connected."} /></Tabs.Panel>
      <Tabs.Panel value="cohorts"><pre className="evidence-json">{JSON.stringify(bundle.decisionMatrix || { state: "unavailable" }, null, 2)}</pre></Tabs.Panel>
      <Tabs.Panel value="robustness"><EmptyState title="Robustness evidence unavailable" detail="No separate verified robustness projection is attached to this ledger stage." /></Tabs.Panel>
      <Tabs.Panel value="costs"><BudgetBar budget={budget} /></Tabs.Panel>
      <Tabs.Panel value="provenance"><div className="object-list">{stage.objects?.map((item, index) => <ObjectRef key={`${item.kind}-${item.id}-${index}`} value={item} />)}</div><p>{receipts.length} immutable Operator receipt(s).</p></Tabs.Panel>
    </Tabs>
  );
}

function StageCanvas({ stage, bundle, receipts }) {
  if (!stage) return <EmptyState title="Stage unavailable" detail="The connected ledger does not contain this stage." />;
  return (
    <div className="research-stage-canvas">
      <Panel title={`${stage.label} stage`} meta={`Core state · ${stage.state}`}>
        <div className="stage-summary"><StatusChip state={tone(stage.state)}>{STATE_LABEL[stage.state] || stage.state}</StatusChip><div className="object-list">{stage.objects?.map((item, index) => <ObjectRef key={`${item.kind}-${item.id}-${index}`} value={item} />)}</div></div>
        {stage.blockers?.length ? <ul className="research-blockers">{stage.blockers.map((item) => <li key={item}>{item}</li>)}</ul> : null}
        {stage.nextValidActions?.length ? <p className="next-actions">Next valid actions: {stage.nextValidActions.join(" · ")}</p> : null}
      </Panel>
      {stage.id === "campaign" ? <><BudgetBar budget={latestCampaignBudget(bundle)} /><CandidateRunTable experiments={bundle.experiments || []} /></> : null}
      {stage.id === "evidence" ? <EvidenceReview stage={stage} bundle={bundle} receipts={receipts} /> : null}
      {stage.id === "approval" || stage.id === "reproduction" ? <div className="receipt-list">{receipts.length ? receipts.map((receipt) => <OperationReceiptCard key={receipt.requestId} receipt={receipt} />) : <EmptyState title="No receipts" detail="No immutable approval or reproduction receipt is available." />}</div> : null}
    </div>
  );
}

function exactCompareRefs(stages) {
  const refs = stages.flatMap((stage) => stage.objects || []).filter((item) => item.version != null && ["factor-definition", "strategy-definition", "experiment-definition"].includes(item.kind));
  for (let index = 0; index < refs.length; index += 1) {
    const match = refs.slice(index + 1).find((item) => item.kind === refs[index].kind && item.id === refs[index].id);
    if (match) return [refs[index], match];
  }
  return [];
}

export function FactorDefinitionEditor({ disabled, busy, onReview }) {
  const [id, setId] = useState("");
  const [version, setVersion] = useState(1);
  const [parentVersion, setParentVersion] = useState("");
  const [createdAt, setCreatedAt] = useState(new Date().toISOString());
  const [hypothesis, setHypothesis] = useState("");
  const [calcKind, setCalcKind] = useState(null);
  const [calcIdentity, setCalcIdentity] = useState("");
  const [calcSourceHash, setCalcSourceHash] = useState("");
  const [parametersJson, setParametersJson] = useState("{}");
  const [outputDirection, setOutputDirection] = useState(null);
  const [outputUnit, setOutputUnit] = useState("");
  const [dataDependenciesJson, setDataDependenciesJson] = useState("[]");
  const [missingDataPolicy, setMissingDataPolicy] = useState("");
  const [cohortJson, setCohortJson] = useState("{}");
  const [expectedHorizon, setExpectedHorizon] = useState("");
  const [requiredTests, setRequiredTests] = useState("");
  const [failureGates, setFailureGates] = useState("");
  const [error, setError] = useState(null);

  const isDisabled = disabled || busy;

  function handleSubmit() {
    setError(null);
    try {
      if (!id.trim()) throw new Error("id is required");
      if (!Number.isInteger(version) || version < 1) throw new Error("version must be a positive integer");

      const parentVersionParsed = parentVersion.trim() === "" ? null : Number(parentVersion);
      if (parentVersionParsed !== null && (!Number.isInteger(parentVersionParsed) || parentVersionParsed < 1)) {
        throw new Error("parentVersion must be blank/null or a positive integer");
      }
      if (parentVersionParsed === null && version !== 1) {
        throw new Error("parentVersion must be provided for versions greater than 1");
      }
      if (!createdAt.trim()) throw new Error("createdAt is required");
      const parsedDate = new Date(createdAt);
      if (isNaN(parsedDate.getTime()) || parsedDate.toISOString() !== createdAt) {
        throw new Error("createdAt is not a valid ISO timestamp");
      }

      const parameters = parseJsonObject(parametersJson);
      const dataDependencies = JSON.parse(dataDependenciesJson);
      if (!Array.isArray(dataDependencies)) throw new Error("dataDependencies must be a JSON array");
      const cohort = parseJsonObject(cohortJson);

      const requiredTestsArray = requiredTests
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

      const failureGatesArray = failureGates
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

      const definition = buildFactorDefinitionDraft({
        identity: {
          id: id.trim(),
          version,
          createdAt,
          parentVersion: parentVersionParsed,
        },
        editable: {
          hypothesis: hypothesis.trim(),
          calculation: {
            kind: calcKind,
            identity: calcIdentity.trim(),
            sourceHash: calcSourceHash.trim(),
          },
          parameters,
          output: {
            direction: outputDirection,
            unit: outputUnit.trim(),
          },
          dataDependencies,
          missingDataPolicy: missingDataPolicy.trim(),
          cohort,
          expectedHorizon: expectedHorizon.trim(),
          requiredTests: requiredTestsArray,
          failureGates: failureGatesArray,
        },
      });

      onReview(definition);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid input");
    }
  }

  return (
    <div className="factor-definition-editor">
      <Panel title="FactorDefinition editor" meta="Structured fields · Core validates">
        <fieldset disabled={isDisabled}>
          <TextInput label="id" value={id} onChange={(e) => setId(e.currentTarget.value)} required disabled={isDisabled} />
          <NumberInput label="version" value={version} onChange={(v) => v !== "" && setVersion(v)} min={1} required disabled={isDisabled} />
          <TextInput label="parentVersion" value={parentVersion} onChange={(e) => setParentVersion(e.currentTarget.value)} placeholder="Leave blank for v1" disabled={isDisabled} />
          <TextInput label="createdAt" value={createdAt} onChange={(e) => setCreatedAt(e.currentTarget.value)} required disabled={isDisabled} />

          <TextInput label="hypothesis" value={hypothesis} onChange={(e) => setHypothesis(e.currentTarget.value)} disabled={isDisabled} />

          <fieldset>
            <legend>calculation</legend>
            <Select label="kind" value={calcKind} onChange={(v) => v && setCalcKind(v)} data={[{ value: "source", label: "source" }, { value: "expression", label: "expression" }]} disabled={isDisabled} />
            <TextInput label="identity" value={calcIdentity} onChange={(e) => setCalcIdentity(e.currentTarget.value)} disabled={isDisabled} />
            <TextInput label="sourceHash" value={calcSourceHash} onChange={(e) => setCalcSourceHash(e.currentTarget.value)} disabled={isDisabled} />
          </fieldset>

          <Textarea label="parameters" description="Technical JSON object" value={parametersJson} onChange={(e) => setParametersJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />

          <fieldset>
            <legend>output</legend>
            <Select label="direction" value={outputDirection} onChange={(v) => v && setOutputDirection(v)} data={[{ value: "higher", label: "higher" }, { value: "lower", label: "lower" }, { value: "bidirectional", label: "bidirectional" }]} disabled={isDisabled} />
            <TextInput label="unit" value={outputUnit} onChange={(e) => setOutputUnit(e.currentTarget.value)} disabled={isDisabled} />
          </fieldset>

          <Textarea label="dataDependencies" description="Technical JSON array" value={dataDependenciesJson} onChange={(e) => setDataDependenciesJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />
          <TextInput label="missingDataPolicy" value={missingDataPolicy} onChange={(e) => setMissingDataPolicy(e.currentTarget.value)} disabled={isDisabled} />
          <Textarea label="cohort" description="Technical JSON object" value={cohortJson} onChange={(e) => setCohortJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />
          <TextInput label="expectedHorizon" value={expectedHorizon} onChange={(e) => setExpectedHorizon(e.currentTarget.value)} disabled={isDisabled} />
          <Textarea label="requiredTests" description="One per line · blank lines ignored" value={requiredTests} onChange={(e) => setRequiredTests(e.currentTarget.value)} autosize minRows={2} maxRows={6} disabled={isDisabled} />
          <Textarea label="failureGates" description="One per line · blank lines ignored" value={failureGates} onChange={(e) => setFailureGates(e.currentTarget.value)} autosize minRows={2} maxRows={6} disabled={isDisabled} />

          {error ? (
            <div className="factor-editor-error" role="alert">
              <p>{error}</p>
            </div>
          ) : null}

          <Button type="button" onClick={handleSubmit} disabled={isDisabled}>
            {busy ? "Validating" : "Review structured definition"}
          </Button>
        </fieldset>
      </Panel>
      <details className="technical-details">
        <summary>Technical Details</summary>
        <p>Fixed identity (kind, schema, status, lineage) comes from the approved <code>buildFactorDefinitionDraft</code> builder. Final validation is Core-owned and occurs on submission through the Operator Port.</p>
      </details>
    </div>
  );
}

export function ExperimentDefinitionEditor({ disabled, busy, onReview }) {
  const [id, setId] = useState("");
  const [version, setVersion] = useState(1);
  const [parentVersion, setParentVersion] = useState("");
  const [createdAt, setCreatedAt] = useState(new Date().toISOString());
  const [definitionRefKind, setDefinitionRefKind] = useState(null);
  const [definitionRefId, setDefinitionRefId] = useState("");
  const [definitionRefVersion, setDefinitionRefVersion] = useState(1);
  const [dataPackageId, setDataPackageId] = useState("");
  const [dataVersion, setDataVersion] = useState("");
  const [subjectKind, setSubjectKind] = useState(null);
  const [subjectId, setSubjectId] = useState("");
  const [subjectVersion, setSubjectVersion] = useState("");
  const [outcomeName, setOutcomeName] = useState("");
  const [outcomeHorizon, setOutcomeHorizon] = useState("");
  const [benchmarkId, setBenchmarkId] = useState("");
  const [benchmarkVersion, setBenchmarkVersion] = useState("");
  const [costPolicyJson, setCostPolicyJson] = useState("{}");
  const [splitPolicyJson, setSplitPolicyJson] = useState("{}");
  const [robustnessJson, setRobustnessJson] = useState("{}");
  const [selectionAdjustmentJson, setSelectionAdjustmentJson] = useState("{}");
  const [holdoutPolicyJson, setHoldoutPolicyJson] = useState("{}");
  const [executorPolicyJson, setExecutorPolicyJson] = useState("{}");
  const [candidateLimit, setCandidateLimit] = useState(0);
  const [wallTimeSeconds, setWallTimeSeconds] = useState(0);
  const [cpuSeconds, setCpuSeconds] = useState(0);
  const [gpuSeconds, setGpuSeconds] = useState(0);
  const [costCurrency, setCostCurrency] = useState("");
  const [costAmount, setCostAmount] = useState("");
  const [stopConditionsText, setStopConditionsText] = useState("");
  const [error, setError] = useState(null);

  const isDisabled = disabled || busy;

  function handleSubmit() {
    setError(null);
    try {
      if (!id.trim()) throw new Error("id is required");
      if (!Number.isInteger(version) || version < 1) throw new Error("version must be a positive integer");

      const parentVersionParsed = parentVersion.trim() === "" ? null : Number(parentVersion);
      if (parentVersionParsed !== null && (!Number.isInteger(parentVersionParsed) || parentVersionParsed < 1)) {
        throw new Error("parentVersion must be blank/null or a positive integer");
      }
      if (parentVersionParsed === null && version !== 1) {
        throw new Error("parentVersion must be provided for versions greater than 1");
      }
      if (!createdAt.trim()) throw new Error("createdAt is required");
      const parsedDate = new Date(createdAt);
      if (isNaN(parsedDate.getTime()) || parsedDate.toISOString() !== createdAt) {
        throw new Error("createdAt is not a valid ISO timestamp");
      }

      if (!definitionRefKind) throw new Error("definitionRef kind is required");
      if (!definitionRefId.trim()) throw new Error("definitionRef id is required");
      if (!Number.isInteger(definitionRefVersion) || definitionRefVersion < 1) throw new Error("definitionRef version must be a positive integer");

      if (!dataPackageId.trim()) throw new Error("data packageId is required");
      if (!dataVersion.trim()) throw new Error("data version is required");

      if (!subjectKind) throw new Error("subject kind is required");
      if (!subjectId.trim()) throw new Error("subject id is required");

      if (!outcomeName.trim()) throw new Error("outcome name is required");
      if (!outcomeHorizon.trim()) throw new Error("outcome horizon is required");

      if (!benchmarkId.trim()) throw new Error("benchmark id is required");
      if (!benchmarkVersion.trim()) throw new Error("benchmark version is required");

      const costPolicy = parseJsonObject(costPolicyJson);
      const splitPolicy = parseJsonObject(splitPolicyJson);
      const robustness = parseJsonObject(robustnessJson);
      const selectionAdjustment = parseJsonObject(selectionAdjustmentJson);
      const holdoutPolicy = parseJsonObject(holdoutPolicyJson);
      const executorPolicy = parseJsonObject(executorPolicyJson);

      if (!Number.isInteger(candidateLimit) || candidateLimit < 1) {
        throw new Error("candidateLimit must be a positive integer");
      }
      if (!Number.isInteger(wallTimeSeconds) || wallTimeSeconds < 1) {
        throw new Error("wallTimeSeconds must be a positive integer");
      }
      if (!Number.isInteger(cpuSeconds) || cpuSeconds < 1) {
        throw new Error("cpuSeconds must be a positive integer");
      }
      if (!Number.isInteger(gpuSeconds) || gpuSeconds < 0) {
        throw new Error("gpuSeconds must be a non-negative integer");
      }

      const costCurrencyTrimmed = costCurrency.trim();
      const costAmountTrimmed = costAmount.trim();

      let cost;
      if (costCurrencyTrimmed === "" && costAmountTrimmed === "") {
        cost = null;
      } else if (costCurrencyTrimmed === "" || costAmountTrimmed === "") {
        throw new Error("cost currency and amount must be provided together");
      } else {
        const amount = Number(costAmountTrimmed);
        if (!Number.isFinite(amount) || amount < 0) {
          throw new Error("cost amount must be a finite non-negative number");
        }
        cost = { currency: costCurrencyTrimmed, amount };
      }

      const budget = {
        candidateLimit,
        wallTimeSeconds,
        cpuSeconds,
        gpuSeconds,
        cost,
      };

      const stopConditions = stopConditionsText
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

      const definition = buildExperimentDefinitionDraft({
        identity: {
          id: id.trim(),
          version,
          createdAt,
          parentVersion: parentVersionParsed,
        },
        editable: {
          definitionRef: {
            kind: definitionRefKind,
            id: definitionRefId.trim(),
            version: definitionRefVersion,
          },
          data: {
            packageId: dataPackageId.trim(),
            version: dataVersion.trim(),
          },
          subject: {
            kind: subjectKind,
            id: subjectId.trim(),
            version: subjectVersion.trim(),
          },
          outcome: {
            name: outcomeName.trim(),
            horizon: outcomeHorizon.trim(),
          },
          benchmark: {
            id: benchmarkId.trim(),
            version: benchmarkVersion.trim(),
          },
          costPolicy,
          splitPolicy,
          robustness,
          selectionAdjustment,
          holdoutPolicy,
          executorPolicy,
          budget,
          stopConditions,
        },
      });

      onReview(definition);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid input");
    }
  }

  const kindOptions = [{ value: "factor", label: "factor" }, { value: "strategy", label: "strategy" }];

  return (
    <div className="experiment-definition-editor">
      <Panel title="ExperimentDefinition editor" meta="Structured fields · Core validates">
        <fieldset disabled={isDisabled}>
          <fieldset>
            <legend>identity</legend>
            <TextInput label="id" value={id} onChange={(e) => setId(e.currentTarget.value)} required disabled={isDisabled} />
            <NumberInput label="version" value={version} onChange={(v) => v !== "" && setVersion(v)} min={1} required disabled={isDisabled} />
            <TextInput label="parentVersion" value={parentVersion} onChange={(e) => setParentVersion(e.currentTarget.value)} placeholder="Leave blank for v1" disabled={isDisabled} />
            <TextInput label="createdAt" value={createdAt} onChange={(e) => setCreatedAt(e.currentTarget.value)} required disabled={isDisabled} />
          </fieldset>

          <fieldset>
            <legend>definitionRef</legend>
            <Select label="kind" value={definitionRefKind} onChange={(v) => v && setDefinitionRefKind(v)} data={kindOptions} disabled={isDisabled} />
            <TextInput label="id" value={definitionRefId} onChange={(e) => setDefinitionRefId(e.currentTarget.value)} required disabled={isDisabled} />
            <NumberInput label="version" value={definitionRefVersion} onChange={(v) => v !== "" && setDefinitionRefVersion(v)} min={1} required disabled={isDisabled} />
          </fieldset>

          <fieldset>
            <legend>data</legend>
            <TextInput label="packageId" value={dataPackageId} onChange={(e) => setDataPackageId(e.currentTarget.value)} required disabled={isDisabled} />
            <TextInput label="version" value={dataVersion} onChange={(e) => setDataVersion(e.currentTarget.value)} required disabled={isDisabled} />
          </fieldset>

          <fieldset>
            <legend>subject</legend>
            <Select label="kind" value={subjectKind} onChange={(v) => v && setSubjectKind(v)} data={kindOptions} disabled={isDisabled} />
            <TextInput label="id" value={subjectId} onChange={(e) => setSubjectId(e.currentTarget.value)} required disabled={isDisabled} />
            <TextInput label="version" value={subjectVersion} onChange={(e) => setSubjectVersion(e.currentTarget.value)} disabled={isDisabled} />
          </fieldset>

          <fieldset>
            <legend>outcome</legend>
            <TextInput label="name" value={outcomeName} onChange={(e) => setOutcomeName(e.currentTarget.value)} required disabled={isDisabled} />
            <TextInput label="horizon" value={outcomeHorizon} onChange={(e) => setOutcomeHorizon(e.currentTarget.value)} required disabled={isDisabled} />
          </fieldset>

          <fieldset>
            <legend>benchmark</legend>
            <TextInput label="id" value={benchmarkId} onChange={(e) => setBenchmarkId(e.currentTarget.value)} required disabled={isDisabled} />
            <TextInput label="version" value={benchmarkVersion} onChange={(e) => setBenchmarkVersion(e.currentTarget.value)} required disabled={isDisabled} />
          </fieldset>

          <Textarea label="costPolicy" description="Technical JSON object" value={costPolicyJson} onChange={(e) => setCostPolicyJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />
          <Textarea label="splitPolicy" description="Technical JSON object" value={splitPolicyJson} onChange={(e) => setSplitPolicyJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />
          <Textarea label="robustness" description="Technical JSON object" value={robustnessJson} onChange={(e) => setRobustnessJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />
          <Textarea label="selectionAdjustment" description="Technical JSON object" value={selectionAdjustmentJson} onChange={(e) => setSelectionAdjustmentJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />
          <Textarea label="holdoutPolicy" description="Technical JSON object" value={holdoutPolicyJson} onChange={(e) => setHoldoutPolicyJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />
          <Textarea label="executorPolicy" description="Technical JSON object" value={executorPolicyJson} onChange={(e) => setExecutorPolicyJson(e.currentTarget.value)} autosize minRows={3} maxRows={8} disabled={isDisabled} />

          <fieldset>
            <legend>budget</legend>
            <NumberInput label="candidateLimit" value={candidateLimit} onChange={(v) => v !== "" && setCandidateLimit(v)} min={0} disabled={isDisabled} />
            <NumberInput label="wallTimeSeconds" value={wallTimeSeconds} onChange={(v) => v !== "" && setWallTimeSeconds(v)} min={0} disabled={isDisabled} />
            <NumberInput label="cpuSeconds" value={cpuSeconds} onChange={(v) => v !== "" && setCpuSeconds(v)} min={0} disabled={isDisabled} />
            <NumberInput label="gpuSeconds" value={gpuSeconds} onChange={(v) => v !== "" && setGpuSeconds(v)} min={0} disabled={isDisabled} />
            <TextInput label="cost currency" value={costCurrency} onChange={(e) => setCostCurrency(e.currentTarget.value)} disabled={isDisabled} />
            <NumberInput label="cost amount" value={costAmount} onChange={(v) => setCostAmount(v === "" ? "" : String(v))} min={0} disabled={isDisabled} />
          </fieldset>

          <Textarea label="stopConditions" description="One per line · blank lines ignored" value={stopConditionsText} onChange={(e) => setStopConditionsText(e.currentTarget.value)} autosize minRows={2} maxRows={6} disabled={isDisabled} />

          {error ? (
            <div className="experiment-editor-error" role="alert">
              <p>{error}</p>
            </div>
          ) : null}

          <Button type="button" onClick={handleSubmit} disabled={isDisabled}>
            {busy ? "Validating" : "Review structured definition"}
          </Button>
        </fieldset>
      </Panel>
      <details className="technical-details">
        <summary>Technical Details</summary>
        <p>Fixed identity (kind, schema, status, lineage) comes from the approved <code>buildExperimentDefinitionDraft</code> builder. Final validation is Core-owned and occurs on submission through the Operator Port.</p>
      </details>
    </div>
  );
}

function validate64Hex(value) {
  if (typeof value !== "string" || value.length !== 64) return false;
  return /^[a-f0-9]{64}$/.test(value);
}

export function ArtifactReviewEditor({ disabled, busy, onReview }) {
  const [id, setId] = useState("");
  const [decision, setDecision] = useState(null);
  const [actorId, setActorId] = useState("");
  const [actorKind, setActorKind] = useState("");
  const [definitionKind, setDefinitionKind] = useState(null);
  const [definitionId, setDefinitionId] = useState("");
  const [definitionVersion, setDefinitionVersion] = useState(1);
  const [definitionHash, setDefinitionHash] = useState("");
  const [evidenceManifestJson, setEvidenceManifestJson] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState(null);

  const isDisabled = disabled || busy;

  function handleSubmit() {
    setError(null);
    try {
      if (!(id && id.trim())) throw new Error("Review id is required.");
      if (!decision) throw new Error("Decision is required.");
      if (!(actorId && actorId.trim())) throw new Error("Actor id is required.");
      if (!(actorKind && actorKind.trim())) throw new Error("Actor kind is required.");
      if (!definitionKind) throw new Error("Definition kind is required.");
      if (!(definitionId && definitionId.trim())) throw new Error("Definition id is required.");
      if (!Number.isInteger(definitionVersion) || definitionVersion < 1) throw new Error("Definition version must be a positive integer.");
      if (!validate64Hex(definitionHash)) throw new Error("Definition hash must be exactly 64 lowercase hex characters.");
      if (!(reason && reason.trim())) throw new Error("Reason is required.");

      const evidenceManifest = parseJsonObject(evidenceManifestJson);

      const review = buildArtifactReviewDraft({
        id: id.trim(),
        decision,
        actor: { id: actorId.trim(), kind: actorKind.trim() },
        definitionRef: { kind: definitionKind, id: definitionId.trim(), version: definitionVersion },
        definitionHash,
        evidenceManifest,
        reason: reason.trim(),
      });

      onReview(review);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid input");
    }
  }

  return (
    <div className="artifact-review-editor">
      <Panel title="Artifact review decision" meta="Structured fields · Core validates">
        <fieldset disabled={isDisabled}>
          <TextInput label="Review id" value={id} onChange={(e) => setId(e.currentTarget.value)} required disabled={isDisabled} />

          <Select label="Decision" value={decision} onChange={(v) => v && setDecision(v)} data={[{ value: "approve", label: "Approve" }, { value: "return-for-revision", label: "Return for revision" }, { value: "retain-as-draft", label: "Retain as draft" }]} disabled={isDisabled} />

          <fieldset>
            <legend>Actor</legend>
            <TextInput label="Actor id" value={actorId} onChange={(e) => setActorId(e.currentTarget.value)} required disabled={isDisabled} />
            <TextInput label="Actor kind" value={actorKind} onChange={(e) => setActorKind(e.currentTarget.value)} required disabled={isDisabled} />
          </fieldset>

          <fieldset>
            <legend>Definition reference</legend>
            <Select label="Definition kind" value={definitionKind} onChange={(v) => v && setDefinitionKind(v)} data={[{ value: "factor", label: "factor" }, { value: "strategy", label: "strategy" }]} disabled={isDisabled} />
            <TextInput label="Definition id" value={definitionId} onChange={(e) => setDefinitionId(e.currentTarget.value)} required disabled={isDisabled} />
            <NumberInput label="Definition version" value={definitionVersion} onChange={(v) => v !== "" && setDefinitionVersion(v)} min={1} required disabled={isDisabled} />
            <TextInput label="Definition hash" value={definitionHash} onChange={(e) => setDefinitionHash(e.currentTarget.value)} required disabled={isDisabled} placeholder="64 hex characters" />
          </fieldset>

          <Textarea label="Core evidenceManifest JSON" description="Paste exact evidenceManifest from Core projection only. Must be a verified 12-field Core evidenceManifest object — do not fabricate or guess. Final authenticity is validated by Core." value={evidenceManifestJson} onChange={(e) => setEvidenceManifestJson(e.currentTarget.value)} autosize minRows={6} maxRows={24} spellCheck={false} disabled={isDisabled} />

          <TextInput label="Reason" value={reason} onChange={(e) => setReason(e.currentTarget.value)} required disabled={isDisabled} />

          {error ? (
            <div className="artifact-review-error" role="alert">
              <p>{error}</p>
            </div>
          ) : null}

          <Button type="button" onClick={handleSubmit} disabled={isDisabled}>
            {busy ? "Validating" : "Review structured artifact decision"}
          </Button>
        </fieldset>
      </Panel>
    </div>
  );
}

export function ReproductionRequestEditor({ disabled, busy, onReview }) {
  const [id, setId] = useState("");
  const [approvalId, setApprovalId] = useState("");
  const [error, setError] = useState(null);

  const isDisabled = disabled || busy;

  function handleSubmit() {
    setError(null);
    try {
      if (!(id && id.trim())) throw new Error("Request id is required.");
      if (!(approvalId && approvalId.trim())) throw new Error("Approved artifact decision id is required.");

      const reproduction = buildReproductionRequestDraft({
        id: id.trim(),
        approvalId: approvalId.trim(),
      });

      onReview(reproduction);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid input");
    }
  }

  return (
    <div className="reproduction-request-editor">
      <Panel title="Reproduction request" meta="Structured fields · Core validates">
        <fieldset disabled={isDisabled}>
          <TextInput label="Request id" value={id} onChange={(e) => setId(e.currentTarget.value)} required disabled={isDisabled} />
          <TextInput label="Approved artifact decision id" value={approvalId} onChange={(e) => setApprovalId(e.currentTarget.value)} required disabled={isDisabled} />

          <p className="reproduction-note">Results are produced exclusively by Core receipt. When no private executor is available, Core must return <code>unavailable</code> — this editor cannot declare results.</p>

          {error ? (
            <div className="reproduction-request-error" role="alert">
              <p>{error}</p>
            </div>
          ) : null}

          <Button type="button" onClick={handleSubmit} disabled={isDisabled}>
            {busy ? "Validating" : "Request reproduction"}
          </Button>
        </fieldset>
      </Panel>
    </div>
  );
}

function ReviewInspector({ selectedStage, receipts, pendingConfirmation, mutationIntent, setMutationIntent, disabled, busy, onMutation, onConfirm, onSaveDraft, onReturnForRevision, campaignRunning, stopCampaign, stopDisabled }) {
  const isFactor = mutationIntent === "definition.factor.create";
  const isExperiment = mutationIntent === "definition.experiment.create";
  const isArtifact = mutationIntent === "artifact.decide";
  const isReproduction = mutationIntent === "reproduction.start";

  return (
    <div className="research-inspector-content">
      <Panel title="Review inspector" meta="Core fields only">
        <p><b>{selectedStage?.label || "No stage"}</b> · {selectedStage?.state || "unavailable"}</p>
        <div className="object-list">{selectedStage?.objects?.map((item, index) => <ObjectRef key={`${item.kind}-${item.id}-${index}`} value={item} />)}</div>
        {campaignRunning ? <div className="button-row"><Button type="button" onClick={stopCampaign} disabled={stopDisabled}>Stop Campaign now</Button></div> : null}
      </Panel>

      <Panel title="Mutation intent" meta="Closed set · Core validates">
        <Select label="Structured intent" value={mutationIntent} onChange={(value) => value && setMutationIntent(value)} data={REVIEW_MUTATION_INTENTS.map((value) => ({ value, label: INTENT_LABEL[value] }))} disabled={disabled || busy} />
      </Panel>

      {isFactor ? (
        <FactorDefinitionEditor disabled={disabled} busy={busy} onReview={(definition) => onMutation({ definition })} />
      ) : isExperiment ? (
        <ExperimentDefinitionEditor disabled={disabled} busy={busy} onReview={(definition) => onMutation({ definition })} />
      ) : isArtifact ? (
        <ArtifactReviewEditor disabled={disabled} busy={busy} onReview={(review) => onMutation({ review })} />
      ) : isReproduction ? (
        <ReproductionRequestEditor disabled={disabled} busy={busy} onReview={(reproduction) => onMutation({ reproduction })} />
      ) : null}

      {disabled ? <p className="notice">Review-only viewport or unavailable Core projection: mutation is disabled.</p> : null}

      {pendingConfirmation ? (
        <Panel title="Confirmation inspector" meta="One primary confirmation boundary">
          <OperationReceiptCard receipt={pendingConfirmation.receipt} />
          <pre>{JSON.stringify({ intent: pendingConfirmation.request.intent, objectRefs: pendingConfirmation.request.objectRefs, budget: pendingConfirmation.request.budget, input: pendingConfirmation.request.input }, null, 2)}</pre>
          <div className="button-row"><Button type="button" onClick={onConfirm} disabled={busy}>Confirm exact request</Button></div>
          <div className="button-row"><Button variant="quiet" type="button" onClick={onSaveDraft} disabled={busy}>Save draft</Button><Button variant="quiet" type="button" onClick={onReturnForRevision} disabled={busy}>Return for revision</Button></div>
        </Panel>
      ) : null}
      <Panel title="Semantic diff" meta="Core-authored"><SemanticDiff receipts={receipts} pendingReceipt={pendingConfirmation?.receipt || null} /></Panel>
    </div>
  );
}

export function ResearchConsole({ snapshot, project, bundle, ledger, diagnostics = [] }) {
  const [activeStageId, setActiveStageId] = useState(ledger?.stages?.[0]?.id || RESEARCH_STAGE_ORDER[0]);
  const [receipts, setReceipts] = useState(ledger?.receipts || []);
  const [status, setStatus] = useState("Ready. No operation is running.");
  const [busy, setBusy] = useState(false);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [mutationIntent, setMutationIntent] = useState(REVIEW_MUTATION_INTENTS[0]);
  const [pendingConfirmation, setPendingConfirmation] = useState(null);
  const [viewportWidth, setViewportWidth] = useState(null);
  const [stopBusy, setStopBusy] = useState(false);
  const stopCampaignRef = useRef(null);
  useEffect(() => {
    const updateViewport = () => setViewportWidth(window.innerWidth);
    updateViewport();
    window.addEventListener("resize", updateViewport);
    return () => window.removeEventListener("resize", updateViewport);
  }, []);
  const desktop = viewportWidth !== null && viewportWidth >= 1024;
  const wide = viewportWidth !== null && viewportWidth >= 1440;
  const drawerMode = desktop && !wide;
  const reviewOnly = viewportWidth === null || !desktop;
  const isPending = pendingConfirmation !== null;
  const stages = useMemo(() => ledger?.stages || [], [ledger]);
  const selectedStage = stages.find((stage) => stage.id === activeStageId) || stages[0];
  const compareRefs = useMemo(() => exactCompareRefs(stages), [stages]);

  async function invoke(request) {
    setBusy(true);
    setStatus(`Submitting ${request.intent} to Core.`);
    try {
      const response = await fetch("/api/studio/operator", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(request) });
      const payload = await response.json();
      const receipt = receiptFromEnvelope(payload);
      setReceipts((current) => [...current.filter((item) => item.requestId !== receipt.requestId), receipt]);
      setStatus(`${receipt.intent} finished with status ${receipt.status}.`);
      return receipt;
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Operator request failed.");
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function runReadOnly(intent) {
    const objectRefs = intent === "research.compare" ? compareRefs : [];
    if (intent === "research.compare" && objectRefs.length !== 2) {
      setStatus("Compare requires two published versions of the same definition.");
      return;
    }
    await invoke(buildOperatorRequest({ snapshot, project, bundle, intent, objectRefs }));
  }

  function reviewMutation(structuredInput) {
    if (structuredInput === undefined) {
      throw new Error("reviewMutation requires explicit structured input; raw JSON whole-contract bypass is not accepted. Use ArtifactReviewEditor or ReproductionRequestEditor.");
    }
    try {
      const request = buildOperatorRequest({ snapshot, project, bundle, intent: mutationIntent, input: structuredInput });
      return invoke(request).then((receipt) => {
        if (receipt?.status === "confirmation-required") {
          setPendingConfirmation({ request, receipt });
          if (drawerMode) setInspectorOpen(true);
        }
      });
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Invalid structured input.");
      return Promise.resolve();
    }
  }

  async function confirmMutation() {
    if (!pendingConfirmation) return;
    const decisionRequest = buildOperatorRequest({
      snapshot,
      project,
      bundle,
      intent: "confirmation.accept",
      input: { executionActor: pendingConfirmation.request.actor },
      objectRefs: pendingConfirmation.request.objectRefs,
      confirmationRef: pendingConfirmation.receipt.requestId,
      actor: { id: "autoquant-studio-local-user", kind: "user" },
    });
    const decision = await invoke(decisionRequest);
    if (decision?.status !== "completed") return;
    const confirmed = buildOperatorRequest({ snapshot, project, bundle, intent: pendingConfirmation.request.intent, input: pendingConfirmation.request.input, objectRefs: pendingConfirmation.request.objectRefs, confirmationRef: decision.requestId });
    const receipt = await invoke(confirmed);
    if (receipt) setPendingConfirmation(null);
  }

  function saveDraft() {
    if (!pendingConfirmation) return;
    setStatus("Draft retained — no changes submitted to Core.");
  }

  function returnForRevision() {
    if (!pendingConfirmation) return;
    setPendingConfirmation(null);
    setStatus("Returned for revision — pending confirmation cleared.");
    if (drawerMode && inspectorOpen) setInspectorOpen(false);
  }

  async function stopCampaign() {
    if (stopCampaignRef.current || !stoppableCampaign) return;
    setStopBusy(true);
    try {
      const promise = invoke(buildOperatorRequest({ snapshot, project, bundle, intent: "campaign.stop", objectRefs: [{ kind: "campaign", id: stoppableCampaign.campaignId, version: null }] }));
      stopCampaignRef.current = promise;
      await promise;
    } finally {
      stopCampaignRef.current = null;
      setStopBusy(false);
    }
  }

  const stoppableCampaign = (bundle.progress || []).find((p) =>
    p.status === "running" &&
    !receipts.some((r) =>
      r.intent === "campaign.stop" &&
      r.status === "stopped" &&
      Array.isArray(r.evidence) &&
      r.evidence.some((e) => e?.kind === "autoquant-campaign-stop-request" && e?.campaignId === p.campaignId)
    )
  ) || null;

  const campaignRunning = Boolean(stoppableCampaign);

  if (!ledger) return <EmptyState title="ResearchLedger unavailable" detail={diagnostics.map((item) => item.message).join(" · ") || "Core did not publish a verified ledger for this Session."} />;

  const stopDisabled = busy || !campaignRunning || stopBusy;

  const inspector = <ReviewInspector selectedStage={selectedStage} receipts={receipts} pendingConfirmation={pendingConfirmation} mutationIntent={mutationIntent} setMutationIntent={setMutationIntent} disabled={Boolean(reviewOnly) || isPending} busy={busy} onMutation={reviewMutation} onConfirm={confirmMutation} onSaveDraft={saveDraft} onReturnForRevision={returnForRevision} campaignRunning={campaignRunning} stopCampaign={stopCampaign} stopDisabled={stopDisabled} />;

  return (
    <section className="research-console" aria-label="Agent research console">
      <a className="skip-link" href="#research-active-canvas">Skip to active research canvas</a>
      <div className="sr-live" role="status" aria-live="polite">{status}</div>
      {reviewOnly ? <div className="review-only-banner" role="note">Review-only below 1024 px. Evidence and receipts remain visible; mutations are disabled.</div> : null}
      <aside className="research-conversation" aria-label="Structured conversation and operations">
        <Panel title="Structured operations" meta="Chat text has no execution authority">
          <div className="structured-actions">{READ_ONLY_INTENTS.map((intent) => <Button key={intent} variant="secondary" type="button" onClick={() => runReadOnly(intent)} disabled={busy || (intent === "research.compare" && compareRefs.length !== 2)}>{INTENT_LABEL[intent]}</Button>)}</div>
        </Panel>
        <StageRail stages={stages} activeId={selectedStage?.id} onSelect={(id) => { setActiveStageId(id); if (drawerMode) setInspectorOpen(true); }} />
        <Panel title="Operation receipts" meta={`${receipts.length} immutable receipt(s)`}><div className="receipt-list">{receipts.length ? receipts.slice().reverse().map((receipt) => <OperationReceiptCard key={receipt.requestId} receipt={receipt} />) : <EmptyState title="No receipts" detail="Run a structured inspect action to create one." />}</div></Panel>
      </aside>
      <section className="research-canvas" id="research-active-canvas" tabIndex={-1} aria-label="Dominant research stage canvas"><StageCanvas stage={selectedStage} bundle={bundle} receipts={receipts} /><details className="research-task-tray"><summary>Task tray · bounded campaign controls</summary><p>Immediate stop uses the closed Operator Port and preserves completed evidence. Start, pause, and resume remain unavailable because Core has not published those intents; no shell or provider command is exposed.</p><div className="button-row"><Button type="button" disabled>Start</Button><Button type="button" disabled>Pause</Button><Button type="button" disabled>Resume</Button><Button type="button" onClick={stopCampaign} disabled={stopDisabled}>Stop now</Button></div></details></section>
      <aside className="research-inspector" aria-label="Review inspector">{!drawerMode && !reviewOnly ? inspector : null}</aside>
      {drawerMode ? <Button className="research-inspector-trigger" type="button" variant="secondary" onClick={() => setInspectorOpen(true)}>Open inspector</Button> : null}
      <Drawer opened={Boolean(drawerMode && inspectorOpen)} onClose={() => setInspectorOpen(false)} title="Research review inspector" position="right" size="360" returnFocus trapFocus>{inspector}</Drawer>
      {reviewOnly ? <section className="research-review-only-inspector" aria-label="Review inspector read-only copy">{inspector}</section> : null}
    </section>
  );
}
