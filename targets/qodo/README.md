# Qodo Adapter

Generates `.qodo/config.json` from `agentroles.yaml`.

## Role Mapping

Qodo Gen supports multi-model configuration via its settings file. All agentroles roles are mapped
directly to model references in Qodo's expected format:

| AgentRoles Role | Qodo Model Reference |
|-----------------|---------------------|
| *(all roles)*   | role_name → { provider, model } |

## Generated File

- `.qodo/config.json` — JSON with a `models` object mapping each role name to a `{ provider, model }`

  pair, plus a `_usage` field describing how to use the config.

## Usage

1. Add `qodo` to your `agentroles.yaml` targets:

   ```yaml
   targets:

     - qodo: ./.qodo/config.json

   ```

2. Run `agentroles build`
3. Reference the generated model config in Qodo Gen's settings UI or configuration file.

## Limitations

- Qodo Gen's configuration format is evolving. This adapter generates a model reference mapping

  that should be adapted to your specific Qodo Gen integration.

- Qodo includes Qodo Gen (IDE agent) and Qodo Merge (PR review). This adapter targets Qodo Gen

  specifically.

## Notes

Qodo (formerly Codium AI) provides AI-powered code generation and testing tools. The multi-model
config allows assigning different models for different coding tasks, aligning with agentroles'
role-based approach.
