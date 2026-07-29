"""Compact verified work contracts for AI research operators."""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

from .checks import candidate_check_state
from .dossiers import load_dossier_status
from .intake import load_project_intake
from .holdouts import HOLDOUT_STATUS_JSON_SCHEMA, load_holdout_status
from .research_agenda import (
    RESEARCH_AGENDA_JSON_SCHEMA,
    build_research_agenda,
    descriptive_audit_agenda,
    waiting_research_agenda,
)
from .research_program import load_research_program
from .runs import list_runs, load_run
from .sessions import list_sessions, load_session, session_snapshot
from .studies import list_studies, load_study
from .workspace import SCHEMA_VERSION, ProjectContext


AGENT_WORK_BRIEF_KIND = "autoquant-agent-work-brief"
AGENT_WORK_BRIEF_METHOD = "verified-project-agent-orientation-v4"
MAX_RESEARCH_QUESTION_CHARS = 4_000
PROTECTED_CATEGORIES = [
    "request",
    "dataset",
    "study",
    "program",
    "judge",
    "mandate",
    "dependencies",
    "runs",
    "experiments",
    "reports",
    "dossiers",
]
EXPECTED_EVIDENCE = {
    "run.execute": "immutable-run",
    "session.start": "research-session",
    "session.show": "session-observation",
    "session.check": "candidate-check",
    "experiment.evaluate": "immutable-experiment",
    "session.promote": "promotion-receipt",
    "session.complete": "completion-receipt",
    "report.publish": "immutable-report",
    "report.show": "immutable-report",
    "dossier.publish": "immutable-dossier",
    "dossier.show": "immutable-dossier",
    "dossier.status": "dossier-status",
    "study.inspect": "study-authority",
    "run.book-risk": "book-risk-diagnostics",
    "run.event-study": "event-study-diagnostics",
    "validate": "structural-validation",
}


_MARKDOWN_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_MARKDOWN_FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def _normalized_heading(value: str) -> str:
    plain = value.rstrip("#").strip()
    plain = re.sub(r"[*_`~]+", "", plain)
    return re.sub(r"[\s_-]+", " ", plain).strip().casefold()


def _bounded_research_question(value: str) -> str:
    if len(value) <= MAX_RESEARCH_QUESTION_CHARS:
        return value
    prefix = value[: MAX_RESEARCH_QUESTION_CHARS - 1]
    boundary = prefix.rfind(" ")
    if boundary >= MAX_RESEARCH_QUESTION_CHARS // 2:
        prefix = prefix[:boundary]
    return prefix.rstrip() + "…"


def _research_brief_question(project: ProjectContext) -> tuple[str, Path] | None:
    """Read one explicitly headed question without imposing a Markdown schema."""

    path = project.root_dir / project.manifest.research_program
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None

    headings: list[tuple[int, int, str]] = []
    fence_character: str | None = None
    for index, line in enumerate(lines):
        fence = _MARKDOWN_FENCE.match(line)
        if fence is not None:
            character = fence.group(1)[0]
            if fence_character is None:
                fence_character = character
            elif fence_character == character:
                fence_character = None
            continue
        if fence_character is not None:
            continue
        heading = _MARKDOWN_HEADING.match(line)
        if heading is None:
            continue
        headings.append(
            (
                index,
                len(heading.group(1)),
                _normalized_heading(heading.group(2)),
            )
        )

    for position, (index, level, heading) in enumerate(headings):
        if not (
            heading == "fixed question"
            or heading == "research question"
            or heading.startswith("research question ")
        ):
            continue
        end = len(lines)
        for next_index, next_level, _ in headings[position + 1 :]:
            if next_level <= level:
                end = next_index
                break
        text = "\n".join(lines[index + 1 : end]).strip()
        if text:
            return _bounded_research_question(text), path
    return None


def _question_projection(
    project: ProjectContext,
    intake: dict[str, Any] | None,
) -> dict[str, Any]:
    if intake is not None:
        request = intake["request"]
        return {
            "title": request["title"],
            "text": request["question"],
            "origin": "delegated-request",
            "sourcePath": str(
                project.root_dir / intake["manifest"]["requestPath"]
            ),
            "requestPath": str(
                project.root_dir / intake["manifest"]["requestPath"]
            ),
        }

    maintained = _research_brief_question(project)
    if maintained is not None:
        text, path = maintained
        return {
            "title": project.manifest.name,
            "text": text,
            "origin": "project-research-brief",
            "sourcePath": str(path),
            "requestPath": None,
        }

    return {
        "title": project.manifest.name,
        "text": project.manifest.description,
        "origin": "local",
        "sourcePath": None,
        "requestPath": None,
    }


def _action(
    value: dict[str, Any],
    *,
    working_directory: Path,
) -> dict[str, Any]:
    argv = [str(item) for item in value["argv"]]
    return {
        "id": value["id"],
        "description": value["description"],
        "argv": argv,
        "display": value.get("display") or shlex.join(argv),
        "effect": value["effect"],
        "workingDirectory": str(working_directory),
        "expectedEvidenceKind": EXPECTED_EVIDENCE.get(
            value["id"],
            "operation-result",
        ),
    }


def _command(
    command_id: str,
    description: str,
    argv: list[str],
    effect: str,
) -> dict[str, Any]:
    return {
        "id": command_id,
        "description": description,
        "argv": argv,
        "effect": effect,
    }


def _session_actions(
    project: ProjectContext,
    session: Any,
    *,
    current_report: dict[str, Any] | None,
) -> tuple[
    dict[str, Any] | None,
    list[dict[str, Any]],
    list[dict[str, str]],
    dict[str, Any],
]:
    manifest = session.manifest
    check_state = candidate_check_state(project, session)
    evaluation = _command(
        "experiment.evaluate",
        "Evaluate this exact candidate with the fixed formal Judge.",
        [
            "aq",
            "experiment",
            "evaluate",
            str(project.root_dir),
            "--session",
            manifest["id"],
            "--hypothesis",
            "Describe the candidate change",
            "--json",
        ],
        "creates-artifact",
    )
    supporting: list[dict[str, Any]] = []
    if not check_state["supported"]:
        primary: dict[str, Any] | None = evaluation
        reasons = [
            {
                "code": "session-active",
                "category": "coordination",
                "message": (
                    "A governed Session owns candidate edits in its disposable "
                    "worktree."
                ),
            }
        ]
    elif not check_state["candidateChanged"]:
        primary = None
        reasons = [
            {
                "code": "candidate-edit-required",
                "category": "coordination",
                "message": (
                    "Edit one declared candidate hypothesis in the Session "
                    "worktree before producing evaluation evidence."
                ),
            }
        ]
    elif check_state["current"] is None:
        primary = _command(
            "session.check",
            "Run the fixed bounded preflight for this exact candidate.",
            [
                "aq",
                "session",
                "check",
                str(project.root_dir),
                "--session",
                manifest["id"],
                "--json",
            ],
            "creates-artifact",
        )
        reasons = [
            {
                "code": "candidate-check-required",
                "category": "evidence",
                "message": (
                    "The changed candidate has no current bounded preflight "
                    "evidence."
                ),
            }
        ]
    elif check_state["current"]["status"] == "failed":
        primary = None
        reasons = [
            {
                "code": "candidate-check-failed",
                "category": "evidence",
                "message": (
                    "The exact candidate failed bounded preflight; edit it "
                    "before spending a formal Judge Run."
                ),
            }
        ]
    else:
        primary = evaluation
        reasons = [
            {
                "code": "candidate-check-passed",
                "category": "evidence",
                "message": (
                    "The exact candidate passed bounded preflight and is ready "
                    "for formal selection evidence."
                ),
            }
        ]
    if manifest["leader"]["runId"] != manifest["baseline"]["runId"]:
        supporting.append(
            _command(
                "session.promote",
                "Promote the exact current KEEP after human review to preserve "
                "the source; promotion is not scientific qualification.",
                [
                    "aq",
                    "session",
                    "promote",
                    str(project.root_dir),
                    "--session",
                    manifest["id"],
                    "--json",
                ],
                "mutates-project",
            )
        )
        reasons.append(
            {
                "code": "promotion-ready",
                "category": "authority",
                "message": (
                    "The Session leader improves on baseline and is eligible "
                    "for guarded promotion."
                ),
            }
        )
    if (
        current_report is not None
        and manifest["leader"] == manifest["baseline"]
    ):
        completion = _command(
            "session.complete",
            "Complete baseline-retaining research with the exact current Report.",
            [
                "aq",
                "session",
                "complete",
                str(project.root_dir),
                "--session",
                manifest["id"],
                "--report",
                current_report["id"],
                "--json",
            ],
            "creates-artifact",
        )
        reasons.append(
            {
                "code": "baseline-completion-ready",
                "category": "evidence",
                "message": (
                    "The current Report freezes the unchanged baseline and "
                    "complete evidence prefix."
                ),
            }
        )
        if not check_state["supported"]:
            return completion, [evaluation, *supporting], reasons, check_state
        supporting.append(completion)
    return primary, supporting, reasons, check_state


def _program_orientation(
    project: ProjectContext,
    program: dict[str, Any],
) -> dict[str, Any]:
    progression = program["progression"]
    reasons: list[dict[str, str]] = []
    primary_raw: dict[str, Any] | None = None
    supporting_raw: list[dict[str, Any]] = []
    focus_lane = next(
        (
            lane
            for lane in program["lanes"]
            if lane["id"] == program["recommendedLaneId"]
        ),
        None,
    )
    if focus_lane is None and progression["focusLaneId"] is not None:
        focus_lane = next(
            lane
            for lane in program["lanes"]
            if lane["id"] == progression["focusLaneId"]
        )
    if focus_lane is None:
        focus_lane = program["lanes"][0]

    session = None
    check_state: dict[str, Any] = {"current": None}
    session_authority_valid = True
    session_summary = focus_lane["latestSession"]
    if (
        session_summary is not None
        and session_summary["status"] == "active"
    ):
        session = load_session(project, session_summary["id"])

    if program["conflicts"]:
        reasons.append(
            {
                "code": "shared-source-conflict",
                "category": "coordination",
                "message": (
                    f"{len(program['conflicts'])} active shared-source "
                    "conflict(s) must be reviewed before advancing research."
                ),
            }
        )
        seen_sessions: set[str] = set()
        for conflict in program["conflicts"]:
            for item in conflict["sessions"]:
                session_id = item["sessionId"]
                if session_id in seen_sessions:
                    continue
                seen_sessions.add(session_id)
                supporting_raw.append(
                    _command(
                        "session.show",
                        f"Inspect conflicting {item['laneId']} Session.",
                        [
                            "aq",
                            "session",
                            "show",
                            str(project.root_dir),
                            "--session",
                            session_id,
                            "--json",
                        ],
                        "read-only",
                    )
                )
    elif session is not None:
        session_authority_valid = session_snapshot(
            project,
            session,
        )["authority"]["valid"]
        if not session_authority_valid:
            primary_raw = _command(
                "session.show",
                "Inspect the stale Session authority before any candidate edit.",
                [
                    "aq",
                    "session",
                    "show",
                    str(project.root_dir),
                    "--session",
                    session.manifest["id"],
                    "--json",
                ],
                "read-only",
            )
            reasons = [
                {
                    "code": "current-evidence-stale",
                    "category": "authority",
                    "message": (
                        "The active Session no longer matches fixed Project "
                        "authority and is not writable."
                    ),
                }
            ]
        else:
            current_report = next(
                (
                    report
                    for report in reversed(focus_lane["reports"])
                    if report["leaderRunId"]
                    == session.manifest["leader"]["runId"]
                ),
                None,
            )
            primary_raw, supporting_raw, reasons, check_state = _session_actions(
                project,
                session,
                current_report=current_report,
            )
    elif program["recommendedAction"] is not None:
        primary_raw = program["recommendedAction"]
        if primary_raw["id"] == "run.execute":
            code = (
                "current-evidence-stale"
                if focus_lane["phase"] == "stale"
                else "baseline-evidence-missing"
            )
            message = (
                "The selected Study needs immutable evidence matching current "
                "source and fixed inputs."
            )
            category = "evidence"
        elif primary_raw["id"] == "session.start":
            blocked_gate = next(
                (
                    gate
                    for gate in progression["gates"]
                    if gate["upstreamLaneId"] == focus_lane["id"]
                    and gate["status"].startswith("blocked")
                ),
                None,
            )
            code = (
                "scientific-gate-blocked"
                if blocked_gate is not None
                else "session-required"
            )
            message = (
                blocked_gate["explanation"]
                if blocked_gate is not None
                else "Current baseline evidence is ready for governed research."
            )
            category = "scientific" if blocked_gate is not None else "coordination"
        elif primary_raw["id"] == "session.complete":
            code = "baseline-completion-ready"
            message = "The current reported baseline can close this research lane."
            category = "evidence"
        else:
            code = "report-required"
            message = primary_raw["description"]
            category = "evidence"
        reasons.append(
            {"code": code, "category": category, "message": message}
        )
    else:
        dossier_status = load_dossier_status(project, optional=True)
        if (
            dossier_status is not None
            and dossier_status["nextAction"] is not None
        ):
            primary_raw = dossier_status["nextAction"]
        reasons.append(
            {
                "code": "required-research-complete",
                "category": "scientific",
                "message": progression["explanation"],
            }
        )

    operating_root = (
        session.worktree_project.root_dir
        if session is not None
        and not program["conflicts"]
        and session_authority_valid
        else project.root_dir
    )
    writable = (
        session is not None
        and not program["conflicts"]
        and session_authority_valid
    )
    editable_paths = (
        list(session.manifest["editablePaths"]) if writable else []
    )
    declared_editable = list(focus_lane["editablePaths"])
    primary = (
        _action(primary_raw, working_directory=operating_root)
        if primary_raw is not None
        else None
    )
    supporting = [
        _action(item, working_directory=operating_root)
        for item in supporting_raw[:3]
    ]
    run = focus_lane["latestRun"]
    latest_report = (
        focus_lane["reports"][-1] if focus_lane["reports"] else None
    )
    if (
        writable
        and reasons[0]["code"]
        in {"candidate-edit-required", "candidate-check-failed"}
    ):
        operating_mode = "edit-and-evaluate"
    elif primary is None or program["conflicts"]:
        operating_mode = "observe"
    else:
        operating_mode = {
            "run.execute": "establish-baseline",
            "session.start": "edit-and-evaluate",
            "session.check": "edit-and-evaluate",
            "experiment.evaluate": "edit-and-evaluate",
            "report.publish": "publish-evidence",
            "dossier.publish": "publish-evidence",
            "session.complete": "complete",
            "session.promote": "promote",
        }.get(primary["id"], "observe")
    review_status = (
        "blocked"
        if program["conflicts"]
        or not session_authority_valid
        or any(reason["code"] == "scientific-gate-blocked" for reason in reasons)
        else "complete"
        if reasons[0]["code"] == "required-research-complete"
        else "active"
        if session is not None
        else "pending"
    )
    return {
        "focus": {
            "laneId": focus_lane["id"],
            "laneName": focus_lane["name"],
            "studyId": focus_lane["study"]["id"],
            "studyName": focus_lane["study"]["name"],
            "coordinationPhase": focus_lane["phase"],
            "scientificStage": progression["stage"],
            "operatingMode": operating_mode,
        },
        "evidence": {
            "runId": run["id"] if run is not None else None,
            "runStatus": run["status"] if run is not None else None,
            "sessionId": (
                session_summary["id"] if session_summary is not None else None
            ),
            "sessionStatus": (
                session_summary["status"]
                if session_summary is not None
                else None
            ),
            "leaderRunId": (
                session_summary["leaderRunId"]
                if session_summary is not None
                else None
            ),
            "reportId": (
                latest_report["id"] if latest_report is not None else None
            ),
            "candidateCheckId": (
                check_state["current"]["id"]
                if check_state["current"] is not None
                else None
            ),
            "candidateCheckStatus": (
                check_state["current"]["status"]
                if check_state["current"] is not None
                else None
            ),
        },
        "reasons": reasons,
        "filesystem": {
            "operatingRoot": str(operating_root),
            "writable": writable,
            "editablePaths": editable_paths,
            "declaredEditablePaths": declared_editable,
            "protectedCategories": PROTECTED_CATEGORIES,
        },
        "authority": {
            "researchAuthority": progression["authority"],
            "selectionSplit": progression["selectionSplit"],
            "testRole": "visible-audit",
            "testEntersSelection": progression["testEntersProgression"],
            "tradingAuthority": progression["tradingAuthority"],
        },
        "primaryAction": primary,
        "supportingActions": supporting,
        "review": {
            "status": review_status,
            "label": reasons[0]["code"].replace("-", " ").upper(),
            "title": (
                "Resolve shared-source conflicts"
                if program["conflicts"]
                else focus_lane["name"]
                if review_status != "complete"
                else "Required research evidence is complete"
            ),
            "detail": reasons[0]["message"],
            "next": (
                primary["description"]
                if primary is not None
                else (
                    "Edit one falsifiable candidate hypothesis in the declared worktree closure."
                    if reasons[0]["code"] == "candidate-edit-required"
                    else "Revise the candidate to address the failed bounded preflight."
                    if reasons[0]["code"] == "candidate-check-failed"
                    else "Review the verified evidence and choose any optional follow-up explicitly."
                )
            ),
            "boundary": "validation selects · visible test audits · no trading authority",
        },
    }


def _single_study_orientation(
    project: ProjectContext,
    study_summaries: list[Any],
) -> dict[str, Any]:
    if len(study_summaries) != 1:
        has_studies = bool(study_summaries)
        reason_code = (
            "study-selection-required" if has_studies else "study-required"
        )
        supporting = [
            _action(
                _command(
                    "study.inspect",
                    f"Inspect fixed Study {item.id}.",
                    [
                        "aq",
                        "study",
                        "inspect",
                        str(project.root_dir),
                        "--study",
                        item.id,
                        "--json",
                    ],
                    "read-only",
                ),
                working_directory=project.root_dir,
            )
            for item in study_summaries[:3]
        ]
        return {
            "focus": {
                "laneId": None,
                "laneName": None,
                "studyId": None,
                "studyName": None,
                "coordinationPhase": "not-started",
                "scientificStage": reason_code,
                "operatingMode": "observe",
            },
            "evidence": {
                "runId": None,
                "runStatus": None,
                "sessionId": None,
                "sessionStatus": None,
                "leaderRunId": None,
                "reportId": None,
                "candidateCheckId": None,
                "candidateCheckStatus": None,
            },
            "reasons": [
                {
                    "code": reason_code,
                    "category": "coordination",
                    "message": (
                        f"The Project has {len(study_summaries)} fixed Studies "
                        "but no research program selects their order."
                        if has_studies
                        else "The Project has no fixed quantitative Study."
                    ),
                }
            ],
            "filesystem": {
                "operatingRoot": str(project.root_dir),
                "writable": False,
                "editablePaths": [],
                "declaredEditablePaths": [],
                "protectedCategories": PROTECTED_CATEGORIES,
            },
            "authority": {
                "researchAuthority": "study-defined",
                "selectionSplit": "study-defined",
                "testRole": "study-defined",
                "testEntersSelection": False,
                "tradingAuthority": "none",
            },
            "primaryAction": None,
            "supportingActions": supporting,
            "review": {
                "status": "pending",
                "label": reason_code.replace("-", " ").upper(),
                "title": (
                    "Choose or coordinate the fixed Studies"
                    if has_studies
                    else "Define one bounded quantitative Study"
                ),
                "detail": (
                    "Multiple Studies exist without a verified research order."
                    if has_studies
                    else "No fixed Study authority exists yet."
                ),
                "next": (
                    "Inspect the Studies and define explicit coordination before running research."
                    if has_studies
                    else "Create a Study before running or editing candidate research."
                ),
                "boundary": "no selection evidence · no trading authority",
            },
        }

    study_summary = study_summaries[0]
    study = load_study(project, study_summary.id)
    sessions = [
        item
        for item in list_sessions(project)
        if item.study_id == study.definition.id
    ]
    latest_session = sessions[-1] if sessions else None
    active_session = (
        load_session(project, latest_session.id)
        if latest_session is not None and latest_session.status == "active"
        else None
    )
    current_runs = []
    for item in list_runs(project):
        if item.study_id != study.definition.id or item.status != "succeeded":
            continue
        run = load_run(project, item.id)
        if run.result["studyInputHash"] == study.input_hash:
            current_runs.append(item)
    current_run = current_runs[-1] if current_runs else None
    active_authority_valid = (
        session_snapshot(project, active_session)["authority"]["valid"]
        if active_session is not None
        else False
    )
    check_state: dict[str, Any] = {"current": None}
    if active_session is not None and active_authority_valid:
        primary_raw, supporting_raw, reasons, check_state = _session_actions(
            project,
            active_session,
            current_report=None,
        )
        operating_root = active_session.worktree_project.root_dir
        editable = list(active_session.manifest["editablePaths"])
        mode = "edit-and-evaluate"
        phase = "researching"
    elif active_session is not None:
        primary_raw = _command(
            "session.show",
            "Inspect the stale Session authority before any candidate edit.",
            [
                "aq",
                "session",
                "show",
                str(project.root_dir),
                "--session",
                active_session.manifest["id"],
                "--json",
            ],
            "read-only",
        )
        supporting_raw = []
        reasons = [
            {
                "code": "current-evidence-stale",
                "category": "authority",
                "message": (
                    "The active Session no longer matches fixed Project "
                    "authority and is not writable."
                ),
            }
        ]
        operating_root = project.root_dir
        editable = []
        mode = "observe"
        phase = "stale"
    elif current_run is None:
        primary_raw = _command(
            "run.execute",
            "Create current immutable baseline evidence for the Study.",
            [
                "aq",
                "run",
                "execute",
                str(project.root_dir),
                "--study",
                study.definition.id,
                "--json",
            ],
            "creates-artifact",
        )
        supporting_raw = []
        reasons = [
            {
                "code": "baseline-evidence-missing",
                "category": "evidence",
                "message": "The Study has no successful Run matching current inputs.",
            }
        ]
        operating_root = project.root_dir
        editable = []
        mode = "establish-baseline"
        phase = "not-started"
    elif study.definition.objective.metric in {
        "current_component_risk_hhi",
        "primary_eligible_event_count",
        "validation_net_sharpe_advantage",
    }:
        event_study = (
            study.definition.objective.metric
            == "primary_eligible_event_count"
        )
        allocation_study = (
            study.definition.objective.metric
            == "validation_net_sharpe_advantage"
        )
        primary_raw = _command(
            (
                "run.event-study"
                if event_study
                else "run.allocation"
                if allocation_study
                else "run.book-risk"
            ),
            (
                "Inspect verified event timing, populations, references, "
                "overlap, uncertainty, and no-trading conclusion evidence."
                if event_study
                else (
                    "Inspect verified same-clock allocation/reference, ERC "
                    "solver, risk, implementation, and current target evidence."
                    if allocation_study
                    else (
                        "Inspect verified reported-book crowding, reduction, "
                        "caller-supplied scenarios, and any caller-bounded "
                        "target-position sizing evidence."
                    )
                )
            ),
            [
                "aq",
                "run",
                (
                    "event-study"
                    if event_study
                    else "allocation"
                    if allocation_study
                    else "book-risk"
                ),
                str(project.root_dir),
                "--run",
                current_run.id,
                "--json",
            ],
            "read-only",
        )
        supporting_raw = []
        reasons = [
            {
                "code": "descriptive-evidence-ready",
                "category": "evidence",
                "message": (
                    "The fixed price-event Study is complete and ready for "
                    "historical evidence review."
                    if event_study
                    else (
                        "The fixed allocation Study is complete and ready for "
                        "decision-support review."
                        if allocation_study
                        else (
                            "The fixed reported-book audit is complete and ready "
                            "for decision-support review."
                        )
                    )
                ),
            }
        ]
        operating_root = project.root_dir
        editable = []
        mode = "observe"
        phase = "evidence-ready"
    else:
        primary_raw = _command(
            "session.start",
            "Start a governed Session from the current immutable baseline.",
            [
                "aq",
                "session",
                "start",
                str(project.root_dir),
                "--study",
                study.definition.id,
                "--json",
            ],
            "creates-artifact",
        )
        supporting_raw = []
        reasons = [
            {
                "code": "session-required",
                "category": "coordination",
                "message": "Current baseline evidence is ready for governed research.",
            }
        ]
        operating_root = project.root_dir
        editable = []
        mode = "edit-and-evaluate"
        phase = "baseline-ready"
    primary = (
        _action(primary_raw, working_directory=operating_root)
        if primary_raw is not None
        else None
    )
    return {
        "focus": {
            "laneId": None,
            "laneName": None,
            "studyId": study.definition.id,
            "studyName": study.definition.name,
            "coordinationPhase": phase,
            "scientificStage": "study-defined",
            "operatingMode": mode,
        },
        "evidence": {
            "runId": current_run.id if current_run is not None else None,
            "runStatus": (
                current_run.status if current_run is not None else None
            ),
            "sessionId": (
                latest_session.id if latest_session is not None else None
            ),
            "sessionStatus": (
                latest_session.status if latest_session is not None else None
            ),
            "leaderRunId": (
                latest_session.leader_run_id
                if latest_session is not None
                else None
            ),
            "reportId": None,
            "candidateCheckId": (
                check_state["current"]["id"]
                if check_state["current"] is not None
                else None
            ),
            "candidateCheckStatus": (
                check_state["current"]["status"]
                if check_state["current"] is not None
                else None
            ),
        },
        "reasons": reasons,
        "filesystem": {
            "operatingRoot": str(operating_root),
            "writable": (
                active_session is not None and active_authority_valid
            ),
            "editablePaths": editable,
            "declaredEditablePaths": list(study.definition.editable["paths"]),
            "protectedCategories": PROTECTED_CATEGORIES,
        },
        "authority": {
            "researchAuthority": (
                "fixed-descriptive-audit"
                if study.definition.objective.metric
                in {
                    "current_component_risk_hhi",
                    "primary_eligible_event_count",
                }
                else "study-defined"
            ),
            "selectionSplit": (
                "none"
                if study.definition.objective.metric
                in {
                    "current_component_risk_hhi",
                    "primary_eligible_event_count",
                }
                else "study-defined"
            ),
            "testRole": (
                (
                    "event-population-and-reference-context"
                    if study.definition.objective.metric
                    == "primary_eligible_event_count"
                    else "lookback-and-rolling-context"
                )
                if study.definition.objective.metric
                in {
                    "current_component_risk_hhi",
                    "primary_eligible_event_count",
                }
                else "study-defined"
            ),
            "testEntersSelection": False,
            "tradingAuthority": "none",
        },
        "primaryAction": primary,
        "supportingActions": [
            _action(item, working_directory=operating_root)
            for item in supporting_raw
        ],
        "review": {
            "status": (
                "active"
                if active_session is not None and active_authority_valid
                else "blocked"
                if active_session is not None
                else "complete"
                if reasons[0]["code"] == "descriptive-evidence-ready"
                else "pending"
            ),
            "label": reasons[0]["code"].replace("-", " ").upper(),
            "title": study.definition.name,
            "detail": reasons[0]["message"],
            "next": (
                primary["description"]
                if primary is not None
                else (
                    "Edit one falsifiable candidate hypothesis in the declared worktree closure."
                    if reasons[0]["code"] == "candidate-edit-required"
                    else "Revise the candidate to address the failed bounded preflight."
                )
            ),
            "boundary": "fixed Study authority · no trading authority",
        },
    }


def _holdout_orientation(
    project: ProjectContext,
    holdout: dict[str, Any],
) -> dict[str, Any]:
    completed = holdout["state"] == "completed"
    action = holdout["nextAction"]
    result = holdout["result"]
    run_id = (
        result["lanes"][-1]["holdout"]["runId"]
        if result is not None and result["lanes"]
        else None
    )
    primary = (
        _action(action, working_directory=project.root_dir)
        if action is not None
        else None
    )
    reason = {
        "code": (
            "external-holdout-complete"
            if completed
            else "external-holdout-bound"
        ),
        "category": "evidence",
        "message": (
            "The frozen research object has completed its strictly later "
            "external-period audit."
            if completed
            else "The exact Dossier leaders are frozen and ready for one "
            "strictly later external-period audit."
        ),
    }
    return {
        "focus": {
            "laneId": "external-holdout",
            "laneName": "Frozen external holdout",
            "studyId": None,
            "studyName": None,
            "coordinationPhase": holdout["state"],
            "scientificStage": reason["code"],
            "operatingMode": "observe" if completed else "external-audit",
        },
        "evidence": {
            "runId": run_id,
            "runStatus": result["status"] if result is not None else None,
            "sessionId": None,
            "sessionStatus": None,
            "leaderRunId": None,
            "reportId": None,
            "candidateCheckId": None,
            "candidateCheckStatus": None,
        },
        "reasons": [reason],
        "filesystem": {
            "operatingRoot": str(project.root_dir),
            "writable": False,
            "editablePaths": [],
            "declaredEditablePaths": [],
            "protectedCategories": [
                *PROTECTED_CATEGORIES,
                "holdout-binding",
                "imported-sources",
            ],
        },
        "authority": {
            "researchAuthority": "frozen-external-temporal-audit",
            "selectionSplit": "none",
            "testRole": "external-period-audit",
            "testEntersSelection": False,
            "tradingAuthority": "none",
        },
        "primaryAction": primary,
        "supportingActions": [],
        "review": {
            "status": "complete" if completed else "pending",
            "label": reason["code"].replace("-", " ").upper(),
            "title": "Frozen external-period challenge",
            "detail": reason["message"],
            "next": (
                primary["description"]
                if primary is not None
                else "Review the immutable result with the requesting workbench."
            ),
            "boundary": (
                "candidate frozen · no selection · no automatic promotion · "
                "no trading authority"
            ),
        },
    }


def build_agent_work_brief(project: ProjectContext) -> dict[str, Any]:
    """Build one compact orientation contract from verified Project state."""

    intake = load_project_intake(project)
    holdout = load_holdout_status(project, optional=True)
    program = load_research_program(project, optional=True)
    studies = list_studies(project)
    projected = (
        _holdout_orientation(project, holdout)
        if holdout is not None
        else _program_orientation(project, program)
        if program is not None
        else _single_study_orientation(
            project,
            studies,
        )
    )
    agenda_run_id = projected["evidence"]["runId"]
    if program is not None:
        agenda_lane = next(
            (
                lane
                for lane in program["lanes"]
                if lane["id"] == projected["focus"]["laneId"]
            ),
            None,
        )
        if agenda_lane is None or not agenda_lane["currentRun"]:
            agenda_run_id = None
    if (
        projected["filesystem"]["writable"]
        and projected["evidence"]["sessionId"] is not None
        and projected["evidence"]["leaderRunId"] is not None
    ):
        agenda_run_id = projected["evidence"]["leaderRunId"]
    descriptive_metric = (
        studies[0].primary_metric
        if projected["focus"]["studyId"] is not None and studies
        else None
    )
    event_descriptive = descriptive_metric == "primary_eligible_event_count"
    allocation_fixed = (
        descriptive_metric == "validation_net_sharpe_advantage"
    )
    fixed_descriptive = descriptive_metric in {
        "current_component_risk_hhi",
        "primary_eligible_event_count",
        "validation_net_sharpe_advantage",
    }
    research_agenda = (
        waiting_research_agenda(
            "external-holdout",
            reason=(
                "Candidate research is frozen in an external-period challenge; "
                "no further selection move is authorized here."
            ),
        )
        if holdout is not None
        else descriptive_audit_agenda(
            project,
            agenda_run_id,
            lane_id=(
                "event-study"
                if event_descriptive
                else "allocation"
                if allocation_fixed
                else "book-risk"
            ),
            reason=(
                (
                    "Price-event history is a fixed descriptive audit. Review "
                    "the verified event ledger, references, overlap, and "
                    "uncertainty; do not manufacture a parameter-search or "
                    "execution agenda."
                )
                if event_descriptive
                else (
                    "Portfolio-native allocation is a fixed construction "
                    "evaluation. Review the verified candidate/reference, "
                    "solver, risk, and current-target evidence; do not "
                    "manufacture a Factor, RL, or execution agenda."
                    if allocation_fixed
                    else (
                        "Reported-book risk is a fixed descriptive audit. Review "
                        "the verified evidence and any bounded target position; "
                        "do not manufacture an optimization or execution agenda."
                    )
                )
            ),
            test_role=(
                "event-population-and-reference-context"
                if event_descriptive
                else "visible-audit-only"
                if allocation_fixed
                else "lookback-and-rolling-context"
            ),
        )
        if fixed_descriptive and agenda_run_id is not None
        else build_research_agenda(
            project,
            agenda_run_id,
            lane_id=projected["focus"]["laneId"],
            editable_paths=projected["filesystem"]["declaredEditablePaths"],
        )
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": AGENT_WORK_BRIEF_KIND,
        "method": AGENT_WORK_BRIEF_METHOD,
        "project": {
            "id": project.manifest.id,
            "name": project.manifest.name,
            "rootDir": str(project.root_dir),
        },
        "question": _question_projection(project, intake),
        "researchAgenda": research_agenda,
        "externalHoldout": holdout,
        **projected,
    }


ACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "id",
        "description",
        "argv",
        "display",
        "effect",
        "workingDirectory",
        "expectedEvidenceKind",
    ],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
        "argv": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        },
        "display": {"type": "string", "minLength": 1},
        "effect": {
            "enum": [
                "read-only",
                "creates-artifact",
                "mutates-workspace",
                "mutates-project",
                "long-running-server",
            ]
        },
        "workingDirectory": {"type": "string", "minLength": 1},
        "expectedEvidenceKind": {"type": "string", "minLength": 1},
    },
}

AGENT_WORK_BRIEF_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AutoQuant AI research operator work brief",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schemaVersion",
        "kind",
        "method",
        "project",
        "question",
        "focus",
        "evidence",
        "reasons",
        "filesystem",
        "authority",
        "researchAgenda",
        "externalHoldout",
        "primaryAction",
        "supportingActions",
        "review",
    ],
    "properties": {
        "schemaVersion": {"const": SCHEMA_VERSION},
        "kind": {"const": AGENT_WORK_BRIEF_KIND},
        "method": {"const": AGENT_WORK_BRIEF_METHOD},
        "project": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "name", "rootDir"],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "name": {"type": "string", "minLength": 1},
                "rootDir": {"type": "string", "minLength": 1},
            },
        },
        "question": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "title",
                "text",
                "origin",
                "sourcePath",
                "requestPath",
            ],
            "properties": {
                "title": {"type": "string", "minLength": 1},
                "text": {"type": "string"},
                "origin": {
                    "enum": [
                        "local",
                        "project-research-brief",
                        "delegated-request",
                    ]
                },
                "sourcePath": {"type": ["string", "null"]},
                "requestPath": {"type": ["string", "null"]},
            },
        },
        "focus": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "laneId",
                "laneName",
                "studyId",
                "studyName",
                "coordinationPhase",
                "scientificStage",
                "operatingMode",
            ],
            "properties": {
                "laneId": {"type": ["string", "null"]},
                "laneName": {"type": ["string", "null"]},
                "studyId": {"type": ["string", "null"]},
                "studyName": {"type": ["string", "null"]},
                "coordinationPhase": {"type": "string", "minLength": 1},
                "scientificStage": {"type": "string", "minLength": 1},
                "operatingMode": {
                    "enum": [
                        "observe",
                        "establish-baseline",
                        "edit-and-evaluate",
                        "publish-evidence",
                        "external-audit",
                        "complete",
                        "promote",
                    ]
                },
            },
        },
        "evidence": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "runId",
                "runStatus",
                "sessionId",
                "sessionStatus",
                "leaderRunId",
                "reportId",
                "candidateCheckId",
                "candidateCheckStatus",
            ],
            "properties": {
                key: {"type": ["string", "null"]}
                for key in (
                    "runId",
                    "runStatus",
                    "sessionId",
                    "sessionStatus",
                    "leaderRunId",
                    "reportId",
                    "candidateCheckId",
                    "candidateCheckStatus",
                )
            },
        },
        "reasons": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["code", "category", "message"],
                "properties": {
                    "code": {"type": "string", "minLength": 1},
                    "category": {
                        "enum": [
                            "coordination",
                            "evidence",
                            "scientific",
                            "authority",
                        ]
                    },
                    "message": {"type": "string", "minLength": 1},
                },
            },
        },
        "filesystem": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "operatingRoot",
                "writable",
                "editablePaths",
                "declaredEditablePaths",
                "protectedCategories",
            ],
            "properties": {
                "operatingRoot": {"type": "string", "minLength": 1},
                "writable": {"type": "boolean"},
                "editablePaths": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "uniqueItems": True,
                },
                "declaredEditablePaths": {
                    "type": "array",
                    "items": {"type": "string", "minLength": 1},
                    "uniqueItems": True,
                },
                "protectedCategories": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                    "uniqueItems": True,
                },
            },
        },
        "authority": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "researchAuthority",
                "selectionSplit",
                "testRole",
                "testEntersSelection",
                "tradingAuthority",
            ],
            "properties": {
                "researchAuthority": {"type": "string", "minLength": 1},
                "selectionSplit": {"type": "string", "minLength": 1},
                "testRole": {"type": "string", "minLength": 1},
                "testEntersSelection": {"const": False},
                "tradingAuthority": {"const": "none"},
            },
        },
        "researchAgenda": RESEARCH_AGENDA_JSON_SCHEMA,
        "externalHoldout": {
            "oneOf": [
                HOLDOUT_STATUS_JSON_SCHEMA,
                {"type": "null"},
            ]
        },
        "primaryAction": {
            "anyOf": [ACTION_SCHEMA, {"type": "null"}]
        },
        "supportingActions": {
            "type": "array",
            "maxItems": 3,
            "items": ACTION_SCHEMA,
        },
        "review": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "status",
                "label",
                "title",
                "detail",
                "next",
                "boundary",
            ],
            "properties": {
                "status": {
                    "enum": ["pending", "active", "blocked", "complete"]
                },
                "label": {"type": "string", "minLength": 1},
                "title": {"type": "string", "minLength": 1},
                "detail": {"type": "string", "minLength": 1},
                "next": {"type": "string", "minLength": 1},
                "boundary": {"type": "string", "minLength": 1},
            },
        },
    },
}
