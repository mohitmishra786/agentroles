# CrewAI

## Generated Files

| File | Description |
|---|---|
| `config/agents.yaml` | Per-role CrewAI Agent definitions with `role`, `goal`, `backstory`, and `llm` fields |
| `config/tasks.yaml` | Per-role Task definitions that reference agents by role name |
| `crew.py` | Standalone Python script that loads agents/tasks and assembles a `Crew` |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and produces a full CrewAI project scaffold:

``` yaml
crewai_output/
├── config/
│   ├── agents.yaml    ← one Agent per role with primary model as llm
│   └── tasks.yaml     ← one Task per role, referencing agent by name
└── crew.py            ← Python entry point: Agent → Task → Crew → kickoff()
```

Each role becomes a CrewAI `Agent` with:

- `role` — the role name from `agentroles.yaml`
- `goal` — a synthesized goal based on the role name
- `backstory` — from `role.notes`, or a sensible default
- `llm` — set to the role's `primary` model string (e.g., `openai/gpt-5.5`)

## Usage

```bash
agentroles build          # generates the files
cd crewai_output
python crew.py            # runs the Crew kickoff
```

## Limitations

- Tasks use placeholder descriptions — replace them with actual work items
- The `llm` string is passed directly; CrewAI's model resolution depends on the installed providers
- Only a linear `Agent → Task` per-role structure is generated; no complex dependencies or delegation
- Fallback models from `agentroles.yaml` are not expressed in the CrewAI config
