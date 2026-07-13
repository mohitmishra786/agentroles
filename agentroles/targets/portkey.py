from __future__ import annotations

import json
from pathlib import Path

from agentroles.models import AgentRolesConfig, RoleConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator


PORTKEY_DEFAULT_STRATEGY = "fallback"


class PortkeyGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.PORTKEY

    def _build_role_config(self, role_name: str, role_config: RoleConfig) -> dict:
        targets: list[dict] = [
            {
                "provider": role_config.primary.split("/")[0],
                "model": role_config.primary,
            }
        ]

        for fb in role_config.fallback:
            targets.append({"provider": fb.split("/")[0], "model": fb})

        entry: dict = {
            "strategy": PORTKEY_DEFAULT_STRATEGY,
            "targets": targets,
        }

        override_params: dict = {}
        if role_config.max_cost_per_call_usd is not None:
            override_params["max_tokens"] = 4096
        if override_params:
            entry["override_params"] = override_params

        return entry

    def generate(
        self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult
    ) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        target = base_dir / output_path

        portkey_config: dict = {}
        for role_name, role_config in config.roles.items():
            portkey_config[role_name] = self._build_role_config(role_name, role_config)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(portkey_config, indent=2) + "\n")
        result.add_file(str(target))
