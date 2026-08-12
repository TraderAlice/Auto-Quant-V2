import { execFile } from "node:child_process";
import { access, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";
import { resolveCoreSnapshotUrl, validateCoreSnapshot } from "@/lib/core-snapshot";
import {
  INTAKE_LIMITS,
  selectIntakeTarget,
  summarizeIntakeResult,
  validateIntakeDocuments,
} from "@/lib/core-intake";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
let activeProjectId = null;

function upload(value, label) {
  if (!value || typeof value.arrayBuffer !== "function" || typeof value.size !== "number") {
    throw new Error(`${label} file is required`);
  }
  return value;
}

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
      return NextResponse.json({ ok: false, error: { code: "studio.intake.origin", message: "Cross-origin data intake is not allowed." } }, { status: 403 });
    }
    const contentLength = Number(request.headers.get("content-length"));
    if (!Number.isSafeInteger(contentLength) || contentLength < 1 || contentLength > INTAKE_LIMITS.totalBytes) {
      throw new Error("Upload requires a valid Content-Length within the 256 MB intake limit");
    }
    if (!request.headers.get("content-type")?.toLowerCase().startsWith("multipart/form-data;")) {
      throw new Error("Data intake requires multipart/form-data");
    }

    const form = await request.formData();
    const target = selectIntakeTarget({
      projectId: form.get("projectId"),
      template: form.get("template"),
      name: form.get("name") || undefined,
    }, await coreSnapshot());
    const requestFile = upload(form.get("request"), "Research Request");
    const packageFile = upload(form.get("dataset"), "Dataset package");
    const sourceFiles = form.getAll("source").map((file) => upload(file, "Data source"));
    const sourcePaths = form.getAll("sourcePath").map(String);

    if (requestFile.size > INTAKE_LIMITS.jsonBytes || packageFile.size > INTAKE_LIMITS.jsonBytes) {
      throw new Error("Request and dataset-package JSON files must each be at most 2 MB");
    }
    if (!sourceFiles.length || sourceFiles.length > INTAKE_LIMITS.sourceFiles || sourceFiles.length !== sourcePaths.length) {
      throw new Error("Upload 1 to 128 data files with matching relative paths");
    }
    if (sourceFiles.some((file) => file.size > INTAKE_LIMITS.sourceBytes)) {
      throw new Error("Each data file must be at most 64 MB");
    }
    const totalBytes = requestFile.size + packageFile.size + sourceFiles.reduce((sum, file) => sum + file.size, 0);
    if (totalBytes > INTAKE_LIMITS.totalBytes) throw new Error("Upload exceeds the 256 MB intake limit");

    const requestText = await requestFile.text();
    const packageText = await packageFile.text();
    validateIntakeDocuments(requestText, packageText, sourcePaths);
    try {
      await access(path.join(target.projectsDir, target.projectId));
      throw new Error("The target Project already exists");
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
    }
    if (activeProjectId) {
      return NextResponse.json({ ok: false, error: { code: "studio.intake.busy", message: `${activeProjectId} is already being imported.` } }, { status: 409 });
    }

    activeProjectId = target.projectId;
    acquired = true;
    staging = await mkdtemp(path.join(os.tmpdir(), "autoquant-studio-intake-"));
    const requestPath = path.join(staging, "request.json");
    const packagePath = path.join(staging, "dataset-package.json");
    await writeFile(requestPath, requestText, { encoding: "utf8", flag: "wx" });
    await writeFile(packagePath, packageText, { encoding: "utf8", flag: "wx" });
    for (let index = 0; index < sourceFiles.length; index += 1) {
      const targetPath = path.resolve(staging, ...sourcePaths[index].split("/"));
      if (path.relative(staging, targetPath).startsWith("..")) throw new Error("Data file escaped the intake boundary");
      await mkdir(path.dirname(targetPath), { recursive: true });
      await writeFile(targetPath, Buffer.from(await sourceFiles[index].arrayBuffer()), { flag: "wx" });
    }

    // ponytail: intake is serialized locally; replace with ComputeJob scheduling when concurrent imports are required.
    const args = ["run", "aq", "project", "intake", target.workspaceRoot, target.projectId, "--request", requestPath, "--dataset", packagePath, "--template", target.template];
    if (target.name) args.push("--name", target.name);
    args.push("--json");
    const { stdout } = await execFileAsync("uv", args, {
      cwd: path.resolve(process.cwd(), ".."),
      windowsHide: true,
      timeout: 180_000,
      maxBuffer: 16 * 1024 * 1024,
    });
    return NextResponse.json({ ok: true, intake: summarizeIntakeResult(JSON.parse(stdout)) }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return NextResponse.json({
      ok: false,
      error: { code: "studio.intake.failed", message: (error instanceof Error ? error.message : "Data intake failed").slice(0, 4000) },
    }, { status: 400, headers: { "Cache-Control": "no-store" } });
  } finally {
    if (acquired) activeProjectId = null;
    if (staging) await rm(staging, { recursive: true, force: true });
  }
}
