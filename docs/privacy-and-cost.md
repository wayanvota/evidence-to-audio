# Privacy and cost

Evidence to Audio can run with local or hosted model endpoints. Those choices have different privacy, cost, and reliability implications.

## Before using a hosted model

Confirm:

- Which text leaves your machine.
- Whether requests are retained or used for training.
- Where logs and backups are stored.
- Which account pays for requests.
- Whether the provider's terms permit your source material.
- Whether sensitive or copyrighted content should be summarized locally first.

Store credentials in environment variables. Never place keys in `config.toml`, source files, run artifacts, issue reports, or audio metadata.

## Before using hosted speech

The renderer requires `--approve-external-tts` for the online `edge-tts` engine. That flag records a conscious decision; it does not create a legal or technical guarantee.

The [`edge-tts`](https://github.com/rany2/edge-tts) package uses Microsoft's online speech service without requiring a personal API key. It is an unofficial client and can change or stop working. Do not use it for material you are unwilling to transmit to that service.

For sensitive scripts, add a local speech adapter or stop after producing `script.txt`.

## Cost controls

- Set provider timeouts and output-token limits.
- Keep the source pack focused.
- Use inexpensive or local models for scouts when quality is adequate.
- Reserve the strongest model for the Critic or final editor when evaluation shows that it helps.
- Treat the runtime as a ceiling.
- Render short voice auditions before a full episode.

Record provider, model, prompt version, runtime, and approximate cost in a private operating log if cost comparisons influence future choices.
