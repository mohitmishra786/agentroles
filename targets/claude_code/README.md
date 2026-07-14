# Claude Code Target

Generates `.claude/agents/<role>.md` subagent files with YAML frontmatter for Claude Code.

## What gets generated

One Markdown file per role in `.claude/agents/`, each with YAML frontmatter:

```markdown

- --

name: planner
description: High-stakes reasoning, architecture decisions.
model: opus
tools: [*]

- --

```

## Anthropic model constraint

Claude Code's `model:` field only accepts `sonnet`, `opus`, `haiku`, or `inherit`. If a role's primary model is not an Anthropic Claude model, the generated file uses `model: inherit` with a comment explaining the situation:

```markdown

- --

name: reviewer
description: Code review agent
model: inherit
tools: [*]

- --

# WARNING: Primary model 'openai/gpt-5.5' is not an Anthropic Claude model

# Route requests through the LiteLLM proxy config instead

```

Roles that use Anthropic models have the family extracted automatically: `anthropic/claude-opus-4-8` becomes `model: opus`, `anthropic/claude-sonnet-5` becomes `model: sonnet`, and `anthropic/claude-haiku-4-5` becomes `model: haiku`.

## Limitations

- Non-Anthropic models cannot be used directly via the `model:` field. Use the LiteLLM proxy target as a workaround: Claude Code points at the proxy, and the proxy routes each role to the correct model.
- Claude Code loads subagent files at session start only. Editing a generated `.md` file requires restarting the Claude Code session.

## Usage

```yaml
targets:

  - claude_code: ./.claude/agents/

```
