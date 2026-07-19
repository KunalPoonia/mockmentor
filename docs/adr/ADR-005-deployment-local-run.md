# ADR-005: Distribute as a local run, not a hosted deployment

**Status:** Accepted
**Date:** 2026-07 (Week 4, deployment planning)

## Context

The project asks for a "live URL" people can visit. But MockMentor runs a local
LLM (ADR-002), which shapes what deployment can realistically mean:

- A local LLM needs a GPU; **free cloud tiers can't host it**, and a GPU cloud
  VM costs real money — which isn't in budget for this project.
- The tunnel approach (run locally, expose via ngrok / Cloudflare Tunnel) gives
  a public URL, but that URL **only works while the developer's laptop is on and
  the app is running** — which isn't practical to guarantee here.

So the two "live URL" paths each have a blocking constraint: cloud costs money
we don't have, and an always-on tunnel needs a machine we can't keep running.

## Decision

**Distribute MockMentor as a one-command local run**, not an always-on hosted
service. The deliverable is: clone the repo, run `start.bat`, open
`http://localhost:5000`. To make that genuinely one-command, `start.bat`
**self-bootstraps**:

1. Creates the virtual environment if it's missing.
2. Installs/repairs dependencies from `requirements.txt` when anything required
   can't be imported.
3. Warns clearly if the ChromaDB store hasn't been built or Ollama isn't
   running, with the exact command to fix it.
4. Starts the Flask server.

A short recorded walkthrough (Loom) can stand in as "proof it works" for anyone
who can't run it locally, and can be added later if desired.

## Options considered

- **A — Always-on tunnel (ngrok / Cloudflare) (rejected).** Satisfies "live URL"
  literally, but depends on the laptop being on 24/7 — not feasible here.
- **B — GPU cloud VM (rejected).** A "real" deployment, but a 7–8B model needs a
  paid GPU instance outside free tiers. No budget.
- **C — Hybrid: hosted small model for the public demo only (rejected).**
  Reintroduces a metered API key (the cost/billing risk ADR-002 avoids) and adds
  a second code path to maintain.
- **D — One-command local run + optional recorded walkthrough (chosen).** Honest
  about what the project is (a fully-local tool), zero cost, and reproducible by
  anyone with the prerequisites. Trades a clickable public URL for a low-friction
  local setup.

## Consequences

**Positive**
- Zero hosting cost and no dependency on keeping a machine online.
- Keeps the "fully local, zero API cost, private" story intact end-to-end
  (consistent with ADR-002).
- `start.bat` self-bootstrapping means a fresh clone runs with one action — no
  manual venv/pip steps for the user.

**Negative / tradeoffs**
- **No always-on public URL.** Anyone evaluating the project must either run it
  locally (needs Python, Ollama, and the pulled model) or watch the recorded
  walkthrough. This is stated plainly in the README so it isn't mistaken for
  hosted infrastructure.
- Two external prerequisites can't be auto-installed by `start.bat`: **Ollama**
  (with `qwen3:8b` pulled) and the **OSTEP PDF** (gitignored for copyright). The
  script detects and explains both rather than failing silently.
- First run is slow: creating the venv, installing dependencies, and the first
  model load all happen up front.

## Related

- ADR-002 (running the model locally is what forces this deployment shape).
