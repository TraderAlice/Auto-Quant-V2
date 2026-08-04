import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";
import { resolveCoreSnapshotUrl, validateCoreSnapshot } from "@/lib/core-snapshot";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
const MAX_BYTES = 64 * 1024 * 1024;
const PROJECT_ID = /^[a-z0-9][a-z0-9-]{0,63}$/;
const ADAPTERS = new Set(["a-share-announcement", "crypto-event", "financial-news"]);
let activeProjectId = null;

async function coreSnapshot() {
  const response = await fetch(resolveCoreSnapshotUrl(process.env.AUTOQUANT_STUDIO_CORE_URL), {
    cache: "no-store",
    headers: { accept: "application/json" },
    redirect: "error",
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`Core returned HTTP ${response.status}`);
  return validateCoreSnapshot(await response.json());
}

export async function POST(request) {
  let staging = null;
  let acquired = false;
  try {
    const origin = request.headers.get("origin");
    if (origin && new URL(origin).origin !== new URL(request.url).origin) {
      return NextResponse.json({ ok: false, error: { code: "studio.event-intake.origin", message: "Cross-origin event intake is not allowed." } }, { status: 403 });
    }
    const contentLength = Number(request.headers.get("content-length"));
    if (!Number.isSafeInteger(contentLength) || contentLength < 1 || contentLength > MAX_BYTES) {
      throw new Error("Event intake requires a valid Content-Length within 64 MiB");
    }
    if (!request.headers.get("content-type")?.toLowerCase().startsWith("multipart/form-data;")) {
      throw new Error("Event intake requires multipart/form-data");
    }
    const form = await request.formData();
    const projectId = String(form.get("projectId") || "");
    const file = form.get("package");
    if (!PROJECT_ID.test(projectId)) throw new Error("A valid existing projectId is required");
    if (!file || typeof file.arrayBuffer !== "function" || file.size < 1 || file.size > MAX_BYTES) throw new Error("A JSON event package up to 64 MiB is required");
    const packageText = await file.text();
    const value = JSON.parse(packageText);
    if (value?.kind !== "autoquant-event-package" || !ADAPTERS.has(value?.adapterKind)) throw new Error("Unsupported event package contract");
    const snapshot = await coreSnapshot();
    const project = snapshot.projects.find((item) => item.id === projectId && item.valid);
    if (!project || !path.isAbsolute(project.rootDir || "")) throw new Error("The selected verified Core Project is unavailable");
    if (activeProjectId) return NextResponse.json({ ok: false, error: { code: "studio.event-intake.busy", message: `${activeProjectId} is already importing events.` } }, { status: 409 });

    activeProjectId = projectId;
    acquired = true;
    staging = await mkdtemp(path.join(os.tmpdir(), "autoquant-studio-events-"));
    const packagePath = path.join(staging, "event-package.json");
    await writeFile(packagePath, packageText, { encoding: "utf8", flag: "wx" });
    const { stdout } = await execFileAsync(
      "uv",
      ["run", "aq", "event", "intake", project.rootDir, "--package", packagePath, "--json"],
      { cwd: path.resolve(process.cwd(), ".."), windowsHide: true, timeout: 120_000, maxBuffer: 16 * 1024 * 1024 },
    );
    const result = JSON.parse(stdout);
    if (result?.ok !== true || result.command !== "event.intake" || typeof result.data?.snapshotHash !== "string") throw new Error("Core did not return a verified event snapshot");
    return NextResponse.json({ ok: true, eventSnapshot: result.data }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return NextResponse.json({ ok: false, error: { code: "studio.event-intake.failed", message: (error instanceof Error ? error.message : "Event intake failed").slice(0, 4000) } }, { status: 400, headers: { "Cache-Control": "no-store" } });
  } finally {
    if (acquired) activeProjectId = null;
    if (staging) await rm(staging, { recursive: true, force: true });
  }
}
