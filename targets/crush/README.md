# Crush Target

**Target type:** `crush`  
**Output file:** `crush.json`

## Overview

The Crush target generates a `crush.json` configuration file with a `providers` block listing each unique provider from the roles, along with API key environment variable references and model-to-role mappings.

## Session-Based Model Switching

Crush supports **session-based model switching** — you can choose which model/provider to use at the start of each session via the `--model` flag or the UI. The generated config lists all available providers and their models, allowing you to quickly switch between role-specific models.

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:
  - crush: ./crush.json
```

Then run:

```bash
agentroles build
```

## Configuration Format

The generated JSON contains:
- `providers` — per-provider config with `name`, `api_key`, and `models` list
- `role_model_map` — mapping of each role to its provider and model

## API Key Setup

Set the environment variables referenced in the config (e.g., `$OPENAI_API_KEY`, `$ANTHROPIC_API_KEY`).

## Reference

- [Crush](https://github.com/crush-org/crush)
