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


class ZedAIGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.ZED_AI

    def _build_settings(self, config: AgentRolesConfig) -> dict[str, Any]:
        settings: dict[str, Any] = {
            "assistant": {},
        }

        primary_role = None
        if config.roles:
            primary_role = list(config.roles.items())[0]

        if primary_role:
            role_name, role_config = primary_role
            settings["assistant"]["default_model"] = {
                "provider": _extract_provider(role_config.primary),
                "model": _extract_model(role_config.primary),
            }
            settings["assistant"]["provider"] = _extract_provider(role_config.primary)

            if role_config.notes:
                settings["_notes"] = (
                    f"Zed AI supports a single assistant model. "
                    f"Primary model set from '{role_name}' role. "
                    f"Original role notes: {role_config.notes}"
                )
            else:
                settings["_notes"] = (
                    f"Zed AI supports a single assistant model. "
                    f"Primary model set from '{role_name}' role."
                )
        else:
            settings["assistant"]["default_model"] = {
                "provider": "anthropic",
                "model": "claude-sonnet-4-5",
            }
            settings["assistant"]["provider"] = "anthropic"

        return settings

    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        settings = self._build_settings(config)

        target = base_dir / output_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(settings, indent=2) + "\n")
        result.add_file(str(target))
