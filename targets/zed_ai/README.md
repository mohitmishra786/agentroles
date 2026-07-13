# Zed AI Adapter

Generates `.zed/settings.json` from `agentroles.yaml`.

## Role Mapping

Zed AI uses a **single-model assistant** architecture. Only one model is active at a time for all
AI features. This adapter maps the **first role** in your agentroles config as the primary assistant
model. If roles are defined, the first role (typically `planner`) is used.

| AgentRoles Role | Zed AI        |
|-----------------|---------------|
| *(first role)*  | default_model  |

## Generated File

- `.zed/settings.json` — JSON with `assistant.default_model` (provider + model) and
  `assistant.provider`. A `_notes` field documents which agentroles role was used and includes the
  original role notes.

## Usage

1. Add `zed_ai` to your `agentroles.yaml` targets:

   ```yaml
   targets:
     - zed_ai: ./.zed/settings.json
   ```

2. Run `agentroles build`
3. Merge the generated settings into `~/.config/zed/settings.json`

## Limitations

- **Single model only.** Zed AI cannot use different models for different tasks (chat, edit, inline
  assist all use the same model). The multi-role approach of agentroles is collapsed into one model.
- Per-role notes are preserved in the `_notes` field for reference.
- The settings file must be merged into your global `~/.config/zed/settings.json` — Zed does not
  read project-level settings for the AI assistant.

## Notes

Zed AI is built into the Zed editor as a first-party feature. It supports OpenAI, Anthropic, Google,
and Ollama providers. The `assistant` settings block controls both inline transformations and the
assistant panel.
