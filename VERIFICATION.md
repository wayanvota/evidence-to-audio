# Verification

This file records checks for the initial public release. It does not claim that model outputs are accurate or that every provider behaves the same way.

## Automated checks

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m evidence_to_audio validate --run examples/sample-run
python3 -m compileall -q evidence_to_audio tests
python3 -m venv /tmp/evidence-to-audio-venv
/tmp/evidence-to-audio-venv/bin/python -m pip install -e .
/tmp/evidence-to-audio-venv/bin/evidence-to-audio validate --run examples/sample-run
```

Expected result:

- Fifteen unit tests pass.
- The synthetic sample run validates.
- Python compilation completes without error.
- A fresh editable installation exposes a working command-line entry point.

## Manual checks

- README quick-start commands match the CLI.
- Every documented file exists.
- Synthetic examples contain no real organizations or private source material.
- `.gitignore` excludes environment files, generated runs, and audio.
- External Edge TTS narration fails unless `--approve-external-tts` is present.
- The final audio step remains separate from the editorial pipeline.
- Every editorial agent receives the configured listener profile and technicality ceiling.
- The script validator rejects spoken URLs, runtime overages, Markdown headings, and visual list markers.
- Public prose contains no unsupported performance or cost claims.

## Not verified by this repository

- Accuracy of any model-generated claim.
- Reliability, retention, privacy, or future availability of a hosted provider.
- Legal permission to process a user's source material.
- Audio quality for every voice, language, or listening environment.
- Independence between agents that use the same model.
