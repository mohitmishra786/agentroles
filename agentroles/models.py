from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RoutingMode(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"


class EscalationSignal(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    TEST_FAILURE = "test_failure"
    PLAN_REVISION = "plan_revision"


class TargetType(str, Enum):
    OPencode = "opencode"
    CLAUDE_CODE = "claude_code"
    AIDER = "aider"
    LITELLM_PROXY = "litellm_proxy"
    CODEX_CLI = "codex_cli"
    GEMINI_CLI = "gemini_cli"
    QWEN_CODE = "qwen_code"
    CRUSH = "crush"
    CLINE = "cline"
    GOOSE = "goose"
    OPENINTERPRETER = "openinterpreter"
    KILOCODE = "kilocode"
    CONTINUE = "continue"
    CODY = "cody"
    PEARAI = "pearai"
    ZED_AI = "zed_ai"
    QODO = "qodo"
    AVANTE_NVIM = "avante_nvim"
    CODECOMPANION_NVIM = "codecompanion_nvim"
    ELLAMA = "ellama"
    GPTEL = "gptel"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    LANGGRAPH = "langgraph"
    METAGPT = "metagpt"
    OPENHANDS = "openhands"
    FACTORY = "factory"
    PORTKEY = "portkey"
    MANIFEST = "manifest"
    BITROUTER = "bitrouter"
    INFERMUX = "infermux"


class RoleConfig(BaseModel):
    primary: str = Field(..., description="Primary model in provider/model-id format")
    fallback: list[str] = Field(
        default_factory=list, description="Ordered fallback models"
    )
    max_cost_per_call_usd: float | None = Field(
        default=None, description="Cost ceiling per call in USD"
    )
    notes: str | None = Field(
        default=None, description="Human-readable notes about this role"
    )


class DynamicRoutingConfig(BaseModel):
    enabled: bool = Field(
        default=False, description="Enable dynamic/escalation routing"
    )
    escalate_on: list[EscalationSignal] = Field(
        default_factory=lambda: [
            EscalationSignal.TEST_FAILURE,
            EscalationSignal.LOW_CONFIDENCE,
        ],
        description="Signals that trigger escalation to fallback model",
    )
    cache_aware: bool = Field(
        default=True, description="Consider cache-miss cost before escalating"
    )

    @classmethod
    def disabled(cls) -> DynamicRoutingConfig:
        return cls(enabled=False, escalate_on=[], cache_aware=False)


class RoutingConfig(BaseModel):
    mode: RoutingMode = Field(
        default=RoutingMode.STATIC, description="Routing strategy: static or dynamic"
    )
    dynamic: DynamicRoutingConfig = Field(
        default_factory=DynamicRoutingConfig.disabled,
        description="Dynamic/escalation routing settings (only used when mode=dynamic)",
    )


class ObservabilityConfig(BaseModel):
    cost_tracking: bool = Field(
        default=True, description="Enable per-call cost tracking"
    )
    tag_calls_with_role: bool = Field(
        default=True, description="Tag outgoing requests with role metadata"
    )


class AgentRolesConfig(BaseModel):
    version: Literal[1] = Field(
        default=1, description="Schema version — only 1 is supported"
    )
    roles: dict[str, RoleConfig] = Field(
        ..., description="Role name → model configuration map"
    )
    routing: RoutingConfig = Field(
        default_factory=RoutingConfig, description="Routing strategy & configuration"
    )
    observability: ObservabilityConfig = Field(
        default_factory=ObservabilityConfig,
        description="Cost tracking & observability settings",
    )
    targets: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of target-tool → output-path mappings",
    )

    def get_target_path(self, target_type: TargetType) -> str | None:
        for entry in self.targets:
            if target_type.value in entry:
                return entry[target_type.value]
        return None

    def has_target(self, target_type: TargetType) -> bool:
        return self.get_target_path(target_type) is not None

    @property
    def enabled_target_types(self) -> list[TargetType]:
        result: list[TargetType] = []
        for entry in self.targets:
            for key in entry:
                try:
                    result.append(TargetType(key))
                except ValueError:
                    pass
        return result
