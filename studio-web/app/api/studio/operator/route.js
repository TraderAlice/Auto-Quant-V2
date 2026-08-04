import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { NextResponse } from "next/server";
import { resolveCoreSnapshotUrl, validateCoreSnapshot } from "@/lib/core-snapshot";
import { validateOperatorRequest } from "@/lib/research-console";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const execFileAsync = promisify(execFile);
const MAX_BODY_BYTES = 1024 * 1024;

function response(payload, status = 200) {
  return NextResponse.json(payload, { status, headers: { "Cache-Control": "no-store" } });
}

export async function POST(request) {
  let temporary = null;
  try {
    const origin = request.headers.get("origin");
    if (origin && new URL(origin).origin !== new URL(request.url).origin) {
      return response({ ok: false, error: { code: "studio.operator.origin", message: "Cross-origin Operator requests are not allowed." } }, 403);
    }
    const declaredLength = Number(request.headers.get("content-length"));
    if (!Number.isSafeInteger(declaredLength) || declaredLength < 1 || declaredLength > MAX_BODY_BYTES) {
      return response({ ok: false, error: { code: "studio.operator.length", message: "Operator request requires a valid Content-Length within 1 MiB." } }, 413);
    }
    const raw = await request.text();
    if (Buffer.byteLength(raw, "utf8") > MAX_BODY_BYTES) throw new Error("Operator request exceeds 1 MiB");

    const snapshotResponse = await fetch(resolveCoreSnapshotUrl(process.env.AUTOQUANT_STUDIO_CORE_URL), {
      cache: "no-store",
      headers: { accept: "application/json" },
      redirect: "error",
      signal: AbortSignal.timeout(15_000),
    });
    if (!snapshotResponse.ok) throw new Error(`Core returned HTTP ${snapshotResponse.status}`);
    const snapshot = validateCoreSnapshot(await snapshotResponse.json());
    const target = validateOperatorRequest(JSON.parse(raw), snapshot);

    temporary = await mkdtemp(join(tmpdir(), "autoquant-operator-"));
    const requestFile = join(temporary, "request.json");
    await writeFile(requestFile, `${JSON.stringify(target.request, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
    const { stdout } = await execFileAsync(
      "uv",
      ["run", "aq", "operator", "invoke", target.project.rootDir, "--request", requestFile, "--json"],
      { cwd: target.project.rootDir, windowsHide: true, timeout: 120_000, maxBuffer: 16 * 1024 * 1024 },
    );
    const payload = JSON.parse(stdout);
    return response(payload, payload.ok === false ? 400 : 200);
  } catch (error) {
    if (typeof error?.stdout === "string" && error.stdout.trim()) {
      try {
        return response(JSON.parse(error.stdout), 400);
      } catch {
        // Fall through to the bounded error envelope.
      }
    }
    return response({ ok: false, error: { code: "studio.operator.failed", message: error instanceof Error ? error.message : "Operator request failed." } }, 400);
  } finally {
    if (temporary) await rm(temporary, { recursive: true, force: true });
  }
}
