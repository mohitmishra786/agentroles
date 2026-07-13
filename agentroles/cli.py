"""CLI for agentroles — the tool-agnostic role→model mapping layer.

Commands:
    agentroles init       Interactive wizard to create agentroles.yaml and generate configs.
    agentroles build      Read agentroles.yaml, regenerate all target configs.
    agentroles validate   Lint the YAML schema and check for target incompatibilities.
    agentroles migrate    Show migration status for the current schema version.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .__init__ import __version__
from .loader import ConfigLoadError, load_config
from .models import AgentRolesConfig, TargetType
from .plugin import GenerationResult
from .targets.aider import AiderGenerator
from .targets.autogen import AutoGenGenerator
from .targets.avante_nvim import AvanteNvimGenerator
from .targets.bitrouter import BitRouterGenerator
from .targets.claude_code import ClaudeCodeGenerator
from .targets.cline import ClineGenerator
from .targets.codecompanion_nvim import CodeCompanionNvimGenerator
from .targets.codex_cli import CodexCLIGenerator
from .targets.cody import CodyGenerator
from .targets.continue_ import ContinueGenerator
from .targets.crewai import CrewAIGenerator
from .targets.crush import CrushGenerator
from .targets.ellama import EllamaGenerator
from .targets.factory import FactoryGenerator
from .targets.gemini_cli import GeminiCLIGenerator
from .targets.goose import GooseGenerator
from .targets.gptel import GptelGenerator
from .targets.infermux import InferMuxGenerator
from .targets.kilocode import KiloCodeGenerator
from .targets.langgraph import LangGraphGenerator
from .targets.litellm import LiteLLMGenerator
from .targets.manifest import ManifestGenerator
from .targets.metagpt import MetaGPTGenerator
from .targets.opencode import OpenCodeGenerator
from .targets.openhands import OpenHandsGenerator
from .targets.openinterpreter import OpenInterpreterGenerator
from .targets.pearai import PearAIGenerator
from .targets.portkey import PortkeyGenerator
from .targets.qodo import QodoGenerator
from .targets.qwen_code import QwenCodeGenerator
from .targets.zed_ai import ZedAIGenerator
from .validators import ValidationLevel, validate_config

DEFAULT_CONFIG_FILE = "agentroles.yaml"

SAMPLE_CONFIG = """\
version: 1

roles:
  planner:
    primary: anthropic/claude-opus-4-8
    fallback: [openai/gpt-5.5]
    max_cost_per_call_usd: 0.50
    notes: "High-stakes reasoning, architecture decisions, ambiguity resolution."

  implementer:
    primary: anthropic/claude-haiku-4-5
    fallback: [openai/gpt-4o-mini]
    max_cost_per_call_usd: 0.02
    notes: "Mechanical edits once a plan exists. High call volume."

  reviewer:
    primary: openai/gpt-5.5
    fallback: [anthropic/claude-sonnet-5]
    notes: "Model-diversity review reduces correlated blind spots."

  tester:
    primary: anthropic/claude-haiku-4-5
    fallback: [openai/gpt-4o-mini]

  summarizer:
    primary: anthropic/claude-haiku-4-5

routing:
  mode: static
  dynamic:
    enabled: false
    escalate_on: [low_confidence, test_failure, plan_revision]
    cache_aware: true

observability:
  cost_tracking: true
  tag_calls_with_role: true

targets:
  - opencode: ./opencode.json
  - claude_code: ./.claude/agents/
  - aider: ./.aider.conf.yml
  - litellm_proxy: ./litellm-config.yaml
""".strip()

TARGET_DESCRIPTIONS: dict[str, str] = {
    "opencode": "OpenCode — generates opencode.json agent block",
    "claude_code": "Claude Code — generates .claude/agents/<role>.md subagent files",
    "aider": "Aider — generates .aider.conf.yml with --model/--editor-model/--weak-model",
    "litellm_proxy": "LiteLLM Proxy — generates litellm-config.yaml with per-role model entries",
    "codex_cli": "Codex CLI — generates .codex/config.yaml with model reference",
    "gemini_cli": "Gemini CLI — generates .gemini/settings.json with provider config",
    "qwen_code": "Qwen Code — generates .qwen/agents/<role>.md subagent files",
    "crush": "Crush — generates crush.json with provider model settings",
    "cline": "Cline — generates .cline/providers.json with provider configs",
    "goose": "Goose — generates .goose/config.yaml with provider assignments",
    "openinterpreter": "OpenInterpreter — generates .openinterpreter/config.json",
    "kilocode": "Kilo Code — generates .kilocode/config.json (OpenCode-compatible)",
    "continue": "Continue — generates .continue/config.yaml with per-role model profiles",
    "cody": "Cody (Sourcegraph) — generates .cody/config.json with chat/autocomplete models",
    "pearai": "PearAI — generates .pearai/config.json (Continue-compatible)",
    "zed_ai": "Zed AI — generates .zed/settings.json with assistant model config",
    "qodo": "Qodo Gen — generates .qodo/config.json with model references",
    "avante_nvim": "avante.nvim — generates avante.lua (Neovim plugin config)",
    "codecompanion_nvim": "codecompanion.nvim — generates codecompanion.lua (Neovim config)",
    "ellama": "Ellama — generates ellama.el (Emacs Lisp config)",
    "gptel": "gptel — generates gptel.el (Emacs Lisp config)",
    "crewai": "CrewAI — generates config/agents.yaml, config/tasks.yaml, crew.py",
    "autogen": "AutoGen — generates autogen_agents.py with AssistantAgent per role",
    "langgraph": "LangGraph — generates langgraph_workflow.py with StateGraph",
    "metagpt": "MetaGPT — generates .metagpt/config2.yaml with per-role LLM config",
    "openhands": "OpenHands — generates config.toml with per-role LLM profiles",
    "factory": "Factory — generates .factory/config.yaml with per-droid model config",
    "portkey": "Portkey — generates portkey-config.json with per-role gateway routes",
    "manifest": "Manifest — generates manifest-routes.json with X-Agent-Role headers",
    "bitrouter": "BitRouter — generates bitrouter-config.toml with per-agent routes",
    "infermux": "Infermux — generates infermux-config.yaml with model routes",
}

GENERATOR_REGISTRY: dict[TargetType, type] = {
    TargetType.OPencode: OpenCodeGenerator,
    TargetType.CLAUDE_CODE: ClaudeCodeGenerator,
    TargetType.AIDER: AiderGenerator,
    TargetType.LITELLM_PROXY: LiteLLMGenerator,
    TargetType.CODEX_CLI: CodexCLIGenerator,
    TargetType.GEMINI_CLI: GeminiCLIGenerator,
    TargetType.QWEN_CODE: QwenCodeGenerator,
    TargetType.CRUSH: CrushGenerator,
    TargetType.CLINE: ClineGenerator,
    TargetType.GOOSE: GooseGenerator,
    TargetType.OPENINTERPRETER: OpenInterpreterGenerator,
    TargetType.KILOCODE: KiloCodeGenerator,
    TargetType.CONTINUE: ContinueGenerator,
    TargetType.CODY: CodyGenerator,
    TargetType.PEARAI: PearAIGenerator,
    TargetType.ZED_AI: ZedAIGenerator,
    TargetType.QODO: QodoGenerator,
    TargetType.AVANTE_NVIM: AvanteNvimGenerator,
    TargetType.CODECOMPANION_NVIM: CodeCompanionNvimGenerator,
    TargetType.ELLAMA: EllamaGenerator,
    TargetType.GPTEL: GptelGenerator,
    TargetType.CREWAI: CrewAIGenerator,
    TargetType.AUTOGEN: AutoGenGenerator,
    TargetType.LANGGRAPH: LangGraphGenerator,
    TargetType.METAGPT: MetaGPTGenerator,
    TargetType.OPENHANDS: OpenHandsGenerator,
    TargetType.FACTORY: FactoryGenerator,
    TargetType.PORTKEY: PortkeyGenerator,
    TargetType.MANIFEST: ManifestGenerator,
    TargetType.BITROUTER: BitRouterGenerator,
    TargetType.INFERMUX: InferMuxGenerator,
}


def _print_result(result: GenerationResult) -> None:
    for f in result.files_written:
        click.echo(f"  Created: {f}")
    for w in result.warnings:
        click.secho(f"  Warning: {w}", fg="yellow")
    for e in result.errors:
        click.secho(f"  Error: {e}", fg="red")


def _run_build(
    config: AgentRolesConfig,
    base_dir: Path,
    verbose: bool = False,
) -> GenerationResult:
    overall = GenerationResult()
    for target_type in config.enabled_target_types:
        generator_cls = GENERATOR_REGISTRY.get(target_type)
        if generator_cls is None:
            overall.add_warning(f"No generator available for target type: {target_type.value}")
            continue
        generator = generator_cls()
        result = GenerationResult()
        generator.generate(config, base_dir, result)
        if verbose:
            click.echo(f"\n[{target_type.value}]")
        _print_result(result)
        overall.files_written.extend(result.files_written)
        overall.warnings.extend(result.warnings)
        overall.errors.extend(result.errors)
    return overall


@click.group()
@click.version_option(version=__version__, prog_name="agentroles")
def main() -> None:
    """agentroles — tool-agnostic role-to-model mapping for agentic coding."""


@main.command()
@click.option(
    "--targets",
    "-t",
    multiple=True,
    type=click.Choice([
        "opencode", "claude_code", "aider", "litellm_proxy",
        "codex_cli", "gemini_cli", "qwen_code", "crush",
        "cline", "goose", "openinterpreter", "kilocode",
        "continue", "cody", "pearai", "zed_ai", "qodo",
        "avante_nvim", "codecompanion_nvim", "ellama", "gptel",
        "crewai", "autogen", "langgraph", "metagpt",
        "openhands", "factory", "portkey", "manifest",
        "bitrouter", "infermux",
    ]),
    help="Which target tools to generate configs for (can be specified multiple times). If not specified, all are offered interactively.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompts; use defaults for all questions.",
)
def init(targets: tuple[str, ...], yes: bool) -> None:
    """Create an agentroles.yaml interactively and generate target configs."""
    config_path = Path.cwd() / DEFAULT_CONFIG_FILE

    if config_path.exists() and not yes:
        if not click.confirm(
            f"{DEFAULT_CONFIG_FILE} already exists. Overwrite?"
        ):
            click.echo("Aborted.")
            return

    click.echo("\nagentroles init — interactive setup\n")
    click.echo("This will create agentroles.yaml with sensible defaults\n")

    chosen_targets: list[str]
    if targets:
        chosen_targets = list(targets)
    else:
        chosen_targets = _interactive_target_selection()

    if not chosen_targets:
        click.echo("No targets selected. Writing agentroles.yaml only.")
    else:
        click.echo(f"\nSelected targets: {', '.join(chosen_targets)}")

    targets_entries = _build_target_entries(chosen_targets)

    config_text = SAMPLE_CONFIG
    if targets_entries:
        config_lines = config_text.split("\n")
        targets_start = None
        for i, line in enumerate(config_lines):
            if line.strip() == "targets:":
                targets_start = i
                break
        if targets_start is not None:
            indent = "  "
            new_targets = ["targets:"]
            for entry in targets_entries:
                new_targets.append(f"{indent}- {entry}")
            config_lines = config_lines[:targets_start]
            config_lines.extend(new_targets)
            config_text = "\n".join(config_lines)

    config_path.write_text(config_text + "\n")
    click.echo(f"\nCreated: {config_path}")

    if not chosen_targets:
        click.echo("\nRun 'agentroles build' after adding targets to agentroles.yaml.")
        return

    try:
        config = load_config(DEFAULT_CONFIG_FILE)
    except ConfigLoadError as e:
        click.secho(f"\nError loading config: {e}", fg="red")
        return

    click.echo("\nGenerating target configs...")
    result = _run_build(config, Path.cwd(), verbose=True)

    if result.success:
        click.secho(f"\nDone! Generated {len(result.files_written)} file(s) from {DEFAULT_CONFIG_FILE}.", fg="green")
    else:
        click.secho(f"\nDone with {len(result.errors)} error(s).", fg="yellow")


def _interactive_target_selection() -> list[str]:
    targets = [
        "opencode", "claude_code", "aider", "litellm_proxy",
        "codex_cli", "gemini_cli", "qwen_code", "crush",
        "cline", "goose", "openinterpreter", "kilocode",
        "continue", "cody", "pearai", "zed_ai", "qodo",
        "avante_nvim", "codecompanion_nvim", "ellama", "gptel",
        "crewai", "autogen", "langgraph", "metagpt",
        "openhands", "factory", "portkey", "manifest",
        "bitrouter", "infermux",
    ]
    chosen: list[str] = []
    click.echo("Which target tools do you want to generate configs for?\n")
    for t in targets:
        desc = TARGET_DESCRIPTIONS.get(t, t)
        if click.confirm(f"  [{t}] {desc}?", default=True):
            chosen.append(t)
    return chosen


def _build_target_entries(chosen: list[str]) -> list[str]:
    default_paths = {
        "opencode": "opencode: ./opencode.json",
        "claude_code": "claude_code: ./.claude/agents/",
        "aider": "aider: ./.aider.conf.yml",
        "litellm_proxy": "litellm_proxy: ./litellm-config.yaml",
        "codex_cli": "codex_cli: ./.codex/config.yaml",
        "gemini_cli": "gemini_cli: ./.gemini/settings.json",
        "qwen_code": "qwen_code: ./.qwen/agents/",
        "crush": "crush: ./crush.json",
        "cline": "cline: ./.cline/providers.json",
        "goose": "goose: ./.goose/config.yaml",
        "openinterpreter": "openinterpreter: ./.openinterpreter/config.json",
        "kilocode": "kilocode: ./.kilocode/config.json",
        "continue": "continue: ./.continue/config.yaml",
        "cody": "cody: ./.cody/config.json",
        "pearai": "pearai: ./.pearai/config.json",
        "zed_ai": "zed_ai: ./.zed/settings.json",
        "qodo": "qodo: ./.qodo/config.json",
        "avante_nvim": "avante_nvim: ./avante.lua",
        "codecompanion_nvim": "codecompanion_nvim: ./codecompanion.lua",
        "ellama": "ellama: ./ellama.el",
        "gptel": "gptel: ./gptel.el",
        "crewai": "crewai: ./config/agents.yaml",
        "autogen": "autogen: ./autogen_agents.py",
        "langgraph": "langgraph: ./langgraph_workflow.py",
        "metagpt": "metagpt: ./.metagpt/config2.yaml",
        "openhands": "openhands: ./config.toml",
        "factory": "factory: ./.factory/config.yaml",
        "portkey": "portkey: ./portkey-config.json",
        "manifest": "manifest: ./manifest-routes.json",
        "bitrouter": "bitrouter: ./bitrouter-config.toml",
        "infermux": "infermux: ./infermux-config.yaml",
    }
    return [default_paths[c] for c in chosen if c in default_paths]


@main.command()
@click.option(
    "--config",
    "-c",
    default=DEFAULT_CONFIG_FILE,
    help=f"Path to agentroles.yaml (default: {DEFAULT_CONFIG_FILE})",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed per-generator output.",
)
def build(config: str, verbose: bool) -> None:
    """Read agentroles.yaml and regenerate all target configs."""
    config_path = Path(config)

    try:
        cfg = load_config(config_path)
    except ConfigLoadError as e:
        click.secho(f"Error: {e}", fg="red")
        sys.exit(1)

    click.echo(f"Building target configs from: {config_path}\n")

    result = _run_build(cfg, config_path.parent, verbose=verbose)

    if result.files_written:
        files = "\n".join(f"  {f}" for f in result.files_written)
        click.secho(f"\nGenerated {len(result.files_written)} file(s):", fg="green")
        click.echo(files)
    else:
        click.secho("\nNo targets specified. Add a 'targets:' section to agentroles.yaml.", fg="yellow")

    if result.errors:
        click.secho(f"\n{len(result.errors)} error(s):", fg="red")
        for e in result.errors:
            click.echo(f"  {e}")
        sys.exit(1)


@main.command()
@click.option(
    "--config",
    "-c",
    default=DEFAULT_CONFIG_FILE,
    help=f"Path to agentroles.yaml (default: {DEFAULT_CONFIG_FILE})",
    type=click.Path(exists=True, dir_okay=False),
)
def validate(config: str) -> None:
    """Validate agentroles.yaml schema and check target compatibility."""
    from .validators import validate_file

    result = validate_file(config)

    click.echo(f"Validating: {config}\n")

    if result.is_valid:
        click.secho("Schema validation: PASSED", fg="green")
    else:
        click.secho("Schema validation: FAILED", fg="red")

    error_count = len(result.errors)
    warning_count = len(result.warnings)
    info_count = len([m for m in result.messages if m.level == ValidationLevel.INFO])

    for msg in result.messages:
        prefix = {"error": "[ERROR]", "warning": "[WARN]", "info": "[INFO]"}[msg.level.value]
        color = {"error": "red", "warning": "yellow", "info": "white"}[msg.level.value]
        context = ""
        if msg.role:
            context += f" (role: {msg.role})"
        if msg.target:
            context += f" (target: {msg.target.value})"
        click.secho(f"  {prefix} {msg.message}{context}", fg=color)

    if error_count == 0 and warning_count == 0:
        click.secho(f"\nAll checks passed. 0 errors, 0 warnings.", fg="green")
    elif error_count == 0:
        click.secho(f"\nValidation passed with {warning_count} warning(s).", fg="yellow")
    else:
        click.secho(
            f"\nValidation failed: {error_count} error(s), {warning_count} warning(s).",
            fg="red",
        )
        sys.exit(1)


@main.command()
def migrate() -> None:
    """Check for and apply schema migrations."""
    click.echo("No migrations needed for schema version 1.")
    click.echo("This command will become active once a schema version 2 is introduced.")
    click.echo("Run 'agentroles validate' to check your current config for issues.")
