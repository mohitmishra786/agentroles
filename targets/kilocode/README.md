# Kilo Code Target

**Target type:** `kilocode`
**Output file:** `.kilocode/config.json`

## Overview

The Kilo Code target generates a `.kilocode/config.json` file using the
**same format** as the OpenCode target. This is possible because Kilo Code is
a fork of OpenCode that reads `opencode.json` — the config format is
compatible.

The generated file includes `agent_type: "kilocode"` metadata to distinguish it from a standard OpenCode config.

## Compatibility with OpenCode Config

Kilo Code reads configuration in the same format as OpenCode's `opencode.json`:

- Top-level `agents` block mapping role names to model configurations
- Each agent has a `model` field and optional `description`

The only difference is the `agent_type` metadata field, which is ignored by
OpenCode but helps identify the config's target tool.

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:

  - kilocode: ./.kilocode/config.json

```

Then run:

```bash
agentroles build
```

## Reference

- [Kilo Code](https://GitHub.com/Kilo-Org/kilocode)
- [OpenCode Agent Roles](https://opencode.ai/docs/guide/custom-agents)
