# OpenHands

## Generated File

| File | Description |
|---|---|
| `config.toml` | TOML configuration with per-role LLM profile sections |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and generates TOML LLM profile entries:

```toml
config.toml

[llm.planner]
model = "anthropic/claude-opus-4-8"
api_key = "${LLM_API_KEY}"

[llm.implementer]
model = "anthropic/claude-haiku-4-5"
api_key = "${LLM_API_KEY}"
```

Each role gets its own `[llm.<role-key>]` TOML section with:

- `model` — the role's primary model in `provider/model-id` format
- `api_key` — `${LLM_API_KEY}` environment variable reference

Role names are normalized: spaces become hyphens and the name is lowercased to form the TOML section key.

## Usage

```bash
export LLM_API_KEY=your-api-key
agentroles build
# Start OpenHands — it reads config.toml from the working directory
```

## Limitations

- `api_key` uses a single environment variable for all profiles — manual adjustment needed for multi-provider setups
- No cost tracking, rate limiting, or retry configuration is generated
- Fallback models from `agentroles.yaml` are not represented in the OpenHands config
- The provider prefix in `model` must be resolvable by OpenHands' model resolution logic
