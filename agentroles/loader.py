from __future__ import annotations

from pathlib import Path

import yaml

from .models import AgentRolesConfig


class ConfigLoadError(Exception):
    pass


def load_config(path: str | Path) -> AgentRolesConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigLoadError(f"Config file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"YAML parse error in {path}: {e}") from e

    if raw is None:
        raise ConfigLoadError(f"Config file is empty: {path}")

    if not isinstance(raw, dict):
        raise ConfigLoadError(f"Config must be a YAML mapping, got {type(raw).__name__}")

    if "roles" not in raw:
        raise ConfigLoadError("Missing required field: roles")

    if not isinstance(raw["roles"], dict):
        raise ConfigLoadError("roles must be a mapping")

    if not raw["roles"]:
        raise ConfigLoadError("roles must contain at least one role definition")

    try:
        return AgentRolesConfig.model_validate(raw)
    except Exception as e:
        raise ConfigLoadError(f"Config validation error: {e}") from e
