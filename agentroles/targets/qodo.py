from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentroles.models import AgentRolesConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator


def _extract_provider(primary: str) -> str:
    return primary.split("/", 1)[0]


def _extract_model(primary: str) -> str:
    return primary.split("/", 1)[1] if "/" in primary else primary


class QodoGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.QODO

    def _build_config(self, config: AgentRolesConfig) -> dict[str, Any]:
        models: dict[str, Any] = {}

        for role_name, role_config in config.roles.items():
            models[role_name] = {
                "provider": _extract_provider(role_config.primary),
                "model": _extract_model(role_config.primary),
            }
            if role_config.notes:
                models[role_name]["description"] = role_config.notes

        qodo_config: dict[str, Any] = {
            "models": models,
            "_usage": (
                "Each role is mapped to a model reference in Qodo Gen's expected format. "
                "Configure Qodo Gen to reference these models in its settings UI or config file."
            ),
        }

        return qodo_config

    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        qodo_config = self._build_config(config)

        target = base_dir / output_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(qodo_config, indent=2) + "\n")
        result.add_file(str(target))
