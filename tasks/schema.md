# Task schema

Each task is a YAML file with:

- `id`: unique string
- `split`: `train` or `heldout`
- `prompt`: user message
- `expected`: exact expected answer line (including `ANSWER:` prefix)
- `mock_tokens`: list of substrings; the mock backend succeeds when all appear in harness text
- `tags`: optional metadata

Checkers: exact match on normalized whitespace for the full response or the `ANSWER:` line.
