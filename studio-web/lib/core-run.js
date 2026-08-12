function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

const STUDY_ID = /^[a-z0-9][a-z0-9._-]{0,127}$/;

export function selectRunTarget(body, snapshot) {
  if (!isRecord(body) || typeof body.studyId !== "string" || !STUDY_ID.test(body.studyId)) {
    throw new Error("A valid studyId is required");
  }
  if (body.projectId !== undefined && typeof body.projectId !== "string") {
    throw new Error("projectId must be a string");
  }

  const project = body.projectId
    ? snapshot.projects.find((item) => item.id === body.projectId)
    : snapshot.projects[0];
  if (!project || !project.valid) throw new Error("The selected Core project is unavailable");
  if (!project.studies.some((item) => item.id === body.studyId)) {
    throw new Error("The selected Study is not part of the verified Core project");
  }
  if (typeof project.rootDir !== "string" || !project.rootDir) {
    throw new Error("The selected Core project has no executable root");
  }
  return { project, studyId: body.studyId };
}

export function summarizeRunResult(value) {
  const data = value?.data;
  if (value?.ok === true && value.command === "job.execute") {
    if (
      typeof data?.id !== "string"
      || data.status !== "succeeded"
      || typeof data?.runRef?.id !== "string"
      || data.tradingAuthority !== "none"
    ) {
      throw new Error("Core did not return a successful ComputeJob receipt");
    }
    return {
      id: data.runRef.id,
      studyId: data.study?.id,
      status: data.status,
      jobId: data.id,
      executor: data.executor,
      tradingAuthority: data.tradingAuthority,
    };
  }
  const metric = data?.objective?.metric;
  if (value?.ok !== true || typeof data?.id !== "string" || data.status !== "succeeded") {
    throw new Error("Core did not return a successful immutable Run");
  }
  return {
    id: data.id,
    studyId: data.study?.id,
    status: data.status,
    summary: data.summary,
    metric,
    value: metric ? data.metrics?.[metric] : null,
  };
}
