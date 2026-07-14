# LiteLLM Proxy Target

Generates a `litellm-config.yaml` file with per-role model entries, fallback chains, cost ceilings, and role metadata tags.

## What gets generated

```yaml
model_list:

  - model_name: role-planner

    litellm_params:
      model: anthropic/claude-opus-4-8
      metadata:
        role: planner
        tags: ["agentroles", "planner"]
      max_cost_per_call_usd: 0.50
    fallbacks:

      - role-planner-fallback-0
  - model_name: role-planner-fallback-0

    litellm_params:
      model: openai/gpt-5.5
      metadata:
        role: planner
        tags: ["agentroles", "planner", "fallback"]
```

When dynamic routing is enabled, a `router_settings` block is included with
`cache-aware-static` strategy, retry and cooldown settings.

## Features

- Each role gets a primary `model_name` entry and one entry per fallback
- Fallback chains use named references for LiteLLM native fallback resolution
- `max_cost_per_call_usd` from agentroles.yaml maps directly to LiteLLM's cost enforcement
- `metadata.role` and `metadata.tags` enable cost dashboard slicing by role
- Dynamic mode adds `router_settings` with retry/cooldown configuration

## Limitations

None. The LiteLLM proxy is the universal fallback target. Any tool that speaks
OpenAI-compatible HTTP can point at the generated proxy config and get
per-role model routing without any tool-side changes.

## Usage

```yaml
targets:

  - litellm_proxy: ./litellm-config.yaml

```

Start the proxy with: `litellm --config litellm-config.yaml`
