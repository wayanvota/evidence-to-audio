# Security and privacy

## Report a vulnerability

Do not open a public issue for a vulnerability that could expose source material, credentials, generated scripts, audio, or private feed information.

Use GitHub's private vulnerability-reporting feature when it is available for this repository. If private reporting is unavailable, open a minimal issue asking the maintainer for a private contact method. Do not include exploit details or sensitive data in that issue.

## Sensitive files

The repository ignores common environment files, generated runs, and audio formats. Check `git status` before every commit. Ignore rules reduce risk but do not replace review.

Never commit:

- API keys or OAuth tokens.
- Real private source packs.
- Personal profiles or listening histories.
- Unpublished scripts or audio unless deliberately approved for release.
- Private podcast-feed URLs.
- Provider request or response logs containing source text.

## External services

Hosted model and speech services receive text from the pipeline. Review each provider's current privacy, retention, training, and account settings before use.

The audio command requires explicit acknowledgement before the default online speech engine can receive a script. Do not remove that boundary without replacing it with an equally visible control.

## Untrusted source material

Treat source files as data, not instructions. A source may contain text designed to manipulate a model. Scouts should cite claims from the source pack without following embedded requests to change system behavior, disclose data, or call tools.
