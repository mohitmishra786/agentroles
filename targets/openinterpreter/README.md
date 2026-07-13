# OpenInterpreter Target

**Target type:** `openinterpreter`  
**Output file:** `.openinterpreter/config.json`

## Overview

The OpenInterpreter target generates a `.openinterpreter/config.json` configuration file with model preferences mapped from the roles defined in `agentroles.yaml`.

## Background

OpenInterpreter is a **fork of OpenAI's Codex CLI** with similar architecture. Its configuration lives in the `.openinterpreter/` directory. Like Codex, it supports a single model at a time via the `--model` flag.

## Limitations

OpenInterpreter is **single-model per session**. The generated config provides a reference mapping of all roles to their models, and sets the first role's primary model as the default. To switch models, use the `--model` CLI flag or edit the config file.

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:
  - openinterpreter: ./.openinterpreter/config.json
```

Then run:

```bash
agentroles build
```

## Configuration Format

The generated JSON contains:
- `default_model` — the model to use (from the first role)
- `model_preferences` — per-role model, provider, API key env var, and notes

## Reference

- [OpenInterpreter](https://github.com/openinterpreter/open-interpreter)
