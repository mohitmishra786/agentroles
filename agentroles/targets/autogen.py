from __future__ import annotations

from pathlib import Path

from agentroles.models import AgentRolesConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator


AUTOGEN_PY_TEMPLATE = '''\
"""autogen_agents.py — Auto-generated AutoGen agents from agentroles.yaml.

Usage:
    python autogen_agents.py
"""

import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

{agent_blocks}

agents = [{agent_names}]

selector_client = {first_role_model}

group_chat = SelectorGroupChat(
    participants=agents,
    model_client=selector_client,
    termination_condition=None,
)


async def main() -> None:
    result = await group_chat.run(task="Execute the agent workflow")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
'''

AGENT_BLOCK_TEMPLATE = """\
{var_name} = AssistantAgent(
    name="{role_name}",
    model_client=OpenAIChatCompletionClient(model="{model}"),
    description="{description}",
)
"""


class AutoGenGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.AUTOGEN

    def _generate_agents_py(self, config: AgentRolesConfig, base_dir: Path, output_rel: str, result: GenerationResult) -> None:
        target = base_dir / output_rel

        agent_blocks: list[str] = []
        agent_var_names: list[str] = []
        first_model = None

        for role_name, role_config in config.roles.items():
            safe_name = role_name.replace("-", "_").replace(" ", "_")
            var_name = f"agent_{safe_name}"

            if first_model is None:
                first_model = role_config.primary

            description = role_config.notes or f"AI agent for {role_name}"
            block = AGENT_BLOCK_TEMPLATE.format(
                var_name=var_name,
                role_name=role_name,
                model=role_config.primary,
                description=description,
            )
            agent_blocks.append(block)
            agent_var_names.append(var_name)

        if not agent_blocks:
            result.add_warning("No roles found — autogen_agents.py will be empty")
            return

        content = AUTOGEN_PY_TEMPLATE.format(
            agent_blocks="\n".join(agent_blocks),
            agent_names=", ".join(agent_var_names),
            first_role_model=f'OpenAIChatCompletionClient(model="{first_model}")',
        )

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        result.add_file(str(target))

    def generate(self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        self._generate_agents_py(config, base_dir, output_path, result)
