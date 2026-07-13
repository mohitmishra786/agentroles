# LangGraph

## Generated File

| File | Description |
|---|---|
| `langgraph_workflow.py` | A Python module with a `StateGraph` workflow — one node per role, each bound to its primary model |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and produces a LangGraph workflow:

1. Defines an `AgentState` TypedDict with a `messages` list and `next` field
2. Creates one `ChatModel` instance per role bound to that role's primary model
3. Registers one graph node per role, each invoking its `ChatModel`
4. Chains nodes in a linear sequence via `add_edge`, then routes the last node to `END`
5. Provides `build_workflow()` and `run_workflow()` entry points

```
langgraph_workflow.py
├── State = AgentState(messages, next)
├── model_<role1> = ChatModel(model="<primary1>")
├── model_<role2> = ChatModel(model="<primary2>")
├── node_<role1>(state) → invokes model_<role1>
├── node_<role2>(state) → invokes model_<role2>
└── build_workflow() → StateGraph with edges + compile()
```

## Usage

```bash
agentroles build
python langgraph_workflow.py
```

## Limitations

- The workflow is strictly linear — it does not generate conditional branching or cycles
- Each node simply invokes the model on the full message history; no tools, memory, or human-in-the-loop
- Fallback models are not wired as backup model instances
- Assumes an OpenAI-compatible `ChatModel` interface; adjust the import if using a different LangChain provider
