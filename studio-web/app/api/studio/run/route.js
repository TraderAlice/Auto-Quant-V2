import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { NextResponse } from "next/server";
import { resolveCoreSnapshotUrl, validateCoreSnapshot } from "@/lib/core-snapshot";
import { selectRunTarget, summarizeRunResult } from "@/lib/core-run";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
let activeStudyId = null;

export async function POST(request) {
  try {
    const origin = request.headers.get("origin");
    if (origin && new URL(origin).origin !== new URL(request.url).origin) {
      return NextResponse.json({ ok: false, error: { code: "studio.run.origin", message: "Cross-origin research execution is not allowed." } }, { status: 403 });
    }

    const response = await fetch(resolveCoreSnapshotUrl(process.env.AUTOQUANT_STUDIO_CORE_URL), {
      cache: "no-store",
      headers: { accept: "application/json" },
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) throw new Error(`Core returned HTTP ${response.status}`);
    const target = selectRunTarget(await request.json(), validateCoreSnapshot(await response.json()));
    if (activeStudyId) {
      return NextResponse.json(
        { ok: false, error: { code: "studio.run.busy", message: `${activeStudyId} is already running.` } },
        { status: 409 },
      );
    }

    activeStudyId = target.studyId;
    try {
      // ponytail: one local execution lock; provider plugins can replace it when concurrent dispatch is real.
      const { stdout } = await execFileAsync(
        "uv",
        ["run", "aq", "job", "execute", target.project.rootDir, "--study", target.studyId, "--executor", "cpu", "--json"],
        { cwd: target.project.rootDir, windowsHide: true, timeout: 120_000, maxBuffer: 16 * 1024 * 1024 },
      );
      return NextResponse.json(
        { ok: true, run: summarizeRunResult(JSON.parse(stdout)) },
        { headers: { "Cache-Control": "no-store" } },
      );
    } finally {
      activeStudyId = null;
    }
  } catch (error) {
    return NextResponse.json(
      { ok: false, error: { code: "studio.run.failed", message: error instanceof Error ? error.message : "Research execution failed." } },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }
}
