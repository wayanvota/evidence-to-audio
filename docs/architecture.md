# Architecture

Evidence to Audio separates editorial reasoning from audio rendering.

## Stage responsibilities

| Stage | Reads | Writes | Decision right |
| --- | --- | --- | --- |
| Source pack | Collected source files | Normalized source context | Human chooses lawful, relevant inputs |
| Scouts | Same source pack | Independent reports | Each scout nominates and challenges ideas |
| Critic | All scout reports | KEEP, COMPRESS, and KILL decisions | Critic sets the editorial spine |
| Editor | Critic decision and scout reports | Draft spoken script | Editor creates coherent narration |
| Producer | Draft and critic decision | Final script | Producer cuts repetition and protects runtime |
| Human gate | Final script and artifacts | Approval or revision request | Human authorizes external narration |
| Renderer | Approved script | Audio file | Deterministic conversion only |

## Why the scouts run in parallel

Sequential scouts can inherit framing from earlier reports. Parallel scouts receive the same source pack and return independent first passes. The Critic sees all reports and can resolve overlap or disagreement.

This does not guarantee independence. Scouts that use the same model may share blind spots. The configuration supports different providers so users can test whether the editorial decision survives model diversity.

## Why narration is separate

Audio rendering can transmit the final script to another service. It can also create an authoritative-sounding artifact that is easy to share without its evidence record. A separate command creates a visible approval boundary and keeps the script available for review.

## Provider boundary

The reference client uses the OpenAI-compatible chat-completions shape because many hosted gateways and local servers support it. Provider-specific capabilities are intentionally excluded from the core. A provider adapter should return text and should not change editorial decisions, write files, or trigger external actions.

## Failure behavior

The pipeline fails closed when:

- A prompt file is missing.
- Fewer than two scouts are configured.
- A provider returns empty or malformed output.
- Required artifacts are absent.
- The final script exceeds its word ceiling.
- The spoken script contains a URL.
- External narration has not been explicitly approved.

Partial run artifacts remain available for diagnosis. A failed run is never treated as an approved episode.
