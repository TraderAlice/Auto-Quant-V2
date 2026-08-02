"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useStudio } from "@/components/studio-context";
import { formatTime } from "@/lib/research";

const navigation = [
  { href: "/", code: "RH", label: "研究首页" },
  { href: "/factors/aq-event-drift", code: "FP", label: "因子护照" },
  { href: "/replay", code: "RP", label: "时序回放" },
  { href: "/events", code: "EV", label: "事件工作台" },
  { href: "/lab", code: "FL", label: "因子实验室" },
  { href: "/results", code: "RS", label: "测试结果" },
  { href: "/portfolio", code: "PF", label: "组合研究" },
  { href: "/rl", code: "RL", label: "治理式 RL" },
  { href: "/jobs", code: "JB", label: "研究任务" },
  { href: "/data", code: "DT", label: "数据目录" },
  { href: "/audit", code: "AU", label: "审计与复现" },
];
const connectedRoutes = new Set(["/", "/portfolio", "/rl"]);

function isActive(pathname, href) {
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

export function StudioShell({ children }) {
  const pathname = usePathname();
  const {
    factor,
    asOf,
    source,
    demoEnabled,
    enableDemo,
    returnToCore,
    retryCore,
  } = useStudio();
  const [menuOpen, setMenuOpen] = useState(false);
  const connected = source.mode === "connected";
  const sourceLabel = demoEnabled
    ? "DEMO DATA"
    : connected
      ? `CORE ${source.snapshot.harness.version}`
      : source.mode.toUpperCase();
  const needsGate = !demoEnabled && (
    source.mode === "loading"
    || source.mode === "unavailable"
    || (connected && !connectedRoutes.has(pathname))
  );
  const activeContext = pathname.startsWith("/portfolio")
    ? { label: "组合", name: "OHLCV Portfolio Quality", href: "/portfolio", version: "CORE" }
    : pathname.startsWith("/rl")
      ? { label: "策略", name: "Governed RL Factor Policy", href: "/rl", version: "CORE" }
      : { label: "因子", name: factor.name, href: `/factors/${factor.id}`, version: factor.version };

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">跳到主要内容</a>
      <aside className={`nav-rail ${menuOpen ? "is-open" : ""}`} aria-label="产品导航">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">AQ</span>
          <div>
            <strong>AutoQuant</strong>
            <span>Studio</span>
          </div>
        </div>
        <nav className="nav-list">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="nav-link"
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              onClick={() => setMenuOpen(false)}
            >
              <span className="nav-code" aria-hidden="true">{item.code}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="nav-footer">
          <span className="state-line"><b>{sourceLabel}</b></span>
          {demoEnabled ? (
            <button className="source-switch" type="button" onClick={returnToCore}>返回 Core</button>
          ) : null}
          <span>无交易、账户或订单能力</span>
        </div>
      </aside>

      <div className="workspace">
        <header className="workspace-bar">
          <button
            type="button"
            className="mobile-menu"
            aria-label="打开产品导航"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            菜单
          </button>
          <div className="context-path">
            <span>{activeContext.label}</span>
            <Link href={activeContext.href}>{activeContext.name}</Link>
            <span className="mono">{activeContext.version}</span>
          </div>
          <div className="bar-status">
            <span className={`status-dot ${connected ? "known" : ""}`} aria-hidden="true" />
            <span>{sourceLabel} · {factor.frameId}</span>
            {asOf ? <time dateTime={asOf}>T = {formatTime(asOf)} CST</time> : <span>T = unavailable</span>}
          </div>
        </header>
        <main id="main-content" className="main-content" tabIndex="-1">
          {needsGate ? (
            <section className="source-gate" aria-live="polite">
              <p className="eyebrow">Research evidence source</p>
              <h1>{source.mode === "loading" ? "正在连接本地 AutoQuant Core" : connected ? "该页面尚未映射 Core 证据" : "本地 Core snapshot 不可用"}</h1>
              <p>
                {source.mode === "loading"
                  ? "只读取 loopback 上的版本化 Studio snapshot。"
                  : connected
                    ? "工作区上下文已连接；本路线当前仍使用确定性演示记录，必须显式进入演示模式。"
                    : "先启动 aq studio serve；也可以显式进入隔离的演示模式检查交互。"}
              </p>
              <div className="button-row">
                {source.mode === "unavailable" ? <button className="button-secondary" type="button" onClick={retryCore}>重试 Core</button> : null}
                {source.mode !== "loading" ? <button className="button" type="button" onClick={enableDemo}>使用演示数据</button> : null}
              </div>
            </section>
          ) : (
            <>
              {demoEnabled ? (
                <div className="source-banner" role="status">
                  <strong>DEMO DATA</strong>
                  <span>本页记录为确定性产品演示，不是 Core 验证证据。</span>
                </div>
              ) : null}
              {children}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
