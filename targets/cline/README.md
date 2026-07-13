# Cline Target

**Target type:** `cline`  
**Output file:** `.cline/providers.json`

## Overview

The Cline target generates a `.cline/providers.json` configuration file with provider entries, API key environment variable references, and role-to-model mappings.

## Configuration Format

The generated JSON contains:
- `providers` — per-provider configuration with `provider` name, `apiKey` env var reference, `defaultModel`, and `availableModels` list
- `role_mappings` — a list mapping each role to its provider, model, and description

## Usage

Add to your `agentroles.yaml`:

```yaml
targets:
  - cline: ./.cline/providers.json
```

Then run:

```bash
agentroles build
```

## API Key Setup

Set the environment variables referenced in the config (e.g., `$OPENAI_API_KEY`, `$ANTHROPIC_API_KEY`, etc.).

## Reference

- [Cline (VS Code Extension)](https://github.com/cline/cline)
