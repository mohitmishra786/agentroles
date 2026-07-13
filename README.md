# agentroles

> "The difference between a good tool and a great tool is how much thinking it saves you for free."
> — borrowed from a conversation with a colleague who was tired of editing five config files every time we swapped a model

Here's the problem: every single agentic coding tool (OpenCode, Claude Code, Aider, LiteLLM) lets you assign different models to different roles. That's table stakes now. The real friction is that they each invented their own config dialect. OpenCode does `provider/model-id` in JSON. Claude Code does `model: sonnet` in YAML frontmatter. Aider does `--editor-model` flags and a `.aider.conf.yml`. None of them talk to each other.

So you end up hand maintaining the same "planner uses Opus, implementer uses Haiku" logic in three or four places. You push a model change to OpenCode, forget Claude Code, and suddenly your review agent is running on a model you didn't intend. This isn't speculation. This is what happens in practice when you have more than one tool in your workflow.

**agentroles** is a single YAML file where you describe which model handles which role, and then it generates the native configs for every tool you use. You never hand write `opencode.json` agent blocks or Claude Code subagent frontmatter again. Delete agentroles entirely and every file it generated keeps working. It's a config compiler, not a runtime you have to keep alive.

## If you're impatient

```bash
pip install agentroles
agentroles init
```

That asks which tools you use, drops a reasonable `agentroles.yaml` into your project root, and immediately generates all the tool specific configs. If you like what you see, `agentroles build` regenerates them on demand. `agentroles validate` checks for the common gotchas like assigning a non Anthropic model to a Claude Code subagent.

What you get out:

| Tool | File Generated | What it does |
|---|---|---|
| OpenCode | `opencode.json` | Per role `agent` block with full `provider/model-id` strings |
| Claude Code | `.claude/agents/*.md` | One subagent file per role, with correct YAML frontmatter |
| Aider | `.aider.conf.yml` | `model`, `editor-model`, `weak-model` mapped from planner/implementer/summarizer |
| LiteLLM proxy | `litellm-config.yaml` | Per role `model_name` entries with fallbacks and role metadata tags |

## The one YAML file

```yaml
version: 1

roles:
  planner:
    primary: anthropic/claude-opus-4-8
    fallback: [openai/gpt-5.5]
    max_cost_per_call_usd: 0.50
    notes: "Design decisions, ambiguity resolution. Worth paying for quality here."

  implementer:
    primary: anthropic/claude-haiku-4-5
    fallback: [openai/gpt-4o-mini]
    max_cost_per_call_usd: 0.02

  reviewer:
    primary: openai/gpt-5.5

routing:
  mode: static

observability:
  cost_tracking: true
  tag_calls_with_role: true

targets:
  - opencode: ./opencode.json
  - claude_code: ./.claude/agents/
  - aider: ./.aider.conf.yml
  - litellm_proxy: ./litellm-config.yaml
```

That's it. Roles can have fallbacks, cost ceilings, and notes. The routing block defaults to static (just generate configs) with an opt in dynamic mode if you want runtime escalation. Everything is optional except `version` and `roles`.

## Schema reference

### Top level

| Field | Type | Required | Notes |
|---|---|---|---|
| `version` | integer | yes | Only `1` exists today. The `migrate` command exists for when we add v2. |
| `roles` | mapping | yes | One entry per role name. Must have at least one. |
| `routing` | object | no | Static by default. |
| `observability` | object | no | Cost tracking and metadata tagging. |
| `targets` | list | no | Which tools to generate configs for and where to put the output. |

### Per role

| Field | Type | Required | Notes |
|---|---|---|---|
| `primary` | string | yes | Model in `provider/model-id` format. `anthropic/claude-sonnet-5`, `openai/gpt-5.5`, `deepseek/deepseek-coder`, etc. |
| `fallback` | string[] | no | Ordered list. The LiteLLM proxy target wires these into native fallback chains. |
| `max_cost_per_call_usd` | number | no | Per call cost ceiling. The LiteLLM proxy enforces this. |
| `notes` | string | no | Free text. Gets threaded into generated agent descriptions where the target tool supports it. |

### Routing

| Field | Type | Default | Notes |
|---|---|---|---|
| `routing.mode` | string | `static` | `static` (generate configs only) or `dynamic` (enable runtime escalation). |
| `routing.dynamic.enabled` | boolean | `false` | Must be explicitly turned on. |
| `routing.dynamic.escalate_on` | string[] | `[test_failure, low_confidence]` | Which concrete signals trigger moving to the next fallback model. |
| `routing.dynamic.cache_aware` | boolean | `true` | Suppress escalation if switching providers would blow the KV cache and the signal isn't severe enough to justify it. |

### Observability

| Field | Type | Default | Notes |
|---|---|---|---|
| `observability.cost_tracking` | boolean | `true` | Enables cost tracking callbacks in the LiteLLM proxy config. |
| `observability.tag_calls_with_role` | boolean | `true` | Adds `role=` metadata to every outgoing request. Lets you slice cost dashboards by role. |

## What each target supports

Tools aren't equal in what they let you configure. This table is honest about the gaps.

| | OpenCode | Claude Code | Aider | LiteLLM proxy |
|---|---|---|---|---|
| Per role static model assignment | Full | Full, Anthropic only via `model:` field | 3 slots only (planner, implementer, summarizer) | Full, any provider |
| Cross provider models | Any provider | Only via `model: inherit` + LiteLLM proxy routing | Any provider | Any provider |
| Dynamic escalation | Via opt in routing mode | Not supported natively | Not supported | Via `router_settings` block |
| Fallback chains | Not generated natively | Not generated natively | Not supported | Full native fallback chains |
| Cost ceilings | Not enforced by OpenCode | Not enforced by Claude Code | Not enforced by Aider | Enforced via `max_cost_per_call_usd` |
| Role metadata tagging | Not natively | Not natively | Not natively | Full `metadata.role` tagging |

### Claude Code: the Anthropic constraint explained

Claude Code's `model:` field in subagent frontmatter only accepts `sonnet`, `opus`, `haiku`, or `inherit`. That's it. No OpenAI models, no Gemini, no DeepSeek.

If you assign a non Anthropic model to a role and you have `claude_code` as a target, agentroles generates the file with `model: inherit` and a clear comment at the top explaining the situation. It tells you to either pick an Anthropic model for that role or route it through the LiteLLM proxy instead. It never silently drops the model or fabricates a mapping that doesn't exist.

### Aider: three slots, no more

Aider has exactly three model slots: `--model` (main/architect), `--editor-model` (mechanical editor), and `--weak-model` (summaries and commit messages). We map `planner -> model`, `implementer -> editor-model`, `summarizer -> weak-model` by convention.

If your `agentroles.yaml` defines more roles than those three, the extras get reported explicitly in the build output: "these roles are not representable in Aider, skipping." You'll see exactly which ones and why. They're not silently dropped.

## Routing modes

### Static (the default)

Reads the YAML, generates configs. No runtime process, no network calls, nothing to keep alive. This is where you should start. It's deterministic and you can check the generated files into version control.

### Dynamic / escalation (opt in)

When you set `routing.mode: dynamic` and `routing.dynamic.enabled: true`, each task starts on the role's primary model and only moves to the next fallback when something concrete happens: a test fails, the model self reports low confidence, or the plan needs revision mid task.

This is signal triggered escalation, not upfront classification. We deliberately avoid trying to guess task difficulty before the model even starts. That approach generalizes poorly on real agentic coding tasks (the ACRouter paper published in 2026 found simple classifiers degrading by 9-21% accuracy out of distribution, sometimes worse than random).

With `cache_aware: true`, the router suppresses cross provider escalation for low severity signals. Switching from Anthropic to OpenAI mid session dumps your KV cache on both sides. That cost can easily erase whatever savings you hoped to get from using a cheaper fallback. The router only allows the switch when the signal severity justifies it (test failure, plan revision).

The escalation runtime is small, well tested, and completely optional. If you disable it, everything behaves identically to static mode with zero overhead.

## CLI commands

```bash
agentroles init        # Interactive setup. Picks targets, writes agentroles.yaml, generates configs.
agentroles build       # Regenerates all target configs from an existing agentroles.yaml.
agentroles validate    # Schema lint + target compatibility warnings.
agentroles migrate     # No-op for schema v1. Exists so the schema version field has a purpose.
```

`init` accepts `-t` flags to skip the interactive prompts: `agentroles init -t opencode -t aider -y`.

`build` and `validate` accept `-c` to point at a non default config path.

## npm wrapper

If you'd rather use npx than manage a Python environment:

```bash
npx agentroles init
```

The npm package shells out to the Python package. It checks for Python 3.11+ on your PATH and installs the pip package if missing. This is a convenience wrapper, not a reimplementation. The tradeoff is you still need Python available.

## Installation from source

```bash
git clone https://github.com/mohitmishra786/agentroles
cd agentroles
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

Apache 2.0. See [LICENSE](LICENSE).
