# avante.nvim Adapter

Generates `avante.lua` — a Lua configuration snippet for the avante.nvim Neovim plugin.

## Role Mapping

AgentRoles → avante.nvim:

| AgentRoles Role | avante.nvim Setting          |
|-----------------|------------------------------|
| planner         | provider (main model)         |
| implementer     | auto*suggestions*provider     |

avante.nvim uses a Lua `setup()` function with two primary model settings: `provider`/`provider_model` for interactive AI conversations, and `auto_suggestions_provider`/`auto_suggestions_model` for inline code completion suggestions.

## Generated File

- `avante.lua` — A Lua table (plugin spec) compatible with lazy.nvim or packer.nvim, configuring:
  - `provider` and `provider_model` from the planner role
  - `auto_suggestions_provider` and `auto_suggestions_model` from the implementer role
  - Default behaviour settings for auto-suggestions

## Usage

1. Add `avante_nvim` to your `agentroles.yaml` targets:

   ```yaml
   targets:

     - avante_nvim: ./avante.lua

   ```

2. Run `agentroles build`
3. In your Neovim config, load the generated file:

   ```lua
   - - lazy.nvim
   return {
     import = "avante",
   }
   - - or, pass the returned plugin-spec table to your plugin manager
   - - The generated avante.lua returns a table with 'opts' containing provider/model settings:
   - - {
   - -   provider = "openai",
   - -   provider_model = "gpt-4o",
   - -   auto_suggestions_provider = "openai",
   - -   auto_suggestions_model = "gpt-4o-mini",
   - -   ...
   - - }
   - - Merge this into your avante.nvim configuration.
   ```

## Limitations

- The generated file is a plugin spec snippet, not a complete Neovim configuration. You'll need to integrate it with your plugin manager (lazy.nvim, packer.nvim, etc.).
- API endpoint URLs use a convention-based format (`https://api.<provider>.com/v1`). Adjust these if your provider uses a different URL.
- Only planner and implementer roles are mapped. Other roles (reviewer, tester, summarizer) are not directly representable in avante.nvim's current architecture.

## Notes

avante.nvim is a Neovim plugin that emulates Cursor-like AI features. It supports multiple AI providers (OpenAI, Anthropic, Ollama, etc.) and provides both chat-based interactions and inline code suggestions.
