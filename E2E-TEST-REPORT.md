# Evidence to Audio end-to-end test report

## Scope

The harness drives the installed CLI through a local fake OpenAI-compatible
endpoint. It exercises all three parallel scouts, the critic, editor, producer,
artifact generation, validation, and the separate narration gate. Fixtures are
fictional. No source text, API key, script, or audio leaves the test process.

## Required categories

| ID | Category | Expected behavior |
| --- | --- | --- |
| U01 | CLI discovery | Run, validate, and render commands are visible |
| U02 | Complete pipeline | Six editorial calls finish and write a script |
| U03 | Validation | Generated run passes a second CLI command |
| U04 | Scout independence | Three named scout artifacts remain inspectable |
| U05 | Provenance | Manifest records the exact source filenames |
| U06 | Audience boundary | Listener profile reaches every editorial agent |
| U07 | Source filtering | Hidden and unsupported files remain excluded |
| U08 | Stable ordering | Nested source filenames have deterministic order |
| U09 | Public sample | Repository sample run remains valid |
| U10 | Narration approval | Audio requires a separate explicit acknowledgement |
| A01 | Empty input | No supported sources stops before provider use |
| A02 | Missing key | Named but absent provider key fails closed |
| A03 | HTTP failure | Provider outage cannot create a completed run |
| A04 | Invalid JSON | Malformed provider response fails closed |
| A05 | Missing content | Response without message text fails closed |
| A06 | Empty content | Blank provider response fails closed |
| A07 | Runtime ceiling | More than 90 minutes is rejected before calls |
| A08 | Spoken URL | Validator rejects a URL in narration copy |
| A09 | Visual Markdown | Headings and list markers are rejected in spoken copy |
| A10 | Changed script | Post-run mutation blocks rendering before external TTS |

## Run locally

Python 3.11 or newer is required. The E2E suite binds only to local loopback.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest tests/test_e2e_contract.py -v
python -m unittest discover -s tests -v
python -m evidence_to_audio validate --run examples/sample-run
python -m py_compile evidence_to_audio/*.py
evidence-to-audio --help
```

## Debug and extend

Run one case by its fully qualified test name. Keep all source packs,
organizations, actors, and claims fictional; use `example.invalid` for domains.
Extend the fake endpoint for response-shape or provider-failure behavior. Do not
add a real provider, key, speech service, generated audio, or private source pack
to the deterministic suite. New features need both a successful user behavior
and the closest privacy, validation, provider, or approval failure.

## Verification record

Status: local and GitHub Actions verification passed on September 11, 2026.
GitHub Actions run
[`34666087892`](https://github.com/wayanvota/evidence-to-audio/actions/runs/34666087892)
passed on Python 3.11, 3.12, and 3.13.

- 20 of 20 explicit E2E categories passed.
- 35 of 35 total tests passed.
- Public sample validation, byte-compilation, and installed CLI discovery passed.
