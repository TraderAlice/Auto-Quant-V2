"""Deterministic, non-accusatory research-claim verification contracts."""

from __future__ import annotations

import math
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from .studies import DIRECTIONS, SHA256, hash_file, hash_json
from .workspace import (
    SCHEMA_VERSION,
    AutoQuantValidationError,
    ProjectContext,
    ValidationIssue,
    confined_path,
)


RESEARCH_CLAIM_KIND = "autoquant-research-claim"
VERIFICATION_ASSESSMENT_KIND = "autoquant-verification-assessment"
VERDICTS = {"invalid-test", "inconclusive", "contradicted", "supported"}
VERIFICATIONS_DIRECTORY = "verifications"
_CLAIM_KEYS = {
    "schemaVersion",
    "kind",
    "id",
    "statement",
    "metric",
    "direction",
    "minimumEffect",
    "requirements",
    "authority",
    "tradingAuthority",
}
_REQUIREMENT_KEYS = {
    "minimumSampleSize",
    "baselineRequired",
    "holdoutRequired",
    "selectionRequired",
}
_EVIDENCE_KINDS = ("run", "explorer", "holdout", "selection")
_ASSESSMENT_KEYS = {
    "schemaVersion",
    "kind",
    "id",
    "claimId",
    "claimHash",
    "verdict",
    "gates",
    "primaryImprovement",
    "limitations",
    "evidenceRefs",
    "authority",
    "tradingAuthority",
}


def _issue(path: Path | str, code: str, message: str) -> ValidationIssue:
    return ValidationIssue(str(path), code, message)


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def build_research_claim(
    *,
    statement: str,
    metric: str,
    direction: str,
    minimum_effect: float = 0.0,
    minimum_sample_size: int = 30,
    baseline_required: bool = True,
    holdout_required: bool = True,
    selection_required: bool = True,
) -> dict[str, Any]:
    """Build one content-addressed claim without inferring author intent."""

    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": RESEARCH_CLAIM_KIND,
        "statement": statement,
        "metric": metric,
        "direction": direction,
        "minimumEffect": minimum_effect,
        "requirements": {
            "minimumSampleSize": minimum_sample_size,
            "baselineRequired": baseline_required,
            "holdoutRequired": holdout_required,
            "selectionRequired": selection_required,
        },
        "authority": "research-validation-only",
        "tradingAuthority": "none",
    }
    claim = {**payload, "id": f"research-claim-{hash_json(payload)[:16]}"}
    return validate_research_claim(claim)


def validate_research_claim(
    value: Any,
    path: Path | str = "researchClaim",
) -> dict[str, Any]:
    """Validate the exact V1 ResearchClaim surface and derived identity."""

    issues: list[ValidationIssue] = []
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "research-claim.type", "ResearchClaim must be an object")]
        )
    for key in sorted(_CLAIM_KEYS - value.keys()):
        issues.append(_issue(f"{path}/{key}", "schema.missing", f"Missing '{key}'"))
    for key in sorted(value.keys() - _CLAIM_KEYS):
        issues.append(_issue(f"{path}/{key}", "schema.unknown", f"Unknown '{key}'"))
    requirements = value.get("requirements")
    if not isinstance(requirements, dict) or set(requirements) != _REQUIREMENT_KEYS:
        issues.append(
            _issue(
                f"{path}/requirements",
                "research-claim.requirements",
                "ResearchClaim requirements must use the exact V1 fields",
            )
        )
        requirements = {}
    if value.get("schemaVersion") != SCHEMA_VERSION:
        issues.append(_issue(f"{path}/schemaVersion", "schema.version", "Expected V1"))
    if value.get("kind") != RESEARCH_CLAIM_KIND:
        issues.append(_issue(f"{path}/kind", "research-claim.kind", "Invalid kind"))
    if not isinstance(value.get("statement"), str) or not value.get("statement", "").strip():
        issues.append(_issue(f"{path}/statement", "research-claim.statement", "Statement must be non-empty"))
    if not isinstance(value.get("metric"), str) or not value.get("metric", "").strip():
        issues.append(_issue(f"{path}/metric", "research-claim.metric", "Metric must be non-empty"))
    if value.get("direction") not in DIRECTIONS:
        issues.append(_issue(f"{path}/direction", "research-claim.direction", "Direction must be maximize or minimize"))
    if not _finite_number(value.get("minimumEffect")) or float(value.get("minimumEffect", -1)) < 0:
        issues.append(_issue(f"{path}/minimumEffect", "research-claim.minimum-effect", "minimumEffect must be finite and non-negative"))
    if (
        not isinstance(requirements.get("minimumSampleSize"), int)
        or isinstance(requirements.get("minimumSampleSize"), bool)
        or requirements.get("minimumSampleSize", 0) < 1
    ):
        issues.append(_issue(f"{path}/requirements/minimumSampleSize", "research-claim.minimum-sample", "minimumSampleSize must be positive"))
    for key in ("baselineRequired", "holdoutRequired", "selectionRequired"):
        if not isinstance(requirements.get(key), bool):
            issues.append(_issue(f"{path}/requirements/{key}", "research-claim.requirement", f"{key} must be boolean"))
    if value.get("authority") != "research-validation-only" or value.get("tradingAuthority") != "none":
        issues.append(_issue(path, "research-claim.authority", "ResearchClaim cannot grant trading authority"))
    payload = {key: value.get(key) for key in _CLAIM_KEYS - {"id"}}
    expected_id = f"research-claim-{hash_json(payload)[:16]}"
    if value.get("id") != expected_id:
        issues.append(_issue(f"{path}/id", "research-claim.derived-id", "ResearchClaim id does not match its content"))
    if issues:
        raise AutoQuantValidationError(issues)
    return {**payload, "id": expected_id}


def _evidence_ref(kind: str, value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    evidence_id = value.get("id")
    evidence_hash = value.get("hash")
    if (
        not isinstance(evidence_id, str)
        or not evidence_id.strip()
        or not isinstance(evidence_hash, str)
        or SHA256.fullmatch(evidence_hash) is None
    ):
        return None
    return {"kind": kind, "id": evidence_id, "sha256": evidence_hash}


def _metric_gate(
    claim: dict[str, Any],
    evidence: Any,
) -> tuple[str, float | None]:
    """Return missing, invalid, low-sample, no-baseline, pass, or contradict."""

    if not isinstance(evidence, dict):
        return "missing", None
    required = {"id", "hash", "metric", "primaryValue", "sampleSize"}
    if not required.issubset(evidence) or _evidence_ref("metric", evidence) is None:
        return "invalid", None
    if evidence.get("metric") != claim["metric"]:
        return "invalid", None
    if not _finite_number(evidence.get("primaryValue")):
        return "invalid", None
    sample_size = evidence.get("sampleSize")
    if not isinstance(sample_size, int) or isinstance(sample_size, bool) or sample_size < 0:
        return "invalid", None
    if sample_size < claim["requirements"]["minimumSampleSize"]:
        return "low-sample", None
    baseline = evidence.get("baselineValue")
    if claim["requirements"]["baselineRequired"] and not _finite_number(baseline):
        return "no-baseline", None
    if not _finite_number(baseline):
        improvement = float(evidence["primaryValue"])
    elif claim["direction"] == "maximize":
        improvement = float(evidence["primaryValue"]) - float(baseline)
    else:
        improvement = float(baseline) - float(evidence["primaryValue"])
    if improvement < 0:
        return "contradict", improvement
    if improvement < float(claim["minimumEffect"]):
        return "below-effect", improvement
    return "pass", improvement


def assess_research_claim(
    claim: dict[str, Any],
    *,
    run_evidence: dict[str, Any] | None,
    explorer_evidence: dict[str, Any] | None,
    holdout_evidence: dict[str, Any] | None = None,
    selection_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assess verified evidence with fixed, conservative verdict precedence."""

    claim = validate_research_claim(claim)
    evidence = {
        "run": run_evidence,
        "explorer": explorer_evidence,
        "holdout": holdout_evidence,
        "selection": selection_evidence,
    }
    refs = [
        ref
        for kind in _EVIDENCE_KINDS
        if (ref := _evidence_ref(kind, evidence[kind])) is not None
    ]
    limitations: list[str] = []
    invalid: list[str] = []
    run = run_evidence if isinstance(run_evidence, dict) else {}
    integrity = run.get("integrity")
    if not run:
        limitations.append("required-run-evidence-missing")
    elif _evidence_ref("run", run) is None or not isinstance(integrity, dict):
        invalid.append("run-evidence-schema-invalid")
    else:
        if integrity.get("tampered") is not False:
            invalid.append("run-integrity-tampered-or-unverified")
        if integrity.get("lookaheadDetected") is not False:
            invalid.append("lookahead-absent-not-proven")
        if integrity.get("schemaValid") is not True:
            invalid.append("run-schema-invalid")
        if integrity.get("authorityValid") is not True:
            invalid.append("run-authority-invalid")

    primary_gate, primary_improvement = _metric_gate(claim, explorer_evidence)
    if primary_gate == "invalid":
        invalid.append("explorer-evidence-schema-invalid")
    elif primary_gate != "pass" and primary_gate != "contradict":
        limitations.append(f"primary-{primary_gate}")

    holdout_gate: str | None = None
    if claim["requirements"]["holdoutRequired"]:
        holdout_gate, _ = _metric_gate(claim, holdout_evidence)
        if holdout_gate == "invalid":
            invalid.append("holdout-evidence-schema-invalid")
        elif holdout_gate != "pass" and holdout_gate != "contradict":
            limitations.append(f"holdout-{holdout_gate}")

    selection_passed: bool | None = None
    if claim["requirements"]["selectionRequired"]:
        if not isinstance(selection_evidence, dict):
            limitations.append("required-selection-evidence-missing")
        elif _evidence_ref("selection", selection_evidence) is None or not isinstance(selection_evidence.get("passed"), bool):
            invalid.append("selection-evidence-schema-invalid")
        else:
            selection_passed = selection_evidence["passed"]
            if not selection_passed:
                limitations.append("selection-gate-failed")

    contradicted = primary_gate == "contradict" or holdout_gate == "contradict"
    indeterminate = any(
        limitation.endswith(("-missing", "-low-sample"))
        for limitation in limitations
    )
    if invalid:
        verdict = "invalid-test"
        limitations = invalid + limitations
    elif indeterminate:
        verdict = "inconclusive"
    elif contradicted:
        verdict = "contradicted"
    elif limitations:
        verdict = "inconclusive"
    else:
        verdict = "supported"
    payload = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": VERIFICATION_ASSESSMENT_KIND,
        "claimId": claim["id"],
        "claimHash": hash_json(claim),
        "verdict": verdict,
        "gates": {
            "primary": primary_gate,
            "holdout": holdout_gate,
            "selectionPassed": selection_passed,
        },
        "primaryImprovement": primary_improvement,
        "limitations": limitations,
        "evidenceRefs": refs,
        "authority": "research-validation-only",
        "tradingAuthority": "none",
    }
    assessment = {
        **payload,
        "id": f"verification-assessment-{hash_json(payload)[:16]}",
    }
    return validate_verification_assessment(assessment)


def validate_verification_assessment(
    value: Any,
    path: Path | str = "verificationAssessment",
) -> dict[str, Any]:
    """Validate the exact V1 assessment surface and immutable identity."""

    issues: list[ValidationIssue] = []
    if not isinstance(value, dict):
        raise AutoQuantValidationError(
            [_issue(path, "verification-assessment.type", "VerificationAssessment must be an object")]
        )
    if set(value) != _ASSESSMENT_KEYS:
        issues.append(_issue(path, "verification-assessment.schema", "VerificationAssessment must use the exact V1 fields"))
    if value.get("schemaVersion") != SCHEMA_VERSION or value.get("kind") != VERIFICATION_ASSESSMENT_KIND:
        issues.append(_issue(path, "verification-assessment.version", "Invalid VerificationAssessment version or kind"))
    if value.get("verdict") not in VERDICTS:
        issues.append(_issue(f"{path}/verdict", "verification-assessment.verdict", "Unknown verdict"))
    if not isinstance(value.get("claimId"), str) or not value.get("claimId", "").startswith("research-claim-"):
        issues.append(_issue(f"{path}/claimId", "verification-assessment.claim", "Invalid claim reference"))
    if not isinstance(value.get("claimHash"), str) or SHA256.fullmatch(value.get("claimHash", "")) is None:
        issues.append(_issue(f"{path}/claimHash", "verification-assessment.claim-hash", "Invalid claim hash"))
    gates = value.get("gates")
    if not isinstance(gates, dict) or set(gates) != {"primary", "holdout", "selectionPassed"}:
        issues.append(_issue(f"{path}/gates", "verification-assessment.gates", "Invalid gate projection"))
    elif (
        gates.get("primary")
        not in {"missing", "invalid", "low-sample", "no-baseline", "below-effect", "contradict", "pass"}
        or gates.get("holdout")
        not in {None, "missing", "invalid", "low-sample", "no-baseline", "below-effect", "contradict", "pass"}
        or gates.get("selectionPassed") not in {None, False, True}
    ):
        issues.append(_issue(f"{path}/gates", "verification-assessment.gates", "Unknown gate result"))
    if value.get("primaryImprovement") is not None and not _finite_number(value.get("primaryImprovement")):
        issues.append(_issue(f"{path}/primaryImprovement", "verification-assessment.improvement", "Improvement must be finite or null"))
    limitations = value.get("limitations")
    if not isinstance(limitations, list) or any(not isinstance(item, str) or not item for item in limitations):
        issues.append(_issue(f"{path}/limitations", "verification-assessment.limitations", "Limitations must be non-empty strings"))
    refs = value.get("evidenceRefs")
    if not isinstance(refs, list) or any(
        not isinstance(ref, dict)
        or set(ref) != {"kind", "id", "sha256"}
        or ref.get("kind") not in _EVIDENCE_KINDS
        or not isinstance(ref.get("id"), str)
        or not isinstance(ref.get("sha256"), str)
        or SHA256.fullmatch(ref.get("sha256", "")) is None
        for ref in refs if isinstance(refs, list)
    ):
        issues.append(_issue(f"{path}/evidenceRefs", "verification-assessment.evidence", "Invalid evidence references"))
    if value.get("authority") != "research-validation-only" or value.get("tradingAuthority") != "none":
        issues.append(_issue(path, "verification-assessment.authority", "VerificationAssessment cannot grant trading authority"))
    payload = {key: value.get(key) for key in _ASSESSMENT_KEYS - {"id"}}
    expected_id = f"verification-assessment-{hash_json(payload)[:16]}"
    if value.get("id") != expected_id:
        issues.append(_issue(f"{path}/id", "verification-assessment.derived-id", "VerificationAssessment id does not match its content"))
    if issues:
        raise AutoQuantValidationError(issues)
    return {**payload, "id": expected_id}


def publish_verification_assessment(
    project: ProjectContext,
    claim: dict[str, Any],
    *,
    run_evidence: dict[str, Any] | None,
    explorer_evidence: dict[str, Any] | None,
    holdout_evidence: dict[str, Any] | None = None,
    selection_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically publish one content-addressed claim and assessment."""

    claim = validate_research_claim(claim)
    assessment = assess_research_claim(
        claim,
        run_evidence=run_evidence,
        explorer_evidence=explorer_evidence,
        holdout_evidence=holdout_evidence,
        selection_evidence=selection_evidence,
    )
    root = confined_path(project.root_dir, VERIFICATIONS_DIRECTORY, "project/verifications")
    root.mkdir(exist_ok=True)
    target = confined_path(root, assessment["id"], "verification-assessment/output")
    if target.exists():
        existing = load_verification_assessment(project, assessment["id"])
        if existing["claim"] == claim and existing["assessment"] == assessment:
            return existing
        raise AutoQuantValidationError(
            [_issue(target, "verification.collision", "Verification id collision")]
        )
    staging = root / f".{assessment['id']}-{uuid.uuid4().hex}"
    staging.mkdir()
    try:
        for name, value in (("claim.json", claim), ("assessment.json", assessment)):
            (staging / name).write_text(
                json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "id": assessment["id"],
            "claimHash": hash_file(staging / "claim.json"),
            "assessmentHash": hash_file(staging / "assessment.json"),
            "completed": True,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(staging, target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return load_verification_assessment(project, assessment["id"])


def load_verification_assessment(
    project: ProjectContext,
    assessment_id: str,
) -> dict[str, Any]:
    """Verify one immutable published claim assessment."""

    if not isinstance(assessment_id, str) or not assessment_id.startswith("verification-assessment-"):
        raise AutoQuantValidationError(
            [_issue(assessment_id, "verification.id", "Invalid VerificationAssessment id")]
        )
    root = confined_path(
        confined_path(project.root_dir, VERIFICATIONS_DIRECTORY, "project/verifications"),
        assessment_id,
        "verification-assessment/id",
    )
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "verification.missing", "Unknown VerificationAssessment")]
        )
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        claim = json.loads((root / "claim.json").read_text(encoding="utf-8"))
        assessment = json.loads((root / "assessment.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AutoQuantValidationError(
            [_issue(root, "verification.read", f"Cannot read VerificationAssessment: {error}")]
        ) from None
    expected_manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "id": assessment_id,
        "claimHash": hash_file(root / "claim.json"),
        "assessmentHash": hash_file(root / "assessment.json"),
        "completed": True,
    }
    if manifest != expected_manifest:
        raise AutoQuantValidationError(
            [_issue(root, "verification.tampered", "Verification manifest integrity check failed")]
        )
    claim = validate_research_claim(claim, root / "claim.json")
    assessment = validate_verification_assessment(assessment, root / "assessment.json")
    if assessment["claimId"] != claim["id"] or assessment["claimHash"] != hash_json(claim):
        raise AutoQuantValidationError(
            [_issue(root, "verification.claim-ref", "Assessment differs from its ResearchClaim")]
        )
    return {"manifest": manifest, "claim": claim, "assessment": assessment}


def list_verification_assessments(project: ProjectContext) -> list[dict[str, Any]]:
    """Verify and list every published claim assessment."""

    root = confined_path(project.root_dir, VERIFICATIONS_DIRECTORY, "project/verifications")
    if not root.exists():
        return []
    if root.is_symlink() or not root.is_dir():
        raise AutoQuantValidationError(
            [_issue(root, "verification.root", "Verification root must be a directory")]
        )
    results = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if entry.name.startswith("."):
            continue
        if entry.is_symlink() or not entry.is_dir():
            raise AutoQuantValidationError(
                [_issue(entry, "verification.entry", "Invalid VerificationAssessment entry")]
            )
        results.append(load_verification_assessment(project, entry.name))
    return results
