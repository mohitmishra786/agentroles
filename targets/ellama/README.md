# Ellama Adapter

Generates `ellama.el` — an Emacs Lisp configuration snippet for the Ellama package.

## Role Mapping

Ellama has separate **per-function providers**, allowing different models for different tasks. This adapter maps agentroles roles to the closest Ellama provider:

| AgentRoles Role | Ellama Provider                      |
|-----------------|--------------------------------------|
| planner         | `ellama-coding-provider`             |
| implementer     | `ellama-coding-provider`             |
| reviewer        | `ellama-summarization-provider`      |
| tester          | `ellama-extraction-provider`         |
| summarizer      | `ellama-summarization-provider`      |

Ellama defines these provider variables:
- `ellama-provider` (default/fallback)
- `ellama-coding-provider`
- `ellama-summarization-provider`
- `ellama-translation-provider`
- `ellama-extraction-provider`
- `ellama-completion-provider`

## Generated File

- `ellama.el` — An Emacs Lisp `use-package` block that configures Ellama with per-role LLM providers using `make-llm-ellama`.

## Usage

1. Add `ellama` to your `agentroles.yaml` targets:
   ```yaml
   targets:
     - ellama: ./ellama.el
   ```
2. Run `agentroles build`
3. Load the generated config in your Emacs init:
   ```elisp
   (load-file "~/.emacs.d/ellama.el")
   ```

## Limitations

- The generated config uses `make-llm-ellama` which requires the `llm` (llm-el) package. Ensure it's installed.
- Ellama's provider assignment is per-function, not per-interaction. You switch providers by changing which Ellama command you invoke.
- The mapping is approximate — Ellama's provider model doesn't perfectly align with agentroles' role-based approach.
- API keys must be configured separately (typically via environment variables or auth sources).

## Notes

Ellama is a popular Emacs package for integrating LLMs into editing workflows. It supports multiple backends (OpenAI, Anthropic, Ollama, etc.) through the `llm` library and allows per-function model assignment.
