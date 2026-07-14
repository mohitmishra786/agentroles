# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in agentroles, please report it privately. Do not open a public issue.

Send a detailed description of the vulnerability to the maintainers via GitHub's private vulnerability reporting feature:

1. Go to the [Security tab](https://GitHub.com/mohitmishra786/agentroles/security) on the repository
2. Click "Report a vulnerability"
3. Provide a detailed description, including steps to reproduce and any proof-of-concept code

You can also email the maintainers directly if you prefer.

## What to Include

- A clear description of the vulnerability
- Steps to reproduce the issue
- The affected versions of agentroles
- Any potential mitigations you've identified

## Response Timeline

- We will acknowledge receipt of your report within 48 hours
- We will provide an initial assessment within 5 business days
- We aim to release a fix within 30 days, depending on severity and complexity

## Supported Versions

Only the latest release receives security patches. Backports to older versions are not provided.

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Security Best Practices for Users

- Keep agentroles updated to the latest version
- Do not commit `agentroles.yaml` files containing API keys to public repositories
- Review generated config files before using them in production
- When using the LiteLLM proxy target, ensure the generated config uses environment variable references for API keys, not hardcoded values

## Supply Chain

- agentroles uses `pip-audit` and `npm audit` in CI to detect known vulnerabilities in dependencies
- Dependabot is configured to automatically open PRs for dependency updates
- All releases are built and published via GitHub Actions with provenance attestation
