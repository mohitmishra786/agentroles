from __future__ import annotations

import json
from pathlib import Path

from agentroles.models import AgentRolesConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator


class ManifestGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.MANIFEST

    def _build_routes(self, config: AgentRolesConfig) -> list[dict]:
        routes: list[dict] = []
        for role_name, role_config in config.roles.items():
            provider, model_id = role_config.primary.split("/", 1)
            route: dict = {
                "id": f"role-{role_name}",
                "method": "POST",
                "path": "/v1/chat/completions",
                "headers": {
                    "X-Agent-Role": role_name,
                },
                "target": {
                    "provider": provider,
                    "model": model_id,
                },
            }
            routes.append(route)
        return routes

    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        target = base_dir / output_path

        routes = self._build_routes(config)
        manifest: dict = {
            "description": "AgentRoles → Manifest per-role routing via X-Agent-Role header",
            "source": "agentroles.yaml",
            "routes": routes,
        }

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(manifest, indent=2) + "\n")
        result.add_file(str(target))
