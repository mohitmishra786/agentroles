from __future__ import annotations

from pathlib import Path

from agentroles.models import AgentRolesConfig, TargetType
from agentroles.plugin import GenerationResult, TargetGenerator


LANGGRAPH_PY_TEMPLATE = '''\
"""langgraph_workflow.py — Auto-generated LangGraph workflow from agentroles.yaml.

Usage:
    python langgraph_workflow.py
"""

import operator
from typing import Annotated, Any, Literal, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph

{chat_model_setup}

{node_functions}

def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

{node_registrations}

    workflow.set_entry_point("{entry_node}")

{edges}

{conditional_routes}

    return workflow.compile()


def run_workflow(task: str) -> dict:
    graph = build_workflow()
    initial_state = {{"messages": [HumanMessage(content=task)], "next": ""}}
    result = graph.invoke(initial_state)
    return result


if __name__ == "__main__":
    result = run_workflow("Execute the agent workflow")
    print(result)
'''

CHAT_MODEL_SETUP_TEMPLATE = """\
# Per-role model bindings
{chat_models}
"""

NODE_FUNC_TEMPLATE = """\
def {func_name}(state: AgentState) -> dict:
    '''Node handler for the {role_name} agent.'''
    messages = state["messages"]
    response = {model_var}.invoke(messages)
    return {{"messages": [response], "next": "{next_role}"}}
"""


class LangGraphGenerator(TargetGenerator):
    @property
    def target_type(self) -> TargetType:
        return TargetType.LANGGRAPH

    def _generate_workflow_py(
        self,
        config: AgentRolesConfig,
        base_dir: Path,
        output_rel: str,
        result: GenerationResult,
    ) -> None:
        target = base_dir / output_rel

        role_names = list(config.roles.keys())
        if not role_names:
            result.add_warning("No roles found — langgraph_workflow.py will be empty")
            return

        model_vars: dict[str, str] = {}
        chat_model_lines: list[str] = []

        for role_name, role_config in config.roles.items():
            safe_name = role_name.replace("-", "_").replace(" ", "_")
            var_name = f"model_{safe_name}"
            model_vars[role_name] = var_name
            chat_model_lines.append(
                f'{var_name} = ChatModel(model="{role_config.primary}")'
            )

        chat_model_setup = CHAT_MODEL_SETUP_TEMPLATE.format(
            chat_models="\n".join(chat_model_lines),
        )

        node_funcs: list[str] = []
        for i, role_name in enumerate(role_names):
            next_role = role_names[i + 1] if i + 1 < len(role_names) else "END"
            safe_name = role_name.replace("-", "_").replace(" ", "_")
            func_text = NODE_FUNC_TEMPLATE.format(
                func_name=f"node_{safe_name}",
                role_name=role_name,
                model_var=model_vars[role_name],
                next_role=next_role,
            )
            node_funcs.append(func_text)

        node_reg_lines: list[str] = []
        for role_name in role_names:
            safe_name = role_name.replace("-", "_").replace(" ", "_")
            node_reg_lines.append(
                f'    workflow.add_node("{safe_name}", node_{safe_name})'
            )

        edge_lines: list[str] = []
        for i in range(len(role_names) - 1):
            src = role_names[i].replace("-", "_").replace(" ", "_")
            dst = role_names[i + 1].replace("-", "_").replace(" ", "_")
            edge_lines.append(f'    workflow.add_edge("{src}", "{dst}")')

        last_role = role_names[-1].replace("-", "_").replace(" ", "_")
        conditional_routes = f'    workflow.add_conditional_edges("{last_role}", lambda s: END, {{END: END}})'

        content = LANGGRAPH_PY_TEMPLATE.format(
            chat_model_setup=chat_model_setup,
            node_functions="\n".join(node_funcs),
            node_registrations="\n".join(node_reg_lines),
            entry_node=role_names[0].replace("-", "_").replace(" ", "_"),
            edges="\n".join(edge_lines) if edge_lines else "    pass",
            conditional_routes=conditional_routes,
        )

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        result.add_file(str(target))

    def generate(
        self, config: AgentRolesConfig, base_dir: Path, result: GenerationResult
    ) -> None:
        output_path = config.get_target_path(self.target_type)
        if not output_path:
            return

        self._generate_workflow_py(config, base_dir, output_path, result)
