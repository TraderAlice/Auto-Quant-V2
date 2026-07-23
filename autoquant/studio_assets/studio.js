const state = {
  snapshot: null,
  projectId: null,
  sessionId: null,
  catalog: "studies",
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
      window.location.hash = encodeURIComponent(state.projectId);
      render();
    });
  });
}

function renderScoreboard(project) {
  const counts = project.counts;
  const values = [
    ["Active Sessions", counts.activeSessions, counts.sessions === 1 ? "1 total" : `${counts.sessions} total`, counts.activeSessions ? "live" : ""],
    ["Running", counts.runningCampaigns, "mutable progress", counts.runningCampaigns ? "live" : ""],
    ["Experiments", counts.verdicts.KEEP + counts.verdicts.REVERT + counts.verdicts.CRASH, `${counts.verdicts.KEEP} kept`, ""],
    ["Immutable Runs", counts.runs, `${counts.campaigns} campaigns`, ""],
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
              <span>${escapeHtml(session.status)} session</span>
              <strong>${escapeHtml(session.studyId)}</strong>
              <code>${escapeHtml(session.id)}</code>
            </span>
            <span class="lane-stat">
              <small>Leader</small>
              <strong>${metric(session.leader.value)}</strong>
            </span>
            <span class="lane-stat">
              <small>Experiments</small>
              <strong>${item.experiments.length}</strong>
            </span>
            <span class="lane-stat">
              <small>Turn</small>
              <strong>${escapeHtml(campaign.turn)}</strong>
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
      render();
      element("inspector-content").scrollTop = 0;
    });
  });
}

function renderTrajectory(project) {
  const session = selectedSession(project);
  const experiments = session?.experiments ?? [];
  element("trajectory-meta").textContent = session
    ? `${session.session.studyId} · leader ${metric(session.session.leader.value)}`
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
  element("inspector-kind").textContent = "SESSION";
  element("inspector-content").innerHTML = `
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
  element("project-state").textContent = project.valid
    ? project.counts.runningCampaigns
      ? "RESEARCHER IN PROGRESS"
      : "VERIFIED RESEARCH PROJECT"
    : "ATTENTION REQUIRED";
  element("project-title").textContent = project.name;
  element("project-description").textContent =
    project.description || "No Project description recorded.";
  document.title = `${project.name} — AutoQuant Studio`;
  renderScoreboard(project);
  renderDiagnostics(project);
  renderSessions(project);
  renderTrajectory(project);
  renderTimeline(project);
  renderCatalog(project);
  renderInspector(project);
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
window.addEventListener("hashchange", () => {
  state.projectId = null;
  state.sessionId = null;
  render();
});

scheduleRefresh();
refresh();
