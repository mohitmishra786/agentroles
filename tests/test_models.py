from __future__ import annotations

from pathlib import Path

import pytest

from agentroles.loader import ConfigLoadError, load_config
from agentroles.models import (
    AgentRolesConfig,
    ObservabilityConfig,
    RoleConfig,
    RoutingConfig,
    RoutingMode,
    TargetType,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLoadConfig:
    def test_load_valid_full_config(self):
        config = load_config(FIXTURES_DIR / "valid_full.yaml")
        assert config.version == 1
        assert len(config.roles) == 5
        assert config.roles["planner"].primary == "anthropic/claude-opus-4-8"
        assert config.roles["planner"].max_cost_per_call_usd == 0.50
        assert len(config.roles["planner"].fallback) == 2
        assert config.roles["implementer"].primary == "anthropic/claude-haiku-4-5"
        assert config.roles["reviewer"].primary == "openai/gpt-5.5"
        assert config.routing.mode == RoutingMode.STATIC
        assert config.routing.dynamic.enabled is False
        assert config.observability.cost_tracking is True
        assert config.observability.tag_calls_with_role is True
        assert config.has_target(TargetType.OPencode)
        assert config.has_target(TargetType.CLAUDE_CODE)
        assert config.has_target(TargetType.AIDER)
        assert config.has_target(TargetType.LITELLM_PROXY)

    def test_load_valid_minimal_config(self):
        config = load_config(FIXTURES_DIR / "valid_minimal.yaml")
        assert config.version == 1
        assert len(config.roles) == 1
        assert config.roles["planner"].primary == "anthropic/claude-sonnet-5"
        assert config.roles["planner"].fallback == []
        assert config.roles["planner"].max_cost_per_call_usd is None
        assert config.has_target(TargetType.OPencode)
        assert not config.has_target(TargetType.CLAUDE_CODE)
        assert config.routing.mode == RoutingMode.STATIC
        assert config.routing.dynamic.enabled is False

    def test_load_missing_roles_raises(self):
        with pytest.raises(ConfigLoadError, match="roles"):
            load_config(FIXTURES_DIR / "invalid_missing_roles.yaml")

    def test_load_nonexistent_file_raises(self):
        with pytest.raises(ConfigLoadError, match="not found"):
            load_config(FIXTURES_DIR / "nonexistent.yaml")

    def test_load_dynamic_routing_config(self):
        config = load_config(FIXTURES_DIR / "valid_dynamic_routing.yaml")
        assert config.routing.mode == RoutingMode.DYNAMIC
        assert config.routing.dynamic.enabled is True
        assert len(config.routing.dynamic.escalate_on) == 3
        assert config.routing.dynamic.cache_aware is True


class TestModels:
    def test_role_config_defaults(self):
        role = RoleConfig(primary="anthropic/claude-sonnet-5")
        assert role.fallback == []
        assert role.max_cost_per_call_usd is None
        assert role.notes is None

    def test_config_defaults(self):
        config = AgentRolesConfig(roles={"test": RoleConfig(primary="openai/gpt-5.5")})
        assert config.routing.mode == RoutingMode.STATIC
        assert config.routing.dynamic.enabled is False
        assert config.targets == []
        assert config.version == 1

    def test_get_target_path(self):
        config = AgentRolesConfig(
            roles={"test": RoleConfig(primary="openai/gpt-5.5")},
            targets=[
                {"opencode": "./opencode.json"},
                {"claude_code": "./.claude/agents/"},
            ],
        )
        assert config.get_target_path(TargetType.OPencode) == "./opencode.json"
        assert config.get_target_path(TargetType.CLAUDE_CODE) == "./.claude/agents/"
        assert config.get_target_path(TargetType.AIDER) is None

    def test_enabled_target_types(self):
        config = AgentRolesConfig(
            roles={"test": RoleConfig(primary="openai/gpt-5.5")},
            targets=[
                {"opencode": "./opencode.json"},
                {"aider": "./.aider.conf.yml"},
            ],
        )
        enabled = config.enabled_target_types
        assert TargetType.OPencode in enabled
        assert TargetType.AIDER in enabled
        assert TargetType.CLAUDE_CODE not in enabled
