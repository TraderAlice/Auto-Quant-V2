import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative } from "node:path";

const roots = ["app", "components", "lib"];
const allowedExtensions = new Set([".js", ".jsx", ".mjs"]);
const forbidden = [
  [/\bAuthorization\b/i, "authenticated header"],
  [/\bCookie\b/i, "cookie forwarding"],
  [/\bx-api-key\b/i, "API key header"],
  [/\bmcp__[a-z0-9_]+\b/i, "private MCP tool name"],
  [/process\.env(?:\.([A-Z0-9_]+)|\[["']([A-Z0-9_]+)["']\])/g, "non-allowlisted environment variable"],
];
const allowedEnv = new Set(["AUTOQUANT_STUDIO_CORE_URL"]);

async function filesUnder(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await filesUnder(path));
    else if (allowedExtensions.has(extname(entry.name))) files.push(path);
  }
  return files;
}

const findings = [];
for (const root of roots) {
  for (const file of await filesUnder(root)) {
    const source = await readFile(file, "utf8");
    for (const [pattern, label] of forbidden) {
      pattern.lastIndex = 0;
      let match;
      while ((match = pattern.exec(source))) {
        if (label === "non-allowlisted environment variable" && allowedEnv.has(match[1] || match[2])) continue;
        findings.push(`${relative(".", file)}: ${label}`);
        if (!pattern.global) break;
      }
    }
  }
}

if (findings.length) {
  throw new Error(`Open-source boundary check failed:\n${findings.join("\n")}`);
}

console.log("Open-source boundary check passed.");
