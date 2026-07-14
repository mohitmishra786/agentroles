# gptel Adapter

Generates `gptel.el` — an Emacs Lisp configuration snippet for the gptel package.

## Role Mapping

gptel uses **per-backend** configuration with `gptel-make-*` constructor
functions. This adapter creates one backend per role/provider combination:

| AgentRoles Role | gptel Backend                              |
|-----------------|--------------------------------------------|
| *(each role)*   | `agentroles-<role>` using `gptel-make-*`   |

Each backend is defined with:

- The appropriate `gptel-make-{gpt,claude,gemini,mistral}` function based on provider
- The model name from the role's primary model
- API key sourced from `auth-source`
- Streaming enabled

All backends are collected in `agentroles-backends` for easy reference.

## Generated File

- `gptel.el` — Emacs Lisp defining one backend per role/provider combination and a list variable for all backends.

## Usage

1. Add `gptel` to your `agentroles.yaml` targets:

   ```yaml
   targets:

     - gptel: ./gptel.el

   ```

2. Run `agentroles build`
3. Load the config in Emacs:

   ```elisp
   (load-file "~/.emacs.d/gptel.el")
   ```

4. Switch backends with `M-x gptel-menu` or set `gptel-backend` to the desired role backend.

## Limitations

- API keys are configured via `auth-source` (`.authinfo` or `.netrc`). You
  must set these up separately with entries like
  `machine api.openai.com login apikey password <key>`.
- Provider mapping: `openai` → `gptel-make-gpt`, `anthropic` →
  `gptel-make-claude`, `google` → `gptel-make-gemini`, `mistral` →
  `gptel-make-mistral`. Unknown providers fall through to use the raw provider
  name which may not have a corresponding `gptel-make-*` function.
- gptel requires manual backend switching per session. There is no automatic
  role-based routing — use `gptel-menu` to select the appropriate backend.

## Notes

gptel is a mature Emacs LLM client that supports OpenAI, Anthropic, Google,
Mistral, and many OpenAI-compatible backends. Its multi-backend architecture
lets you define multiple model configurations and switch between them at
runtime, making it a natural fit for agentroles' multi-model approach.
