from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

from .models import AgentRolesConfig, TargetType


class ValidationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationMessage:
    level: ValidationLevel
    message: str
    role: str | None = None
    target: TargetType | None = None


@dataclass
class ValidationResult:
    messages: list[ValidationMessage] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationMessage]:
        return [m for m in self.messages if m.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> list[ValidationMessage]:
        return [m for m in self.messages if m.level == ValidationLevel.WARNING]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def info(self, message: str, **kwargs: object) -> None:
        self.messages.append(ValidationMessage(ValidationLevel.INFO, message, **kwargs))  # type: ignore[arg-type]

    def warning(self, message: str, **kwargs: object) -> None:
        self.messages.append(ValidationMessage(ValidationLevel.WARNING, message, **kwargs))  # type: ignore[arg-type]

    def error(self, message: str, **kwargs: object) -> None:
        self.messages.append(ValidationMessage(ValidationLevel.ERROR, message, **kwargs))  # type: ignore[arg-type]


ANTHROPIC_MODELS = {"opus", "sonnet", "haiku"}

AIDER_SLOTS = 3
AIDER_ROLE_MAP = {
    "planner": "main model (--model)",
    "implementer": "editor model (--editor-model)",
    "summarizer": "weak model (--weak-model)",
}

AIDER_SLOT_NAMES: dict[str, str] = {
    "planner": "model",
    "implementer": "editor-model",
    "summarizer": "weak-model",
}


def extract_model_family(model_id: str) -> str | None:
    """Extract the model family identifier from a provider/model-id string."""
    parts = model_id.split("/", 1)
    if len(parts) != 2:
        return None
    model_name = parts[1].lower()
    if model_name.startswith("claude-"):
        suffix = model_name[len("claude-"):]
        for family in ANTHROPIC_MODELS:
            if suffix.startswith(family):
                return family
    return None


def is_anthropic_model(model_id: str) -> bool:
    return model_id.startswith("anthropic/")


def is_claude_model(model_id: str) -> bool:
    return is_anthropic_model(model_id) and extract_model_family(model_id) is not None


_VALIDATORS: list[Callable[[AgentRolesConfig, ValidationResult], None]] = []


def register_validator(fn: Callable[[AgentRolesConfig, ValidationResult], None]) -> Callable:
    _VALIDATORS.append(fn)
    return fn


def validate_config(config: AgentRolesConfig) -> ValidationResult:
    result = ValidationResult()
    for validator in _VALIDATORS:
        validator(config, result)
    return result


@register_validator
def _check_roles_exist(config: AgentRolesConfig, result: ValidationResult) -> None:
    if not config.roles:
        result.error("No roles defined in configuration")
    for role_name in config.roles:
        if not role_name.strip():
            result.error("Role name cannot be empty")


@register_validator
def _check_model_format(config: AgentRolesConfig, result: ValidationResult) -> None:
    for role_name, role_config in config.roles.items():
        primary = role_config.primary
        if "/" not in primary:
            result.error(
                f"Primary model '{primary}' is not in provider/model-id format",
                role=role_name,
            )
        for fb in role_config.fallback:
            if "/" not in fb:
                result.error(
                    f"Fallback model '{fb}' is not in provider/model-id format",
                    role=role_name,
                )


@register_validator
def _check_claude_code_compatibility(config: AgentRolesConfig, result: ValidationResult) -> None:
    if not config.has_target(TargetType.CLAUDE_CODE):
        return
    for role_name, role_config in config.roles.items():
        if not is_claude_model(role_config.primary):
            result.warning(
                f"Role '{role_name}' primary model '{role_config.primary}' is not an Anthropic Claude model. "
                f"Claude Code's model: field only supports sonnet|opus|haiku|inherit. "
                f"The generated .claude/agents/{role_name}.md will use model: inherit with a "
                f"comment directing users to route through the LiteLLM proxy target.",
                role=role_name,
                target=TargetType.CLAUDE_CODE,
            )


@register_validator
def _check_aider_slot_limit(config: AgentRolesConfig, result: ValidationResult) -> None:
    if not config.has_target(TargetType.AIDER):
        return
    aider_mappable = sum(1 for r in config.roles if r in AIDER_ROLE_MAP)
    total_roles = len(config.roles)

    if total_roles > AIDER_SLOTS:
        unmapped = [r for r in config.roles if r not in AIDER_ROLE_MAP]
        mapped = [r for r in config.roles if r in AIDER_ROLE_MAP]
        result.warning(
            f"Aider only supports 3 model slots (--model, --editor-model, --weak-model). "
            f"Mapped roles: {mapped}. "
            f"Roles not representable in Aider (will be skipped): {unmapped}. "
            f"The default convention maps planner→model, implementer→editor-model, summarizer→weak-model.",
            target=TargetType.AIDER,
        )

    if aider_mappable == 0:
        result.warning(
            "No roles map to Aider's 3 model slots (planner→model, implementer→editor-model, summarizer→weak-model). "
            "The generated .aider.conf.yml will have no model assignments.",
            target=TargetType.AIDER,
        )


@register_validator
def _check_target_paths(config: AgentRolesConfig, result: ValidationResult) -> None:
    seen_types: set[str] = set()
    for entry in config.targets:
        if not isinstance(entry, dict) or len(entry) != 1:
            result.error(f"Each target entry must be a single key-value pair, got: {entry}")
            continue
        for key in entry:
            if key in seen_types:
                result.error(f"Duplicate target type '{key}' — each target type may only appear once")
            seen_types.add(key)
            try:
                TargetType(key)
            except ValueError:
                result.warning(f"Unknown target type '{key}' — supported types: {[t.value for t in TargetType]}")


@register_validator
def _check_roles_have_primary(config: AgentRolesConfig, result: ValidationResult) -> None:
    for role_name, role_config in config.roles.items():
        if not role_config.primary:
            result.error(f"Role '{role_name}' has an empty primary model", role=role_name)


def validate_file(path: str | Path) -> ValidationResult:
    path = Path(path)
    from .loader import ConfigLoadError, load_config

    result = ValidationResult()
    try:
        config = load_config(path)
    except ConfigLoadError as e:
        result.error(str(e))
        return ValidationResult(messages=result.messages)

    return validate_config(config)
