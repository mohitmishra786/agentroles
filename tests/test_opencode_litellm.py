from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agentroles.loader import load_config
from agentroles.plugin import GenerationResult
from agentroles.targets.opencode import OpenCodeGenerator
from agentroles.targets.litellm import LiteLLMGenerator

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestOpenCodeGenerator:
    def test_generates_valid_opencode_json(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = OpenCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            assert len(result.files_written) == 1
            output_path = Path(result.files_written[0])
            assert output_path.exists()
            content = json.loads(output_path.read_text())
            assert "agents" in content
            agents = content["agents"]
            assert "planner" in agents
            assert agents["planner"]["model"] == "anthropic/claude-opus-4-8"
            assert agents["implementer"]["model"] == "anthropic/claude-haiku-4-5"
            assert agents["reviewer"]["model"] == "openai/gpt-5.5"
            assert agents["tester"]["model"] == "anthropic/claude-haiku-4-5"
            assert agents["summarizer"]["model"] == "anthropic/claude-haiku-4-5"

    def test_generates_with_description(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = OpenCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            output_path = Path(result.files_written[0])
            content = json.loads(output_path.read_text())
            planner = content["agents"]["planner"]
            assert "description" in planner
            assert "High-stakes" in planner["description"]

    def test_skips_when_no_target(self):
        from agentroles.models import AgentRolesConfig, RoleConfig

        config = AgentRolesConfig(
            roles={"test": RoleConfig(primary="openai/gpt-5.5")},
            targets=[{"litellm_proxy": "./litellm-config.yaml"}],
        )
        gen = OpenCodeGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            gen.generate(config, Path(tmpdir), result)
            assert len(result.files_written) == 0


class TestLiteLLMGenerator:
    def test_generates_valid_litellm_config(self):
        import yaml

        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = LiteLLMGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            assert len(result.files_written) == 1
            output_path = Path(result.files_written[0])
            content = yaml.safe_load(output_path.read_text())
            assert "model_list" in content
            model_list = content["model_list"]
            assert len(model_list) >= 5

            model_names = [m["model_name"] for m in model_list]
            assert "role-planner" in model_names
            assert "role-implementer" in model_names
            assert "role-reviewer" in model_names
            assert "role-tester" in model_names
            assert "role-summarizer" in model_names

    def test_generates_fallback_entries(self):
        import yaml

        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = LiteLLMGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            output_path = Path(result.files_written[0])
            content = yaml.safe_load(output_path.read_text())
            model_list = content["model_list"]

            planner = next(m for m in model_list if m["model_name"] == "role-planner")
            assert "fallbacks" in planner
            assert len(planner["fallbacks"]) == 2

    def test_includes_metadata(self):
        import yaml

        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        gen = LiteLLMGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            output_path = Path(result.files_written[0])
            content = yaml.safe_load(output_path.read_text())
            model_list = content["model_list"]

            reviewer = next(m for m in model_list if m["model_name"] == "role-reviewer")
            metadata = reviewer["litellm_params"]["metadata"]
            assert metadata["role"] == "reviewer"
            assert "agentroles" in metadata["tags"]

    def test_generates_dynamic_routing_config(self):
        import yaml

        config = load_config(FIXTURES_DIR / "valid_dynamic_routing.yaml")
        gen = LiteLLMGenerator()
        result = GenerationResult()

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gen.generate(config, base, result)

            output_path = Path(result.files_written[0])
            content = yaml.safe_load(output_path.read_text())
            assert "router_settings" in content
            assert (
                content["router_settings"]["routing_strategy"] == "cache-aware-static"
            )
