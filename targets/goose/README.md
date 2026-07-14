# Goose Target

**Target type:** `goose`
**Output file:** `~/.config/goose/config.yaml`

## Overview

The Goose target generates a `~/.config/goose/config.yaml` configuration with provider and model assignments for each role defined in `agentroles.yaml`.

## Configuration Format

The generated YAML contains:

- `default` — the default provider and model (from the first role)
- `providers` — per-provider configuration with `type`, `api_key` env var reference, and `default_model`
- `roles` — each role's provider, model, and description

Goose supports [15+ providers](https://block.GitHub.io/goose/docs/provider-reference) including OpenAI, Anthropic, Google, Groq, DeepSeek, Ollama, and more.

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:

  - goose: ~/.config/goose/config.yaml

```

Then run:

```bash
agentroles build
```

## API Key Setup

Set the environment variables referenced in the config (e.g., `$OPENAI_API_KEY`, `$ANTHROPIC_API_KEY`).

## Reference

- [Goose](https://GitHub.com/block/goose)
- [Goose Provider Reference](https://block.GitHub.io/goose/docs/provider-reference)
