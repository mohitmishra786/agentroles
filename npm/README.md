# agentroles

> Tool-agnostic role-to-model mapping for agentic coding workflows

**[agentroles](https://github.com/mohitmishra786/agentroles)** is a config
compiler — define role → model mappings once in a YAML file and generate
native configs for every agentic coding tool (OpenCode, Claude Code, Aider,
LiteLLM, and 25+ others).

## Quick start

```bash
npx @mohitmishra7/agentroles init
```

This interactively asks which tools you use, creates an `agentroles.yaml` with
sensible defaults, and immediately generates all tool-specific configs.

## CLI commands

```bash
npx @mohitmishra7/agentroles init       # Interactive setup
npx @mohitmishra7/agentroles build      # Regenerate target configs
npx @mohitmishra7/agentroles validate   # Schema lint + compatibility checks
npx @mohitmishra7/agentroles migrate    # Schema migrations
```

## How it works

This npm package is a lightweight Node.js wrapper that shells out to the
[Python package](https://pypi.org/project/agentroles/). It checks for
Python 3.11+ on your PATH and installs the pip package if missing.

## Requirements

- Node.js 20.0.0+
- Python 3.11+

## License

Apache 2.0
