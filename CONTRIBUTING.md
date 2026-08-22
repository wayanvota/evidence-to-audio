# Contributing

Evidence to Audio welcomes focused contributions that improve evidence quality, provider portability, validation, privacy, or listening value.

## Before opening an issue

Search existing issues. Use synthetic or public examples. Never include credentials, private source packs, personal audio, private feed addresses, copyrighted full text, or personal data.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

## Pull-request standard

A pull request should:

- Solve one defined problem.
- Explain the user-facing effect.
- Include or update tests.
- Preserve the human approval gate before external narration.
- Avoid adding a required paid service to the core package.
- Avoid committing generated runs, source packs, credentials, or audio.
- Update documentation when behavior changes.

For changes to prompts, explain which failure the change addresses and how you tested it. More instructions are not automatically better instructions.

## Commit style

Use a short imperative subject, such as:

```text
Add transcript length validation
Clarify external speech approval
Support per-agent provider settings
```

## Code style

- Support Python 3.11 and newer.
- Prefer the standard library for core behavior.
- Keep provider-specific code behind a small adapter.
- Fail with a clear message rather than silently substituting a provider or source.
- Preserve partial artifacts when they help diagnose a failed run.
