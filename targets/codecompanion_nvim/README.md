# codecompanion.nvim Adapter

Generates `codecompanion.lua` — a Lua configuration snippet for the codecompanion.nvim Neovim plugin.

## Role Mapping

codecompanion.nvim supports **multiple adapters**, each targeting a different strategy (chat, inline, cmd). This adapter maps roles to separate adapter profiles:

| AgentRoles Role | Adapter Profile      |
|-----------------|---------------------|
| planner         | `anthropic`         |
| implementer     | `anthropic_fast`    |
| reviewer        | `openai`            |
| tester          | `anthropic_fast`    |
| summarizer      | `anthropic_fast`    |

The adapter profiles are assigned to strategies:

- `chat` → uses the planner's adapter (anthropic)
- `inline` → uses the implementer's adapter (anthropic_fast)
- `cmd` → uses the planner's adapter (anthropic)

## Generated File

- `codecompanion.lua` — A lazy.nvim plugin spec with `adapters` functions and `strategies` mapping. Each adapter is defined as a function that calls `require("codecompanion.adapters").extend()` with the appropriate model.

## Usage

1. Add `codecompanion_nvim` to your `agentroles.yaml` targets:

   ```yaml
   targets:

     - codecompanion_nvim: ./codecompanion.lua

   ```

2. Run `agentroles build`
3. In your Neovim config:

   ```lua

   - - lazy.nvim

   return require("codecompanion")
   ```

## Limitations

- The adapter mapping uses provider-based naming (anthropic, openai). Non-standard providers may need adjustments.
- Each role maps to an adapter by its assigned provider, not by individual model. Multiple roles with the same provider will share an adapter profile (with the last one winning).
- The generated Lua requires `codecompanion.nvim` and its dependencies (`plenary.nvim`, `nvim-treesitter`).

## Notes

codecompanion.nvim provides a Copilot Chat-like experience in Neovim with support for multiple LLM backends. Its multi-adapter architecture allows assigning different models to different interaction strategies (chat vs. inline completions).
