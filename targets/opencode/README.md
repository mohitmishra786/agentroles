# OpenCode Target

Generates an `opencode.json` file with per-role agent model bindings in OpenCode's native `provider/model-id` format.

## What gets generated

A JSON file with an `agents` block. Each role from `agentroles.yaml` becomes an agent entry:

```json
{
  "agents": {
    "planner": {
      "model": "anthropic/claude-opus-4-8",
      "description": "High-stakes reasoning..."
    },
    "implementer": {
      "model": "anthropic/claude-haiku-4-5"
    }
  }
}
```

Roles with `notes` fields include a `description` key. Roles without notes get a minimal entry with just the model.

## Limitations

None. OpenCode's `agents` config block is the best matching surface for `agentroles.yaml`.
The `provider/model-id` format is identical to what agentroles stores internally.
Every role maps cleanly with no information loss.

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:
  - opencode: ./opencode.json
```

OpenCode reads `opencode.json` from the project root automatically. No additional configuration needed.
