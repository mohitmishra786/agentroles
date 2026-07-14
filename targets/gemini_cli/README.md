# Gemini CLI Target

**Target type:** `gemini_cli`
**Output file:** `.gemini/settings.json`

## Overview

The Gemini CLI target generates a `.gemini/settings.json` configuration file
with the primary model from the first defined role set as the default model,
along with provider metadata and API key environment variable references.

## Limitations

Gemini CLI supports **a single model per session**. The generator sets the
first role's primary model as the default. To switch models for different role
types, manually edit the `model` field in `.gemini/settings.json`.

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:

  - gemini_cli: ./.gemini/settings.json

```

Then run:

```bash
agentroles build
```

## Configuration Format

The generated JSON contains:

- `model` — an object with a `name` field for the default model (from the first role)
- `providers` — provider configurations with available models and API key env vars
- `roles_reference` — mapping of role names to their model/provider assignments

## API Key Setup

Set the appropriate environment variable for your provider (e.g., `$OPENAI_API_KEY`, `$ANTHROPIC_API_KEY`, `$GEMINI_API_KEY`).

## Reference

- [Gemini CLI](https://GitHub.com/google-gemini/gemini-cli)
