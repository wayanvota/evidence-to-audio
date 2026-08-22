from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ENV_PATTERN = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


class ConfigError(ValueError):
    """Raised when configuration is missing or internally inconsistent."""


@dataclass(frozen=True)
class ProjectSettings:
    title: str
    max_minutes: int
    target_words_per_minute: int
    output_dir: Path


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    kind: str
    base_url: str
    model: str
    api_key_env: str
    timeout_seconds: int
    max_output_tokens: int


@dataclass(frozen=True)
class AgentSettings:
    name: str
    provider: str
    prompt: Path


@dataclass(frozen=True)
class AudioSettings:
    engine: str
    voice: str
    rate: str
    pitch: str
    format: str


@dataclass(frozen=True)
class Settings:
    root: Path
    project: ProjectSettings
    providers: dict[str, ProviderSettings]
    scouts: tuple[AgentSettings, ...]
    critic: AgentSettings
    editor: AgentSettings
    producer: AgentSettings
    audio: AudioSettings


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), ""), value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def _required(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ConfigError(f"Missing {context}.{key}")
    return mapping[key]


def _agent(name: str, raw: dict[str, Any], root: Path) -> AgentSettings:
    return AgentSettings(
        name=name,
        provider=str(_required(raw, "provider", f"agents.{name}")),
        prompt=(root / str(_required(raw, "prompt", f"agents.{name}"))).resolve(),
    )


def load_settings(path: str | Path) -> Settings:
    config_path = Path(path).resolve()
    root = config_path.parent
    with config_path.open("rb") as handle:
        raw = _expand_env(tomllib.load(handle))

    project_raw = raw.get("project", {})
    project = ProjectSettings(
        title=str(project_raw.get("title", "Personal Audio Brief")),
        max_minutes=int(project_raw.get("max_minutes", 90)),
        target_words_per_minute=int(project_raw.get("target_words_per_minute", 160)),
        output_dir=(root / str(project_raw.get("output_dir", "runs"))).resolve(),
    )
    if project.max_minutes < 1 or project.max_minutes > 90:
        raise ConfigError("project.max_minutes must be between 1 and 90")
    if project.target_words_per_minute < 100 or project.target_words_per_minute > 220:
        raise ConfigError("project.target_words_per_minute must be between 100 and 220")

    providers: dict[str, ProviderSettings] = {}
    for name, provider_raw in raw.get("providers", {}).items():
        providers[name] = ProviderSettings(
            name=name,
            kind=str(provider_raw.get("kind", "openai_compatible")),
            base_url=str(_required(provider_raw, "base_url", f"providers.{name}")).rstrip("/"),
            model=str(_required(provider_raw, "model", f"providers.{name}")),
            api_key_env=str(provider_raw.get("api_key_env", "")),
            timeout_seconds=int(provider_raw.get("timeout_seconds", 120)),
            max_output_tokens=int(provider_raw.get("max_output_tokens", 6000)),
        )
    if not providers:
        raise ConfigError("At least one provider must be configured")

    agents_raw = raw.get("agents", {})
    scouts_raw = agents_raw.get("scouts", {})
    if len(scouts_raw) < 2:
        raise ConfigError("Configure at least two independent scouts")
    scouts = tuple(_agent(name, value, root) for name, value in scouts_raw.items())
    critic = _agent("critic", _required(agents_raw, "critic", "agents"), root)
    editor = _agent("editor", _required(agents_raw, "editor", "agents"), root)
    producer = _agent("producer", _required(agents_raw, "producer", "agents"), root)

    for agent in (*scouts, critic, editor, producer):
        if agent.provider not in providers:
            raise ConfigError(f"Agent {agent.name} names unknown provider {agent.provider}")
        if not agent.prompt.is_file():
            raise ConfigError(f"Prompt file not found for {agent.name}: {agent.prompt}")

    audio_raw = raw.get("audio", {})
    audio = AudioSettings(
        engine=str(audio_raw.get("engine", "edge-tts")),
        voice=str(audio_raw.get("voice", "en-AU-NatashaNeural")),
        rate=str(audio_raw.get("rate", "+8%")),
        pitch=str(audio_raw.get("pitch", "-2Hz")),
        format=str(audio_raw.get("format", "mp3")),
    )

    return Settings(
        root=root,
        project=project,
        providers=providers,
        scouts=scouts,
        critic=critic,
        editor=editor,
        producer=producer,
        audio=audio,
    )
