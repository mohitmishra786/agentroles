# Aider Target

Generates an `.aider.conf.yml` file with model bindings for Aider's three named slots.

## What gets generated

```yaml
model: anthropic/claude-opus-4-8
editor-model: anthropic/claude-haiku-4-5
weak-model: anthropic/claude-haiku-4-5
```

## Role mapping convention

Aider has exactly three model slots. The convention maps:

| Aider Slot | agentroles Role |
|---|---|
| `--model` (main/architect) | `planner` |
| `--editor-model` (mechanical edits) | `implementer` |
| `--weak-model` (summaries, commit messages) | `summarizer` |

## Unrepresentable roles

If your `agentroles.yaml` defines roles beyond these three, the generator reports them in the build output: "Roles not representable in Aider: ['reviewer', 'tester']." These roles are explicitly called out rather than silently dropped. They won't appear in the generated `.aider.conf.yml`.

If none of the three standard roles exist in your config, the generator warns and produces an empty config.

## Limitations

- Only 3 model slots. Any tool with more than 3 defined roles loses information in the Aider mapping.
- The role mapping is convention-based. If you prefer different mappings, edit the generated file directly or adjust your `agentroles.yaml` role names.

## Usage

```yaml
targets:
  - aider: ./.aider.conf.yml
```
