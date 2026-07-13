from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentroles.models import AgentRolesConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator

ROLE_MAP = {
    "planner": "chat",
    "implementer": "autocomplete",
}


def _extract_provider(primary: str) -> str:
    return primary.split("/", 1)[0]


def _extract_model(primary: str) -> str:
    return primary.split("/", 1)[1] if "/" in primary else primary


class CodyGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.CODY

    def _build_config(self, config: AgentRolesConfig) -> dict[str, Any]:
        cfg: dict[str, Any] = {
            "models": {},
        }

        for role_name, role_config in config.roles.items():
            if role_name in ROLE_MAP:
                mapped_key = ROLE_MAP[role_name]
                cfg["models"][mapped_key] = {
                    "provider": _extract_provider(role_config.primary),
                    "model": _extract_model(role_config.primary),
                }

        if "chat" not in cfg["models"]:
            cfg["models"]["chat"] = {"provider": "anthropic", "model": "claude-sonnet-4-5"}
        if "autocomplete" not in cfg["models"]:
            cfg["models"]["autocomplete"] = {"provider": "anthropic", "model": "claude-haiku-4-5"}

        return cfg

    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        cody_config = self._build_config(config)

        target = base_dir / output_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(cody_config, indent=2) + "\n")
        result.add_file(str(target))
