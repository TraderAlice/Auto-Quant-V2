# Trading request field trials

Status: active acceptance record.

Related: [[plans/real-trading-request-field-trials]],
[[docs/design/agent-native-quant-workbench]],
[[docs/design/research-intake-and-dataset-snapshots]], and
[[docs/design/request-bound-portfolio-mandates]].

## Purpose

This record starts from the questions an OpenAlice investment-research Agent
may delegate during real trading work. It tests whether an AutoQuant coworker
can preserve the caller's intended decision, clarify material ambiguity,
choose an appropriate quantitative route, and return verified evidence.

The raw request is not a strict schema and does not need to name Factor,
Portfolio, RL, a template, or an evaluation method. Those are researcher-owned
choices. A field trial fails semantically if it quietly changes the assets,
direction, horizon, risk appetite, opportunity-cost reference, or requested
decision merely to fit an existing Lab.

## Initial request matrix

| ID | Raw delegated request | Material clarification before research | Intended route | Initial support |
| --- | --- | --- | --- | --- |
| `equity-allocation` | “我想在 AAPL、MSFT、NVDA、AMZN、GOOGL、META、AVGO 里挑未来一个月最值得超配的几只。如果只做多、每周调整一次、组合年化波动别超过 15%、单票不超过 25%，相对 QQQ 到底该怎么配？” | Confirm that “one month” means 20 XNYS sessions; cash is allowed; output is a model target rather than an account order; bind cost, no-trade, and reference-capital assumptions. | Daily cross-sectional Factor evidence followed by request-bound long/cash Portfolio evidence and a current historical decision handoff. | Candidate: the Research Desk owns the required horizon, benchmark, caps, volatility ceiling, cadence, costs, target weights, and evidence. |
| `crypto-context-timing` | “BTC 这位置还能不能加？我一小时看一次，希望 4h 和 1d 趋势都别太差；ETH、SOL 和大盘币可以拿来做环境判断。” | Confirm a numerical holding/forecast horizon, which assets may actually receive weight, maximum BTC weight and volatility budget, venue/data source, cost assumption, and whether cash is allowed. | Continuous 1h package with causal 4h/1d context, BTC tradable and peers context-only, then Factor/Portfolio current-state evidence. | Candidate: multi-interval inputs and context-only assets exist; the single-tradable-asset decision path still needs a field trial. |
| `relative-value` | “NVDA 相对半导体板块是不是涨过头了？如果做 NVDA 和 SOXX 的相对价值，未来两周值不值得，仓位怎么控制？” | Clarify allowed long/short signs, whether dollar neutrality or beta neutrality is intended, 10-session horizon, borrow/cost assumptions, gross and per-leg limits, and acceptable proxies. | Role-aware relative-value mandate with a wider semiconductor context universe and cash benchmark. | Partial: sign roles and dollar-neutral weights exist; beta neutrality, borrow, and financing do not and must not be implied. |
| `book-crowding` | “我现在主要拿着 AAPL、MSFT、NVDA 和 QQQ，这几个是不是其实一笔交易？如果要降风险先减谁？” | Current account weights, tax/lot constraints, decision horizon, risk budget, whether the caller wants historical model risk or live-account action, and allowed replacements. | Historical covariance/diversification and marginal-risk research; OpenAlice/UTA retains authenticated current positions and performs the live comparison. | Partial: AutoQuant explains modeled concentration and target books but does not ingest or reconcile authenticated live holdings. |
| `protective-orders` | “这笔仓位止盈止损挂哪里，Agent 一小时醒一次也能管住？” | Venue/order capabilities, entry and current position, gap policy, trigger semantics, time in force, slippage, and loss budget. | OpenAlice execution discussion informed by quantitative volatility/path evidence. | Boundary: historical Order/TPSL research is paused and live order authority belongs to UTA; target-weight evidence must not masquerade as an order plan. |
| `event-reaction` | “财报跳空以后第三天买回去有没有优势？” | Exact event definition and timestamp, eligible universe, corporate-action treatment, entry clock, holding horizon, survivorship policy, and event-data source. | Event-study factor research with locked event observations plus OHLCV. | Unsupported today: the public intake contract locks OHLCV but has no event-observation package contract. |
| `future-or-fx` | “用小时线看看黄金期货和美元，什么时候适合做多黄金？” | Exact instruments/contracts, roll method, trading sessions, timezone, leverage/margin, direction, horizon, and data authority. | Time-series/context research under a contract-aware futures/FX market clock. | Unsupported today: the request schema names these asset classes, but current verified clocks and data semantics do not cover futures roll or general FX sessions. |

## Field-trial protocol

Each exercised row must leave:

1. the raw caller statement and clarification dialogue summarized in English
   in Project-root `research.md`;
2. a strict request only after caller-owned facts are resolved;
3. a provider-described, content-locked, non-toy OHLCV package;
4. public `aq` construction, orientation, execution, Session, and handoff
   evidence;
5. a useful conclusion even when the hypothesis fails;
6. Project-local `framework-needs.md` observations that distinguish research
   method work from reusable Workbench defects.

## Trial status

| ID | Project | Status | Evidence and conclusion |
| --- | --- | --- | --- |
| `equity-allocation` | `us-megacap-one-month-signal` | completed — negative | The first intake (`us-megacap-one-month-allocation`) exposed an invalid implicit novelty claim and remains preserved. The corrected `decision-signal` Session retained five-session reversal over the full research universe at validation IC `0.084686`, but HAC t `1.715`, uneven folds, and family-adjusted p `0.258767` failed qualification. An authorized-seven-only check fell to `0.061599` and was reverted. Report `report-20260728T081902704910Z-bcb2bc282fd6` therefore withheld target weights and downstream Portfolio/RL work. The trial directly produced the claim-aware prediction-universe contract in AutoQuant `0.3.0`. |
| `crypto-context-timing` | `crypto-btc-one-day-portfolio` | completed — negative with one open correctness gap | Binance Spot provided 9,408 closed hourly bars for BTC, ETH, SOL, BNB, and XRP with completed 3h/4h/6h/12h/1d surfaces. AutoQuant `0.4.0` added single-asset temporal evaluation after the preserved `0.3.0` population failure. Direct multi-horizon continuation reverted at validation IC `-0.178427`; overextension reversion retained IC `0.178427`, HAC t `2.391`, and positive folds. The clean `0.4.1` reproduction adjusted p to `0.033568`. AutoQuant `0.4.1`/`0.4.2` then repaired repeated-simulation performance and bounded the complete hourly Portfolio Judge at 180 seconds. Run `run-20260728T100043368147Z-bf56b58eeef7` completed in 144,399 ms: validation gross Sharpe `1.920`, net Sharpe `-1.819`, annualized one-way turnover `82.473`, and only 40% of the 15 fixed configurations had positive net Sharpe. The request therefore does not support adding BTC under the fixed hourly implementation. The Run also exposed an open Core defect: post-drift executed BTC weight reached `0.316860` despite the caller's `0.30` cap. |
| `relative-value` | pending | not started | Pending semiconductor universe and explicit sign/neutrality clarification. |

## Current boundary

AutoQuant is a quantitative research desk, not a second UTA. A supported
request may end with verified model target weights, historical state,
uncertainty, risk, capacity, and implementation assumptions. The delegating
OpenAlice Agent may compare that evidence with current authenticated holdings
and discuss execution with the user. AutoQuant must return an explicit
boundary when the question instead requires live account truth, venue
capability, or data semantics it does not own.
