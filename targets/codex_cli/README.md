# Codex CLI Target

**Target type:** `codex_cli`
**Output file:** `.codex/config.yaml`

## Overview

The Codex CLI target generates a `.codex/config.yaml` reference file that
maps each role defined in `agentroles.yaml` to its primary model.

## Limitations

Codex CLI supports **a single model per session**. You switch models using
the `--model` CLI flag or by editing the `model:` key in `.codex/config.yaml`.
Multi-model role-based routing is not possible natively in Codex CLI.

To work with multiple roles:

1. Edit the `model:` field in `.codex/config.yaml` to the model you want for your current task.
2. Reference the role→model comments at the bottom of the generated config to pick the right model for each role type.

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:

  - codex_cli: ./.codex/config.yaml

```

Then run:

```bash
agentroles build
```

## Configuration Format

The generated YAML contains:

- `model:` — the primary model from the first defined role
- Commented entries mapping each role name → suggested model

## Reference

- [Codex CLI GitHub](https://GitHub.com/openai/codex)
