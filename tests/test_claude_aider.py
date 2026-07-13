from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from agentroles.loader import load_config
from agentroles.plugin import GenerationResult
from agentroles.targets.claude_code import ClaudeCodeGenerator
from agentroles.targets.aider import AiderGenerator

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestClaudeCodeGenerator:
    def test_generates_markdown_files(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = ClaudeCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            assert len(result.files_written) == 5
            files = {Path(f).name for f in result.files_written}
            assert "planner.md" in files
            assert "implementer.md" in files
            assert "reviewer.md" in files
            assert "tester.md" in files
            assert "summarizer.md" in files

    def test_anthropic_role_has_correct_model_field(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = ClaudeCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            planner_path = base / ".claude" / "agents" / "planner.md"
            content = planner_path.read_text()

            assert "model: opus" in content
            assert "name: planner" in content

            implementer_path = base / ".claude" / "agents" / "implementer.md"
            impl_content = implementer_path.read_text()
            assert "model: haiku" in impl_content

    def test_non_anthropic_role_uses_inherit_with_comment(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = ClaudeCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            reviewer_path = base / ".claude" / "agents" / "reviewer.md"
            content = reviewer_path.read_text()

            assert "model: inherit" in content
            assert "WARNING" in content
            assert "openai/gpt-5.5" in content
            assert "LiteLLM" in content

    def test_has_correct_frontmatter(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = ClaudeCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            planner_path = base / ".claude" / "agents" / "planner.md"
            content = planner_path.read_text()

            assert content.startswith("---")
            assert "tools:" in content
            assert "description:" in content

    def test_includes_notes_in_body(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = ClaudeCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            planner_path = base / ".claude" / "agents" / "planner.md"
            content = planner_path.read_text()
            assert "High-stakes" in content


class TestAiderGenerator:
    def test_generates_aider_conf(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = AiderGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            assert len(result.files_written) == 1
            output_path = Path(result.files_written[0])
            content = yaml.safe_load(output_path.read_text())

            assert content["model"] == "anthropic/claude-opus-4-8"
            assert content["editor-model"] == "anthropic/claude-haiku-4-5"
            assert content["weak-model"] == "anthropic/claude-haiku-4-5"

    def test_warns_on_unrepresentable_roles(self):
        config = load_config(FIXTURES_DIR / "invalid_extra_aider_role.yaml")
        gen = AiderGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            assert len(result.warnings) > 0
            warning_text = " ".join(result.warnings)
            assert "not representable" in warning_text.lower()
            assert "technical_lead" in warning_text or "architect" in warning_text

    def test_generates_empty_with_no_mappable_roles(self):
        from agentroles.models import AgentRolesConfig, RoleConfig

        config = AgentRolesConfig(
            roles={
                "custom_role": RoleConfig(primary="openai/gpt-5.5"),
            },
            targets=[{"aider": "./.aider.conf.yml"}],
        )
        gen = AiderGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            assert len(result.warnings) > 0

    def test_aider_only_config_maps_correctly(self):
        config = load_config(FIXTURES_DIR / "valid_aider_only.yaml")
        gen = AiderGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            output_path = Path(result.files_written[0])
            content = yaml.safe_load(output_path.read_text())

            assert content["model"] == "anthropic/claude-opus-4-8"
            assert content["editor-model"] == "anthropic/claude-haiku-4-5"
            assert content["weak-model"] == "anthropic/claude-haiku-4-5"
            assert len(result.warnings) == 0
