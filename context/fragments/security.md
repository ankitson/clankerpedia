# Security: Secrets & Credentials
- If you need a secret, check 1password with the `op` CLI - see the 1password skill
- NEVER output passwords, API keys, tokens, secrets, or credentials of any kind in messages, tool calls, tool results, thinking traces, or any other output. This includes in log output, error messages, debug info, or any content that could be visible to users or persisted.
- When displaying or returning results that contain secrets, redact them (e.g., `sk-****...****`).
- When checking environment variables or config files for debugging, mask or truncate any secret values before displaying them.
