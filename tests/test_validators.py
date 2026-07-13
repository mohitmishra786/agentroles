from __future__ import annotations

from pathlib import Path

from agentroles.loader import load_config
from agentroles.validators import validate_config, validate_file

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestValidateConfig:
    def test_valid_full_passes(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        result = validate_config(config)
        errors = result.errors
        assert len(errors) == 0, f"Unexpected errors: {[e.message for e in errors]}"

    def test_valid_minimal_passes(self):
        config = load_config(FIXTURES_DIR / "valid_minimal.yaml")
        result = validate_config(config)
        assert len(result.errors) == 0

    def test_missing_roles_triggers_validation_error(self):
        config = load_config(FIXTURES_DIR / "valid_minimal.yaml")
        config.roles = {}
        result = validate_config(config)
        assert len(result.errors) > 0
        assert any("No roles" in e.message for e in result.errors)


class TestClaudeCodeCompatibility:
    def test_non_anthropic_model_triggers_warning(self):
        config = load_config(FIXTURES_DIR / "invalid_claude_non_anthropic.yaml")
        result = validate_config(config)
        warnings = result.warnings
        reviewer_warnings = [w for w in warnings if w.role == "reviewer"]
        assert len(reviewer_warnings) > 0
        assert "not an anthropic" in reviewer_warnings[0].message.lower()

    def test_anthropic_model_no_warning(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        config.targets = [{"claude_code": "./.claude/agents/"}]
        config.roles = {
            "planner": config.roles["planner"],
        }
        result = validate_config(config)
        claude_warnings = [w for w in result.warnings if w.role == "planner"]
        assert len(claude_warnings) == 0


class TestAiderSlotLimit:
    def test_extra_roles_trigger_warning(self):
        config = load_config(FIXTURES_DIR / "invalid_extra_aider_role.yaml")
        result = validate_config(config)
        aider_warnings = [
            w for w in result.warnings if w.target and w.target.value == "aider"
        ]
        assert len(aider_warnings) > 0
        assert "not representable" in aider_warnings[0].message.lower()

    def test_aider_mappable_roles_no_warning(self):
        config = load_config(FIXTURES_DIR / "valid_aider_only.yaml")
        result = validate_config(config)
        aider_warnings = [
            w for w in result.warnings if w.target and w.target.value == "aider"
        ]
        assert len(aider_warnings) == 0


class TestModelFormat:
    def test_malformed_model_triggers_error(self):
        from agentroles.models import RoleConfig, AgentRolesConfig

        config = AgentRolesConfig(
            roles={
                "test": RoleConfig(primary="no-provider-format"),
            },
        )
        result = validate_config(config)
        assert len(result.errors) > 0
        assert any("provider/model-id" in e.message for e in result.errors)

    def test_malformed_fallback_triggers_error(self):
        from agentroles.models import RoleConfig, AgentRolesConfig

        config = AgentRolesConfig(
            roles={
                "test": RoleConfig(primary="openai/gpt-5.5", fallback=["badformat"]),
            },
        )
        result = validate_config(config)
        assert len(result.errors) > 0
        assert any("provider/model-id" in e.message for e in result.errors)


class TestValidateFile:
    def test_validate_file_valid(self):
        result = validate_file(FIXTURES_DIR / "valid_full.yaml")
        assert result.is_valid

    def test_validate_file_missing(self):
        result = validate_file(FIXTURES_DIR / "nonexistent.yaml")
        assert not result.is_valid
        assert any("not found" in e.message for e in result.errors)
