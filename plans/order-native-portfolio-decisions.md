# Order-native portfolio decisions

- Status: `paused`
- Updated: `2026-07-27`
- Related design: [[docs/design/order-native-portfolio-decisions]],
  [[docs/design/quant-research-lifecycle]],
  [[docs/design/portfolio-construction-lab]], and
  [[docs/design/rl-factor-policy-lab]].

## Outcome

Let AutoQuant answer a real local or delegated research request with an
evidence-backed target portfolio and a bounded order/TPSL realization plan,
while keeping factor research, portfolio construction, RL, bar execution, and
external live-trading authority distinct and composable.

## Context

The current Portfolio Judge correctly maps causal factor state into unequal
request-constrained target weights. It then treats each weight delta as a
complete close execution and credits the following close return.

That model cannot study an hourly Agent which leaves a limit entry and
protective TP/SL orders working between decisions. It also cannot distinguish
factor failure, sizing failure, unfilled intent, protective-exit behavior, or
OHLC same-bar path ambiguity.

AutoQuant must research decisions that can later map into an external trading
workflow without claiming that an order was staged or executed. In an
OpenAlice-hosted Workspace, authenticated accounts and stage → commit →
approval → push remain OpenAlice/UTA authority.

## Scope

### In scope

- Preserve factor → signal → target-weight portfolio construction.
- Add a strict `DecisionPlan` boundary containing the target portfolio,
  risk-at-stop evidence, and order realization intent.
- Add deterministic OHLCV bar execution for market, limit, stop, stop-limit,
  parent/child bracket TP/SL, OCO cancellation, expiry, and gap behavior.
- Make ambiguous same-bar paths explicit and conservatively evaluated.
- Reconcile target, order, fill, protected quantity, actual weight, return,
  cost, and exit reason in immutable evidence.
- Keep rule-based, statistical, ML, and RL factor representations valid.
- Let mechanical and RL decision policies consume the same factor/portfolio
  state and execute through the same fixed order kernel.
- Return a current decision-support artifact without account or trading
  authority.
- Use breaking schema updates; do not preserve obsolete implicit-close
  execution evidence.

### Out of scope

- L2 replay, queue position, exchange-specific latency, smart routing, or HFT.
- Authenticated UTA state, broker credentials, order staging, approval, push,
  or fill confirmation.
- Pretending one OHLC bar proves an unknowable intrabar path.
- Every exotic order type or venue-specific capability in the first slice.

## Acceptance

- [ ] Factor evidence, target weights, order plans, fills, and actual portfolio
  state are separate but content-linked evidence layers.
- [ ] Position size explains conviction, volatility/covariance limits,
  per-asset caps, stop distance, and portfolio loss-at-stop contribution.
- [ ] Market/limit entry and bracket TPSL lifecycles are deterministic,
  causal, gap-aware, OCO-safe, and tested for long and short positions.
- [ ] Same-bar TP/SL or entry/exit ambiguity is never silently resolved in the
  candidate's favor.
- [ ] Unfilled/expired/cancelled intent and partially protected exposure cannot
  be reported as a completed target portfolio.
- [ ] Mechanical and governed-RL policies use the same execution contract and
  publish comparable baselines.
- [ ] Reports/Dossiers expose a current target portfolio and conditional order
  template with `tradingAuthority: none`.
- [ ] A realistic hourly standalone scenario and the same host-delegated
  scenario pass bounded end-to-end verification and complete regression.

## Work

- [x] Audit the current factor, target, execution, RL, and handoff contracts.
- [x] Verify the OpenAlice Workspace/Inbox/UTA authority and order vocabulary.
- [ ] Define the breaking DecisionPlan, order lifecycle, and evidence schemas.
- [ ] Implement the standalone deterministic bar-order kernel and fixtures.
- [ ] Integrate target-weight realization into the mechanical Portfolio lane.
- [ ] Integrate the shared kernel into governed RL and its baselines.
- [ ] Add current portfolio context and decision-support delivery surfaces.
- [ ] Add execution/trade/risk metrics expected by a working quant researcher.
- [ ] Verify Studio/CLI/Report/Dossier parity, complete regression, commit, and
  push.

## Findings and decisions

- 2026-07-27 — Target weights remain the answer to “how large should this
  position be?” Order/TPSL semantics realize and protect that answer; they do
  not replace portfolio construction.
- 2026-07-27 — The current Core has a clean insertion point: target weights and
  weight deltas already precede one shared `simulate_targets` accounting path.
- 2026-07-27 — Current close-target execution has no pending order, entry
  price, fill, expiry, OCO, or protective-order state and must be replaced
  rather than wrapped as if it were equivalent.
- 2026-07-27 — RL remains first-class in two roles: causal factor/state
  representation and constrained decision policy. It never owns fixed
  execution truth or future-bar access.
- 2026-07-27 — OpenAlice UTA's common order vocabulary is a useful
  compatibility target, but AutoQuant plans use weights/reference NAV and have
  no `aliceId`, account, stage, commit, approval, or push authority.

## Verification

Pending.

## Progress log

- 2026-07-27 — Plan activated after aligning the existing target-weight engine
  with the product requirement for hourly Agent decisions and persistent
  limit/TPSL protection.
- 2026-07-27 — Implementation paused while
  [[plans/agent-native-workbench-documentation]] makes the standalone
  Agent-native workbench and optional OpenAlice desk relationship canonical.
  The order-native design remains active system direction and is not
  superseded.

## Completion

Pending.
