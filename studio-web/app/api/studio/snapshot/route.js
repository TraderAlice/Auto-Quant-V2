import { NextResponse } from "next/server";
import { resolveCoreSnapshotUrl, validateCoreSnapshot } from "@/lib/core-snapshot";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const url = resolveCoreSnapshotUrl(process.env.AUTOQUANT_STUDIO_CORE_URL);
    const response = await fetch(url, {
      cache: "no-store",
      headers: { accept: "application/json" },
      redirect: "error",
      signal: AbortSignal.timeout(15_000),
    });
    if (!response.ok) throw new Error(`Core returned HTTP ${response.status}`);
    const snapshot = validateCoreSnapshot(await response.json());
    return NextResponse.json(snapshot, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json(
      {
        ok: false,
        error: {
          code: "studio.core.unavailable",
          message: "The local read-only AutoQuant Core snapshot is unavailable.",
        },
      },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
