# Contributing

agentroles was designed so that adding a new target tool doesn't touch any core code. The target generator system
is a plugin interface. If you want agentroles to emit configs for CrewAI, LangGraph, or GitHub Copilot custom
agents, you write one class and register it. That's the whole contract.

## The plugin interface

Every target generator implements `TargetGenerator` from `agentroles.plugin`:

```python
from agentroles.plugin import TargetGenerator, GenerationResult
from agentroles.models import AgentRolesConfig
from pathlib import Path

class CrewAIGenerator(TargetGenerator):
    @property
    def target_type(self):
        from agentroles.models import TargetType
        return TargetType("crewai")

    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        target = base_dir / output_path
        target.parent.mkdir(parents=True, exist_ok=True)

        # Read config.roles, build your tool specific config, write it.
        crew_config = build_my_crew_config(config)
        target.write_text(crew_config)
        result.add_file(str(target))
```

Three things happen in `generate`:

1. **Check for your target path.** If the user hasn't included your tool in their `targets:` list, return immediately.
2. **Build the config.** `config.roles` is a dict of `RoleConfig` objects. Each has `primary`, `fallback`,
   `max_cost_per_call_usd`, and `notes`. You have the full validated model at your disposal.
3. **Record what you wrote.** Call `result.add_file()` for each file. If something is off but not fatal, call
   `result.add_warning()`. Call `result.add_error()` for anything that should stop the build.

### Registering your generator

Add an entry point to your package's `pyproject.toml`:

```toml
[project.entry-points."agentroles.targets"]
crewai = "my_crewai_package.generator:CrewAIGenerator"
```

When `agentroles build` encounters `targets: [{crewai: ./crew_config.py}]`, it discovers your generator through
the entry point and runs it. You never touch agentroles source.

### A note on TargetType

Core tool types (`opencode`, `claude_code`, `aider`, `litellm_proxy`) are enumerated in `TargetType`.
If you're adding a plugin, you can either propose adding your type to the enum (for tools with broad
adoption) or use the string form directly. The validator will emit a warning for unknown types but won't
block the build.

## How the generators that ship with agentroles work

If you're curious about existing patterns, here's what each built in generator deals with:

**OpenCode** is the easiest. OpenCode's `agents` block already uses `provider/model-id` strings, which is
exactly how agentroles stores them internally. The generator is essentially a key for key translation
with the `agents` wrapper.

**Claude Code** requires model name extraction. `anthropic/claude-opus-4-8` becomes `model: opus`.
For non Anthropic models, it emits `model: inherit` with a warning comment. This is deliberate: silently
dropping the model assignment would be worse than being explicit about the limitation.

**Aider** has exactly three slots. If you define five roles in agentroles, two of them won't map to any
Aider concept. The generator reports which ones and why in the build output. The convention maps planner
to `--model`, implementer to `--editor-model`, and summarizer to `--weak-model`. If your config only
has a `tester` role and no planner, the generator warns but still produces a config file (empty or partial).

**LiteLLM proxy** is the universal fallback. It produces a complete `model_list` with per role entries,
fallback chains as separate named entries, cost ceilings, and role metadata tags. Any tool that speaks
OpenAI compatible HTTP can point at this proxy and get role aware routing without understanding agentroles at all.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The test suite lives in `tests/`. Fixtures are YAML files in `tests/fixtures/`. The full run:

```bash
pytest -v
```

Tests cover:

- Model validation and Pydantic serialization
- Every target generator with snapshot output checks
- The escalation router with static, dynamic, and cache aware scenarios
- CLI commands via Click's test runner
- Schema validation edge cases (Claude Code non Anthropic roles, Aider extra roles, malformed model strings)

## What we deliberately left for later

These are explicitly out of scope for v1. Each is a natural plugin:

- **CrewAI / AutoGen / LangGraph generators**: Python code emits for per agent model binding. The plugin interface
  above was designed specifically so these can ship as separate packages.
- **GitHub Copilot `.agent.md` generator**: The `.github/agents/*.agent.md` format is still evolving. Once it
  stabilizes, this is a straightforward plugin.
- **A trained complexity classifier for routing**: The current escalation router uses signal triggers only (test
  failure, low confidence, plan revision). A learned classifier for upfront difficulty estimation would be a separate
  plugin. The ACRouter paper showed these generalize poorly without coding specific training data, so this needs real
  research before it's a default.
- **CrewAI native integration in the CLI**: The `crewai` target type doesn't exist yet in the enum. Adding it
  means either a PR to the enum or an external plugin via entry points.

Each of these can be built and shipped independently, with zero changes to the agentroles core. That's the whole
point of the plugin architecture.

## Release process

1. Tag a commit: `git tag v0.1.1`
2. Push the tag: `git push origin v0.1.1`
3. GitHub Actions builds, runs tests, publishes to PyPI and npm, creates a release with changelog from merged PR titles.

The release workflow references `PYPI_API_TOKEN` and `NPM_TOKEN` secrets. You'll need to configure those in the repo
settings.

## License

Apache 2.0. Same as the project.
