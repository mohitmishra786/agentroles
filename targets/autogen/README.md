# AutoGen

## Generated File

| File | Description |
|---|---|
| `autogen_agents.py` | Creates one `AssistantAgent` per role with its own `OpenAIChatCompletionClient`, plus a `SelectorGroupChat` |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and produces a Python script that:

1. Creates one `AssistantAgent` per role, each bound to a distinct `OpenAIChatCompletionClient(model="<primary>")`
2. Compiles all agents into a `SelectorGroupChat` using the first role's model as the selector
3. Provides an `async main()` entry point that runs the group chat

``` bash
autogen_agents.py
├── agent_<role1> = AssistantAgent(name="<role1>", model_client=...)
├── agent_<role2> = AssistantAgent(name="<role2>", model_client=...)
├── agents = [agent_<role1>, agent_<role2>, ...]
└── group_chat = SelectorGroupChat(participants=agents, model_client=...)
```

## Usage

```bash
agentroles build
python autogen_agents.py
```

## Limitations

- The selector model defaults to the first role's primary model — adjust if you want a different router
- `OpenAIChatCompletionClient` is used for all providers; provider-specific
  authentication must be configured via environment variables
- Fallback models from `agentroles.yaml` are not wired into AutoGen
- Termination conditions are not set — add `MaxMessageTermination` or `TextMentionTermination` for production use
