from __future__ import annotations

JSON_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AgentRoles Configuration",
    "description": "Tool-agnostic role-to-model mapping for agentic coding workflows.",
    "type": "object",
    "required": ["version", "roles"],
    "properties": {
        "version": {
            "type": "integer",
            "enum": [1],
            "description": "Schema version — only 1 is currently supported.",
        },
        "roles": {
            "type": "object",
            "description": "Role name → model configuration map.",
            "minProperties": 1,
            "additionalProperties": {
                "type": "object",
                "required": ["primary"],
                "properties": {
                    "primary": {
                        "type": "string",
                        "description": "Primary model in provider/model-id format (e.g., anthropic/claude-opus-4-8).",
                        "pattern": "^[a-z][a-z0-9_]*/[a-zA-Z0-9._\\-]+$",
                    },
                    "fallback": {
                        "type": "array",
                        "description": "Ordered fallback models.",
                        "items": {
                            "type": "string",
                            "pattern": "^[a-z][a-z0-9_]*/[a-zA-Z0-9._\\-]+$",
                        },
                    },
                    "max_cost_per_call_usd": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Cost ceiling per call in USD.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Human-readable notes about this role.",
                    },
                },
                "additionalProperties": False,
            },
        },
        "routing": {
            "type": "object",
            "description": "Routing strategy & dynamic escalation configuration.",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["static", "dynamic"],
                    "description": "Routing strategy (static = generate configs only; dynamic = enable runtime escalation).",
                },
                "dynamic": {
                    "type": "object",
                    "description": "Dynamic/escalation routing settings (used only when mode=dynamic).",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "Enable runtime escalation component.",
                        },
                        "escalate_on": {
                            "type": "array",
                            "description": "Signals that trigger escalation to the next fallback model.",
                            "items": {
                                "type": "string",
                                "enum": ["low_confidence", "test_failure", "plan_revision"],
                            },
                            "uniqueItems": True,
                        },
                        "cache_aware": {
                            "type": "boolean",
                            "description": "Consider cache-miss costs before escalating (avoid provider-switch on minor signals).",
                        },
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
        "observability": {
            "type": "object",
            "description": "Cost tracking & observability settings.",
            "properties": {
                "cost_tracking": {
                    "type": "boolean",
                    "description": "Enable per-call cost tracking.",
                },
                "tag_calls_with_role": {
                    "type": "boolean",
                    "description": "Tag outgoing requests with role= metadata for gateway dashboards.",
                },
            },
            "additionalProperties": False,
        },
        "targets": {
            "type": "array",
            "description": "List of target tool → output path mappings to generate configs for.",
            "items": {
                "type": "object",
                "minProperties": 1,
                "maxProperties": 1,
                "properties": {
                    "opencode": {"type": "string"},
                    "claude_code": {"type": "string"},
                    "aider": {"type": "string"},
                    "litellm_proxy": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}
