# Customization

## Define the listener first

The same source pack can produce a technical briefing, an executive briefing, or a practical builder briefing. Set the audience before changing agent prompts:

```toml
[audience]
role = "A business builder who directs AI agents but does not write the implementation"
goal = "Give better direction, judge the result, and improve the next iteration"
workflow = "I define the outcome and constraints; an AI agent builds and tests; I review the evidence and decide what happens next"
technicality = 3
```

Technicality runs from one to ten. One focuses almost entirely on business outcomes and observable checks. Ten assumes the listener wants implementation details. The pipeline passes this profile to every agent so selection changes before the script is written.

## Add a scout

Create a prompt under `prompts/`, then add an entry under `[agents.scouts]` in `config.toml`:

```toml
[agents.scouts.legal]
provider = "primary"
prompt = "prompts/scout-legal.md"
```

The pipeline discovers configured scouts and runs them in parallel. Keep at least two.

## Use different models by role

Add another provider and assign it to one or more agents:

```toml
[providers.critic_model]
kind = "openai_compatible"
base_url = "https://your-provider.example/v1"
model = "your-model"
api_key_env = "CRITIC_API_KEY"

[agents.critic]
provider = "critic_model"
prompt = "prompts/critic.md"
```

## Change the subject

Replace the source pack and revise the scout prompts. Keep the Critic, Editor, Producer, human gate, and run artifacts unless the new use case provides a reason to change them.

## Add another speech engine

Implement another branch in `evidence_to_audio/audio.py`. A speech adapter should:

- Accept only an approved script path.
- Write one explicit output path.
- Fail when credentials or dependencies are missing.
- Disclose whether text leaves the machine.
- Verify that a nonempty audio file was created.

Do not hide external transmission inside a generic local-sounding engine name.

For the built-in local macOS narrator, use an installed system voice, an integer
rate in words per minute, and an AIFF output:

```toml
[audio]
engine = "macos-say"
voice = "Samantha"
rate = "175"
pitch = "0Hz"
format = "aiff"
```
