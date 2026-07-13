# Agentic Coding Tools — Target Research

Last researched: 14 July 2026

## Research Methodology

Systematic web searches across GitHub topics (`ai-coding-agent`, `agentic-coding`), awesome lists (`awesome-generative-ai`), and direct documentation visits for each candidate tool. Categories searched independently: CLI coding agents, AI-native IDEs, VS Code/JetBrains/Neovim/Emacs plugins, cloud autonomous agents, multi-agent frameworks, and LLM routers/gateways.

## Active Tools with Config Surfaces (Adapters Built)

### CLI/Desktop Coding Agents

| # | Tool | Description | Config Surface | Per-Role Models | Adapter |
|---|------|-------------|----------------|-----------------|---------|
| 1 | **OpenCode** (anomalyco) | OSS AI coding agent with built-in agents (build, plan) and subagents | `opencode.json` — JSON with `agents` block, `provider/model-id` syntax | Yes — full per-agent model assignment | `targets/opencode/` |
| 2 | **Claude Code** | Anthropic's agentic coding tool | `.claude/settings.json` + `.claude/agents/*.md` subagent frontmatter with `model: sonnet|opus|haiku|inherit` | Yes — per-subagent model in frontmatter, Anthropic-only | `targets/claude_code/` |
| 3 | **Aider** | Git-aware AI pair programmer in terminal | `.aider.conf.yml` — YAML with `model`, `editor-model`, `weak-model` slots | Three slots (architect/editor/weak) | `targets/aider/` |
| 4 | **Codex CLI** | OpenAI's Rust-based CLI coding agent | `.codex/` directory, `--model` flag, OAuth/subscription auth | No per-role — single model per session | `targets/codex_cli/` |
| 5 | **Gemini CLI** | Google's open-source terminal AI agent | `~/.gemini/settings.json` + `.gemini/config.yaml`, `-m` flag | No per-role — single model per session | `targets/gemini_cli/` |
| 6 | **Kilo Code** | Fork of OpenCode with 500+ models, multi-surface | Inherits OpenCode's `opencode.json` agent blocks + `.kilo/` config | Yes — full per-agent model, same as OpenCode | `targets/kilocode/` (shares OpenCode logic) |
| 7 | **Qwen Code** | Fork of Gemini CLI, multi-protocol (OpenAI/Anthropic/Gemini/Qwen) | `.qwen/agents/` directory, `--model` flag | Partial — subagent support via `.qwen/agents/` | `targets/qwen_code/` |
| 8 | **Crush** | Charmbracelet's Go-based TUI coding agent | `crush.json` — JSON with `providers` block, per-provider models | No — single model per session, Ctrl+L switcher | `targets/crush/` |
| 9 | **Cline** (CLI + VS Code) | Autonomous coding agent, multi-surface, 5M+ installs | `.cline/` project dir, `providers.json`, `.clinerules`, `-m`/`-P` flags | No — single model per session | `targets/cline/` |
| 10 | **Goose** | General-purpose AI agent in Rust (AAIF/Linux Foundation) | CLI flags + env vars for 15+ providers, desktop app | No — single model per session | `targets/goose/` |
| 11 | **OpenInterpreter** | Fork of Codex CLI, harness emulation | `~/.openinterpreter/` config, `/model` in TUI | No — single model per session | `targets/openinterpreter/` |

### IDE Plugins & Extensions

| # | Tool | Description | Config Surface | Per-Role Models | Adapter |
|---|------|-------------|----------------|-----------------|---------|
| 12 | **Continue** | OSS configurable AI assistant with declarative model roles | `config.yaml` (or `config.json`) with `models` array and explicit roles: `chat`, `edit`, `apply`, `autocomplete`, `embed`, `rerank` | Yes — the most explicit per-role model config of any tool, 6 distinct roles | `targets/continue/` |
| 13 | **Cody** (Sourcegraph) | AI coding assistant with chat and autocomplete | `.cody/` config, separate model selection for Chat vs Autocomplete, BYOK support | Partial — chat vs autocomplete split | `targets/cody/` |
| 14 | **PearAI** | Open-source AI code editor, fork of VS Code with Continue | `~/.pearai/config.json` — JSON in Continue format, supports provider + model per role | Yes — inherits Continue's per-role model config | `targets/pearai/` |
| 15 | **Zed AI** | High-performance collaborative editor with assistant panel | `~/.config/zed/settings.json` — JSON with `assistant.default_model` | No — single assistant model | `targets/zed_ai/` |
| 16 | **Qodo Gen** (formerly Codium) | Code generation + review + testing agent, 880K installs | Settings UI, multi-model support (Claude, GPT) | No — single model per session | `targets/qodo/` |
| 17 | **avante.nvim** | Cursor-like AI agent in Neovim (18k stars) | Lua `setup()` config, per-provider config, `dual_boost` two-provider mode | Partial — separate `provider` and `auto_suggestions_provider` | `targets/avante_nvim/` |
| 18 | **codecompanion.nvim** | Full AI coding platform in Neovim (6.7k stars) | Lua `setup()` config, multiple adapters, workflows, prompt library | Yes — multiple adapters with different models per workflow | `targets/codecompanion_nvim/` |
| 19 | **Ellama** (Emacs) | Full AI assistant with plan-and-act loops, subagents | Elisp config with separate providers per function: `ellama-coding-provider`, `ellama-summarization-provider`, etc. + subagent providers | Yes — most sophisticated per-role config in any editor | `targets/ellama/` |
| 20 | **gptel** (Emacs) | LLM client for Emacs, tool-use, 20+ backends | Elisp config with `gptel-make-*` functions per backend, switch per buffer | Yes — multiple backends, manual per-session switching | `targets/gptel/` |

### Multi-Agent Frameworks

| # | Tool | Description | Config Surface | Per-Role Models | Adapter |
|---|------|-------------|----------------|-----------------|---------|
| 21 | **CrewAI** | Python framework for role-playing AI agents | `config/agents.yaml` + `config/tasks.yaml`, per-Agent `llm=` config | Yes — each Agent gets its own LLM | `targets/crewai/` |
| 22 | **AutoGen** (Microsoft) | Multi-agent conversation framework | Python API with `OpenAIChatCompletionClient(model=...)` per agent, `SelectorGroupChat` with separate model | Yes — each agent gets its own `model_client` | `targets/autogen/` |
| 23 | **LangGraph** (LangChain) | Stateful multi-actor graph framework | Python API with per-node `ChatModel` binding | Yes — each graph node can use a different LLM | `targets/langgraph/` |
| 24 | **MetaGPT** | Software company SOP with PM/architect/engineer roles | `~/.metagpt/config2.yaml` — YAML with `llm` config per role | Partial — global LLM shared, roles configurable programmatically | `targets/metagpt/` |
| 25 | **OpenHands** | Self-hosted agent canvas for coding agents | `config.toml` + LLM Profiles, per-agent backend with its own model | Yes — multiple agent backends, each with own LLM profile | `targets/openhands/` |
| 26 | **Factory** | AI-native dev platform with Custom Droids | Settings config for models, Custom Droids with per-droid model assignments | Yes — per-droid model assignment | `targets/factory/` |

### LLM Routers & Gateways

| # | Tool | Description | Config Surface | Per-Role Models | Adapter |
|---|------|-------------|----------------|-----------------|---------|
| 27 | **LiteLLM** | OSS AI Gateway for 100+ LLMs | `config.yaml` — YAML with `model_list`, `litellm_params`, routing strategies | Yes — model aliases per role, fallback chains | `targets/litellm_proxy/` |
| 28 | **Portkey** | AI Gateway with integrated guardrails (1,600+ LLMs) | JSON config object with `strategy`, `targets`, `override_params`, conditional routing | Partial — conditional routing by header/criteria | `targets/portkey/` |
| 29 | **Manifest** | OSS model router for AI agents, complexity-based routing | DB-driven, API-based, routing by header (`X-Agent-Role: coder`) | Yes — header-based routing per role | `targets/manifest/` |
| 30 | **BitRouter** | Context-aware agentic LLM gateway, Rust | TOML/YAML config, agent-aware routing | Yes — context-aware per-agent model routing | `targets/bitrouter/` |
| 31 | **Infermux** | Multi-provider inference router, Go | YAML/JSON config, load balancing, cost tracking | Unknown — general router | `targets/infermux/` |

## Tools Not Adapted (With Reason)

| Tool | Reason |
|------|--------|
| **Cursor** | UI-only model selection; no machine-generatable config file |
| **Windsurf** (Cognition) | UI-only model selection; Cognition-managed model routing |
| **Devin** (Cognition) | Per-session model selection via web UI/CLI; no config file to generate |
| **GitHub Copilot Coding Agent** | Model selection managed by GitHub; Agent HQ auto-routing; no user config file |
| **Codex Cloud Agent** | Model via subscription/CLI flag; no persistent config file to generate |
| **Tabnine** | Enterprise console-based config; no file-based model-per-role surface |
| **Augment Code** | Platform UI-based; `.augment/` is rules only, not model config |
| **JetBrains AI Assistant** | IDE settings UI; no file-based per-role config |
| **Amazon Q Developer** | Winding down — stopped new sign-ups May 2026, IDE support ending 2027 |
| **Gemini Code Assist** | Individual tier ending June 18, 2026 |
| **Roo Code** | Shut down May 15, 2026 |
| **SuperAGI** | Development inactive; no config file for agentic coding |
| **Agency Swarm** | Repository 404 at test time |
| **TaskWeaver** | Archived by Microsoft Mar 23, 2026 |
| **BabyAGI** | Historical artifact; no longer maintained or used for production coding |
| **AgentGPT** | General web agent builder, not coding-specific |
| **GPT-Engineer** | Archived Apr 22, 2026; replaced by Lovable |
| **Sweep** | No machine-generatable config surface (BYOK with custom prompts only) |
| **Replit Agent** | UI-only mode selection; no config file |
| **Bolt.new** | No public model config surface documented |
| **Lovable** | Opaque model selection; platform-managed |
| **v0 (Vercel)** | Environment variables only; no multi-model role config |
| **AppMap Navie** | UI-only model selection in editor; no config file |
| **Supermaven** | Acquired by Cursor Nov 2024; tech folded into Cursor Tab |
| **Pythagora** | Docs unreachable at test time |
| **Codegen** | Docs unreachable at test time |
| **Tempo Labs** | Docs returned 404 at test time |
| **OpenRouter** | Cloud service; no local config file to generate |
| **Helicone** | Observability platform; `bifrost/` is internal, not standalone |
| **RouteLLM** | Academic research project; dormant since 2024; binary routing only |
| **Aurelio Semantic Router** | Python library, not a gateway; no config file to generate from |
| **vLLM** | Inference engine, not a router/gateway |
| **ClawRouter** | Smart/automatic routing, not role-based; no role mapping config surface |
| **Bifrost** | Internal Helicone component, not standalone |
| **Nyro** | Protocol translation proxy, not role router |
| **Olla** | Local model serving aggregation, not role router |
| **Nexus LLM Router** | Task-aware router, not role-based; Python config only |
| **Warp** | Terminal environment with built-in AI; hosts other agents but no model config to generate |
| **Plandex** | Cloud-hosted with env-var model selection; no role config surface |
| **SWE-agent** | Academic benchmark tool; superseded by mini-SWE-agent |
| **OpenClaw** | Personal AI assistant, not coding-primary |
