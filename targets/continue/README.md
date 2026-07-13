# Continue Adapter

Generates `.continue/config.yaml` and `.continue/config.json` from `agentroles.yaml`.

## Role Mapping

AgentRoles → Continue roles:

| AgentRoles Role | Continue Role    |
|-----------------|------------------|
| planner         | chat             |
| implementer     | edit             |
| reviewer        | apply            |
| summarizer      | autocomplete     |

Continue defines 6 model roles: `chat`, `edit`, `apply`, `autocomplete`, `embed`, `rerank`. The agentroles roles map to four of these; any unmapped roles (embed, rerank) receive a sensible default (`gpt-4o-mini` / `openai`) to ensure the config is valid.

## Generated Files

- `.continue/config.yaml` — primary config (YAML format)
- `.continue/config.json` — legacy format for backward compatibility

Both contain a `models` array with `model`, `provider`, and `roles` fields per entry.

## Usage

1. Add `continue` to your `agentroles.yaml` targets:
   ```yaml
   targets:
     - continue: ./.continue/config.yaml
   ```
2. Run `agentroles build`
3. Continue will pick up the config from `.continue/config.yaml`

## Limitations

- Embed and rerank roles are not mapped from agentroles roles. They receive sensible defaults. Customize these in the generated config if needed.
- Continue uses a legacy `config.json` format alongside the newer `config.yaml`. Both are generated; Continue reads `config.yaml` if present.

## Notes

Continue was acquired by Cursor in 2025. The `.continue/config.yaml` format continues to work in PearAI (a fork of Continue) — see the `pearai` target for a dedicated adapter.
