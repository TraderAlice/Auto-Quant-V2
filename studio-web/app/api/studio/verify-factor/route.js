import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";
import { resolveCoreSnapshotUrl, validateCoreSnapshot } from "@/lib/core-snapshot";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
const SAFE_ID = /^[a-z0-9][a-z0-9._-]{0,127}$/;
let activeRunId = null;

async function coreSnapshot() {
  const response = await fetch(resolveCoreSnapshotUrl(process.env.AUTOQUANT_STUDIO_CORE_URL), {
    cache: "no-store", headers: { accept: "application/json" }, redirect: "error", signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`Core returned HTTP ${response.status}`);
  return validateCoreSnapshot(await response.json());
}

export async function POST(request) {
  try {
    const origin = request.headers.get("origin");
    if (origin && new URL(origin).origin !== new URL(request.url).origin) return NextResponse.json({ ok: false, error: { code: "studio.verify.origin", message: "Cross-origin verification is not allowed." } }, { status: 403 });
    const body = await request.json();
    const statement = typeof body?.statement === "string" ? body.statement.trim() : "";
    const minimumEffect = Number(body?.minimumEffect);
    const minimumSampleSize = Number(body?.minimumSampleSize);
    if (!SAFE_ID.test(body?.projectId || "") || !SAFE_ID.test(body?.runId || "")) throw new Error("Valid projectId and runId are required");
    if (!statement || statement.length > 500) throw new Error("Claim statement must contain 1 to 500 characters");
    if (!Number.isFinite(minimumEffect) || minimumEffect < 0) throw new Error("minimumEffect must be non-negative");
    if (!Number.isInteger(minimumSampleSize) || minimumSampleSize < 1 || minimumSampleSize > 1_000_000) throw new Error("minimumSampleSize must be an integer from 1 to 1,000,000");
    if (typeof body.requireHoldout !== "boolean" || typeof body.requireSelection !== "boolean") throw new Error("Claim evidence requirements must be explicit booleans");
    const snapshot = await coreSnapshot();
    const project = snapshot.projects.find((item) => item.id === body.projectId && item.valid);
    const run = project?.runs?.find((item) => item.id === body.runId && item.primaryMetric === "validation_mean_ic");
    if (!project || !run || !path.isAbsolute(project.rootDir || "")) throw new Error("The selected verified Factor Run is unavailable");
    if (activeRunId) return NextResponse.json({ ok: false, error: { code: "studio.verify.busy", message: `${activeRunId} is already being assessed.` } }, { status: 409 });
    activeRunId = body.runId;
    try {
      const args = ["run", "aq", "verify", "factor", project.rootDir, "--run", body.runId, "--statement", statement, "--minimum-effect", String(minimumEffect), "--minimum-sample-size", String(minimumSampleSize)];
      if (body.requireHoldout) args.push("--require-holdout");
      if (body.requireSelection) args.push("--require-selection");
      args.push("--json");
      const { stdout } = await execFileAsync("uv", args, { cwd: path.resolve(process.cwd(), ".."), windowsHide: true, timeout: 120_000, maxBuffer: 16 * 1024 * 1024 });
      const result = JSON.parse(stdout);
      if (result?.ok !== true || result.command !== "verify.factor" || typeof result.data?.assessment?.id !== "string") throw new Error("Core did not return a verified assessment");
      return NextResponse.json({ ok: true, verification: result.data }, { headers: { "Cache-Control": "no-store" } });
    } finally {
      activeRunId = null;
    }
  } catch (error) {
    return NextResponse.json({ ok: false, error: { code: "studio.verify.failed", message: (error instanceof Error ? error.message : "Verification failed").slice(0, 4000) } }, { status: 400, headers: { "Cache-Control": "no-store" } });
  }
}
