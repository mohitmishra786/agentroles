# Portkey

## Generated File

| File | Description |
|---|---|
| `portkey-config.json` | Per-role Portkey gateway config with fallback chains |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and produces a JSON object keyed by role name:

```json
{
  "planner": {
    "strategy": "fallback",
    "targets": [
      {"provider": "anthropic", "model": "anthropic/claude-opus-4-8"},
      {"provider": "openai", "model": "openai/gpt-5.5"}
    ],
    "override_params": {"max_tokens": 4096}
  },
  "implementer": {
    "strategy": "fallback",
    "targets": [
      {"provider": "anthropic", "model": "anthropic/claude-haiku-4-5"}
    ]
  }
}
```

Each role entry has:

- `strategy` — `"fallback"` (tries each target in order, falling through on failure)
- `targets` — ordered list of `{provider, model}` objects: primary first, then fallbacks
- `override_params` — includes `max_tokens` when a cost ceiling is set

## Usage

```bash
agentroles build
# Use portkey-config.json as the gateway configuration
```

## Limitations

- Only the `fallback` strategy is generated; `single` and `loadbalance` are not used by default
- `override_params` only sets `max_tokens` based on cost ceiling — other params can be added manually
- Provider name is extracted from the `provider/model-id` string — ensure it matches Portkey's provider names
- API keys must be provided via Portkey's environment or vault; they are not included in the generated config
