# Manifest

## Generated File

| File | Description |
|---|---|
| `manifest-routes.json` | Database-driven routing config via `X-Agent-Role` headers |

## How It Works

The `agentroles` command reads your `agentroles.yaml` and generates a routing reference JSON:

```json
{
  "description": "AgentRoles → Manifest per-role routing via X-Agent-Role header",
  "source": "agentroles.yaml",
  "routes": [
    {
      "id": "role-planner",
      "method": "POST",
      "path": "/v1/chat/completions",
      "headers": {"X-Agent-Role": "planner"},
      "target": {"provider": "anthropic", "model": "claude-opus-4-8"}
    },
    {
      "id": "role-implementer",
      "method": "POST",
      "path": "/v1/chat/completions",
      "headers": {"X-Agent-Role": "implementer"},
      "target": {"provider": "anthropic", "model": "claude-haiku-4-5"}
    }
  ]
}
```

Each route:

- Uses `X-Agent-Role` header to identify which role is making the request
- Routes to the role's primary model and provider

## Usage

```bash
agentroles build                     # generates manifest-routes.json

# Import into Manifest's database or use as reference for manual setup

```

## Limitations

- This is a **configuration reference**, not a runnable Manifest database migration
- You must import the routes into Manifest's actual database or API
- Fallback models are not included — only primary models are routed
- The `provider` value needs to match Manifest's provider naming convention
