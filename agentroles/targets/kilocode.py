from __future__ import annotations

import json
from pathlib import Path

from agentroles.models import AgentRolesConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator

_PRIMARY_ROLES = {"planner", "implementer"}


class KiloCodeGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.KILOCODE

    def _build_agent_block(self, config: AgentRolesConfig) -> dict:
        agents: dict[str, dict] = {}
        for role_name, role_config in config.roles.items():
            agent_entry: dict = {
                "mode": "primary" if role_name in _PRIMARY_ROLES else "subagent",
                "model": role_config.primary,
            }
            if role_config.notes:
                agent_entry["description"] = role_config.notes
            agents[role_name] = agent_entry
        return {
            "agent_type": "kilocode",
            "agent": agents,
        }

    def generate(
        self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult
    ) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        target = base_dir / output_path
        agents_block = self._build_agent_block(config)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(agents_block, indent=2) + "\n")
        result.add_file(str(target))
