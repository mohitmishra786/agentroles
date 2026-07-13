# Different Models for Different Jobs: The State of Multi-LLM Orchestration in Agentic Coding Systems (Mid-2026)

*Research report — July 2026*

---

## 1. Executive Summary

Assigning different LLMs to different roles inside a coding agent — a strong reasoning model for planning, a cheaper/faster model for mechanical implementation, a third model for review — is no longer a research curiosity. By mid-2026 it is a mainstream, shipping pattern across nearly every major agentic coding surface, though the sophistication of the implementation varies enormously by vendor.

**Key findings:**

- **OpenCode is the clearest existing example of a configurable, per-agent, per-role model assignment system that works across providers.** Its `agent`/`agents` config lets you bind a specific model (from any provider, including local ones) to each primary agent (Build, Plan) and each subagent (reviewer, tester, explorer, etc.), entirely declaratively, in JSON or Markdown frontmatter.
- **Dynamic, runtime routing has moved from academic prototype to production feature in 2026.** Cognition's Devin Fusion (a "sidekick" architecture: frontier model plans/reviews, a cheaper model executes, with mid-session re-routing) reports a 35–41% cost reduction on its FrontierCode benchmark while holding quality roughly flat. Devin's older "Adaptive" router already did static tiering; Fusion adds continuous re-evaluation.
- **A mature open-source and commercial toolchain already exists for the routing/orchestration layer itself**: LiteLLM (proxy + Router + a newer built-in Auto/complexity Router), Aurelio's Semantic Router, RouteLLM (2024 academic baseline, largely superseded), vLLM Semantic Router (inference-level, ModernBERT-based reasoning/non-reasoning classification), and academic systems like MasRouter and ACRouter that formalize *multi-agent* routing (which model, which role, which collaboration topology) rather than single-call routing.
- **Proprietary IDEs (Cursor, Windsurf) give users model *choice* but only shallow, largely opaque routing control** — "Auto" modes pick a model per request behind the scenes, and neither exposes a declarative per-subagent-role config file the way OpenCode or Claude Code do.
- **The core unsolved problem is not "can you call two different models" — that's solved — it's making heterogeneous models behave consistently as collaborators**: differing tool-calling formats, context/state handoff, cache invalidation when models change mid-task, and getting genuinely mergeable code rather than merely benchmark-passing code. Cognition's own framing of Devin Fusion explicitly calls out this "looks good on benchmark, unmergeable in practice" failure mode of naive routers.
- **A universal, config-driven "model-role" layer that works across tools is a real and buildable opportunity**, but it can't be a single artifact — it has to be a *convention plus a thin adapter library*, because it must bridge the tool-defines-its-own-model-syntax problem (OpenCode's `provider/model-id`, Claude Code's `model: sonnet`, Aider's `--editor-model`, LiteLLM's `model_name`) rather than replace any of them.

**Bottom line for practitioners:** if you use OpenCode, Claude Code, or Aider today, you already have first-class, low-friction support for per-role model assignment — use it. If you build custom agent pipelines (CrewAI/AutoGen/LangGraph), per-agent model binding is native to all three frameworks. The gap is a *standard*, not a *capability*: every tool solves this problem in its own config dialect, and nothing yet lets you write one role→model map and have it work unmodified across OpenCode, Claude Code, Aider, and a LangGraph pipeline.

---

## 2. Current Landscape Analysis

### 2.1 OpenCode — the reference implementation for static, config-driven per-agent models

OpenCode's agent system is the most explicit, most portable example of "different models for different roles" available today.

- **Two built-in primary agents**: `build` (full tool access — file edits, shell) and `plan` (restricted — read/analyze/suggest, edits and shell default to "ask"). The docs explicitly frame Plan as the mode for "analyze code, suggest changes, or create plans without making any actual modifications."
- **Three built-in subagents**: `general` (parallel multi-step execution, full tools except todo), `explore` (fast, read-only), and `scout` (read-only, for cloning/inspecting external dependency repos).
- **Model binding is per-agent and cross-provider.** The `model` field takes a `provider/model-id` string (e.g., `anthropic/claude-sonnet-4-5`, `opencode/gpt-5.1-codex`), and the docs are explicit about the intent: *"Useful for using different models optimized for different tasks. For example, a faster model for planning, a more capable model for implementation."*
- **Inheritance rule**: primary agents fall back to the globally configured model if unset; subagents inherit the primary agent's model if unset. This gives a sane default while allowing full override.
- **Two config surfaces**: a single `opencode.json`/`opencode.jsonc` (with a `agent` or `agents` map) or individual Markdown files with YAML frontmatter (`.opencode/agents/*.md` or `~/.config/opencode/agents/*.md`), where the frontmatter sets `mode`, `model`, `permission`, `color`, `steps`, and the document body becomes the system prompt. Community configs (e.g., the `gotar/opencode-config` repo) build entire subagent taxonomies this way — `analyst`, `builder`, `coder`, `reviewer`, `tester` — each independently model-bound.
- **Config layering**: remote/organizational defaults → global user config → env-var custom config → project config, with later sources overriding earlier ones, and "managed settings" as an org-level override on top. This is a real multi-tenant config precedence model, not just a flat file.
- **V2 schema** (in preview) adds per-agent request header/body overlays (e.g., custom `temperature` per agent) though the current runner doesn't yet apply all of them to the outgoing request — a sign the schema is still evolving toward finer per-role control (reasoning effort variants like `claude-sonnet-4-5#high` are already supported).

**Limitation:** OpenCode's routing is entirely static/declarative. There is no first-party dynamic complexity classifier — if you want "start cheap, escalate if the task turns out to be hard," you have to build that yourself (e.g., have the Plan agent, once it sees real task complexity, dispatch to a subagent bound to a stronger model).

### 2.2 Claude Code — subagents with per-subagent model override

Claude Code's `.claude/agents/*.md` subagent system is structurally very close to OpenCode's:

- Each subagent is a Markdown file with YAML frontmatter (`name`, `description`, `tools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, etc.) and the body as system prompt.
- `model` accepts `sonnet`, `opus`, `haiku`, or `inherit`. This is Anthropic-model-only (no OpenAI/Gemini binding at the subagent level via this mechanism), which is the key contrast with OpenCode's fully cross-provider `provider/model-id` scheme.
- Automatic delegation: the orchestrating Claude model matches a task to a subagent based on the subagent's `description`, or the user can force it by name ("Use the code-reviewer agent to...").
- The SDK version of subagents supports *dynamic, runtime-defined* agents (constructing agent configs programmatically, including choosing a stronger model conditionally for e.g. "strict" reviews) — this is closer to a routing primitive than the static Markdown files.
- **Gotcha**: filesystem-based subagents load at session start only; editing the file requires a session restart (agents created via the interactive flow apply immediately).

### 2.3 Devin (Cognition) — the most sophisticated dynamic router shipping today

Devin has moved through three routing generations:

1. **Adaptive** — a per-request router that draws down quota at a fixed rate regardless of which underlying model actually serves the request, automatically sending simpler requests to lighter models. Effectively a coarse static/rule-tiered router, marketed on "you shouldn't have to think about model choice."
2. **Devin Fusion (previewed late June 2026)** — the most advanced production coding router publicly described in detail. Key architectural ideas:
   - **"Sidekick" architecture**: two agents run in parallel. A frontier model retains planning, ambiguity resolution, and final review; a cheaper "sidekick" model does the mechanical work — fetching info, skimming sources, running well-scoped sub-tasks — using context the frontier model has already cached.
   - **Mid-session dynamic re-routing**: routing decisions are re-evaluated as a task evolves, addressing the well-known failure mode where an innocuous-looking prompt ("fix xyz bug") turns out to require a full re-architecture partway through.
   - **Cache-miss avoidance**: Cognition explicitly designed around the fact that naive routing between models mid-conversation blows the KV/prompt cache, which is a major hidden cost driver most routing literature ignores.
   - **Reported results**: 35% cost reduction vs. running GPT-5.5/Opus-4.8 for every step on Cognition's own FrontierCode benchmark, at roughly matched quality (47.9 vs. 44.8/48.8 scores). When Fable 5 was available as the frontier component, cost reduction reached 41% at matched Fable-level quality. Internally, Cognition reports 88% of merged PRs during the trial were driven entirely by the automated router.
   - Cognition frames this explicitly as a critique of "conventional" routers: they "pass benchmarks but fail to write code you'd actually merge" — a useful reminder that *routing accuracy on a benchmark and routing usefulness in production are different metrics.*

**Limitation:** Devin Fusion is a closed, Cognition-only harness. There's no config file a third-party tool can adopt; the routing logic and the "what counts as escalation-worthy" judgment live entirely inside Cognition's product.

### 2.4 Cursor and Windsurf — model *choice*, not model *routing configuration*

- **Cursor**: exposes the broadest manual model menu of the mainstream IDEs (Claude, GPT, Gemini, and others) and has an "Auto" mode that silently picks a model per request without consuming premium credits — described by reviewers as convenient but opaque ("model routing opacity... you don't always know why"). There is no first-party declarative "planning agent uses X, coding agent uses Y" config file; per-role model assignment is a manual, session-level user choice, not a saved system.
- **Windsurf** (now under Cognition, post-acquisition): built around its own in-house models (SWE-1, SWE-1.5, SWE-1-mini) with flat per-message pricing instead of per-token, explicitly optimized for speed over per-task model selection. Windsurf's differentiator in this space is **Arena Mode** (blind side-by-side comparison of multiple models on the same task) rather than declarative routing — useful for *evaluating* which model to standardize on, not for *automating* per-role assignment.
- Both tools are converging toward Devin-style integration (Cognition's stated roadmap folds Devin into Windsurf), which will likely bring Fusion-style routing into the IDE over time — but as of mid-2026 that is roadmap, not shipped IDE functionality.

### 2.5 GitHub Copilot / Codex agents

- Copilot's coding agent (the asynchronous, cloud, PR-opening agent) shipped a **model picker** through 2026 (Pro/Pro+ in December 2025/February 2026, then Business/Enterprise) letting a user pick the model for that *specific delegated task* — this is task-level, not role-level, selection, and "Auto" is the default, optimizing for speed/availability rather than an explicit cost/quality tradeoff a user controls.
- GitHub's **custom agents** (`.agent.md` files under `.github/agents/`, mirrored in Visual Studio's `.agent.md` support) let a repo define named agents with their own preferred model, tools, and MCP connections — structurally similar to OpenCode/Claude Code subagent files, and a genuine per-agent model binding mechanism, but newer and less battle-tested.
- Codex (OpenAI, via the Codex CLI/app and now surfaced through Copilot as a third-party agent option) added subagent workflows in 2026 — parallel specialized agents with their own model setups combined into one response, plus custom agent creation with "tailored model setups."
- Copilot's guidance for teams explicitly recommends *manual A/B testing across agents/models* on representative tasks rather than trusting Auto for high-stakes changes — a tell that the ecosystem still lacks a good deterministic way to decide "when is a task too important to route automatically."

### 2.6 Aider — the longest-running, most mature two-model pattern in an open-source CLI coding tool

Aider's **architect/editor split** predates most of the 2026 hype and is worth treating as a proof-of-concept for the whole report's thesis:

- **Architect model**: analyzes the request and proposes a solution/plan (good use case for strong-reasoning models like o-series or Sonnet).
- **Editor model**: turns the architect's proposal into concrete file edits in a specific diff format — often a different, sometimes cheaper or format-specialized, model.
- **Weak model**: a third, separate role — used for commit messages and chat-history summarization — normally the cheapest tier.
- All three are independently configurable via CLI flags (`--model`, `--editor-model`, `--weak-model`), environment variables, or a YAML config file, and Aider ships sensible per-model defaults for editor/weak-model pairing (`model-settings.yml`) so users don't have to hand-pick a compatible editor model for every architect model.
- **Known friction** (from real GitHub issues): switching the main model via `/model` implicitly changes the editor model too, which breaks manual overrides; users have asked for independent `/editor-model` and `/weak-model` slash commands to avoid this coupling. This is a concrete, small-scale instance of the "state consistency across model swaps" problem that shows up at every scale of this pattern.

### 2.7 General multi-agent frameworks (CrewAI, AutoGen, LangGraph, Semantic Kernel)

All three mainstream open-source agent frameworks support per-agent model binding natively — the differentiator is *how explicit and fine-grained* the control is:

| Framework | Per-agent model model | Mental model | Fit for coding-role routing |
|---|---|---|---|
| **CrewAI** | Native per-agent LLM config (each `Agent` gets its own `llm=`) | Role-based "crew" of specialists (researcher/writer/critic-style) | Good for a fixed pipeline (planner → coder → reviewer agents), less good for dynamic mid-task re-routing |
| **AutoGen** (v0.4+) | Per-agent `ModelClient`/`llm_config` (each `AssistantAgent` can point at a different `config_list`) | Conversational group chat; agents message each other | Good for critique/review loops (one model drafts, another critiques) |
| **LangGraph** | Cleanest per-node model routing — each graph node is a function that can call any model | Explicit state machine / directed graph | Best fit for *conditional* routing (a node classifies task complexity, an edge routes to a cheap-model node or an expensive-model node) — this is effectively hand-rolled RouteLLM |
| **Semantic Kernel / LlamaIndex Workflows / others** | Per-step model binding also supported | Plugin/workflow-oriented | Comparable capability, smaller mindshare for coding agents specifically |

A common production pattern reported by teams building on these frameworks: use LangGraph as the top-level orchestrator with explicit state and human-approval gates, and call into a CrewAI sub-pipeline for a well-scoped content/code-generation step — i.e., **frameworks are already being mixed**, which reinforces that no single framework is "the" universal layer; routing logic tends to live at the orchestrator level regardless of which framework executes the leaf work.

### 2.8 Landscape summary table

| System | Static per-role model config | Dynamic/runtime routing | Cross-provider | Config format | Openness |
|---|---|---|---|---|---|
| OpenCode | ✅ Full (per primary agent + subagent) | ❌ (manual only) | ✅ Any provider | JSON + Markdown frontmatter | Open source |
| Claude Code | ✅ Per subagent | Partial (SDK dynamic agent creation) | ❌ Anthropic models only via `model:` field | Markdown frontmatter | Anthropic product, agent files are portable |
| Devin (Fusion) | ➖ (implicit, not user-configured) | ✅ Advanced (sidekick + mid-session re-route) | ✅ (model-agnostic per Cognition) | None exposed to user | Closed |
| Cursor | Manual per-session choice | "Auto" (opaque) | ✅ | None (no saved role config) | Closed |
| Windsurf | Manual (+ Arena compare mode) | Limited | Partial (own models + some third-party) | None | Closed |
| GitHub Copilot / Codex | Per-task picker; `.agent.md` per-agent model | "Auto" mode | ✅ (multi-provider via Copilot) | Markdown (`.agent.md`) | Semi-open (agent files portable, backend closed) |
| Aider | ✅ Architect/editor/weak-model | ❌ | ✅ | CLI flags / YAML | Open source |
| CrewAI/AutoGen/LangGraph | ✅ Per-agent/node | Buildable (esp. LangGraph) | ✅ | Python config | Open source |

---

## 3. Existing Patterns & Frameworks

### 3.1 Catalog of routing approaches

**A. Static role-based assignment** ("planner uses model A, executor uses model B")
- Examples: OpenCode agent config, Claude Code subagent `model:` field, Aider architect/editor/weak-model.
- Pros: fully predictable cost and behavior, trivial to reason about and audit, zero added latency for a routing decision, easy to version-control.
- Cons: doesn't adapt if a "simple" task turns out to be hard (or vice versa); requires the human to have good judgment about role/model fit up front.
- Maturity: **high** — this is the most production-proven pattern in the report.

**B. Dynamic/runtime routing**
- **Complexity classification** (a small model or classifier estimates task difficulty, then picks a tier): LiteLLM's Auto Router / complexity_router config, GitHub Copilot's "Auto," Devin's Adaptive.
- **Semantic routing** (embed the query, match against reference "utterance" sets per route): Aurelio's Semantic Router, vLLM Semantic Router (adds a ModernBERT classifier deciding reasoning-path vs. fast-path, reporting ~10%, and >20% in specialized domains, accuracy improvement over non-routed baselines).
- **Learned/trained routers**: RouteLLM (2024 academic baseline pairing weaker/stronger LLMs using human-preference-trained routers; per a December 2025 status note, RouteLLM itself has been dormant since August 2024, though it remains the reference baseline everyone benchmarks against), FrugalGPT (LLM cascades achieving up to 98% cost reduction via prompt adaptation + cascaded model calls), commercial learned routers (Not Diamond, Martian).
- **Contextual-bandit / online-learning routers**: 2026's newer entrants (BaRP, PILOT) update online from feedback rather than relying on a fixed classifier trained once — positioned as the next step past static classifiers, though the coding-specific ACRouter research (below) found even these still lag a context-aware agentic router on out-of-distribution tasks.
- **Cascades**: try cheap model first, escalate only on low-confidence/failure signal (FrugalGPT's core idea; also implicit in Devin Fusion's sidekick-escalates-to-frontier pattern).
- Pros: adapts per-request, captures savings statically-configured pipelines can't.
- Cons: routing decisions can be wrong (send an easy-looking-but-hard task to a weak model and waste more tokens fixing the resulting mess); adds a classification step (latency + its own cost); most classifiers are trained on chat/QA benchmarks, not agentic coding tasks specifically, and the ACRouter paper found lightweight trained classifiers overfit badly out-of-distribution on real agentic coding workloads (accuracy dropping from ~1.3% gap in-distribution to 9–21% out-of-distribution, worse than random in some setups) — a genuinely important caution against assuming a routing classifier will generalize.
- Maturity: **medium** for chat-style routing (RouteLLM-class), **early/emerging** for agentic-coding-specific routing (MasRouter, ACRouter, Devin Fusion — all 2025/2026 work).

**C. Multi-agent-system routing (routing the whole team, not just one call)**
- **MasRouter** (ACL 2025): formalizes *Multi-Agent System Routing* — a single cascaded controller decides (1) whether collaboration/multi-agent structure is even needed, (2) what roles to allocate, (3) which LLM backs each role — as one joint decision rather than three separate ones. Reported: up to 8.2% performance improvement and up to 52% cost reduction on coding benchmarks (MBPP/HumanEval), and 17–28% overhead reduction when plugged into existing MAS frameworks as a drop-in layer. This is the most directly relevant academic system to this report's "universal layer" question, because it is explicitly designed to be plug-and-play across "mainstream MAS frameworks."
- **ACRouter / Agent-as-a-Router** (2026): studies agentic *programming* tasks specifically (as opposed to single-turn coding benchmarks) and compares lightweight trained classifiers, contextual bandits, and a context-aware "Orchestrator + Memory + Verifier" agentic router. Its central finding matters for anyone building a universal router: **simple trained classifiers generalize poorly out-of-distribution on agentic coding tasks**, while a context-aware router with memory and verification holds up far better, at a real but bounded extra cost (paying for kNN memory + verifier overhead) — reported near-best performance ($13.21/task) versus a naive always-frontier baseline ($34.02/task) or a cheap trained classifier that's fast but fragile.

### 3.2 Hybrid approaches
Nearly every production system that actually ships (Devin Fusion, OpenCode's model-per-agent + human-directed subagent invocation, LiteLLM's Auto Router with a `complexity_router_default_model` fallback) is a **hybrid**: static defaults with an escape hatch for dynamic override, or dynamic routing bounded by a static fallback. Pure dynamic routing without a safe static fallback is rare in anything shipping to real users — the fallback is a risk-management necessity, not an afterthought.

---

## 4. Utility & Value Analysis

### 4.1 What the evidence actually shows

| Source | Reported benefit | Task domain |
|---|---|---|
| Devin Fusion (Cognition, FrontierCode) | 35% cost reduction, matched quality vs. frontier-only; 41% with Fable 5 | Real-world agentic coding (their own benchmark) |
| FrugalGPT | Up to 98% cost reduction via cascading | General LLM tasks (not coding-specific) |
| MasRouter | Up to 52.07% overhead reduction, 1.8–8.2% performance gain | MBPP / HumanEval (coding benchmarks) |
| MasRouter (plug-and-play mode) | 17.21–28% overhead reduction when layered onto existing MAS frameworks | Coding + general |
| vLLM Semantic Router | ~10% accuracy gain overall, >20% in specialized domains, from routing reasoning vs. non-reasoning paths | General inference-serving |
| ACRouter cost tiers (2026 arXiv) | Cheap-tier classifiers: near-DimensionBest performance at $6.81–$7.69/task vs. Always-Opus at $34.02/task | Agentic programming (OOD-aware benchmark) |

Even taking vendor-reported numbers with the appropriate grain of salt (Cognition's and academic authors' own benchmarks, not independently audited), the *direction* is highly consistent across every independent source: **mixing models in coding-agent workflows reliably saves 30–90%+ of cost depending on how aggressive the routing is, with the best-designed systems holding quality roughly flat and the worst-designed naive routers producing benchmark-passing-but-unmergeable code** (Cognition's own critique of "conventional routing").

### 4.2 Illustrative, plausible workflow economics

A representative "feature ticket" workflow, mixing roles the way OpenCode/Aider/CrewAI already support:

1. **Planning/architecture** — one call to a frontier reasoning model (e.g., a Sonnet/Opus/GPT-5.5-class model) to break the ticket into a concrete plan and file list. This is low-frequency, high-value — worth paying for quality.
2. **Code generation/editing** — many calls to a fast, cheap model (e.g., a Haiku/GPT-4o-mini/DeepSeek-Coder-class model) executing the plan file-by-file. This is high-frequency — the multiplier where savings actually compound.
3. **Verification/review** — one or two calls to a different model family than the one that wrote the code (diversity reduces correlated blind spots), checking for regressions, missing tests, and security issues.

Because step 2 dominates token volume in most real agentic sessions (many small edit/read/tool-call round-trips vs. one planning call), routing step 2 to a materially cheaper model is where the bulk of the 30–90% figures above come from — this matches Devin's own architectural rationale for putting the frontier model in a "monitor and delegate" role rather than doing every action itself.

### 4.3 Where mixing models helps least (or backfires)
- Tasks with high ambiguity that only reveal their true difficulty partway through — a naive static router picks wrong up front; this is precisely the failure mode Devin's mid-session re-routing targets.
- Tight refactors spanning many interdependent files, where switching models mid-task risks losing implicit "style" consistency — Kunal Ganglani's Cursor/Windsurf comparison notes this concretely: two different models given the same instructions produce differently-styled code, which matters for long-term codebase consistency even when both outputs are "correct."
- Any workflow where cache-locality matters a lot (long agentic sessions with large cached context) — swapping models forces a cache miss, which can erase some or all of the token-cost benefit of using a cheaper model, a point Cognition explicitly designed Devin Fusion around.

---

## 5. Gaps & Pain Points

1. **No standard config format.** OpenCode's `provider/model-id` string, Claude Code's `model: sonnet|opus|haiku|inherit`, Aider's `--editor-model`/`--weak-model` flags, LiteLLM's `model_name` + `litellm_params.model`, and CrewAI/AutoGen's Python `llm=`/`config_list` objects are five different vocabularies for the same underlying idea. A role→model mapping written for one tool is not portable to another without a translation layer.
2. **Vendor lock-in at the routing-intelligence layer, not just the model layer.** Devin Fusion's actual routing logic (when to escalate, how to avoid cache misses, how to judge "mergeable" quality) is Cognition's proprietary IP — being "model-agnostic" about *which LLMs* you can route between doesn't mean the *routing decision logic* is open or portable.
3. **Dynamic routers trained on general/chat benchmarks don't generalize to agentic coding.** The ACRouter findings on OOD collapse for lightweight classifiers are the clearest evidence in this research that "just drop in RouteLLM/a generic complexity classifier" is not a safe default for a coding-specific universal layer — coding-agent routing needs coding-agent-specific training data and evaluation, not repurposed chat routers.
4. **State/context handoff between models is unsolved in general.** Different providers' tool-calling schemas, streaming formats, and function-calling conventions differ enough that a naive "swap the model" mid-conversation risks malformed tool calls, lost reasoning traces, or silently dropped context (LiteLLM's own "context-aware fallback" feature — stripping unsupported params like `response_format` before switching providers — exists specifically because this class of bug is common enough to need first-party handling).
5. **Cache economics are routing-model-specific and not exposed uniformly.** Prompt/KV-cache benefits (a major real-world cost lever) are provider-specific in mechanics and pricing, and a router optimizing purely for "cheapest model for this step" can easily be a net cost *increase* once cache invalidation from switching providers is priced in — this is a genuinely underexplored problem in most public routing literature, which optimizes headline "cost per model" rather than "cost per session including cache effects."
6. **Observability/cost-tracking is fragmented.** Gateways (LiteLLM, Portkey, Requesty, OpenRouter) each have their own cost-tracking/tracing dashboards; none of them natively understand "this call was the Plan-role vs. this call was the Build-role" unless you thread that metadata through yourself (e.g., LiteLLM per-agent request header overlays, which OpenCode's V2 schema is only now starting to define but doesn't yet fully apply).
7. **Quality auditing for routing decisions is manual and ad hoc.** GitHub's own Copilot guidance recommends manually spot-checking 1-in-10 tasks across models/agents to calibrate trust — there's no standardized, automated "did this routing decision actually produce mergeable code" feedback loop analogous to Cognition's FrontierCode benchmark, generalized across tools.
8. **Local/on-device models are supported unevenly.** LiteLLM+Ollama stacks demonstrate a workable pattern (cost break-even in ~2 weeks at 5K queries/day per one practitioner's write-up), but native agentic coding tools (Cursor, Windsurf, Devin, Copilot) offer little to no first-class local-model routing story — it's mostly a DIY LiteLLM-proxy pattern layered in front of a tool that thinks it's talking to a single cloud API.

---

## 6. Opportunity: A Universal Framework/Layer

### 6.1 What "universal" can realistically mean

A genuinely universal solution can't be a new agent runtime competing with OpenCode/Claude Code/Aider/Cursor — that's a nonstarter for adoption. The realistic shape is:

**A config convention + a thin proxy/adapter, not a new framework.**

- **Config convention**: a small, tool-agnostic YAML/JSON schema mapping *semantic roles* (`planner`, `implementer`, `reviewer`, `tester`, `summarizer`) to model identifiers, cost tiers, and fallback chains — designed to be *translated into* each tool's native format (an OpenCode `opencode.json` agent block, a Claude Code subagent frontmatter file, Aider CLI flags, a LiteLLM `model_list`) rather than replacing any of them.
- **Adapter/generator, not a runtime**: a small CLI/library that reads the universal config and emits the tool-specific files OpenCode/Claude Code/Aider actually consume, plus a LiteLLM proxy config for anything that just wants an OpenAI-compatible endpoint per role.
- **Routing intelligence as an optional, pluggable layer behind an OpenAI-compatible proxy** (i.e., build on LiteLLM/vLLM Semantic Router rather than reinventing them) — the static role-map is the default, the dynamic classifier is opt-in and clearly labeled as a work-in-progress for coding-specific tasks given the ACRouter OOD findings above.

### 6.2 Recommended config schema

```yaml
# agentroles.yaml — a tool-agnostic role→model map
version: 1

roles:
  planner:
    primary: anthropic/claude-opus-4-8
    fallback: [openai/gpt-5.5, anthropic/claude-sonnet-5]
    max_cost_per_call_usd: 0.50
    notes: "High-stakes reasoning, architecture decisions, ambiguity resolution."

  implementer:
    primary: anthropic/claude-haiku-4-5
    fallback: [openai/gpt-4o-mini, deepseek/deepseek-coder]
    max_cost_per_call_usd: 0.02
    notes: "Mechanical edits once a plan exists. High call volume."

  reviewer:
    primary: openai/gpt-5.5          # deliberately a different vendor than implementer
    fallback: [anthropic/claude-sonnet-5]
    notes: "Model-diversity review reduces correlated blind spots."

  tester:
    primary: anthropic/claude-haiku-4-5
    fallback: [openai/gpt-4o-mini]

  summarizer:
    primary: anthropic/claude-haiku-4-5

routing:
  mode: static            # static | dynamic | hybrid
  dynamic:
    enabled: false         # opt-in; coding-specific classifiers are immature (see Section 5)
    classifier: vllm-semantic-router
    escalate_on: ["low_confidence", "test_failure", "plan_revision"]
    cache_aware: true       # avoid switching provider mid-session unless escalation justifies the cache-miss cost

observability:
  cost_tracking: true
  tag_calls_with_role: true   # every outgoing request carries role= metadata for gateway dashboards

targets:                       # which tool-specific files to generate from this one source
  - opencode: ./opencode.json
  - claude_code: ./.claude/agents/
  - aider: ./.aider.conf.yml
  - litellm_proxy: ./litellm-config.yaml
```

### 6.3 Routing strategy recommendation

- **Default to static.** Given the OOD-generalization problems documented for coding-specific dynamic routers (ACRouter findings), a universal layer's *safe default* should be the human-authored role map above, not an auto-classifier.
- **Offer dynamic routing as an explicit opt-in**, built on cache-aware, coding-domain-tuned classifiers (following the vLLM Semantic Router / ACRouter research direction) rather than repurposed general-purpose routers like the original RouteLLM.
- **Escalation over classification** where possible: rather than trying to classify difficulty up front (hard, and shown to generalize poorly), prefer Devin Fusion's approach — start cheap, escalate on concrete signals (test failures, low self-reported confidence, a plan revision mid-task) — this sidesteps the up-front-classification generalization problem entirely.

### 6.4 Integration approaches for existing tools

| Tool | How the universal layer integrates | Friction |
|---|---|---|
| OpenCode | Generate/patch `opencode.json`'s `agent`/`agents` block directly — near-perfect schema match already | Very low |
| Claude Code | Generate `.claude/agents/*.md` frontmatter (`model: sonnet\|opus\|haiku`) — Anthropic-only unless routed via a proxy `ANTHROPIC_BASE_URL` override to LiteLLM for cross-provider subagents | Low–medium |
| Aider | Generate `--model` / `--editor-model` / `--weak-model` flags or `.aider.conf.yml` | Low |
| Cursor/Windsurf | No config surface to target — best you can do is document manual model choices per workflow, or proxy their API base if the tool supports a custom endpoint | High (closed surface) |
| CrewAI/AutoGen/LangGraph | Generate the Python `llm=`/`config_list` per agent/node directly from the role map | Low |
| GitHub Copilot custom agents | Generate `.agent.md` files under `.github/agents/` | Low–medium (newer surface) |
| Anything OpenAI-compatible | Point at a generated LiteLLM proxy config; the proxy itself performs role-aware routing/fallback/cost-tracking | Very low (this is what LiteLLM is *for*) |

### 6.5 Support for local models, cost tracking, observability
- Build the proxy layer on **LiteLLM** (self-hostable, 100+ providers, native fallback/cooldown/retry, per-key/team routing rules, existing cost-pricing table) rather than reinventing a gateway — this is the single clearest "don't rebuild what already exists" recommendation from the research.
- Local models slot in as just another `model_list` entry (LiteLLM + Ollama is already a proven, documented pattern with real break-even economics for moderate query volumes).
- Tag every request with `role=` metadata so existing gateway dashboards (LiteLLM's own UI, or piping logs to Portkey/Helicone) can slice cost/latency/quality by *role*, not just by raw model name — this is a small addition to existing tools, not new infrastructure.

---

## 7. Proposed Implementation Sketch

### 7.1 High-level components

```
┌─────────────────────────────┐
│   agentroles.yaml (source)  │   <- human-authored role→model map
└──────────────┬───────────────┘
               │  "compile"
               ▼
┌─────────────────────────────────────────────────────────┐
│  Adapter/Generator CLI (thin, open-source)                │
│  - emits opencode.json agent block                         │
│  - emits .claude/agents/*.md                                │
│  - emits .aider.conf.yml                                     │
│  - emits litellm-config.yaml (proxy, for anything else)       │
└──────────────┬───────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  LiteLLM Proxy (existing OSS project, not reinvented)      │
│  - model_list per role, with fallbacks                       │
│  - optional Auto/complexity router (opt-in, off by default)   │
│  - role= tag on every request for cost/latency dashboards      │
└──────────────┬───────────────────────────────────────────┘
               │  OpenAI-compatible endpoint
               ▼
      OpenCode / Claude Code / Aider / CrewAI / LangGraph / …
```

### 7.2 Example generated LiteLLM config (from the role map above)

```yaml
model_list:
  - model_name: role-planner
    litellm_params:
      model: anthropic/claude-opus-4-8
      metadata: {role: planner}
    fallbacks: [role-planner-fallback]
  - model_name: role-implementer
    litellm_params:
      model: anthropic/claude-haiku-4-5
      metadata: {role: implementer}
    fallbacks: [role-implementer-fallback]
  - model_name: role-reviewer
    litellm_params:
      model: openai/gpt-5.5
      metadata: {role: reviewer}

router_settings:
  routing_strategy: cache-aware-static   # custom strategy: avoid mid-session provider swap unless escalation triggers fire
  num_retries: 2
  cooldown_time: 30
```

### 7.3 Escalation pseudocode (Devin-Fusion-style, cache-aware)

```python
def route_step(task_state, role_map):
    role = task_state.current_role          # e.g. "implementer"
    model = role_map[role].primary

    if task_state.escalation_signal in (
        "test_failure", "low_confidence", "plan_revision_requested"
    ):
        # Escalate only on concrete signal, not upfront classification
        model = role_map["planner"].primary
        task_state.log("escalated", from_role=role, reason=task_state.escalation_signal)

    # Cache-awareness: don't escalate for a single trivial retry if the
    # cost of a cache miss exceeds the expected benefit of a stronger model
    if model != task_state.last_model_used and not task_state.escalation_justifies_cache_miss():
        model = task_state.last_model_used

    return call_llm(model, task_state.context, role=role)  # role= tagged for observability
```

### 7.4 Suggested tech stack
- **Proxy/routing core**: LiteLLM (self-hosted) — mature, OSS, wide provider support, existing fallback/cost-tracking primitives.
- **Optional semantic/dynamic layer**: Aurelio Semantic Router or vLLM Semantic Router, used opt-in and scoped to non-critical routing decisions given known OOD generalization risk for coding-specific classifiers.
- **Adapter/generator CLI**: small, single-purpose, open-source (Python or Go), whose *only* job is translating `agentroles.yaml` into each tool's native config — deliberately not a runtime, to minimize maintenance burden and maximize the chance tool maintainers will accept PRs supporting the format natively over time.
- **Observability**: LiteLLM's own dashboards or exported logs into Portkey/Helicone-style tools, sliced by the injected `role=` tag.

---

## 8. Challenges, Risks & Mitigations

| Challenge | Risk | Mitigation |
|---|---|---|
| Tool-specific config dialects drift over time (OpenCode, Claude Code, Copilot's `.agent.md` all evolving fast in 2026) | Adapter breaks on every tool update | Treat the adapter as a thin, versioned translation layer with tests against each tool's schema; accept it will need frequent small PRs, not a one-time build |
| Dynamic routers misclassify agentic coding tasks (documented OOD failure) | Silent quality degradation that looks fine on a benchmark but produces unmergeable code (Cognition's own critique) | Default to static role maps; treat dynamic routing as escalation-triggered, not upfront-classified; require human-in-the-loop spot-checks (as GitHub itself recommends) before trusting a new dynamic route in production |
| Model-switch cache misses erase cost savings | A routing decision that looks cheaper on paper is actually more expensive once cache invalidation is counted | Cache-aware routing logic (don't switch model mid-session unless an escalation signal justifies it) — directly modeled on Devin Fusion's design rationale |
| Tool-calling/function-calling format differences across providers | Malformed tool calls or dropped context when swapping models mid-task | Route through an OpenAI-compatible proxy (LiteLLM) that already handles context-aware parameter stripping/adaptation between providers, rather than hand-rolling per-provider adapters |
| Vendor lock-in at the *routing intelligence* layer even if models are swappable | "Model-agnostic" marketing doesn't guarantee the routing logic itself is portable or auditable | Keep the routing rules and role map in a plain, versioned, human-readable file the user owns — not inside a vendor's closed harness |
| Privacy/data residency when mixing local + cloud models | Sensitive code sent to the wrong tier (e.g., a "cheap" cloud model that isn't covered by the same DPA as the primary vendor) | Make provider/region an explicit, auditable field per role in the config (not inferred), and support local models as first-class fallback options for sensitive roles |
| Adoption friction — asking every tool maintainer to support a new standard | Standards without buy-in die | Ship the adapter as *pure config generation*, imposing zero runtime dependency on the target tools; a user who ignores the universal layer entirely and just edits `opencode.json` directly loses nothing — the universal layer is additive, not a lock-in itself |

---

## 9. Recommendations & Next Steps

1. **Building a universal role-map convention + adapter is worthwhile, but should be positioned as a config generator, not a new agent runtime.** The market already has enough runtimes (OpenCode, Claude Code, Aider, CrewAI, LangGraph, AutoGen); another one competing for mindshare would fail. A thin, boring, well-tested translation layer that "just" turns one YAML file into the five formats you actually need has a realistic adoption path, especially for teams already standardizing configs across multiple tools (e.g., a team using both Claude Code locally and Copilot cloud agents).
2. **Who benefits most**: teams running *more than one* coding agent tool across a codebase or org (increasingly common — GitHub itself now lets you assign the same task to Copilot, Claude, and Codex side by side), and teams with cost-governance requirements wanting a single source of truth for "what model can touch what kind of task," independent of which tool a given developer prefers.
3. **Open-source potential is high** for the adapter/generator and the static role-map schema; genuinely differentiated IP would need to be in the *dynamic routing/escalation logic tuned for agentic coding specifically* (following the ACRouter/MasRouter research direction) — that's the part worth investing real engineering effort in, since the generic chat-routing tooling (RouteLLM-class) is known to generalize poorly here.
4. **Prioritized roadmap**:
   - **Phase 1 (weeks):** ship the static role-map schema + adapter targeting OpenCode, Claude Code, and Aider (the three tools with the cleanest existing per-role model config surfaces) plus a LiteLLM proxy config generator for everything else.
   - **Phase 2 (1–2 months):** add CrewAI/LangGraph/AutoGen Python-config generation; add role-tagged cost observability on top of LiteLLM.
   - **Phase 3 (2–4 months, research-heavy):** prototype an opt-in, coding-domain-tuned escalation classifier (cache-aware, signal-triggered rather than upfront-classified, following the Devin Fusion / ACRouter design principles), evaluated against a held-out set of real agentic coding tasks — not a repurposed chat-routing benchmark — before recommending it as a default for anyone.
   - **Ongoing:** track Cursor/Windsurf/Copilot for any move toward an exposed, declarative per-role config surface (their current model-picker-only UX is the biggest ecosystem gap this layer cannot currently reach) and add adapters the moment one appears.

---

## 10. References & Sources

- OpenCode — Agents & Config docs: https://opencode.ai/docs/agents/ , https://opencode.ai/docs/config/
- OpenCode V2 agents (schema preview): https://v2.opencode.ai/agents
- OpenCode community config example: https://github.com/gotar/opencode-config
- Devin Fusion announcement (Cognition): https://cognition.com/blog/devin-fusion
- Devin Adaptive docs: https://docs.devin.ai/desktop/adaptive
- ZenML LLMOps case study on Devin Fusion: https://www.zenml.io/llmops-database/multi-model-routing-for-cost-efficient-ai-code-generation
- LiteLLM Router / Auto Router / Fallbacks docs: https://docs.litellm.ai/docs/routing-load-balancing , https://docs.litellm.ai/docs/proxy/auto_routing , https://docs.litellm.ai/docs/proxy/reliability
- Aurelio Semantic Router: https://docs.aurelio.ai/semantic-router/get-started/introduction , https://github.com/aurelio-labs/semantic-router
- vLLM Semantic Router: https://vllm-semantic-router.com/
- "When to Reason: Semantic Router for vLLM" (arXiv): https://arxiv.org/html/2510.08731v1
- RouteLLM / FrugalGPT overview: https://github.com/Not-Diamond/awesome-ai-model-routing
- MasRouter (ACL 2025): https://aclanthology.org/2025.acl-long.757/ , https://arxiv.org/abs/2502.11133
- Agent-as-a-Router / ACRouter (2026, arXiv): https://arxiv.org/html/2606.22902
- Claude Code subagents docs: https://code.claude.com/docs/en/sub-agents , https://claude.com/blog/subagents-in-claude-code
- Claude Agent SDK subagents: https://platform.claude.com/docs/en/agent-sdk/subagents
- Aider chat modes / advanced model settings: https://aider.chat/docs/usage/modes.html , https://aider.chat/docs/config/adv-model-settings.html
- CrewAI vs LangGraph vs AutoGen comparisons: https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen , https://dev.to/hemangjoshi37a/crewai-vs-langgraph-vs-autogen-which-framework-for-production-ai-agents-1ggl
- Cursor vs Windsurf 2026 comparisons: https://tech-insider.org/cursor-vs-windsurf-2026/ , https://www.verdent.ai/guides/windsurf-vs-cursor-2026
- GitHub Copilot coding agent model picker: https://github.blog/changelog/2026-02-19-model-picker-for-copilot-coding-agent-for-copilot-business-and-enterprise-users/ , https://github.blog/ai-and-ml/github-copilot/whats-new-with-github-copilot-coding-agent/
- Visual Studio custom agents (`.agent.md`): https://devblogs.microsoft.com/visualstudio/visual-studio-march-update-build-your-own-custom-agents/
- LLM gateway comparisons (LiteLLM/Portkey/OpenRouter/Requesty, 2026): https://www.requesty.ai/blog/best-llm-routing-platforms-compared-2026-requesty-portkey-litellm-openrouter , https://www.truefoundry.com/blog/openrouter-vs-portkey

*Note on Fable 5 / Mythos references above: Anthropic suspended access to Claude Fable 5 and Claude Mythos 5 on June 12, 2026 under a U.S. Department of Commerce export-control directive, and restored access July 1, 2026 after the controls were lifted. Benchmark figures referencing Fable 5 in this report reflect data collected before the suspension, as noted by the sources themselves.*
