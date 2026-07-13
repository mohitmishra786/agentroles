from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from agentroles.models import AgentRolesConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator

ROLE_MAP = {
    "planner": "chat",
    "implementer": "edit",
    "summarizer": "autocomplete",
    "reviewer": "apply",
}

LEGACY_ROLES = ["chat", "edit", "apply", "autocomplete", "embed", "rerank"]


def _extract_provider(primary: str) -> str:
    return primary.split("/", 1)[0]


def _extract_model(primary: str) -> str:
    return primary.split("/", 1)[1] if "/" in primary else primary


class PearAIGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.PEARAI

    def _build_models(self, config: AgentRolesConfig) -> list[dict[str, Any]]:
        models: list[dict[str, Any]] = []
        assigned_roles: set[str] = set()

        for role_name, role_config in config.roles.items():
            if role_name in ROLE_MAP:
                mapped_role = ROLE_MAP[role_name]
                assigned_roles.add(mapped_role)
                provider = _extract_provider(role_config.primary)
                model_id = _extract_model(role_config.primary)
                models.append({
                    "model": model_id,
                    "provider": provider,
                    "roles": [mapped_role],
                })

        for legacy_role in LEGACY_ROLES:
            if legacy_role not in assigned_roles:
                models.append({
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "roles": [legacy_role],
                })

        return models

    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        models = self._build_models(config)

        target = base_dir / output_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"models": models}, indent=2) + "\n")
        result.add_file(str(target))
