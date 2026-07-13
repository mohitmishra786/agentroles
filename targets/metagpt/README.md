# MetaGPT

## Generated File

| File | Description |
|---|---|
| `.metagpt/config2.yaml` | MetaGPT configuration with per-role LLM blocks mapped to software company roles |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and maps each role to MetaGPT's software company role system:

| agentroles role | MetaGPT role |
|---|---|
| `planner`, `pm` | `PM` |
| `architect` | `Architect` |
| `implementer`, `engineer` | `Engineer` |
| `tester`, `qa` | `QA` |
| `reviewer` | `Reviewer` |
| any other role | `Custom_<rolename>` |

Each mapped role gets an `llm` section with:
- `api_type` — inferred from the provider prefix (`openai`, `anthropic`, `azure`)
- `model` — the model ID portion of the primary model
- `base_url` — default OpenAI-compatible endpoint
- `api_key` — placeholder `YOUR_API_KEY`

```
.metagpt/config2.yaml
PM:
  llm:
    api_type: anthropic
    model: claude-opus-4-8
    base_url: https://api.openai.com/v1
    api_key: YOUR_API_KEY
Engineer:
  llm:
    api_type: anthropic
    model: claude-haiku-4-5
    ...
```

## Usage

```bash
agentroles build
# Then run MetaGPT — it will pick up .metagpt/config2.yaml automatically
```

## Limitations

- `api_key` is a placeholder — replace with your actual key or reference an environment variable
- `base_url` defaults to OpenAI's endpoint; update for Anthropic or Azure providers
- Roles not in the standard map (PM, Architect, Engineer, QA, Reviewer) get `Custom_` prefixed entries
- Fallback models are not expressed in MetaGPT's configuration format
