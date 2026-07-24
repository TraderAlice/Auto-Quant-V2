const state = {
  snapshot: null,
  projectId: null,
  sessionId: null,
  evidenceLane: null,
  catalog: "studies",
  factorView: "ic",
  factorHorizon: "1",
  factorSplit: "validation",
  factorStability: "regimes",
  portfolioView: "performance",
  attributionSplit: "validation",
  rlView: "performance",
  rlSplit: "validation",
  matrixView: "selection",
  autoRefresh: true,
  loading: false,
  timer: null,
};

const element = (id) => document.getElementById(id);
const studio = element("studio");
const syncState = element("sync-state");

const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[character],
  );

const normalizedStatus = (value) =>
  String(value ?? "unknown").toLowerCase().replaceAll(" ", "_");

const metric = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const number = Number(value);
  if (Math.abs(number) >= 1000) return number.toLocaleString(undefined, { maximumFractionDigits: 1 });
  return number.toLocaleString(undefined, { maximumFractionDigits: 4 });
};

const percent = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  return `${metric(Number(value) * 100)}%`;
};

const capital = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const number = Number(value);
  const magnitude = Math.abs(number);
  if (magnitude >= 1e9) return `$${metric(number / 1e9)}B`;
  if (magnitude >= 1e6) return `$${metric(number / 1e6)}M`;
  if (magnitude >= 1e3) return `$${metric(number / 1e3)}K`;
  return `$${metric(number)}`;
};

const probabilityMetric = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const number = Number(value);
  if (number !== 0 && Math.abs(number) < 0.0001) {
    return number.toExponential(2);
  }
  return metric(number);
};

const selectionEvidence = (integrity) => {
  const family = integrity?.researchFamily ?? null;
  const adjustment = integrity?.selectionAdjustment ?? null;
  if (!family || !adjustment) {
    return {
      family,
      adjustment,
      label: "NOT AVAILABLE",
      tone: "blocked",
    };
  }
  if (adjustment.status !== "available") {
    return {
      family,
      adjustment,
      label: "UNSUPPORTED",
      tone: "blocked",
    };
  }
  return {
    family,
    adjustment,
    label: adjustment.passes ? "SURVIVES 95%" : "BELOW 95%",
    tone: adjustment.passes ? "active" : "adverse",
  };
};

const selectionContext = (integrity) => {
  const evidence = selectionEvidence(integrity);
  if (!evidence.family) return "selection adjustment unavailable";
  return (
    `${evidence.family.uniqueSourceTrials} family trial` +
    `${evidence.family.uniqueSourceTrials === 1 ? "" : "s"} · ` +
    `${evidence.label.toLowerCase()}`
  );
};

const selectionRiskSection = (integrity) => {
  const evidence = selectionEvidence(integrity);
  const family = evidence.family;
  const adjustment = evidence.adjustment;
  if (!family || !adjustment) return "";
  const statistics = adjustment.statistics;
  let statisticalRows = "";
  if (adjustment.method === "bonferroni-hac-v1" && statistics) {
    statisticalRows = `
      <dt>Raw HAC p</dt><dd>${probabilityMetric(statistics.rawHacPValue)}</dd>
      <dt>Adjusted p</dt><dd>${probabilityMetric(statistics.familywiseAdjustedPValue)}</dd>
      <dt>Family confidence</dt><dd>${percent(statistics.familywiseConfidence)}</dd>`;
  } else if (
    adjustment.method === "deflated-sharpe-ratio-v1" &&
    statistics
  ) {
    statisticalRows = `
      <dt>PSR / DSR</dt><dd>${percent(statistics.probabilisticSharpeProbability)} / ${percent(statistics.deflatedSharpeProbability)}</dd>
      <dt>Sharpe observed / expected max</dt><dd>${metric(statistics.observedAnnualizedSharpe)} / ${metric(statistics.expectedMaximumAnnualizedSharpe)}</dd>
      <dt>Track record</dt><dd>${statistics.observations} / ${statistics.minimumTrackRecordObservations ?? "unreachable"} required</dd>`;
  } else if (adjustment.reason) {
    statisticalRows = `
      <dt>Reason</dt><dd>${escapeHtml(adjustment.reason)}</dd>`;
  }
  return `
    <section class="inspector-section selection-risk">
      <small>Selection risk · diagnostic only</small>
      <h3>${escapeHtml(adjustment.method ?? "No valid single-path adjustment")}</h3>
      <span class="status-chip ${evidence.tone}">${escapeHtml(evidence.label)}</span>
      <dl class="inspector-kv">
        <dt>Research family</dt><dd title="${escapeHtml(family.id)}">${escapeHtml(family.id)}</dd>
        <dt>Unique trials</dt><dd>${family.uniqueSourceTrials}</dd>
        <dt>Executions / duplicates</dt><dd>${family.totalExecutions} / ${family.duplicateExecutions}</dd>
        <dt>Reproducible</dt><dd>${family.reproducible ? "yes" : "no"}</dd>
        ${statisticalRows}
      </dl>
      <p>${escapeHtml(adjustment.interpretation ?? "Core published the selection-adjustment evidence shown above.")} Project-wide fixed-evaluation family; restarting a Session does not reset the trial count.</p>
    </section>`;
};

const signedPercent = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const number = Number(value) * 100;
  return `${number > 0 ? "+" : ""}${metric(number)}%`;
};

const valueTone = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number) || number >= 0) return "";
  return "bad";
};

const latestSuccessfulRun = (project) =>
  project.runs
    .slice()
    .reverse()
    .find((run) => run.status === "succeeded" && run.metricLayers) ?? null;

const projectFocusLane = (project) => {
  const program = project.researchProgramStatus;
  if (!program) return null;
  return (
    program.lanes.find((lane) => lane.id === program.recommendedLaneId) ??
    program.lanes[0] ??
    null
  );
};

const projectFocusRun = (project) => {
  const lane = projectFocusLane(project);
  if (lane?.latestRun?.id) {
    const run = project.runs.find((item) => item.id === lane.latestRun.id);
    if (run?.status === "succeeded" && run.metricLayers) return run;
  }
  return latestSuccessfulRun(project);
};

const laneKind = (lane) => {
  if (["factor", "portfolio", "rl"].includes(lane?.id)) return lane.id;
  return {
    "causal-predictive-evidence": "factor",
    "mechanical-portfolio-evidence": "portfolio",
    "adaptive-policy-challenge": "rl",
  }[lane?.role] ?? null;
};

const runForLane = (project, lane) => {
  if (!lane?.latestRun?.id) return null;
  return project.runs.find((run) => run.id === lane.latestRun.id) ?? null;
};

const latestRunForLaneKind = (project, kind) =>
  project.runs
    .slice()
    .reverse()
    .find(
      (run) =>
        run.status === "succeeded" &&
        (kind === "rl"
          ? run.metricLayers?.kind === "rl-policy"
          : run.metricLayers?.kind === kind),
    ) ?? null;

const laneReadout = (project, lane) => {
  const kind = laneKind(lane);
  const run = runForLane(project, lane);
  const layers = run?.metricLayers;
  if (kind === "factor") {
    const value = layers?.kind === "factor" ? layers.validationMeanIc : lane?.latestRun?.value;
    if (!Number.isFinite(Number(value))) {
      return {
        kind,
        metric: "Validation rank IC",
        value,
        display: "—",
        tone: "warning",
        verdict: "EVIDENCE PENDING",
        detail: "No current immutable Factor Run is available",
      };
    }
    return {
      kind,
      metric: "Validation rank IC",
      value,
      display: metric(value),
      tone: Number(value) < 0 ? "bad" : "neutral",
      verdict: Number(value) < 0 ? "NEGATIVE VALIDATION IC" : "NON-NEGATIVE VALIDATION IC",
      detail:
        Number(value) < 0
          ? "Validation cross-sectional association is adverse"
          : "Direction is non-negative; fixed uncertainty and acceptance evidence still govern",
    };
  }
  if (kind === "portfolio") {
    const value =
      layers?.kind === "portfolio"
        ? layers.portfolio.validationNetSharpe
        : lane?.latestRun?.value;
    if (!Number.isFinite(Number(value))) {
      return {
        kind,
        metric: "Validation net Sharpe",
        value,
        display: "—",
        tone: "warning",
        verdict: "EVIDENCE PENDING",
        detail: "No current immutable Portfolio Run is available",
      };
    }
    return {
      kind,
      metric: "Validation net Sharpe",
      value,
      display: metric(value),
      tone: Number(value) < 0 ? "bad" : "neutral",
      verdict: Number(value) < 0 ? "NEGATIVE AFTER COSTS" : "NON-NEGATIVE AFTER COSTS",
      detail:
        Number(value) < 0
          ? "Mechanical portfolio evidence is adverse after implementation"
          : "Costed return is non-negative; robustness and fixed gates still govern",
    };
  }
  if (kind === "rl") {
    const value =
      layers?.kind === "rl-policy"
        ? layers.validationBaselineAdvantage
        : lane?.latestRun?.value;
    if (!Number.isFinite(Number(value))) {
      return {
        kind,
        metric: "RL vs best baseline",
        value,
        display: "—",
        tone: "warning",
        verdict: "EVIDENCE PENDING",
        detail: "No current immutable adaptive-policy Run is available",
      };
    }
    return {
      kind,
      metric: "RL vs best baseline",
      value,
      display: metric(value),
      tone: Number(value) < 0 ? "bad" : "neutral",
      verdict: Number(value) < 0 ? "TRAILS BEST BASELINE" : "ABOVE BEST BASELINE",
      detail:
        Number(value) >= 0
          ? "RL exceeds the fixed validation-selected baseline; this is not a promotion verdict"
          : "RL trails the best fixed validation-selected baseline",
    };
  }
  return {
    kind: kind ?? "unknown",
    metric: lane?.study?.objective?.metric ?? "Objective",
    value: lane?.latestRun?.value,
    display: metric(lane?.latestRun?.value),
    tone: "",
    verdict: lane?.latestRun ? "BASELINE READY" : "EVIDENCE PENDING",
    detail: lane?.latestRun ? "Immutable evidence is available" : "Run the fixed Study",
  };
};

const programAssessment = (project) => {
  const program = project.researchProgramStatus;
  if (!program) return null;
  const readouts = program.lanes.map((lane) => laneReadout(project, lane));
  const adverse = readouts.filter((item) => item.tone === "bad");
  const missing = program.lanes.filter((lane) => !lane.latestRun || !lane.currentRun);
  const recommended = program.lanes.find(
    (lane) => lane.id === program.recommendedLaneId,
  );
  if (program.summary.conflicts) {
    return {
      tone: "warning",
      label: "COORDINATION REQUIRED",
      title: "Resolve shared-source conflicts",
      detail: `${program.summary.conflicts} active conflict${program.summary.conflicts === 1 ? "" : "s"} can invalidate downstream evidence.`,
    };
  }
  if (missing.length) {
    return {
      tone: "warning",
      label: "EVIDENCE INCOMPLETE",
      title: "Refresh the research chain",
      detail: `${missing.length} lane${missing.length === 1 ? "" : "s"} lack current immutable evidence.`,
    };
  }
  if (adverse.length) {
    return {
      tone: "bad",
      label: "ADVERSE EVIDENCE",
      title: recommended ? `Next: ${recommended.name}` : "Review the earliest adverse lane",
      detail: `${adverse.map((item) => item.verdict.toLowerCase()).join(" · ")}. These are observed relationships, not a browser-authored verdict.`,
    };
  }
  return {
    tone: "neutral",
    label: "NO SIGN-LEVEL WARNING",
    title: recommended ? `Next: ${recommended.name}` : "Inspect fixed acceptance evidence",
    detail: "Headline values are non-negative. Only Core-owned gates, uncertainty, robustness, and verified reports may support promotion.",
  };
};

const shortHash = (value) =>
  typeof value === "string" && value.length > 14
    ? `${value.slice(0, 8)}…${value.slice(-6)}`
    : String(value ?? "—");

const relativeTime = (value) => {
  const milliseconds = Date.now() - new Date(value).getTime();
  if (!Number.isFinite(milliseconds)) return "unknown";
  const seconds = Math.max(0, Math.round(milliseconds / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
};

const selectedProject = () => {
  const projects = state.snapshot?.projects ?? [];
  return projects.find((project) => project.id === state.projectId) ?? projects[0] ?? null;
};

const selectedSession = (project = selectedProject()) => {
  const sessions = project?.sessions ?? [];
  return sessions.find((item) => item.session.id === state.sessionId) ?? sessions.at(-1) ?? null;
};

const hashProjectId = () => {
  try {
    return decodeURIComponent(window.location.hash.slice(1));
  } catch {
    return "";
  }
};

function setConnection(kind, label) {
  syncState.className = `sync-state ${kind}`;
  syncState.querySelector("span").textContent = label;
}

function projectMonogram(project) {
  return project.id
    .split("-")
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function renderProjects() {
  const projects = state.snapshot.projects;
  element("project-count").textContent = String(projects.length);
  element("project-list").innerHTML =
    projects
      .map((project) => {
        const active = project.id === state.projectId;
        const status = project.valid
          ? project.counts.runningCampaigns > 0 || project.counts.activeSessions > 0
            ? "active"
            : ""
          : "warning";
        return `
          <button class="project-button ${active ? "active" : ""}" type="button"
            data-project="${escapeHtml(project.id)}" aria-pressed="${active}">
            <span class="project-monogram">${escapeHtml(projectMonogram(project))}</span>
            <span>
              <strong>${escapeHtml(project.name)}</strong>
              <small>${project.counts.activeSessions} active · ${project.counts.runs} runs</small>
            </span>
            <i class="${status}" aria-hidden="true"></i>
          </button>`;
      })
      .join("") || '<p class="empty-copy">No valid Projects discovered.</p>';
  document.querySelectorAll("[data-project]").forEach((button) => {
    button.addEventListener("click", () => {
      state.projectId = button.dataset.project;
      state.sessionId = null;
      state.evidenceLane = null;
      window.location.hash = encodeURIComponent(state.projectId);
      render();
    });
  });
}

function renderScoreboard(project) {
  const counts = project.counts;
  const program = project.researchProgramStatus;
  if (program) {
    const readouts = Object.fromEntries(
      program.lanes.map((lane) => {
        const readout = laneReadout(project, lane);
        return [readout.kind, readout];
      }),
    );
    const current = program.lanes.filter(
      (lane) => lane.currentRun && lane.latestRun?.status === "succeeded",
    ).length;
    const values = [
      ["Current evidence", `${current}/${program.lanes.length}`, "immutable lane baselines", current === program.lanes.length ? "good" : "live"],
      [
        readouts.factor?.metric ?? "Factor evidence",
        readouts.factor?.display ?? "—",
        "validation selection",
        readouts.factor?.tone ?? "",
      ],
      [
        readouts.portfolio?.metric ?? "Portfolio evidence",
        readouts.portfolio?.display ?? "—",
        "costed implementation",
        readouts.portfolio?.tone ?? "",
      ],
      [
        readouts.rl?.metric ?? "Adaptive evidence",
        readouts.rl?.display ?? "—",
        "validation value-add",
        readouts.rl?.tone ?? "",
      ],
    ];
    element("scoreboard").innerHTML = values
      .map(
        ([label, value, note, className]) => `
          <div class="score-cell ${className}">
            <small>${escapeHtml(label)}</small>
            <strong>${escapeHtml(value)}</strong>
            <span>${escapeHtml(note)}</span>
          </div>`,
      )
      .join("");
    return;
  }
  const run = projectFocusRun(project);
  const layers = run?.metricLayers;
  let values;
  if (layers?.kind === "portfolio") {
    values = [
      ["Validation net Sharpe", metric(layers.portfolio.validationNetSharpe), "selection · baseline", valueTone(layers.portfolio.validationNetSharpe)],
      ["Validation rank IC", metric(layers.factor.validationRankIc), "causal factor", valueTone(layers.factor.validationRankIc)],
      ["Test max drawdown", percent(layers.portfolio.testMaximumDrawdown), "visible audit only", valueTone(layers.portfolio.testMaximumDrawdown)],
      ["25 bps stress", metric(layers.robustness.test25bpsSharpe), "test stress · audit", valueTone(layers.robustness.test25bpsSharpe)],
    ];
  } else if (layers?.kind === "rl-policy") {
    values = [
      ["Validation net Sharpe", metric(layers.validationMeanNetSharpe), "seed/fold mean", valueTone(layers.validationMeanNetSharpe)],
      ["Baseline advantage", metric(layers.validationBaselineAdvantage), "validation only", valueTone(layers.validationBaselineAdvantage)],
      ["Seed/fold dispersion", metric(layers.validationSeedFoldStd), "lower is steadier", ""],
      ["Failure rate", percent(layers.failureRate), `${layers.folds}×${layers.seeds} fold/seed`, layers.failureRate > 0 ? "bad" : "good"],
    ];
  } else if (layers?.kind === "factor") {
    values = [
      ["Validation rank IC", metric(layers.validationMeanIc), "1 bar · selection", valueTone(layers.validationMeanIc)],
      ["HAC t-stat", metric(layers.validationHacTStatistic), "dependence-aware", valueTone(layers.validationHacTStatistic)],
      ["Worst fold IC", metric(layers.validationWorstFoldMeanIc), "stability floor", valueTone(layers.validationWorstFoldMeanIc)],
      ["Test rank IC", metric(layers.testMeanIc), "visible audit only", valueTone(layers.testMeanIc)],
    ];
  } else {
    values = [
      ["Active Sessions", counts.activeSessions, counts.sessions === 1 ? "1 total" : `${counts.sessions} total`, counts.activeSessions ? "live" : ""],
      ["Running", counts.runningCampaigns, "mutable progress", counts.runningCampaigns ? "live" : ""],
      ["Reports", counts.reports, `${counts.delegatedSessions} delegated`, counts.reports ? "live" : ""],
      ["Immutable Runs", counts.runs, `${counts.verdicts.KEEP} kept · ${counts.campaigns} campaigns`, ""],
    ];
  }
  element("scoreboard").innerHTML = values
    .map(
      ([label, value, note, className]) => `
        <div class="score-cell ${className}">
          <small>${escapeHtml(label)}</small>
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(note)}</span>
        </div>`,
    )
    .join("");
}

function currentCampaign(session) {
  if (session.progress.length) {
    const progress = session.progress.at(-1);
    return {
      live: true,
      status: progress.phase,
      message: progress.message,
      turn: `${progress.turn}/${progress.budget.maxTurns}`,
    };
  }
  if (session.campaigns.length) {
    const campaign = session.campaigns.at(-1);
    return {
      live: false,
      status: campaign.status,
      message: campaign.reason,
      turn: String(campaign.turnsCompleted),
    };
  }
  return {
    live: false,
    status: session.session.status,
    message: "Manual Session",
    turn: "—",
  };
}

function renderSessions(project) {
  const sessions = project.sessions;
  const active = sessions.filter((item) => item.session.status === "active").length;
  const running = sessions.reduce((total, item) => total + item.progress.length, 0);
  element("pulse-meta").textContent = running
    ? `${running} Researcher ${running === 1 ? "is" : "are"} in progress`
    : `${active} active ${active === 1 ? "Session" : "Sessions"}`;
  element("session-lanes").innerHTML =
    sessions
      .map((item) => {
        const session = item.session;
        const campaign = currentCampaign(item);
        const selected = session.id === state.sessionId;
        return `
          <button class="session-lane ${selected ? "active" : ""}" type="button"
            data-session="${escapeHtml(session.id)}" aria-pressed="${selected}">
            <span class="lane-identity">
              <span>${item.delegation ? "delegated" : escapeHtml(session.status)} session</span>
              <strong>${escapeHtml(item.delegation?.request?.title ?? session.studyId)}</strong>
              <code>${escapeHtml(session.id)}</code>
            </span>
            <span class="lane-stat">
              <small>Leader</small>
              <strong>${metric(session.leader.value)}</strong>
            </span>
            <span class="lane-stat">
              <small>Family trials</small>
              <strong>${item.selectionIntegrity.researchFamily?.uniqueSourceTrials ?? item.experiments.length}</strong>
            </span>
            <span class="lane-stat">
              <small>Turn</small>
              <strong>${escapeHtml(campaign.turn)}</strong>
            </span>
            <span class="lane-stat">
              <small>Reports</small>
              <strong>${item.reports.length}</strong>
            </span>
            <span class="lane-state ${campaign.live ? "live" : normalizedStatus(campaign.status) === "failed" ? "warning" : ""}">
              <i aria-hidden="true"></i>
              <span>
                <small>${escapeHtml(campaign.status)}</small>
                <span>${escapeHtml(campaign.message)}</span>
              </span>
            </span>
          </button>`;
      })
      .join("") ||
    '<div class="empty-panel">No Sessions yet. Start one with <code>aq session start</code>.</div>';
  document.querySelectorAll("[data-session]").forEach((button) => {
    button.addEventListener("click", () => {
      state.sessionId = button.dataset.session;
      const session = project.sessions.find(
        (item) => item.session.id === state.sessionId,
      );
      const lane = evidenceLaneForStudy(project, session?.session.studyId);
      if (lane) state.evidenceLane = lane;
      render();
      element("inspector-content").scrollTop = 0;
    });
  });
}

function commandFor(session, id) {
  return session?.commands?.find((item) => item.id === id) ?? null;
}

function copyCommandButton(command, label = "Copy command") {
  if (!command) return "";
  return `
    <button class="command-button" type="button"
      data-copy-command="${escapeHtml(command.display)}"
      data-copy-label="${escapeHtml(label)}"
      title="${escapeHtml(command.display)}">
      <span>${escapeHtml(label)}</span>
      <code>${escapeHtml(command.display)}</code>
    </button>`;
}

function compactCommandButton(command, label = "Copy CLI") {
  if (!command) return "";
  return `
    <button class="command-button compact-command" type="button"
      data-copy-command="${escapeHtml(command.display)}"
      data-copy-label="${escapeHtml(label)}"
      title="${escapeHtml(command.display)}">
      <span>${escapeHtml(label)}</span>
      <code>${escapeHtml(command.display)}</code>
    </button>`;
}

function bindCopyCommands() {
  document.querySelectorAll("[data-copy-command]").forEach((button) => {
    button.addEventListener("click", async () => {
      const label = button.querySelector("span");
      try {
        await navigator.clipboard.writeText(button.dataset.copyCommand);
        if (label) label.textContent = "Copied";
      } catch {
        if (label) label.textContent = "Copy failed";
      }
      window.setTimeout(() => {
        if (label) label.textContent = button.dataset.copyLabel ?? "Copy command";
      }, 1600);
    });
  });
}

function dossierState(project) {
  const status = project.dossierStatus;
  if (!status) return null;
  const latest = status.latestDossier;
  const current = Boolean(latest?.current);
  return {
    status,
    latest,
    current,
    label: current ? "PUBLISHED" : status.ready ? "READY TO SYNTHESIZE" : "BLOCKED",
    tone: current ? "published" : status.ready ? "active" : "blocked",
    command: status.nextAction,
  };
}

function dossierInspectorSection(project) {
  const dossier = dossierState(project);
  if (!dossier) return "";
  const included = dossier.status.includedLaneIds.join(", ") || "none";
  const omissions = dossier.status.omittedOptionalLanes
    .map((lane) => `${lane.name}: ${lane.reason}`)
    .join(" · ");
  const blockerSummary = dossier.status.blockers
    .map((blocker) => blocker.message)
    .join(" · ");
  return `
    <section class="inspector-section dossier-inspector">
      <small>OpenAlice return artifact</small>
      <h3>${escapeHtml(dossier.latest?.title ?? "Project Research Dossier")}</h3>
      <span class="status-chip ${escapeHtml(dossier.tone)}">${escapeHtml(dossier.label)}</span>
      <p>${escapeHtml(
        dossier.latest?.executiveSummary ??
          (dossier.status.ready
            ? "Current Factor and Portfolio lane Reports are ready for Agent-authored cross-lane synthesis."
            : blockerSummary || "Required lane evidence is incomplete."),
      )}</p>
      <dl class="inspector-kv">
        <dt>Included lanes</dt><dd>${escapeHtml(included)}</dd>
        <dt>Optional omissions</dt><dd>${escapeHtml(omissions || "none")}</dd>
        <dt>Trading authority</dt><dd>none</dd>
      </dl>
      ${copyCommandButton(dossier.command, dossier.current ? "Copy Dossier show CLI" : "Copy next Dossier CLI")}
    </section>`;
}

function renderHandoff(project) {
  const session = selectedSession(project);
  const delegation = session?.delegation;
  const section = element("research-handoff");
  section.classList.remove("compact");
  const dossier = dossierState(project);
  if (dossier && project.intake) {
    const request = project.intake.request;
    const dataset = project.intake.dataset;
    const readyLanes = dossier.status.lanes.filter((lane) => lane.status === "ready");
    const reportCount = dossier.status.lanes.filter((lane) => lane.report).length;
    const omissions = dossier.status.omittedOptionalLanes;
    const blockers = dossier.status.blockers;
    const currentTitle = dossier.latest?.title ?? "Cross-lane synthesis pending";
    const currentSummary =
      dossier.latest?.executiveSummary ??
      (dossier.status.ready
        ? "Agent analysis can now compose the verified lane Reports into one immutable Project answer."
        : blockers[0]?.message ?? "Required lane evidence is incomplete.");
    element("handoff-flow").textContent =
      "REQUEST → LANE REPORTS → PROJECT DOSSIER → OPENALICE";
    element("handoff-meta").textContent = dossier.current
      ? `Current Dossier · ${dossier.status.includedLaneIds.length} lanes`
      : dossier.status.ready
        ? `${reportCount} current lane Reports · synthesis pending`
        : `${blockers.length} required evidence blocker${blockers.length === 1 ? "" : "s"}`;
    element("handoff-board").innerHTML = `
      <article class="handoff-card request-card">
        <small>01 · Incoming request</small>
        <h3>${escapeHtml(request.title)}</h3>
        <p>${escapeHtml(request.question)}</p>
        <dl class="handoff-kv">
          <dt>Assets</dt><dd>${escapeHtml(request.assets.map((item) => item.symbol).join(", "))}</dd>
          <dt>Direction</dt><dd>${escapeHtml(request.direction)}</dd>
          <dt>Horizon</dt><dd>${escapeHtml(request.horizon)}</dd>
        </dl>
        <span class="context-note">Caller-supplied context · ${escapeHtml(request.source.system)} / ${escapeHtml(request.source.workspaceId ?? "unspecified")}</span>
      </article>
      <article class="handoff-card evidence-card">
        <small>02 · Governed lane Reports</small>
        <h3>${readyLanes.length}/${dossier.status.lanes.length} lanes composable</h3>
        <p>Factor and Portfolio are required. Adaptive policy evidence is optional and can only join when its frozen Factor dependency matches.</p>
        <div class="handoff-metrics">
          <span><b>${readyLanes.length}</b><small>ready lanes</small></span>
          <span><b>${reportCount}</b><small>current reports</small></span>
          <span><b>${dossier.status.blockers.length}</b><small>blockers</small></span>
        </div>
        <span class="context-note">${escapeHtml(dataset.id)}@${escapeHtml(dataset.version)} · ${escapeHtml(dataset.timeRange.start)} → ${escapeHtml(dataset.timeRange.end)}${omissions.length ? ` · omitted: ${escapeHtml(omissions.map((lane) => lane.name).join(", "))}` : ""}</span>
      </article>
      <article class="handoff-card report-card ${dossier.current ? "ready" : ""}">
        <small>03 · OpenAlice return artifact</small>
        <h3>${escapeHtml(currentTitle)}</h3>
        <p>${escapeHtml(currentSummary)}</p>
        <span class="status-chip ${escapeHtml(dossier.tone)}">${escapeHtml(dossier.label)}</span>
        ${copyCommandButton(dossier.command, dossier.current ? "Copy Dossier show CLI" : "Copy next governed CLI")}
      </article>`;
    return;
  }
  if (!session || !delegation) {
    const intake = project.intake;
    if (intake) {
      const request = intake.request;
      const dataset = intake.dataset;
      const source = request.source;
      const program = project.researchProgramStatus;
      const lane = projectFocusLane(project);
      const next =
        program?.recommendedAction ??
        intake.commands.find((item) => item.id === "session.start");
      const baseline = projectFocusRun(project);
      const layers = baseline?.metricLayers;
      const portfolio = layers?.kind === "portfolio" ? layers : null;
      const baselineTone = valueTone(baseline?.primaryValue);
      element("handoff-flow").textContent =
        "REQUEST → DATASET → BASELINE → ITERATE";
      element("handoff-meta").textContent = baseline
        ? `${baseline.primaryMetric} ${metric(baseline.primaryValue)} · Session not started`
        : "Content locked · baseline pending";
      element("handoff-board").innerHTML = `
        <article class="handoff-card request-card">
          <small>01 · Research mandate</small>
          <h3>${escapeHtml(request.title)}</h3>
          <p>${escapeHtml(request.question)}</p>
          <dl class="handoff-kv">
            <dt>Requested assets</dt><dd>${escapeHtml(request.assets.map((item) => item.symbol).join(", "))}</dd>
            <dt>Direction</dt><dd>${escapeHtml(request.direction)}</dd>
            <dt>Horizon</dt><dd>${escapeHtml(request.horizon)}</dd>
          </dl>
          <span class="context-note">Caller-supplied context · ${escapeHtml(source.system)} / ${escapeHtml(source.workspaceId ?? "unspecified")}</span>
        </article>
        <article class="handoff-card evidence-card">
          <small>02 · Research universe</small>
          <h3>${dataset.universe.length}-asset content-locked panel</h3>
          <p>${escapeHtml(dataset.universe.join(" · "))}</p>
          <div class="handoff-metrics">
            <span><b>${escapeHtml(dataset.frequency)}</b><small>frequency</small></span>
            <span><b>${dataset.assets[0]?.observations ?? "—"}</b><small>sessions</small></span>
            <span><b>${escapeHtml(dataset.market.calendar)}</b><small>calendar claim</small></span>
          </div>
          <span class="context-note">${escapeHtml(dataset.provider.name)} · ${escapeHtml(dataset.priceAdjustment)} · ${escapeHtml(dataset.timeRange.start)} → ${escapeHtml(dataset.timeRange.end)} · provider claims</span>
        </article>
        <article class="handoff-card report-card ${baseline ? "ready" : ""}">
          <small>03 · ${lane ? escapeHtml(lane.name) : "Baseline"} &amp; next action</small>
          <h3>${baseline ? `${escapeHtml(baseline.primaryMetric)} = ${metric(baseline.primaryValue)}` : escapeHtml(intake.study.name)}</h3>
          <p>${baseline ? "The immutable baseline is descriptive evidence, not a recommendation. Start a governed Session to test candidates against validation-only selection." : "Start a governed Session to run a fresh baseline and freeze this request into its derived Brief."}</p>
          ${portfolio ? `
          <div class="handoff-metrics">
            <span class="${valueTone(portfolio.factor.validationRankIc)}"><b>${metric(portfolio.factor.validationRankIc)}</b><small>validation IC</small></span>
            <span class="${valueTone(portfolio.portfolio.testMaximumDrawdown)}"><b>${percent(portfolio.portfolio.testMaximumDrawdown)}</b><small>test max DD</small></span>
            <span class="${valueTone(portfolio.robustness.test25bpsSharpe)}"><b>${metric(portfolio.robustness.test25bpsSharpe)}</b><small>25bps audit</small></span>
          </div>` : ""}
          <span class="status-chip ${baselineTone === "bad" ? "revert" : "active"}">${baseline ? (baselineTone === "bad" ? "negative baseline" : "baseline verified") : "ready"}</span>
          ${copyCommandButton(next, program ? "Copy recommended command" : "Copy start command")}
        </article>`;
      return;
    }
    element("handoff-flow").textContent = "REQUEST → EVIDENCE → REPORT";
    element("handoff-meta").textContent = "No delegated request";
    section.classList.add("compact");
    element("handoff-board").innerHTML = `
      <div class="empty-panel handoff-empty">
        <span><b>No caller brief is bound.</b> Add <code>--request request.json</code> when another
        OpenAlice workbench delegates a question; AutoQuant will preserve intent, evidence identity,
        and the return-report boundary.</span>
      </div>`;
    return;
  }
  const request = delegation.request;
  const source = request.source;
  const latestReport = session.reports.at(-1);
  const publish = commandFor(session, "report.publish");
  const show = commandFor(session, "report.show");
  const assets = request.assets.map((item) => item.symbol).join(", ");
  element("handoff-flow").textContent = "REQUEST → EVIDENCE → REPORT";
  element("handoff-meta").textContent =
    latestReport ? `${session.reports.length} verified report${session.reports.length === 1 ? "" : "s"}` : "Report analysis pending";
  element("handoff-board").innerHTML = `
    <article class="handoff-card request-card">
      <small>01 · Incoming request</small>
      <h3>${escapeHtml(request.title)}</h3>
      <p>${escapeHtml(request.question)}</p>
      <dl class="handoff-kv">
        <dt>Assets</dt><dd>${escapeHtml(assets)}</dd>
        <dt>Direction</dt><dd>${escapeHtml(request.direction)}</dd>
        <dt>Horizon</dt><dd>${escapeHtml(request.horizon)}</dd>
      </dl>
      <span class="context-note">Caller-supplied context · ${escapeHtml(source.system)} / ${escapeHtml(source.workspaceId ?? "unspecified")}</span>
    </article>
    <article class="handoff-card evidence-card">
      <small>02 · Governed evidence</small>
      <h3>${escapeHtml(session.session.studyId)}</h3>
      <p>${session.authority.valid ? "Fixed Study authority is verified." : "Authority needs attention before publication."}</p>
      <div class="handoff-metrics">
        <span><b>${metric(session.session.leader.value)}</b><small>leader</small></span>
        <span><b>${session.selectionIntegrity.researchFamily?.uniqueSourceTrials ?? session.experiments.length}</b><small>family trials</small></span>
        <span><b>${session.campaigns.length}</b><small>campaigns</small></span>
      </div>
      <span class="context-note">${escapeHtml(session.selectionIntegrity.selectionMetric)} · ${escapeHtml(session.selectionIntegrity.selectionSplit)} selection · ${escapeHtml(selectionContext(session.selectionIntegrity))} · ${escapeHtml(session.selectionIntegrity.testRole)} test${session.selectionIntegrity.externalHoldoutRequired ? " · new holdout required" : ""}</span>
    </article>
    <article class="handoff-card report-card ${latestReport ? "ready" : ""}">
      <small>03 · Decision-support report</small>
      <h3>${escapeHtml(latestReport?.title ?? "Analysis not published")}</h3>
      <p>${escapeHtml(latestReport?.executiveSummary ?? "An Agent supplies strict findings; Core verifies references and renders the report.")}</p>
      <span class="status-chip ${latestReport ? "published" : "active"}">${latestReport ? "verified" : "pending"}</span>
      ${copyCommandButton(latestReport ? show : publish)}
    </article>`;
}

function programPhaseLabel(phase) {
  return {
    "not-started": "NOT STARTED",
    "baseline-ready": "BASELINE READY",
    researching: "RESEARCHING",
    reported: "REPORTED",
    stale: "STALE EVIDENCE",
  }[phase] ?? String(phase ?? "unknown").toUpperCase();
}

function renderResearchProgram(project) {
  const section = element("research-program-status");
  const program = project.researchProgramStatus;
  if (!program) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  const summary = program.summary;
  const recommended = program.recommendedAction;
  const assessment = programAssessment(project);
  const dossier = dossierState(project);
  const currentRuns = program.lanes.filter(
    (lane) => lane.currentRun && lane.latestRun?.status === "succeeded",
  ).length;
  element("research-program-meta").textContent =
    `${program.dataset.universe.length} assets · one snapshot · ${summary.lanes} fixed Studies`;
  element("research-program-summary").innerHTML = [
    ["Evidence chain", `${currentRuns}/${summary.lanes}`, "current immutable baselines"],
    ["Active researchers", summary.activeSessions, "governed Sessions"],
    ["Lane reports", summary.reports, "verified decision-support evidence"],
    [
      "OpenAlice dossier",
      dossier?.current ? "PUBLISHED" : dossier?.status.ready ? "READY" : "BLOCKED",
      dossier?.current
        ? `${dossier.status.includedLaneIds.length} frozen lanes`
        : dossier?.status.ready
          ? "Agent synthesis pending"
          : `${dossier?.status.blockers.length ?? 0} required blockers`,
    ],
  ]
    .map(
      ([label, value, note], index) => `
        <span class="${index === 3 ? (dossier?.current ? "ready" : dossier?.status.ready ? "warning" : "warning") : ""}">
          <small>${escapeHtml(label)}</small>
          <b>${escapeHtml(value)}</b>
          <i>${escapeHtml(note)}</i>
        </span>`,
    )
    .join("");
  element("research-program-assessment").innerHTML = `
    <span class="assessment-signal ${escapeHtml(assessment.tone)}">
      <i aria-hidden="true"></i>
      <small>Evidence readout</small>
      <b>${escapeHtml(assessment.label)}</b>
    </span>
    <span class="assessment-copy">
      <strong>${escapeHtml(assessment.title)}</strong>
      <span>${escapeHtml(assessment.detail)}</span>
    </span>
    <span class="assessment-boundary">Validation decides · test audits · no trading authority</span>`;
  element("research-program-lanes").innerHTML = program.lanes
    .map((lane, index) => {
      const session = lane.latestSession;
      const selected = lane.id === program.recommendedLaneId;
      const kind = laneKind(lane);
      const readout = laneReadout(project, lane);
      const evidenceSelected = kind === state.evidenceLane;
      const command =
        lane.commands.find((item) => item.id === recommended?.id) ??
        lane.commands.find((item) => item.id === "session.show") ??
        lane.commands.find((item) => item.id === "run.execute") ??
        lane.commands[0];
      return `
        <article class="program-lane ${lane.phase} ${selected ? "recommended" : ""} ${evidenceSelected ? "evidence-selected" : ""}">
          <header>
            <span>${String(index + 1).padStart(2, "0")}</span>
            <small>${escapeHtml(lane.role)}</small>
          </header>
          <h3>${escapeHtml(lane.name)}</h3>
          <div class="program-lane-readout ${escapeHtml(readout.tone)}">
            <small>${escapeHtml(readout.metric)}</small>
            <strong>${escapeHtml(readout.display)}</strong>
            <b>${escapeHtml(readout.verdict)}</b>
          </div>
          <p>${escapeHtml(readout.detail)}</p>
          <dl>
            <dt>Session</dt>
            <dd>${session ? `${escapeHtml(session.status)} · ${session.experiments} experiments` : "not started"}</dd>
            <dt>Source</dt>
            <dd>${escapeHtml(lane.editablePaths.join(", "))}</dd>
            ${lane.dependencyPaths?.length ? `
              <dt>Fixed input</dt>
              <dd>${escapeHtml(lane.dependencyPaths.join(", "))}</dd>
            ` : ""}
          </dl>
          <div class="program-lane-foot">
            <span class="program-phase ${lane.phase}">${escapeHtml(programPhaseLabel(lane.phase))}</span>
            ${selected ? "<b>NEXT RESEARCH LANE</b>" : ""}
          </div>
          <div class="program-lane-actions">
            <button class="lane-open-button" type="button" data-open-evidence="${escapeHtml(kind)}">
              Inspect evidence
            </button>
            ${compactCommandButton(command)}
          </div>
        </article>`;
    })
    .join("");
  element("research-program-footer").innerHTML = `
    <span>
      <b>${program.conflicts.length ? "Shared-source conflict" : "Integration boundary"}</b>
      ${escapeHtml(program.warnings.join(" · "))} · Dossier composition is Core-verified and has no trading authority.
    </span>
    ${copyCommandButton(dossier?.command ?? recommended, dossier ? "Copy Dossier next action" : "Copy recommended command")}`;
}

const evidenceLanes = [
  {
    id: "factor",
    label: "Factor",
    question: "Does the signal predict?",
    explorer: "factorExplorer",
    section: "factor-explorer",
  },
  {
    id: "portfolio",
    label: "Portfolio",
    question: "Does the edge survive implementation?",
    explorer: "portfolioExplorer",
    section: "portfolio-explorer",
  },
  {
    id: "rl",
    label: "Adaptive policy",
    question: "Does RL beat the best simpler policy?",
    explorer: "rlExplorer",
    section: "rl-explorer",
  },
];

const studyIdsByEvidenceLane = {
  factor: "ohlcv-factor-quality",
  portfolio: "ohlcv-portfolio-quality",
  rl: "ohlcv-rl-factor-policy",
};

function evidenceLaneForStudy(project, studyId) {
  const programLane = project.researchProgramStatus?.lanes.find(
    (lane) => lane.studyId === studyId,
  );
  return laneKind(programLane) ??
    Object.entries(studyIdsByEvidenceLane).find(
      ([, candidateStudyId]) => candidateStudyId === studyId,
    )?.[0] ??
    null;
}

function sessionForEvidenceLane(project, laneId) {
  const programLane = project.researchProgramStatus?.lanes.find(
    (lane) => laneKind(lane) === laneId,
  );
  const latestSessionId = programLane?.latestSession?.id;
  return (
    project.sessions.find(
      (item) => item.session.id === latestSessionId,
    ) ??
    project.sessions
      .slice()
      .reverse()
      .find(
        (item) =>
          evidenceLaneForStudy(project, item.session.studyId) === laneId,
      ) ??
    null
  );
}

function syncEvidenceSelection(project) {
  const available = evidenceLanes.filter((lane) => project[lane.explorer]);
  if (!available.length) return;
  const recommendedKind = laneKind(projectFocusLane(project));
  if (!available.some((lane) => lane.id === state.evidenceLane)) {
    state.evidenceLane =
      available.find((lane) => lane.id === recommendedKind)?.id ??
      available[0].id;
  }
  const selected = selectedSession(project);
  if (
    evidenceLaneForStudy(project, selected?.session.studyId) !==
    state.evidenceLane
  ) {
    state.sessionId =
      sessionForEvidenceLane(project, state.evidenceLane)?.session.id ??
      state.sessionId;
  }
}

function renderEvidenceWorkbench(project) {
  const section = element("evidence-workbench");
  const available = evidenceLanes.filter((lane) => project[lane.explorer]);
  if (!available.length) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  const recommendedKind = laneKind(projectFocusLane(project));
  if (!available.some((lane) => lane.id === state.evidenceLane)) {
    state.evidenceLane =
      available.find((lane) => lane.id === recommendedKind)?.id ?? available[0].id;
  }
  const selected = available.find((lane) => lane.id === state.evidenceLane);
  element("evidence-workbench-meta").textContent =
    `${selected.label} lane · immutable Run evidence`;
  element("evidence-lane-tabs").innerHTML = available
    .map((lane, index) => {
      const laneProgram = project.researchProgramStatus?.lanes.find(
        (item) => laneKind(item) === lane.id,
      );
      const fallbackRun = latestRunForLaneKind(project, lane.id);
      const readout = laneReadout(
        project,
        laneProgram ?? {
          id: lane.id,
          latestRun: fallbackRun ? { id: fallbackRun.id, value: fallbackRun.primaryValue } : null,
        },
      );
      const active = lane.id === state.evidenceLane;
      return `
        <button type="button" role="tab" aria-selected="${active}"
          data-evidence-lane="${escapeHtml(lane.id)}">
          <span>${String(index + 1).padStart(2, "0")} · ${escapeHtml(lane.label)}</span>
          <strong>${escapeHtml(readout.verdict)}</strong>
          <small>${escapeHtml(lane.question)}</small>
        </button>`;
    })
    .join("");
  evidenceLanes.forEach((lane) => {
    const explorer = element(lane.section);
    if (!project[lane.explorer]) return;
    explorer.hidden = lane.id !== state.evidenceLane;
  });
  document
    .querySelectorAll("[data-evidence-lane], [data-open-evidence]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        state.evidenceLane =
          button.dataset.evidenceLane ?? button.dataset.openEvidence;
        state.sessionId =
          sessionForEvidenceLane(project, state.evidenceLane)?.session.id ??
          state.sessionId;
        render();
        element("evidence-workbench").scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      });
    });
}

function chartTime(timestamp) {
  return Date.parse(`${timestamp}T00:00:00Z`);
}

function chartPath(points, value, xScale, yScale) {
  return points
    .map((point, index) => {
      const x = xScale(chartTime(point.timestamp));
      const y = yScale(Number(value(point)));
      return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

function factorSeriesPath(points, key, xScale, yScale) {
  return points
    .filter((point) => Number.isFinite(Number(point[key])))
    .map((point, index) => {
      const x = xScale(chartTime(point.timestamp));
      const y = yScale(Number(point[key]));
      return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

function factorChartDateLabels(points, xScale, y) {
  if (!points.length) return "";
  const first = points[0].timestamp;
  const last = points.at(-1).timestamp;
  return [first, last]
    .map(
      (timestamp, index) => `
        <text class="chart-axis-label" x="${xScale(chartTime(timestamp)).toFixed(2)}"
          y="${y}" text-anchor="${index ? "end" : "start"}">
          ${escapeHtml(timestamp)}
        </text>`,
    )
    .join("");
}

function renderFactorChart(explorer) {
  const chart = element("factor-chart");
  const horizon = state.factorHorizon;
  const split = state.factorSplit;
  const audit = split === "test";
  const source =
    state.factorView === "quantiles"
      ? explorer.quantilePath.points.filter(
          (point) =>
            point.split === split && String(point.horizon) === horizon,
        )
      : explorer.icPath.points.filter((point) => point.split === split);
  document.querySelectorAll("[data-factor-view]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.factorView === state.factorView),
    );
  });
  document.querySelectorAll("[data-factor-horizon]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.factorHorizon === horizon),
    );
  });
  document.querySelectorAll("[data-factor-split]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.factorSplit === split),
    );
  });
  element("factor-chart-title").textContent =
    state.factorView === "quantiles"
      ? "Fixed-tertile forward returns"
      : "Rank & Pearson IC path";
  element("factor-chart-note").textContent =
    `${horizon}-bar · ${split}${audit ? " · VISIBLE AUDIT ONLY" : " · SELECTION"} · ${source.length} sampled points`;
  if (!source.length) {
    chart.innerHTML =
      '<div class="empty-panel">No finite evidence for this fixed split and horizon.</div>';
    return;
  }
  const width = 760;
  const height = 270;
  const left = 46;
  const right = 14;
  const top = 20;
  const bottom = 34;
  const firstTime = chartTime(source[0].timestamp);
  const lastTime = chartTime(source.at(-1).timestamp);
  const timeSpread = Math.max(1, lastTime - firstTime);
  const xScale = (value) =>
    left + ((value - firstTime) / timeSpread) * (width - left - right);
  const keys =
    state.factorView === "quantiles"
      ? ["low", "middle", "high", "highMinusLow"]
      : [`rankIcH${horizon}`, `pearsonIcH${horizon}`];
  const values = [
    0,
    ...source.flatMap((point) =>
      keys
        .map((key) => Number(point[key]))
        .filter((value) => Number.isFinite(value)),
    ),
  ];
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const padding = Math.max(1e-6, (maximum - minimum) * 0.08);
  const low = minimum - padding;
  const high = maximum + padding;
  const spread = Math.max(1e-9, high - low);
  const yScale = (value) =>
    top + ((high - value) / spread) * (height - top - bottom);
  const zero = yScale(0);
  const palette =
    state.factorView === "quantiles"
      ? [
          ["low", "factor-low", "Low"],
          ["middle", "factor-middle", "Middle"],
          ["high", "factor-high", "High"],
          ["highMinusLow", "factor-spread", "High − low"],
        ]
      : [
          [`rankIcH${horizon}`, "factor-rank", "Rank IC"],
          [`pearsonIcH${horizon}`, "factor-pearson", "Pearson IC"],
        ];
  chart.innerHTML = `
    <svg class="factor-svg" viewBox="0 0 ${width} ${height}" role="img"
      aria-label="${escapeHtml(state.factorView === "quantiles" ? "Quantile forward-return path" : "Rank and Pearson information-coefficient path")}">
      <line class="factor-zero" x1="${left}" x2="${width - right}" y1="${zero}" y2="${zero}"></line>
      <text class="chart-axis-label" x="${left - 6}" y="${top + 4}" text-anchor="end">${escapeHtml(metric(high))}</text>
      <text class="chart-axis-label" x="${left - 6}" y="${zero + 4}" text-anchor="end">0</text>
      <text class="chart-axis-label" x="${left - 6}" y="${height - bottom}" text-anchor="end">${escapeHtml(metric(low))}</text>
      ${palette
        .map(
          ([key, className, label]) => `
            <path class="factor-line ${className}" d="${factorSeriesPath(source, key, xScale, yScale)}">
              <title>${escapeHtml(label)}</title>
            </path>`,
        )
        .join("")}
      ${factorChartDateLabels(source, xScale, height - 8)}
    </svg>
    <div class="factor-legend">
      ${palette
        .map(
          ([, className, label]) => `
            <span class="${className}"><i></i>${escapeHtml(label)}</span>`,
        )
        .join("")}
      <span class="${audit ? "audit-label" : "selection-label"}">${audit ? "TEST · AUDIT ONLY" : "VALIDATION · SELECTION"}</span>
    </div>`;
}

function renderFactorHorizons(explorer) {
  const rows = explorer.horizonProfile;
  element("factor-horizons").innerHTML = `
    <table class="factor-table horizon-table" aria-label="Fixed factor horizon profile">
      <thead>
        <tr>
          <th>Horizon</th>
          <th>Train</th>
          <th>Validation</th>
          <th>Test audit</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr>
                <th>${row.horizon} bar${row.horizon === 1 ? "" : "s"}</th>
                <td><b>${metric(row.train.meanRankIc)}</b><small>IC · ${row.train.observations} obs</small></td>
                <td class="selection-cell"><b>${metric(row.validation.meanRankIc)}</b><small>IC · t ${metric(row.validation.hacTStatistic)}</small></td>
                <td class="audit-cell"><b>${metric(row.test.meanRankIc)}</b><small>AUDIT · ${row.test.observations} obs</small></td>
              </tr>`,
          )
          .join("")}
      </tbody>
    </table>`;
}

function renderFactorStability(explorer) {
  const split = state.factorSplit;
  const kind = state.factorStability;
  document.querySelectorAll("[data-factor-stability]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.factorStability === kind),
    );
  });
  const definitions = {
    regimes: {
      rows: explorer.stability.causalRegimes.filter(
        (row) => row.split === split,
      ),
      name: (row) => row.regime,
      value: (row) => row.meanRankIc,
      detail: (row) =>
        `${row.observations} obs · ${row.sufficient ? "sufficient" : "sparse"}`,
      label: "Mean rank IC",
    },
    folds: {
      rows: explorer.stability.chronologicalFolds.filter(
        (row) => row.split === split,
      ),
      name: (row) => row.id,
      value: (row) => row.meanRankIc,
      detail: (row) => `${row.observations} obs · ICIR ${metric(row.rankIcir)}`,
      label: "Mean rank IC",
    },
    assets: {
      rows: explorer.stability.assets.filter((row) => row.split === split),
      name: (row) => row.asset,
      value: (row) => row.rankCorrelation,
      detail: (row) => `${row.observations} paired observations`,
      label: "Time-series rank corr.",
    },
    styles: {
      rows: explorer.stability.styles.filter((row) => row.split === split),
      name: (row) => row.style.replaceAll("_", " "),
      value: (row) => row.meanRankCorrelation,
      detail: (row) =>
        `|corr| mean ${metric(row.meanAbsoluteRankCorrelation)} · ${row.observations} obs`,
      label: "Mean rank overlap",
    },
  };
  const definition = definitions[kind];
  element("factor-stability").innerHTML = `
    <div class="factor-stability-meta">
      <span>${escapeHtml(definition.label)}</span>
      <b class="${split === "test" ? "audit-label" : "selection-label"}">${split === "test" ? "TEST · AUDIT ONLY" : "VALIDATION · SELECTION CONTEXT"}</b>
    </div>
    <div class="factor-stability-grid">
      ${definition.rows
        .map((row) => {
          const value = definition.value(row);
          const magnitude = Number.isFinite(Number(value))
            ? Math.min(100, Math.abs(Number(value)) * 100)
            : 0;
          return `
            <div class="factor-stability-row">
              <span>
                <b>${escapeHtml(definition.name(row))}</b>
                <small>${escapeHtml(definition.detail(row))}</small>
              </span>
              <i><u style="width:${magnitude}%"></u></i>
              <strong>${metric(value)}</strong>
            </div>`;
        })
        .join("") || '<div class="empty-panel">No stability rows for this split.</div>'}
    </div>`;
}

function renderFactorExplorer(project) {
  const section = element("factor-explorer");
  const explorer = project.factorExplorer;
  if (!explorer) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  const summary = explorer.summary;
  const validation = summary.validation;
  const test = summary.testAudit;
  element("factor-meta").textContent =
    `${explorer.run.id} · ${explorer.dataset.universe.length} assets · validation selection`;
  element("factor-summary").innerHTML = [
    ["Validation rank IC", metric(validation.meanRankIc), `${validation.observations} observations`],
    ["HAC t / p", `${metric(validation.hacTStatistic)} / ${metric(validation.hacNormalPValue)}`, "normal approximation"],
    ["Weakest validation fold", metric(summary.weakestValidationFold?.meanRankIc), summary.weakestValidationFold?.id ?? "unavailable"],
    ["Maximum style overlap", metric(summary.maximumValidationStyleOverlap?.absoluteMeanRankCorrelation), summary.maximumValidationStyleOverlap?.style?.replaceAll("_", " ") ?? "unavailable"],
    ["Coverage", percent(summary.meanCoverage), "mean asset availability"],
    ["Rank turnover", percent(summary.meanRankTurnover), "full-scope diagnostic"],
    ["Test rank IC", metric(test.meanRankIc), "VISIBLE AUDIT ONLY"],
  ]
    .map(
      ([label, value, note]) => `
        <span>
          <small>${escapeHtml(label)}</small>
          <b>${escapeHtml(value)}</b>
          <i>${escapeHtml(note)}</i>
        </span>`,
    )
    .join("");
  renderFactorChart(explorer);
  renderFactorHorizons(explorer);
  renderFactorStability(explorer);
  const command = project.commands?.find((item) => item.id === "run.factor");
  element("factor-warning").innerHTML = `
    <span>${escapeHtml(explorer.warning)}</span>
    ${copyCommandButton(command, "Copy Factor JSON command")}`;
}

function splitBands(explorer, xScale, top, height) {
  const splits = explorer.selection.splits;
  return ["train", "validation", "test"]
    .map((name) => {
      const split = splits[name];
      const left = xScale(chartTime(split.start));
      const right = xScale(chartTime(split.end));
      return `
        <rect class="split-band ${name}" x="${left.toFixed(2)}" y="${top}"
          width="${Math.max(0, right - left).toFixed(2)}" height="${height}">
          <title>${escapeHtml(name)} · ${escapeHtml(split.role)}</title>
        </rect>`;
    })
    .join("");
}

function chartDateLabels(explorer, xScale, y) {
  const first = explorer.path.points[0].timestamp;
  const last = explorer.path.points.at(-1).timestamp;
  const validation = explorer.selection.splits.validation.start;
  const test = explorer.selection.splits.test.start;
  return [first, validation, test, last]
    .map(
      (timestamp, index, values) => `
        <text class="chart-axis-label" x="${xScale(chartTime(timestamp)).toFixed(2)}"
          y="${y}" text-anchor="${index === 0 ? "start" : index === values.length - 1 ? "end" : "middle"}">
          ${escapeHtml(timestamp)}
        </text>`,
    )
    .join("");
}

function renderPerformanceChart(explorer) {
  const points = explorer.path.points;
  const width = 760;
  const left = 42;
  const right = 12;
  const firstTime = chartTime(points[0].timestamp);
  const lastTime = chartTime(points.at(-1).timestamp);
  const timeSpread = Math.max(1, lastTime - firstTime);
  const xScale = (value) => {
    const ratio = Math.max(0, Math.min(1, (value - firstTime) / timeSpread));
    return left + ratio * (width - left - right);
  };
  const growthValues = points.flatMap((point) => [
    point.netGrowth,
    point.grossGrowth,
    point.benchmarkGrowth,
  ]);
  const growthMin = Math.min(...growthValues);
  const growthMax = Math.max(...growthValues);
  const growthSpread = Math.max(1e-9, growthMax - growthMin);
  const growthTop = 18;
  const growthHeight = 164;
  const growthY = (value) =>
    growthTop + ((growthMax - value) / growthSpread) * growthHeight;
  const drawdownTop = 207;
  const drawdownHeight = 52;
  const drawdownMin = Math.min(
    -1e-9,
    ...points.map((point) => point.drawdown),
  );
  const drawdownY = (value) =>
    drawdownTop + (value / drawdownMin) * drawdownHeight;
  const drawdownArea = `${chartPath(points, (point) => point.drawdown, xScale, drawdownY)} L${xScale(lastTime).toFixed(2)},${drawdownTop} L${xScale(firstTime).toFixed(2)},${drawdownTop} Z`;
  return `
    <svg viewBox="0 0 ${width} 286" role="img"
      aria-label="Net, gross, and benchmark growth with net drawdown">
      ${splitBands(explorer, xScale, growthTop, 241)}
      <line class="chart-grid-line" x1="${left}" x2="${width - right}"
        y1="${growthY(1).toFixed(2)}" y2="${growthY(1).toFixed(2)}"></line>
      <text class="chart-value-label" x="4" y="${(growthTop + 8).toFixed(2)}">${metric(growthMax)}×</text>
      <text class="chart-value-label" x="4" y="${(growthTop + growthHeight).toFixed(2)}">${metric(growthMin)}×</text>
      <path class="chart-line benchmark" d="${chartPath(points, (point) => point.benchmarkGrowth, xScale, growthY)}"></path>
      <path class="chart-line gross" d="${chartPath(points, (point) => point.grossGrowth, xScale, growthY)}"></path>
      <path class="chart-line net" d="${chartPath(points, (point) => point.netGrowth, xScale, growthY)}"></path>
      <line class="chart-grid-line" x1="${left}" x2="${width - right}"
        y1="${drawdownTop}" y2="${drawdownTop}"></line>
      <path class="drawdown-area" d="${drawdownArea}"></path>
      <text class="chart-value-label adverse" x="4" y="${drawdownTop + drawdownHeight}">${signedPercent(drawdownMin)}</text>
      ${chartDateLabels(explorer, xScale, 280)}
    </svg>
    <div class="chart-legend">
      <span><i class="net"></i>Net growth</span>
      <span><i class="gross"></i>Gross growth</span>
      <span><i class="benchmark"></i>Benchmark</span>
      <span><i class="drawdown"></i>Net drawdown</span>
      <span class="chart-role">validation = selection · test = visible audit</span>
    </div>`;
}

function renderExposureChart(explorer) {
  const points = explorer.path.points;
  const width = 760;
  const left = 42;
  const right = 12;
  const firstTime = chartTime(points[0].timestamp);
  const lastTime = chartTime(points.at(-1).timestamp);
  const timeSpread = Math.max(1, lastTime - firstTime);
  const xScale = (value) => {
    const ratio = Math.max(0, Math.min(1, (value - firstTime) / timeSpread));
    return left + ratio * (width - left - right);
  };
  const exposureValues = points.flatMap((point) => [
    point.grossExposure,
    point.netExposure,
  ]);
  const exposureMin = Math.min(-0.05, ...exposureValues);
  const exposureMax = Math.max(0.05, ...exposureValues);
  const exposureSpread = exposureMax - exposureMin;
  const exposureTop = 18;
  const exposureHeight = 164;
  const exposureY = (value) =>
    exposureTop + ((exposureMax - value) / exposureSpread) * exposureHeight;
  const turnoverTop = 207;
  const turnoverHeight = 52;
  const maximumTurnover = Math.max(
    1e-9,
    ...points.map((point) => point.oneWayTurnover),
  );
  const barWidth = Math.max(
    1,
    (width - left - right) / Math.max(points.length, 1) - 1,
  );
  const bars = points
    .map((point) => {
      const height = (point.oneWayTurnover / maximumTurnover) * turnoverHeight;
      return `<rect class="turnover-bar ${point.rebalanced ? "rebalanced" : ""}"
        x="${(xScale(chartTime(point.timestamp)) - barWidth / 2).toFixed(2)}"
        y="${(turnoverTop + turnoverHeight - height).toFixed(2)}"
        width="${barWidth.toFixed(2)}" height="${height.toFixed(2)}">
        <title>${escapeHtml(point.timestamp)} · turnover ${metric(point.oneWayTurnover)} · cost ${metric(point.cost)}</title>
      </rect>`;
    })
    .join("");
  return `
    <svg viewBox="0 0 ${width} 286" role="img"
      aria-label="Gross and net exposure with one-way turnover">
      ${splitBands(explorer, xScale, exposureTop, 241)}
      <line class="chart-grid-line" x1="${left}" x2="${width - right}"
        y1="${exposureY(0).toFixed(2)}" y2="${exposureY(0).toFixed(2)}"></line>
      <text class="chart-value-label" x="4" y="${exposureTop + 8}">${metric(exposureMax)}×</text>
      <text class="chart-value-label" x="4" y="${exposureTop + exposureHeight}">${metric(exposureMin)}×</text>
      <path class="chart-line exposure-gross" d="${chartPath(points, (point) => point.grossExposure, xScale, exposureY)}"></path>
      <path class="chart-line exposure-net" d="${chartPath(points, (point) => point.netExposure, xScale, exposureY)}"></path>
      <line class="chart-grid-line" x1="${left}" x2="${width - right}"
        y1="${turnoverTop + turnoverHeight}" y2="${turnoverTop + turnoverHeight}"></line>
      ${bars}
      <text class="chart-value-label" x="4" y="${turnoverTop + 9}">turn</text>
      ${chartDateLabels(explorer, xScale, 280)}
    </svg>
    <div class="chart-legend">
      <span><i class="exposure-gross"></i>Gross exposure</span>
      <span><i class="exposure-net"></i>Net exposure</span>
      <span><i class="turnover"></i>One-way turnover</span>
      <span class="chart-role">historical research weights · not live holdings</span>
    </div>`;
}

function renderPortfolioChart(explorer) {
  const performance = state.portfolioView === "performance";
  element("portfolio-chart-title").textContent = performance
    ? "Growth & drawdown"
    : "Exposure & implementation";
  element("portfolio-chart-note").textContent = performance
    ? `${explorer.path.totalRows} full rows → ${explorer.path.sampledRows} deterministic points`
    : "Executed book, one-way turnover, and rebalance days";
  element("portfolio-chart").innerHTML = performance
    ? renderPerformanceChart(explorer)
    : renderExposureChart(explorer);
  document.querySelectorAll("[data-portfolio-view]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.portfolioView === state.portfolioView),
    );
  });
}

function signalStateLabel(value) {
  if (value === 1) return "LONG";
  if (value === -1) return "SHORT";
  return "FLAT";
}

function mandateMarkup(mandate) {
  const tradable = mandate.tradableAssets.join(", ");
  const context = mandate.contextAssets.length
    ? `${mandate.contextAssets.length} context-only`
    : "no context-only assets";
  const lock = mandate.available
    ? `LOCKED · ${String(mandate.id).slice(-8)}`
    : "LEGACY · implicit";
  const risk = mandate.riskPolicy;
  const riskLabel = risk
    ? `${percent(risk.annualizedVolatilityCeiling)} · scale-down only`
    : "legacy · none";
  return `
    <span class="mandate-direction">${escapeHtml(mandate.direction.toUpperCase())}</span>
    <span><small>Construction</small><b>${escapeHtml(mandate.family)}</b></span>
    <span class="mandate-assets"><small>Authorized positions</small><b>${escapeHtml(tradable)}</b><i>${escapeHtml(context)}</i></span>
    <span><small>Gross / cap</small><b>${metric(mandate.grossLimit)} / ${percent(mandate.maxAbsWeight)}</b></span>
    <span><small>Risk ceiling</small><b>${escapeHtml(riskLabel)}</b></span>
    <span><small>Benchmark</small><b>${escapeHtml(mandate.benchmark)}</b></span>
    <code>${escapeHtml(lock)}</code>`;
}

function renderPortfolioBook(explorer) {
  const book = explorer.currentBook;
  const latestCapacity = explorer.liquidityCapacity?.latestTrade;
  const capacityDisclosure = latestCapacity
    ? latestCapacity.status === "available"
      ? ` · latest rebalance ${latestCapacity.timestamp}: 1% capacity ${capital(latestCapacity.capacity1Pct)} · binding ${latestCapacity.bindingAsset}`
      : ` · latest rebalance ${latestCapacity.timestamp}: capacity unavailable`
    : "";
  const maximumWeight = Number(
    explorer.signalPolicy?.parameters?.max_abs_weight ?? 0.3,
  );
  element("portfolio-book-note").textContent =
    `${book.timestamp} · gross ${metric(book.grossExposure)} · net ${metric(book.netExposure)} · cash ${percent(book.cashWeight)} · risk ${book.riskGovernorStatus} · scale ${metric(book.riskGovernorScale)}`;
  element("portfolio-book").innerHTML = `
    <div class="book-disclosure">Historical target/executed weights · covariance forecast ${percent(book.riskForecastPreAnnualized)} → ${percent(book.riskForecastPostAnnualized)} · ceiling ${percent(book.riskVolatilityCeilingAnnualized)}${escapeHtml(capacityDisclosure)} · no Broker or account state</div>
    <div class="position-table" role="table" aria-label="Latest mechanical research book">
      <div class="position-row heading" role="row">
        <span>Asset / state</span><span>Target</span><span>Executed</span><span>Action</span>
      </div>
      ${book.positions
        .map((position) => {
          const stateLabel = position.tradable
            ? signalStateLabel(position.signalState)
            : "CONTEXT";
          const side = !position.tradable
            ? "context"
            : position.executedWeight > 0
              ? "long"
              : position.executedWeight < 0
                ? "short"
                : "flat";
          const magnitude = Math.min(
            100,
            (Math.abs(position.executedWeight) / Math.max(maximumWeight, 1e-12)) * 100,
          );
          return `
            <div class="position-row ${position.tradable ? "" : "context-only"}" role="row">
              <span class="position-asset">
                <b>${escapeHtml(position.asset)}</b>
                <i class="${side}">${stateLabel}</i>
                <small>${escapeHtml(position.allocationStatus)} · ${escapeHtml(position.executionAction)}</small>
              </span>
              <span title="Pre-governor ${signedPercent(position.preGovernorTargetWeight)} → governed ${signedPercent(position.targetWeight)}">
                ${signedPercent(position.targetWeight)}
              </span>
              <span class="position-weight ${side}">
                <b>${signedPercent(position.executedWeight)}</b>
                <i style="--position-size:${magnitude.toFixed(2)}%"></i>
              </span>
              <span class="position-action" title="${escapeHtml(position.executionReason)}">
                ${escapeHtml(position.executionAction)}
              </span>
            </div>`;
        })
        .join("")}
    </div>`;
}

function renderPortfolioAttribution(explorer) {
  const split = state.attributionSplit;
  const rows = explorer.attribution[split];
  const maximum = Math.max(
    1e-12,
    ...rows.map((item) => Math.abs(item.annualizedNetContribution)),
  );
  element("portfolio-attribution").innerHTML = `
    <div class="attribution-disclosure">${split === "validation" ? "Selection split" : "Visible audit only"} · annualized net contribution and mean component-risk share</div>
    <div class="attribution-table">
      ${rows
        .map((item) => {
          const contribution = item.annualizedNetContribution;
          const width = Math.abs(contribution) / maximum * 50;
          const left = contribution >= 0 ? 50 : 50 - width;
          return `
            <div class="attribution-row">
              <b>${escapeHtml(item.asset)}</b>
              <span class="contribution-track">
                <i class="${contribution >= 0 ? "positive" : "negative"}"
                  style="left:${left.toFixed(2)}%;width:${width.toFixed(2)}%"></i>
              </span>
              <span class="${contribution < 0 ? "adverse" : ""}">${signedPercent(contribution)}</span>
              <small>risk ${signedPercent(item.meanVarianceContributionShare)}</small>
            </div>`;
        })
        .join("")}
    </div>`;
  document.querySelectorAll("[data-attribution-split]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.attributionSplit === split),
    );
  });
}

function renderPortfolioTransitions(explorer) {
  const transitions = explorer.recentTransitions.slice().reverse().slice(0, 10);
  element("portfolio-transitions").innerHTML =
    transitions
      .map(
        (item) => `
          <div class="transition-row">
            <time>${escapeHtml(item.timestamp)}</time>
            <b>${escapeHtml(item.asset)}</b>
            <span>${escapeHtml(item.signalEvent)}</span>
            <code>${signalStateLabel(item.priorSignalState)} → ${signalStateLabel(item.signalState)}</code>
            <small>${escapeHtml(item.executionAction)} · ${signedPercent(item.tradeWeight)} · ${escapeHtml(item.executionReason)}</small>
          </div>`,
      )
      .join("") ||
    '<div class="empty-panel">No mechanical transitions in the bounded evidence window.</div>';
}

function renderPortfolioExplorer(project) {
  const section = element("portfolio-explorer");
  const explorer = project.portfolioExplorer;
  if (!explorer) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  const summary = explorer.path.summary;
  const validationCapacity = explorer.liquidityCapacity?.validation;
  element("portfolio-meta").textContent =
    `${explorer.run.id} · ${explorer.selection.selectionSplit} selection · ${explorer.selection.testRole} test`;
  element("portfolio-mandate").innerHTML = mandateMarkup(explorer.mandate);
  element("portfolio-summary").innerHTML = [
    ["Net total return", signedPercent(summary.netTotalReturn), summary.netTotalReturn < 0 ? "bad" : ""],
    ["Maximum drawdown", signedPercent(summary.maximumDrawdown), "bad"],
    ["Total cost drag", percent(summary.totalCost), summary.totalCost > 0 ? "bad" : ""],
    ["One-way turnover", metric(summary.totalOneWayTurnover), "neutral"],
    ["Rebalance days", summary.rebalanceDays, "neutral"],
    [
      "Validation risk-limited",
      percent(explorer.signalPolicy.validation.riskLimitedRate),
      explorer.signalPolicy.validation.riskLimitedRate > 0 ? "warning" : "neutral",
    ],
    [
      "1% capacity · p10",
      validationCapacity?.capacity1Pct?.status === "available"
        ? capital(validationCapacity.capacity1Pct.tenthPercentileNav)
        : "UNAVAILABLE",
      validationCapacity?.capacity1Pct?.status === "available" ? "neutral" : "warning",
    ],
    [
      "Capacity coverage",
      validationCapacity ? percent(validationCapacity.tradeDateCoverage) : "LEGACY",
      validationCapacity?.tradeDateCoverage === 1 ? "neutral" : "warning",
    ],
  ]
    .map(
      ([label, value, tone]) => `
        <span class="${tone}">
          <small>${escapeHtml(label)}</small>
          <b>${escapeHtml(value)}</b>
        </span>`,
    )
    .join("");
  renderPortfolioChart(explorer);
  renderPortfolioBook(explorer);
  renderPortfolioAttribution(explorer);
  renderPortfolioTransitions(explorer);
}

function rlBaselineLabel(value) {
  return String(value ?? "")
    .replace("fixed:", "")
    .replace("best-training-expert", "training expert")
    .replace("contextual-ridge", "contextual ridge")
    .replaceAll("_", " ");
}

function rlTrialLabel(trial) {
  return `${trial.fold.replace("fold-", "F")} · s${trial.seed}`;
}

function rlSplitEvidence(trial) {
  return state.rlSplit === "test" ? trial.test : trial.validation;
}

function rlAdvantage(trial) {
  return state.rlSplit === "test"
    ? trial.testAdvantage
    : trial.validationAdvantage;
}

function renderRlPerformance(explorer) {
  const trials = explorer.trials;
  const split = state.rlSplit;
  const selected = explorer.baselines.filter((row) => row.selectedOnValidation);
  const values = [
    ...trials.map((trial) => rlSplitEvidence(trial).netSharpe),
    ...selected.map((row) => row[split].netSharpe),
  ];
  const width = 760;
  const left = 48;
  const right = 16;
  const top = 22;
  const height = 210;
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const padding = Math.max(0.5, (maximum - minimum) * 0.08);
  const low = minimum - padding;
  const high = maximum + padding;
  const spread = Math.max(1e-9, high - low);
  const y = (value) => top + ((high - value) / spread) * height;
  const step = (width - left - right) / Math.max(1, trials.length);
  const x = (index) => left + step * (index + 0.5);
  const baselineLines = explorer.protocol.folds
    .map((fold) => {
      const foldIndices = trials
        .map((trial, index) => [trial, index])
        .filter(([trial]) => trial.fold === fold)
        .map(([, index]) => index);
      const baseline = selected.find((row) => row.fold === fold);
      if (!baseline || !foldIndices.length) return "";
      const value = baseline[split].netSharpe;
      return `
        <line class="rl-baseline-line"
          x1="${(x(foldIndices[0]) - step * 0.38).toFixed(2)}"
          x2="${(x(foldIndices.at(-1)) + step * 0.38).toFixed(2)}"
          y1="${y(value).toFixed(2)}" y2="${y(value).toFixed(2)}">
          <title>${escapeHtml(fold)} · ${escapeHtml(rlBaselineLabel(baseline.name))} · ${metric(value)}</title>
        </line>`;
    })
    .join("");
  const points = trials
    .map((trial, index) => {
      const value = rlSplitEvidence(trial).netSharpe;
      const advantage = rlAdvantage(trial);
      return `
        <g class="rl-trial-point ${advantage >= 0 ? "positive" : "negative"}">
          <circle cx="${x(index).toFixed(2)}" cy="${y(value).toFixed(2)}" r="5">
            <title>${escapeHtml(rlTrialLabel(trial))} · Sharpe ${metric(value)} · advantage ${metric(advantage)}</title>
          </circle>
          <text x="${x(index).toFixed(2)}" y="${(y(value) - 10).toFixed(2)}"
            text-anchor="middle">${metric(value)}</text>
          <text class="rl-axis-label" x="${x(index).toFixed(2)}" y="258"
            text-anchor="middle">${escapeHtml(rlTrialLabel(trial))}</text>
        </g>`;
    })
    .join("");
  const zero = low <= 0 && high >= 0
    ? `<line class="rl-zero-line" x1="${left}" x2="${width - right}" y1="${y(0)}" y2="${y(0)}"></line>`
    : "";
  return `
    <svg viewBox="0 0 ${width} 270" role="img"
      aria-label="Every RL fold and seed compared with the validation-selected baseline">
      ${zero}
      <text class="rl-axis-label" x="5" y="${top + 5}">${metric(high)}</text>
      <text class="rl-axis-label" x="5" y="${top + height}">${metric(low)}</text>
      ${baselineLines}
      ${points}
    </svg>
    <div class="rl-legend">
      <span><i class="rl-positive"></i>RL beats selected baseline</span>
      <span><i class="rl-negative"></i>RL trails selected baseline</span>
      <span><i class="rl-baseline"></i>Validation-selected baseline</span>
      <b>${split === "validation" ? "SELECTION" : "TEST · VISIBLE AUDIT ONLY"}</b>
    </div>`;
}

function renderRlTraining(explorer) {
  const rows = explorer.training;
  const trials = explorer.trials;
  const values = rows.map((row) => row.totalReward);
  const width = 760;
  const left = 48;
  const right = 16;
  const top = 22;
  const height = 210;
  const low = Math.min(...values);
  const high = Math.max(...values);
  const spread = Math.max(1e-9, high - low);
  const x = (episode) =>
    left + ((episode - 1) / Math.max(1, explorer.protocol.episodes - 1)) *
      (width - left - right);
  const y = (value) => top + ((high - value) / spread) * height;
  const colors = ["c0", "c1", "c2", "c3", "c4", "c5"];
  const lines = trials
    .map((trial, index) => {
      const history = rows.filter(
        (row) => row.fold === trial.fold && row.seed === trial.seed,
      );
      const path = history
        .map(
          (row, pointIndex) =>
            `${pointIndex ? "L" : "M"}${x(row.episode).toFixed(2)},${y(row.totalReward).toFixed(2)}`,
        )
        .join(" ");
      const final = history.at(-1);
      return `
        <path class="rl-training-line ${colors[index % colors.length]}" d="${path}">
          <title>${escapeHtml(rlTrialLabel(trial))} · final reward ${metric(final?.totalReward)}</title>
        </path>
        <text class="rl-training-label ${colors[index % colors.length]}"
          x="${(x(final.episode) - 4).toFixed(2)}"
          y="${(y(final.totalReward) - 4 + index * 2).toFixed(2)}"
          text-anchor="end">${escapeHtml(rlTrialLabel(trial))}</text>`;
    })
    .join("");
  const episodeLabels = Array.from(
    { length: explorer.protocol.episodes },
    (_, index) => index + 1,
  )
    .map(
      (episode) => `
        <text class="rl-axis-label" x="${x(episode).toFixed(2)}" y="258"
          text-anchor="middle">E${episode}</text>`,
    )
    .join("");
  return `
    <svg viewBox="0 0 ${width} 270" role="img"
      aria-label="Training total reward for every fold and seed">
      <line class="rl-zero-line" x1="${left}" x2="${width - right}"
        y1="${y(Math.max(low, Math.min(high, 0))).toFixed(2)}"
        y2="${y(Math.max(low, Math.min(high, 0))).toFixed(2)}"></line>
      <text class="rl-axis-label" x="5" y="${top + 5}">${metric(high)}</text>
      <text class="rl-axis-label" x="5" y="${top + height}">${metric(low)}</text>
      ${lines}
      ${episodeLabels}
    </svg>
    <div class="rl-legend">
      <span>Exact fixed-budget training history · all ${trials.length} trials</span>
      <b>DESCRIPTIVE · NOT A PROMOTION METRIC</b>
    </div>`;
}

function renderRlActions(explorer) {
  const rows = explorer.actionSummaries.filter(
    (row) => row.split === state.rlSplit,
  );
  const actions = explorer.protocol.actions;
  const width = 760;
  const left = 48;
  const right = 16;
  const top = 22;
  const height = 210;
  const step = (width - left - right) / Math.max(1, rows.length);
  const barWidth = step * 0.58;
  const bars = rows
    .map((row, index) => {
      let cumulative = 0;
      const segments = actions
        .map((action) => {
          const value = row.actionFrequency[action];
          const y = top + height * (1 - cumulative - value);
          cumulative += value;
          return `
            <rect class="rl-action-${escapeHtml(action)}"
              x="${(left + index * step + (step - barWidth) / 2).toFixed(2)}"
              y="${y.toFixed(2)}" width="${barWidth.toFixed(2)}"
              height="${(height * value).toFixed(2)}">
              <title>${escapeHtml(action)} · ${percent(value)}</title>
            </rect>`;
        })
        .join("");
      return `${segments}
        <text class="rl-axis-label" x="${(left + step * (index + 0.5)).toFixed(2)}"
          y="258" text-anchor="middle">${escapeHtml(row.fold.replace("fold-", "F"))} · s${row.seed}</text>`;
    })
    .join("");
  return `
    <svg viewBox="0 0 ${width} 270" role="img"
      aria-label="Fixed factor-mixture action allocation for every fold and seed">
      <text class="rl-axis-label" x="5" y="${top + 5}">100%</text>
      <text class="rl-axis-label" x="20" y="${top + height}">0</text>
      ${bars}
    </svg>
    <div class="rl-legend">
      ${actions
        .map(
          (action) =>
            `<span><i class="rl-action-${escapeHtml(action)}"></i>${escapeHtml(action)}</span>`,
        )
        .join("")}
      <b>${state.rlSplit === "validation" ? "SELECTION" : "TEST · VISIBLE AUDIT ONLY"}</b>
    </div>`;
}

function renderRlChart(explorer) {
  const title = {
    performance: "RL versus selected baseline",
    training: "Fixed-budget training behavior",
    actions: "Fixed factor-sleeve allocation",
  }[state.rlView];
  const note = {
    performance: "Every declared fold and seed · baseline chosen by fixed Judge",
    training: "Every episode · no lucky-seed selection",
    actions: "Allocation, transitions, turnover, and cost",
  }[state.rlView];
  element("rl-chart-title").textContent = title;
  element("rl-chart-note").textContent = note;
  element("rl-chart").innerHTML =
    state.rlView === "training"
      ? renderRlTraining(explorer)
      : state.rlView === "actions"
        ? renderRlActions(explorer)
        : renderRlPerformance(explorer);
  document.querySelectorAll("[data-rl-view]").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.rlView === state.rlView));
  });
  document.querySelectorAll("[data-rl-split]").forEach((button) => {
    button.setAttribute("aria-selected", String(button.dataset.rlSplit === state.rlSplit));
  });
}

function renderRlTrials(explorer) {
  const split = state.rlSplit;
  element("rl-trials").innerHTML = `
    <div class="rl-trial-table" role="table" aria-label="RL fold and seed audit">
      <div class="rl-trial-row heading" role="row">
        <span>Trial</span><span>Sharpe</span><span>vs baseline</span>
      </div>
      ${explorer.trials
        .map((trial) => {
          const evidence = trial[split];
          const advantage = split === "validation"
            ? trial.validationAdvantage
            : trial.testAdvantage;
          return `
            <div class="rl-trial-row ${advantage >= 0 ? "positive" : "negative"}" role="row">
              <span>
                <b>${escapeHtml(rlTrialLabel(trial))}</b>
                <small>${escapeHtml(rlBaselineLabel(trial.selectedBaseline))}</small>
              </span>
              <strong>${metric(evidence.netSharpe)}</strong>
              <i>${advantage > 0 ? "+" : ""}${metric(advantage)}</i>
            </div>`;
        })
        .join("")}
    </div>`;
}

function renderRlBaselines(explorer) {
  const split = state.rlSplit;
  const byName = new Map();
  for (const row of explorer.baselines) {
    const values = byName.get(row.name) ?? [];
    values.push(row[split].netSharpe);
    byName.set(row.name, values);
  }
  const rows = [...byName.entries()]
    .map(([name, values]) => ({
      name,
      mean: values.reduce((sum, value) => sum + value, 0) / values.length,
      selected: explorer.baselines.some(
        (row) => row.name === name && row.selectedOnValidation,
      ),
    }))
    .sort((left, right) => right.mean - left.mean);
  const maximum = Math.max(...rows.map((row) => row.mean));
  const minimum = Math.min(0, ...rows.map((row) => row.mean));
  const spread = Math.max(1e-9, maximum - minimum);
  element("rl-baselines").innerHTML = `
    <div class="rl-baseline-list">
      ${rows
        .map(
          (row) => `
            <div class="rl-baseline-row ${row.selected ? "selected" : ""}">
              <span>
                <b>${escapeHtml(rlBaselineLabel(row.name))}</b>
                <small>${row.selected ? "selected in ≥1 fold" : "declared comparator"}</small>
              </span>
              <i><u style="width:${Math.max(0, (row.mean - minimum) / spread * 100).toFixed(2)}%"></u></i>
              <strong>${metric(row.mean)}</strong>
            </div>`,
        )
        .join("")}
    </div>`;
}

function renderRlDetail(explorer) {
  const rows = explorer.actionSummaries.filter(
    (row) => row.split === state.rlSplit,
  );
  const actions = explorer.protocol.actions;
  const meanFrequency = Object.fromEntries(
    actions.map((action) => [
      action,
      rows.reduce((sum, row) => sum + row.actionFrequency[action], 0) /
        Math.max(1, rows.length),
    ]),
  );
  const transitions = rows.reduce((sum, row) => sum + row.actionTransitions, 0);
  const turnover = rows.reduce((sum, row) => sum + row.meanOneWayTurnover, 0) /
    Math.max(1, rows.length);
  const cost = rows.reduce((sum, row) => sum + row.totalCostDrag, 0) /
    Math.max(1, rows.length);
  element("rl-detail").innerHTML = `
    <div class="rl-action-mix">
      ${actions
        .map(
          (action) => `
            <div>
              <span><i class="rl-action-${escapeHtml(action)}"></i>${escapeHtml(action)}</span>
              <b>${percent(meanFrequency[action])}</b>
            </div>`,
        )
        .join("")}
    </div>
    <div class="rl-implementation-grid">
      <span><small>Mean one-way turnover</small><b>${metric(turnover)}</b></span>
      <span><small>Mean total cost drag</small><b>${percent(cost)}</b></span>
      <span><small>Action transitions</small><b>${metric(transitions)}</b></span>
      <span><small>Cost assumption</small><b>${metric(explorer.protocol.configuration.costBps)} bps</b></span>
    </div>
    <p class="book-disclosure">Actions select the content-locked candidate factor, fixed reference factors, or their governed blend. They are historical research evidence, not orders or account positions.</p>`;
}

function renderRlExplorer(project) {
  const section = element("rl-explorer");
  const explorer = project.rlExplorer;
  if (!explorer) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  const summary = explorer.summary;
  const fusion = explorer.factorFusion;
  const advantage = summary.meanValidationAdvantageVsBestBaseline;
  const candidateAdvantage = fusion.meanValidationAdvantageVsCandidateFactor;
  element("rl-meta").textContent =
    `${explorer.run.id} · ${summary.trialCount} fold/seed trials · validation selection`;
  element("rl-mandate").innerHTML = mandateMarkup(explorer.portfolioMandate);
  const fusionCards = fusion.available
    ? [
        ["vs candidate factor", `${candidateAdvantage > 0 ? "+" : ""}${metric(candidateAdvantage)}`, "content-locked baseline", candidateAdvantage >= 0 ? "positive" : "negative"],
        ["Candidate usage", percent(fusion.meanValidationCandidateActionFrequency), "validation action frequency", ""],
      ]
    : [
        ["Factor fusion", "Legacy", "reference sleeves only", "audit"],
      ];
  element("rl-summary").innerHTML = [
    ["RL value-add", `${advantage > 0 ? "+" : ""}${metric(advantage)}`, "vs best validation baseline", advantage >= 0 ? "positive" : "negative"],
    ...fusionCards,
    ["Validation Sharpe", metric(summary.validation.mean), `minimum ${metric(summary.validation.minimum)}`, ""],
    ["Seed / fold dispersion", metric(summary.validation.standardDeviation), `${summary.validation.observations} trials`, ""],
    ["Failure rate", percent(summary.failureRate), "all declared trials", summary.failureRate ? "negative" : ""],
    ["Mean turnover", metric(summary.meanValidationOneWayTurnover), "one-way · validation", ""],
    ["Mean cost drag", percent(summary.meanValidationCostDrag), "validation", ""],
    ["Test Sharpe", metric(summary.testAudit.mean), "VISIBLE AUDIT ONLY", "audit"],
  ]
    .map(
      ([label, value, note, tone]) => `
        <span class="${tone}">
          <small>${escapeHtml(label)}</small>
          <b>${escapeHtml(value)}</b>
          <i>${escapeHtml(note)}</i>
        </span>`,
    )
    .join("");
  renderRlChart(explorer);
  renderRlTrials(explorer);
  renderRlBaselines(explorer);
  renderRlDetail(explorer);
  const command = project.commands?.find((item) => item.id === "run.rl");
  element("rl-warning").innerHTML = `
    <span>${escapeHtml(explorer.warning)}</span>
    ${copyCommandButton(command, "Copy RL JSON command")}`;
}

function matrixValue(value, unit) {
  if (unit === "percent") return percent(value);
  if (unit === "count") {
    return value === null || value === undefined ? "—" : metric(Math.round(Number(value)));
  }
  return metric(value);
}

function matrixRelationLabel(relation) {
  return {
    better: "BETTER",
    worse: "WORSE",
    same: "SAME",
    context: "CONTEXT",
    unavailable: "N/A",
    "audit-better": "AUDIT ↑",
    "audit-worse": "AUDIT ↓",
    "audit-same": "AUDIT =",
    "display-better": "DISPLAY ↑",
    "display-worse": "DISPLAY ↓",
    "display-same": "DISPLAY =",
  }[relation] ?? "";
}

function renderDecisionMatrix(project) {
  const section = element("decision-matrix");
  const session = selectedSession(project);
  const matrix = session?.decisionMatrix;
  if (!matrix) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  const descriptors = matrix.metrics.filter(
    (item) => state.matrixView === "all" || item.split !== "test",
  );
  const descriptorByKey = Object.fromEntries(
    matrix.metrics.map((item) => [item.key, item]),
  );
  const leader = matrix.trials.find((trial) => trial.isCurrentLeader);
  const leaderTradeoffs = matrix.tradeoffs.leaderVsBaseline;
  const comparableCount = matrix.tradeoffs.selectionEligibleMetricKeys.length;
  element("decision-matrix-meta").textContent =
    `${matrix.metricFamily} · ${matrix.scope.displayedCandidateTrials}/${matrix.scope.totalCandidateTrials} candidates · ${matrix.selectionIntegrity.selectionSplit} selection`;
  element("decision-summary").innerHTML = [
    [
      "Leader objective",
      matrixValue(leader?.primaryValue, "number"),
      matrix.objective.metric,
      "leader",
    ],
    [
      "Better vs baseline",
      `${leaderTradeoffs.improved.length}/${comparableCount}`,
      "validation-eligible fields",
      "better",
    ],
    [
      "Worse vs baseline",
      `${leaderTradeoffs.regressed.length}/${comparableCount}`,
      "trade-offs to inspect",
      leaderTradeoffs.regressed.length ? "worse" : "",
    ],
    [
      "Non-dominated",
      matrix.tradeoffs.nonDominatedRunIds.length,
      "displayed successful Runs",
      "neutral",
    ],
  ]
    .map(
      ([label, value, note, tone]) => `
        <span class="${tone}">
          <small>${escapeHtml(label)}</small>
          <b>${escapeHtml(value)}</b>
          <i>${escapeHtml(note)}</i>
        </span>`,
    )
    .join("");

  const trialHeaders = matrix.trials
    .map((trial) => {
      const identity =
        trial.role === "baseline"
          ? "B0"
          : `E${String(trial.sequence).padStart(2, "0")}`;
      return `
        <th class="matrix-trial-head ${normalizedStatus(trial.verdict)} ${trial.isCurrentLeader ? "leader" : ""}"
          scope="col" title="${escapeHtml(trial.hypothesis)}">
          <small>${identity}${trial.isCurrentLeader ? " · LEADER" : ""}</small>
          <b>${escapeHtml(trial.verdict)}</b>
          <code>${escapeHtml(shortHash(trial.runId))}</code>
        </th>`;
    })
    .join("");
  let previousGroup = null;
  const rows = [];
  for (const descriptor of descriptors) {
    if (descriptor.group !== previousGroup) {
      rows.push(`
        <tr class="matrix-group-row">
          <th colspan="${matrix.trials.length + 1}">${escapeHtml(descriptor.group)} · ${escapeHtml(descriptor.split)}</th>
        </tr>`);
      previousGroup = descriptor.group;
    }
    const cells = matrix.trials
      .map((trial) => {
        const value = trial.metrics[descriptor.key];
        const relation = trial.vsBaseline[descriptor.key];
        const failed = trial.status !== "succeeded";
        return `
          <td class="matrix-value ${failed ? "failed" : normalizedStatus(relation)} ${trial.isCurrentLeader ? "leader" : ""}">
            <b>${failed ? "CRASH" : escapeHtml(matrixValue(value, descriptor.unit))}</b>
            <small>${trial.role === "baseline" ? "REFERENCE" : escapeHtml(matrixRelationLabel(relation))}</small>
          </td>`;
      })
      .join("");
    rows.push(`
      <tr class="${descriptor.primary ? "primary" : ""} ${descriptor.split === "test" ? "audit" : ""}">
        <th class="matrix-metric" scope="row">
          <b>${escapeHtml(descriptor.label)}</b>
          <small>${descriptor.primary ? "PRIMARY · " : ""}${escapeHtml(descriptor.preference)}${descriptor.selectionEligible ? " · COMPARED" : " · DISPLAY ONLY"}</small>
        </th>
        ${cells}
      </tr>`);
  }
  element("decision-matrix-table").innerHTML = `
    <table class="decision-table" aria-label="Verified Session metric comparison">
      <thead>
        <tr>
          <th class="matrix-corner" scope="col">
            <small>METRIC DICTIONARY</small>
            <b>${descriptors.length} evidence rows</b>
          </th>
          ${trialHeaders}
        </tr>
      </thead>
      <tbody>${rows.join("")}</tbody>
    </table>`;
  const labels = (keys) =>
    keys
      .map((key) => descriptorByKey[key]?.label ?? key)
      .join(", ") || "none";
  element("decision-matrix-note").textContent =
    state.matrixView === "all"
      ? "Test evidence is visible audit only and remains excluded from every comparison claim."
      : "Validation and fixed full-scope evidence; test audit is hidden.";
  element("decision-tradeoff-note").innerHTML =
    `<b>Leader gains:</b> ${escapeHtml(labels(leaderTradeoffs.improved))} ` +
    `<span>·</span> <b>Watch:</b> ${escapeHtml(labels(leaderTradeoffs.regressed))} ` +
    `<span>·</span> ${escapeHtml(matrix.tradeoffs.warning)}`;
  document.querySelectorAll("[data-matrix-view]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.matrixView === state.matrixView),
    );
  });
}

function renderTrajectory(project) {
  const session = selectedSession(project);
  const experiments = session?.experiments ?? [];
  const familyTrials =
    session?.selectionIntegrity.researchFamily?.uniqueSourceTrials ??
    session?.selectionIntegrity.candidateTrials ??
    0;
  element("trajectory-meta").textContent = session
    ? `${session.session.studyId} · ${familyTrials} Project-family trials · ${selectionContext(session.selectionIntegrity)} · ${session.selectionIntegrity.selectionSplit} selection · ${session.selectionIntegrity.externalHoldoutRequired ? "new holdout required" : session.selectionIntegrity.testRole}`
    : "No Experiments";
  if (!experiments.length) {
    element("trajectory-chart").innerHTML =
      '<div class="empty-panel">Candidate verdicts will appear here.</div>';
    return;
  }
  const numeric = experiments
    .map((item) => item.candidateValue)
    .filter((value) => value !== null && Number.isFinite(Number(value)))
    .map(Number);
  const low = Math.min(...numeric, Number(session.session.baseline.value));
  const high = Math.max(...numeric, Number(session.session.leader.value));
  const spread = Math.max(0.000001, high - low);
  element("trajectory-chart").innerHTML = experiments
    .map((experiment, index) => {
      const value = experiment.candidateValue;
      const height =
        experiment.verdict === "CRASH" || value === null
          ? 7
          : 24 + ((Number(value) - low) / spread) * 130;
      const level = Math.max(1, Math.min(20, Math.ceil(height / 8)));
      const title = `${experiment.verdict}: ${experiment.hypothesis} — ${metric(value)}`;
      return `
        <button class="trace-column ${normalizedStatus(experiment.verdict)}" type="button"
          data-experiment="${escapeHtml(experiment.id)}" title="${escapeHtml(title)}"
          aria-label="${escapeHtml(title)}">
          <i class="trace-level-${level}"></i>
          <span>${index + 1}</span>
        </button>`;
    })
    .join("");
  document.querySelectorAll("[data-experiment]").forEach((button) => {
    button.addEventListener("click", () => {
      const experiment = experiments.find((item) => item.id === button.dataset.experiment);
      if (experiment) renderExperimentInspector(session, experiment);
    });
  });
}

function eventSubtitle(event) {
  const labels = {
    run: "Immutable Run",
    session: "Session pointer",
    experiment: "Experiment verdict",
    campaign: "Terminal Campaign",
    report: "Immutable Research Report",
    dossier: "Immutable Project Research Dossier",
    progress: "Mutable Campaign progress",
  };
  return `${labels[event.kind] ?? event.kind} · ${event.status}`;
}

function renderTimeline(project) {
  element("evidence-stream").innerHTML =
    project.timeline
      .slice(0, 14)
      .map(
        (event) => `
          <li class="evidence-item ${normalizedStatus(event.status)} ${event.mutable ? "mutable" : ""}">
            <i aria-hidden="true"></i>
            <span class="evidence-copy">
              <b>${escapeHtml(event.title)}</b>
              <small>${escapeHtml(eventSubtitle(event))}</small>
            </span>
            <time datetime="${escapeHtml(event.at)}">${escapeHtml(relativeTime(event.at))}</time>
          </li>`,
      )
      .join("") || '<li class="empty-panel">No verified evidence yet.</li>';
}

function runMetricLayers(item) {
  const layers = item.metricLayers;
  if (!layers) return "";
  if (layers.kind === "portfolio") {
    const signal = layers.signalPolicy;
    const attribution = layers.attribution;
    return `
      <div class="catalog-evidence" aria-label="Portfolio evidence">
        <span><b>${metric(layers.factor.validationRankIc)}</b><i>validation IC</i></span>
        <span><b>${metric(layers.portfolio.validationNetSharpe)}</b><i>validation</i></span>
        ${signal ? `<span><b>${metric(signal.validationStateChangeRate)}</b><i>state change</i></span>` : ""}
        ${signal ? `<span><b>${metric(signal.validationTransitionReductionRate)}</b><i>hysteresis saved</i></span>` : ""}
        ${attribution ? `<span><b>${metric(attribution.validationMaximumAbsoluteNetContributionShare)}</b><i>max asset contrib.</i></span>` : ""}
        ${attribution ? `<span><b>${metric(attribution.validationMaximumAbsoluteRiskContributionShare)}</b><i>max risk contrib.</i></span>` : ""}
        ${attribution ? `<span><b>${attribution.validationReconciliationPassed ? "pass" : "fail"}</b><i>attribution</i></span>` : ""}
        <span><b>${metric(layers.portfolio.testNetSharpe)}</b><i>test audit</i></span>
        <span><b>${metric(layers.implementation.testAnnualizedTurnover)}</b><i>ann. turn</i></span>
        <span><b>${metric(layers.robustness.test25bpsSharpe)}</b><i>25bps</i></span>
      </div>`;
  }
  if (layers.kind === "rl-policy") {
    return `
      <div class="catalog-evidence" aria-label="RL policy evidence">
        <span><b>${metric(layers.validationMeanNetSharpe)}</b><i>validation</i></span>
        <span><b>${metric(layers.testMeanNetSharpe)}</b><i>test audit</i></span>
        <span><b>${metric(layers.validationSeedFoldStd)}</b><i>seed/fold σ</i></span>
        <span><b>${metric(layers.validationBaselineAdvantage)}</b><i>vs baseline</i></span>
        <span><b>${metric(layers.failureRate)}</b><i>fail rate</i></span>
        <span><b>${layers.folds}×${layers.seeds}</b><i>folds × seeds</i></span>
      </div>`;
  }
  if (layers.kind === "factor") {
    return `
      <div class="catalog-evidence" aria-label="Factor evidence">
        <span><b>${metric(layers.validationMeanIc)}</b><i>validation 1b IC</i></span>
        <span><b>${metric(layers.validationPearsonIc)}</b><i>Pearson IC</i></span>
        <span><b>${metric(layers.validationHacTStatistic)}</b><i>HAC t-stat</i></span>
        <span><b>${metric(layers.validationHorizon5MeanIc)}</b><i>validation 5b IC</i></span>
        <span><b>${metric(layers.validationQuantileSpread)}</b><i>tertile spread</i></span>
        <span><b>${metric(layers.validationWorstFoldMeanIc)}</b><i>worst fold IC</i></span>
        <span><b>${metric(layers.validationMaximumAbsoluteStyleCorrelation)}</b><i>max style |ρ|</i></span>
        <span><b>${metric(layers.testMeanIc)}</b><i>test audit IC</i></span>
        <span><b>${metric(layers.meanRankTurnover)}</b><i>rank turn</i></span>
      </div>`;
  }
  return "";
}

function renderCatalog(project) {
  const items = project[state.catalog];
  document.querySelectorAll("[data-catalog]").forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.catalog === state.catalog),
    );
  });
  if (!items.length) {
    element("catalog").innerHTML = `<div class="empty-panel">No ${escapeHtml(state.catalog)} yet.</div>`;
    return;
  }
  element("catalog").innerHTML = `
    <div class="catalog-grid">
      ${items
        .slice()
        .reverse()
        .slice(0, 12)
        .map((item) =>
          state.catalog === "studies"
            ? `
              <article class="catalog-card">
                <small>${escapeHtml(item.subjectKind)} · ${escapeHtml(item.direction)}</small>
                <strong>${escapeHtml(item.name)}</strong>
                <p>${escapeHtml(item.description || "No description recorded.")}</p>
                <code>${escapeHtml(item.primaryMetric)} · ${escapeHtml(item.id)}</code>
              </article>`
            : `
              <article class="catalog-card">
                <small>${escapeHtml(item.status)} · ${escapeHtml(item.subject.kind)}</small>
                <strong>${escapeHtml(item.studyId)}</strong>
                <p>${escapeHtml(item.primaryMetric)} = ${metric(item.primaryValue)}</p>
                ${runMetricLayers(item)}
                <code>${escapeHtml(relativeTime(item.startedAt))} · ${item.durationMs}ms</code>
              </article>`,
        )
        .join("")}
    </div>`;
}

function campaignRows(session) {
  const running = session.progress.map(
    (progress) => `
      <div class="campaign-row">
        <span>
          <strong>${escapeHtml(progress.message)}</strong>
          <small>turn ${progress.turn}/${progress.budget.maxTurns} · mutable</small>
        </span>
        <span class="status-chip running">${escapeHtml(progress.phase)}</span>
      </div>`,
  );
  const terminal = session.campaigns
    .slice()
    .reverse()
    .slice(0, 5)
    .map(
      (campaign) => `
        <div class="campaign-row">
          <span>
            <strong>${escapeHtml(campaign.reason)}</strong>
            <small>${campaign.experiments} experiments · ${escapeHtml(relativeTime(campaign.completedAt))}</small>
          </span>
          <span class="status-chip ${normalizedStatus(campaign.status)}">${escapeHtml(campaign.status)}</span>
        </div>`,
    );
  return [...running, ...terminal].join("") || '<p class="empty-copy">No Campaigns recorded.</p>';
}

function renderInspector(project) {
  const session = selectedSession(project);
  if (!session) {
    element("inspector-kind").textContent = "PROJECT";
    const intake = project.intake;
    const baseline = projectFocusRun(project);
    if (intake) {
      const request = intake.request;
      const dataset = intake.dataset;
      const program = project.researchProgramStatus;
      const lane = projectFocusLane(project);
      const portfolio =
        baseline?.metricLayers?.kind === "portfolio"
          ? baseline.metricLayers
          : null;
      const next =
        program?.recommendedAction ??
        intake.commands.find((item) => item.id === "session.start");
      element("inspector-content").innerHTML = `
        <section class="inspector-section">
          <small>Research mandate</small>
          <h3>${escapeHtml(request.title)}</h3>
          <p>${escapeHtml(request.question)}</p>
          <dl class="inspector-kv">
            <dt>Requested</dt><dd>${escapeHtml(request.assets.map((item) => item.symbol).join(", "))}</dd>
            <dt>Research universe</dt><dd>${escapeHtml(dataset.universe.join(", "))}</dd>
            <dt>Direction</dt><dd>${escapeHtml(request.direction)}</dd>
            <dt>Horizon</dt><dd>${escapeHtml(request.horizon)}</dd>
          </dl>
        </section>
        <section class="inspector-section">
          <small>Dataset authority</small>
          <h3>${escapeHtml(dataset.id)}@${escapeHtml(dataset.version)}</h3>
          <p>Provider, calendar, venue, and adjustment values are caller-supplied claims. Canonical Project-local bytes are content locked.</p>
          <dl class="inspector-kv">
            <dt>Provider claim</dt><dd>${escapeHtml(dataset.provider.name)}</dd>
            <dt>Adjustment</dt><dd>${escapeHtml(dataset.priceAdjustment)}</dd>
            <dt>Calendar</dt><dd>${escapeHtml(dataset.market.calendar)} · ${escapeHtml(dataset.frequency)}</dd>
            <dt>Coverage</dt><dd>${escapeHtml(dataset.timeRange.start)} → ${escapeHtml(dataset.timeRange.end)}</dd>
            <dt>Dataset hash</dt><dd title="${escapeHtml(intake.manifest.datasetHash)}">${escapeHtml(shortHash(intake.manifest.datasetHash))}</dd>
          </dl>
        </section>
        <section class="inspector-section">
          <small>${lane ? "Recommended lane evidence" : "Immutable baseline"}</small>
          <h3>${escapeHtml(lane?.name ?? baseline?.studyId ?? intake.study.name)}</h3>
          ${baseline ? `<span class="status-chip ${valueTone(baseline.primaryValue) === "bad" ? "revert" : "published"}">${escapeHtml(baseline.status)}</span>` : '<span class="status-chip active">pending</span>'}
          <dl class="inspector-kv">
            <dt>${escapeHtml(baseline?.primaryMetric ?? "Primary metric")}</dt><dd>${metric(baseline?.primaryValue)}</dd>
            ${portfolio ? `<dt>Validation rank IC</dt><dd>${metric(portfolio.factor.validationRankIc)}</dd>
            <dt>Test max drawdown</dt><dd>${percent(portfolio.portfolio.testMaximumDrawdown)}</dd>
            <dt>Annual turnover</dt><dd>${percent(portfolio.implementation.testAnnualizedTurnover)}</dd>
            <dt>Cost drag</dt><dd>${percent(portfolio.implementation.testCostDrag)}</dd>` : ""}
            <dt>Selection</dt><dd>validation only</dd>
          </dl>
          ${copyCommandButton(next, program ? "Copy recommended command" : "Copy start command")}
        </section>
        ${dossierInspectorSection(project)}
        <details class="program-details">
          <summary>Research program</summary>
          <pre class="program-copy">${escapeHtml(project.researchProgram.text)}</pre>
        </details>`;
      return;
    }
    const program = project.researchProgramStatus;
    if (program) {
      const assessment = programAssessment(project);
      const laneRows = program.lanes
        .map((lane) => {
          const readout = laneReadout(project, lane);
          return `
            <button class="inspector-lane" type="button" data-open-evidence="${escapeHtml(readout.kind)}">
              <span>
                <small>${escapeHtml(lane.name)}</small>
                <strong>${escapeHtml(readout.verdict)}</strong>
              </span>
              <b class="${escapeHtml(readout.tone)}">${escapeHtml(readout.display)}</b>
            </button>`;
        })
        .join("");
      element("inspector-content").innerHTML = `
        <section class="inspector-section program-verdict">
          <small>Current evidence readout</small>
          <h3>${escapeHtml(assessment.title)}</h3>
          <span class="status-chip ${assessment.tone === "bad" ? "adverse" : "active"}">${escapeHtml(assessment.label)}</span>
          <p>${escapeHtml(assessment.detail)}</p>
        </section>
        <section class="inspector-section">
          <small>Evidence chain</small>
          <div class="inspector-lanes">${laneRows}</div>
        </section>
        <section class="inspector-section">
          <small>Research scope</small>
          <h3>${escapeHtml(program.dataset.id)}@${escapeHtml(program.dataset.version)}</h3>
          <dl class="inspector-kv">
            <dt>Universe</dt><dd>${program.dataset.universe.length} assets</dd>
            <dt>Asset class</dt><dd>${escapeHtml(program.dataset.assetClass)}</dd>
            <dt>Coverage</dt><dd>${escapeHtml(program.dataset.timeRange.start)} → ${escapeHtml(program.dataset.timeRange.end)}</dd>
            <dt>Evidence</dt><dd>validation selects</dd>
          </dl>
        </section>
        <section class="inspector-section">
          <small>Next governed action</small>
          <p>Work the earliest failed lane before interpreting downstream complexity as value-add.</p>
          ${copyCommandButton(program.recommendedAction, "Copy recommended CLI")}
        </section>
        <details class="program-details">
          <summary>Program contract</summary>
          <pre class="program-copy">${escapeHtml(project.researchProgram.text)}</pre>
        </details>`;
      return;
    }
    element("inspector-content").innerHTML = `
      <section class="inspector-section">
        <small>Research program</small>
        <h3>${escapeHtml(project.name)}</h3>
        <p>${escapeHtml(project.description || "No Project description recorded.")}</p>
        <pre class="program-copy">${escapeHtml(project.researchProgram.text)}</pre>
      </section>`;
    return;
  }
  const manifest = session.session;
  const delegation = session.delegation;
  const latestReport = session.reports.at(-1);
  element("inspector-kind").textContent = "SESSION";
  element("inspector-content").innerHTML = `
    ${delegation ? `
    <section class="inspector-section">
      <small>Incoming research brief</small>
      <h3>${escapeHtml(delegation.request.title)}</h3>
      <p>${escapeHtml(delegation.request.question)}</p>
      <dl class="inspector-kv">
        <dt>Direction</dt><dd>${escapeHtml(delegation.request.direction)}</dd>
        <dt>Horizon</dt><dd>${escapeHtml(delegation.request.horizon)}</dd>
        <dt>Brief</dt><dd title="${escapeHtml(delegation.brief.id)}">${escapeHtml(delegation.brief.id)}</dd>
        <dt>Origin</dt><dd>caller-supplied</dd>
      </dl>
    </section>` : ""}
    <section class="inspector-section">
      <small>Current leader</small>
      <h3>${escapeHtml(manifest.studyId)}</h3>
      <span class="status-chip ${normalizedStatus(manifest.status)}">${escapeHtml(manifest.status)}</span>
      <dl class="inspector-kv">
        <dt>Metric</dt><dd>${escapeHtml(manifest.leader.metric)}</dd>
        <dt>Value</dt><dd>${metric(manifest.leader.value)}</dd>
        <dt>Baseline</dt><dd>${metric(manifest.baseline.value)}</dd>
        <dt>Experiments</dt><dd>${session.experiments.length}</dd>
        <dt>Authority</dt><dd>${session.authority.valid ? "verified" : "stale"}</dd>
      </dl>
    </section>
    ${selectionRiskSection(session.selectionIntegrity)}
    <section class="inspector-section">
      <small>Researcher Campaigns</small>
      <div class="campaign-list">${campaignRows(session)}</div>
    </section>
    <section class="inspector-section">
      <small>Candidate worktree</small>
      <p>${escapeHtml(session.candidate?.differsFromLeader ? "Candidate differs from the verified leader." : "Candidate matches the verified leader.")}</p>
      <dl class="inspector-kv">
        <dt>Session</dt><dd title="${escapeHtml(manifest.id)}">${escapeHtml(manifest.id)}</dd>
        <dt>Next sequence</dt><dd>${manifest.nextExperiment}</dd>
        <dt>Editable</dt><dd>${escapeHtml(manifest.editablePaths.join(", "))}</dd>
      </dl>
    </section>
    <section class="inspector-section">
      <small>Research report</small>
      <h3>${escapeHtml(latestReport?.title ?? "No report published")}</h3>
      <p>${escapeHtml(latestReport?.executiveSummary ?? (delegation ? "Publish structured analysis when the evidence is ready." : "This manual Session has no delegated report brief."))}</p>
      ${delegation ? copyCommandButton(commandFor(session, latestReport ? "report.show" : "report.publish")) : ""}
    </section>
    ${dossierInspectorSection(project)}
    <section class="inspector-section">
      <small>Agent control surface</small>
      ${copyCommandButton(commandFor(session, "session.complete"), "Copy completion CLI")}
      ${copyCommandButton(commandFor(session, "session.show"))}
    </section>
    <section class="inspector-section">
      <small>Research program</small>
      <pre class="program-copy">${escapeHtml(project.researchProgram.text)}</pre>
    </section>`;
}

function renderExperimentInspector(session, experiment) {
  element("inspector-kind").textContent = "EXPERIMENT";
  element("inspector-content").innerHTML = `
    <section class="inspector-section">
      <small>Immutable verdict</small>
      <h3>${escapeHtml(experiment.hypothesis)}</h3>
      <span class="status-chip ${normalizedStatus(experiment.verdict)}">${escapeHtml(experiment.verdict)}</span>
      <dl class="inspector-kv">
        <dt>Leader</dt><dd>${metric(experiment.leaderValue)}</dd>
        <dt>Candidate</dt><dd>${metric(experiment.candidateValue)}</dd>
        <dt>Improvement</dt><dd>${metric(experiment.improvement)}</dd>
        <dt>Sequence</dt><dd>${experiment.sequence}</dd>
        <dt>Completed</dt><dd>${escapeHtml(relativeTime(experiment.completedAt))}</dd>
      </dl>
    </section>
    <section class="inspector-section">
      <small>Evidence identity</small>
      <dl class="inspector-kv">
        <dt>Experiment</dt><dd title="${escapeHtml(experiment.id)}">${escapeHtml(experiment.id)}</dd>
        <dt>Candidate Run</dt><dd title="${escapeHtml(experiment.runId)}">${escapeHtml(experiment.runId)}</dd>
        <dt>Session</dt><dd title="${escapeHtml(session.session.id)}">${escapeHtml(session.session.id)}</dd>
      </dl>
    </section>`;
}

function renderDiagnostics(project) {
  const all = [...state.snapshot.diagnostics, ...project.diagnostics];
  const banner = element("diagnostics");
  if (!all.length) {
    banner.hidden = true;
    banner.textContent = "";
    return;
  }
  banner.hidden = false;
  banner.textContent = `${all.length} verification ${all.length === 1 ? "issue" : "issues"} — ${all
    .slice(0, 2)
    .map((issue) => `${issue.category}: ${issue.message}`)
    .join(" · ")}`;
}

function renderEmptyWorkspace(message = "Create a Project with aq project create.") {
  element("project-state").textContent = "EMPTY WORKSPACE";
  element("project-title").textContent = "No research Projects yet";
  element("project-description").textContent = message;
  element("scoreboard").innerHTML = ["Projects", "Studies", "Runs", "Sessions"]
    .map(
      (label) => `
        <div class="score-cell">
          <small>${label}</small>
          <strong>0</strong>
          <span>waiting</span>
        </div>`,
    )
    .join("");
  element("pulse-meta").textContent = "No active Sessions";
  element("session-lanes").innerHTML =
    '<div class="empty-panel">A governed Session will appear here after its first fixed baseline.</div>';
  element("handoff-flow").textContent = "REQUEST → EVIDENCE → REPORT";
  element("handoff-meta").textContent = "No delegated request";
  element("handoff-board").innerHTML =
    '<div class="empty-panel handoff-empty">Delegated research requests will appear here.</div>';
  element("research-program-status").hidden = true;
  element("evidence-workbench").hidden = true;
  element("factor-explorer").hidden = true;
  element("portfolio-explorer").hidden = true;
  element("rl-explorer").hidden = true;
  element("decision-matrix").hidden = true;
  element("trajectory-meta").textContent = "No Experiments";
  element("trajectory-chart").innerHTML =
    '<div class="empty-panel">Candidate verdicts will appear here.</div>';
  element("evidence-stream").innerHTML =
    '<li class="empty-panel">No verified evidence yet.</li>';
  element("catalog").innerHTML =
    '<div class="empty-panel">No fixed Studies yet.</div>';
  const diagnostics = state.snapshot?.diagnostics ?? [];
  element("diagnostics").hidden = diagnostics.length === 0;
  element("diagnostics").textContent = diagnostics.length
    ? `${diagnostics.length} Workspace verification ${diagnostics.length === 1 ? "issue" : "issues"} — ${diagnostics
        .slice(0, 2)
        .map((issue) => `${issue.category}: ${issue.message}`)
        .join(" · ")}`
    : "";
  element("inspector-kind").textContent = "WORKSPACE";
  element("inspector-content").innerHTML =
    '<p class="empty-copy">Workspace discovery is ready. Projects remain self-contained.</p>';
  document.title = "AutoQuant Studio";
  studio.setAttribute("aria-busy", "false");
}

function render() {
  if (!state.snapshot) return;
  const projects = state.snapshot.projects;
  if (!projects.some((project) => project.id === state.projectId)) {
    const hashId = hashProjectId();
    const workspaceDefault = state.snapshot.source.workspace?.defaultProject;
    state.projectId =
      projects.find((project) => project.id === hashId)?.id ??
      projects.find((project) => project.id === workspaceDefault)?.id ??
      projects[0]?.id ??
      null;
  }
  const project = selectedProject();
  renderProjects();
  if (!project) {
    renderEmptyWorkspace();
    return;
  }
  if (!project.sessions.some((item) => item.session.id === state.sessionId)) {
    state.sessionId =
      project.sessions
        .slice()
        .reverse()
        .find((item) => item.session.status === "active")?.session.id ??
      project.sessions.at(-1)?.session.id ??
      null;
  }
  syncEvidenceSelection(project);
  element("project-state").textContent = project.valid
    ? project.counts.runningCampaigns
      ? "RESEARCHER IN PROGRESS"
      : project.intake && project.counts.sessions === 0
        ? "CONTENT-LOCKED INTAKE READY"
        : "VERIFIED RESEARCH PROJECT"
    : "ATTENTION REQUIRED";
  element("project-title").textContent = project.name;
  element("project-description").textContent =
    project.description ||
    (project.researchProgramStatus
      ? "One research question tested through predictive signal, costed portfolio, and adaptive-policy evidence."
      : "No Project description recorded.");
  document.title = `${project.name} — AutoQuant Studio`;
  renderScoreboard(project);
  renderDiagnostics(project);
  renderHandoff(project);
  renderResearchProgram(project);
  renderFactorExplorer(project);
  renderPortfolioExplorer(project);
  renderRlExplorer(project);
  renderSessions(project);
  renderDecisionMatrix(project);
  renderTrajectory(project);
  renderTimeline(project);
  renderCatalog(project);
  renderInspector(project);
  renderEvidenceWorkbench(project);
  bindCopyCommands();
  studio.setAttribute("aria-busy", "false");
}

async function refresh({ quiet = false } = {}) {
  if (state.loading) return;
  state.loading = true;
  if (!quiet) setConnection("", "Verifying");
  try {
    const response = await fetch("/api/v1/snapshot", {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) {
      const failure = await response.json().catch(() => null);
      throw new Error(failure?.error?.message ?? `Snapshot failed (${response.status})`);
    }
    state.snapshot = await response.json();
    const source = state.snapshot.source;
    element("source-scope").textContent =
      `${source.scope.toUpperCase()} / LOCAL / READ ONLY`;
    element("source-name").textContent =
      source.workspace?.name ?? source.rootDir;
    render();
    setConnection("live", `Synced ${relativeTime(state.snapshot.generatedAt)}`);
  } catch (error) {
    setConnection("error", "Sync failed");
    if (!state.snapshot) {
      renderEmptyWorkspace(`Studio could not verify this source: ${error.message}`);
    }
  } finally {
    state.loading = false;
  }
}

function scheduleRefresh() {
  window.clearInterval(state.timer);
  if (state.autoRefresh) {
    state.timer = window.setInterval(() => {
      if (!document.hidden) refresh({ quiet: true });
    }, 4000);
  }
}

element("refresh").addEventListener("click", () => refresh());
element("auto-refresh").addEventListener("click", (event) => {
  state.autoRefresh = !state.autoRefresh;
  event.currentTarget.setAttribute("aria-pressed", String(state.autoRefresh));
  scheduleRefresh();
});
document.querySelectorAll("[data-catalog]").forEach((button) => {
  button.addEventListener("click", () => {
    state.catalog = button.dataset.catalog;
    const project = selectedProject();
    if (project) renderCatalog(project);
  });
});
document.querySelectorAll("[data-portfolio-view]").forEach((button) => {
  button.addEventListener("click", () => {
    state.portfolioView = button.dataset.portfolioView;
    const explorer = selectedProject()?.portfolioExplorer;
    if (explorer) renderPortfolioChart(explorer);
  });
});
document.querySelectorAll("[data-factor-view]").forEach((button) => {
  button.addEventListener("click", () => {
    state.factorView = button.dataset.factorView;
    const explorer = selectedProject()?.factorExplorer;
    if (explorer) renderFactorChart(explorer);
  });
});
document.querySelectorAll("[data-factor-horizon]").forEach((button) => {
  button.addEventListener("click", () => {
    state.factorHorizon = button.dataset.factorHorizon;
    const explorer = selectedProject()?.factorExplorer;
    if (explorer) renderFactorChart(explorer);
  });
});
document.querySelectorAll("[data-factor-split]").forEach((button) => {
  button.addEventListener("click", () => {
    state.factorSplit = button.dataset.factorSplit;
    const explorer = selectedProject()?.factorExplorer;
    if (explorer) {
      renderFactorChart(explorer);
      renderFactorStability(explorer);
    }
  });
});
document.querySelectorAll("[data-factor-stability]").forEach((button) => {
  button.addEventListener("click", () => {
    state.factorStability = button.dataset.factorStability;
    const explorer = selectedProject()?.factorExplorer;
    if (explorer) renderFactorStability(explorer);
  });
});
document.querySelectorAll("[data-attribution-split]").forEach((button) => {
  button.addEventListener("click", () => {
    state.attributionSplit = button.dataset.attributionSplit;
    const explorer = selectedProject()?.portfolioExplorer;
    if (explorer) renderPortfolioAttribution(explorer);
  });
});
document.querySelectorAll("[data-rl-view]").forEach((button) => {
  button.addEventListener("click", () => {
    state.rlView = button.dataset.rlView;
    const explorer = selectedProject()?.rlExplorer;
    if (explorer) renderRlChart(explorer);
  });
});
document.querySelectorAll("[data-rl-split]").forEach((button) => {
  button.addEventListener("click", () => {
    state.rlSplit = button.dataset.rlSplit;
    const explorer = selectedProject()?.rlExplorer;
    if (explorer) {
      renderRlChart(explorer);
      renderRlTrials(explorer);
      renderRlBaselines(explorer);
      renderRlDetail(explorer);
    }
  });
});
document.querySelectorAll("[data-matrix-view]").forEach((button) => {
  button.addEventListener("click", () => {
    state.matrixView = button.dataset.matrixView;
    const project = selectedProject();
    if (project) renderDecisionMatrix(project);
  });
});
window.addEventListener("hashchange", () => {
  state.projectId = null;
  state.sessionId = null;
  render();
});

scheduleRefresh();
refresh();
