# PearAI Adapter

Generates `.pearai/config.json` from `agentroles.yaml`.

## Role Mapping

AgentRoles → PearAI (identical to Continue's format):

| AgentRoles Role | PearAI Role       |
|-----------------|-------------------|
| planner         | chat              |
| implementer     | edit              |
| reviewer        | apply             |
| summarizer      | autocomplete      |

PearAI uses Continue's config format (`.continue/config.json`) since it is a fork of Continue. The 6 role slots are: `chat`, `edit`, `apply`, `autocomplete`, `embed`, `rerank`. Unmapped roles receive defaults.

## Generated File

- `.pearai/config.json` — JSON with `models` array containing `model`, `provider`, and `roles` fields.

## Usage

1. Add `pearai` to your `agentroles.yaml` targets:
   ```yaml
   targets:
     - pearai: ./.pearai/config.json
   ```
2. Run `agentroles build`
3. Copy the generated config to `~/.pearai/config.json`

## Limitations

- This adapter generates the config in the project directory, not in `~/.pearai/`. You must copy or symlink the file to the expected PearAI config location.
- The format is identical to Continue's config. If you also use Continue, the `continue` target produces the same format at `.continue/config.yaml` and `.continue/config.json`.

## Notes

PearAI is a fork of Continue that was initially released in 2024. It shares the same model configuration format and accepts `.pearai/config.json` (or `.continue/config.json` for backward compatibility). After Continue was acquired by Cursor, PearAI remained an independent project maintaining the same configuration conventions.
