# Cody Adapter

Generates `.cody/config.json` from `agentroles.yaml`.

## Role Mapping

AgentRoles → Cody:

| AgentRoles Role | Cody Slot        |
|-----------------|------------------|
| planner         | chat model       |
| implementer     | autocomplete model |

Cody uses a **dual-model architecture**: one model for chat (interactive conversations, planning) and a separate model for autocomplete (inline code suggestions). This adapter maps planner to the chat model and implementer to the autocomplete model, reflecting the typical use case where a powerful model handles reasoning while a faster model provides completions.

## Generated File

- `.cody/config.json` — JSON with `models.chat` and `models.autocomplete` entries, each containing `provider` and `model`.

## Usage

1. Add `cody` to your `agentroles.yaml` targets:
   ```yaml
   targets:
     - cody: ./.cody/config.json
   ```
2. Run `agentroles build`
3. Copy `.cody/config.json` to your Cody config directory or merge it with your existing Cody settings.

## Limitations

- Cody's model configuration is typically managed via its VS Code extension settings or the Sourcegraph web UI. The generated config is a reference file for manual integration.
- Only chat and autocomplete models are supported. Other Cody features (mentions, commands) use the chat model by default.

## Notes

Cody is part of the Sourcegraph platform. The dual-model split allows using a large model for complex reasoning while a lightweight model handles low-latency completions, aligning with the planner/implementer divide in agentroles.
