# Factory

## Generated File

| File | Description |
|---|---|
| `.factory/config.yaml` | Factory configuration with droid entries per role |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and generates droid definitions for the Factory platform:

``` yaml
.factory/config.yaml

droids:

  - name: planner

    description: High-stakes reasoning, architecture decisions
    model: anthropic/claude-opus-4-8
    fallback_models:

      - openai/gpt-5.5

    max_cost_per_call: 0.50

  - name: implementer

    description: Mechanical edits once a plan exists
    model: anthropic/claude-haiku-4-5
    fallback_models:

      - openai/gpt-4o-mini

    max_cost_per_call: 0.02

cost_tracking:
  enabled: true
```

Each role becomes a droid with:

- `name` — the role name
- `description` — from `role.notes`, or a sensible default
- `model` — the role's primary model
- `fallback_models` — optional, from `role.fallback`
- `max_cost_per_call` — optional, from `role.max_cost_per_call_usd`

## Usage

```bash
agentroles build

# Factory reads .factory/config.yaml automatically from the project root

```

## Limitations

- Droid behavior, tools, and permissions are not configured — add them to the generated YAML
- The `description` field is informational only; Factory may have its own role semantics
- Cost tracking is enabled globally via a `cost_tracking.enabled: true` flag
