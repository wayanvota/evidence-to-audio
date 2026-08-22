from __future__ import annotations

import concurrent.futures
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from .config import AgentSettings, Settings
from .providers import TextProvider, build_provider


SUPPORTED_SOURCE_SUFFIXES = {".md", ".txt", ".json"}
SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def load_source_pack(source_dir: str | Path) -> tuple[str, list[str]]:
    root = Path(source_dir).resolve()
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_SOURCE_SUFFIXES
        and not any(part.startswith(".") for part in path.relative_to(root).parts)
    )
    if not files:
        raise ValueError(f"No supported source files found in {root}")

    sections: list[str] = []
    names: list[str] = []
    for path in files:
        relative = str(path.relative_to(root))
        names.append(relative)
        sections.append(
            f"\n\n===== SOURCE: {relative} =====\n\n"
            + path.read_text(encoding="utf-8")
        )
    return "".join(sections).strip(), names


def _read_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _agent_slug(name: str) -> str:
    return SAFE_NAME.sub("-", name).strip("-").lower()


class Pipeline:
    def __init__(
        self,
        settings: Settings,
        provider_factory: Callable[[object], TextProvider] = build_provider,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self.settings = settings
        self.provider_factory = provider_factory
        self.clock = clock

    def _run_agent(self, agent: AgentSettings, context: str) -> str:
        provider = self.provider_factory(self.settings.providers[agent.provider])
        return provider.complete(_read_prompt(agent.prompt), context)

    def run(self, source_dir: str | Path) -> Path:
        source_pack, source_names = load_source_pack(source_dir)
        started = self.clock()
        run_name = started.strftime("%Y%m%dT%H%M%SZ")
        run_dir = self.settings.project.output_dir / run_name
        scouts_dir = run_dir / "scouts"
        scouts_dir.mkdir(parents=True, exist_ok=False)

        scout_results: dict[str, str] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.settings.scouts)) as pool:
            pending = {
                pool.submit(self._run_agent, agent, source_pack): agent
                for agent in self.settings.scouts
            }
            for future in concurrent.futures.as_completed(pending):
                agent = pending[future]
                scout_results[agent.name] = future.result()

        for name in sorted(scout_results):
            (scouts_dir / f"{_agent_slug(name)}.md").write_text(
                scout_results[name].rstrip() + "\n", encoding="utf-8"
            )

        combined_scouts = "\n\n".join(
            f"===== SCOUT: {name} =====\n\n{scout_results[name]}"
            for name in sorted(scout_results)
        )
        critic_context = (
            "Review these independent scout reports. The source files are listed below.\n\n"
            + "\n".join(f"- {name}" for name in source_names)
            + "\n\n"
            + combined_scouts
        )
        critic = self._run_agent(self.settings.critic, critic_context)
        (run_dir / "critic.md").write_text(critic.rstrip() + "\n", encoding="utf-8")

        editor_context = (
            f"Episode title: {self.settings.project.title}\n\n"
            f"Maximum runtime: {self.settings.project.max_minutes} minutes. "
            "Shorter is preferred when the evidence does not justify the time.\n\n"
            f"===== CRITIC DECISION =====\n\n{critic}\n\n"
            f"===== SCOUT REPORTS =====\n\n{combined_scouts}"
        )
        draft = self._run_agent(self.settings.editor, editor_context)
        (run_dir / "draft-script.txt").write_text(draft.rstrip() + "\n", encoding="utf-8")

        max_words = (
            self.settings.project.max_minutes
            * self.settings.project.target_words_per_minute
        )
        producer_context = (
            f"Maximum spoken-word ceiling: {max_words} words. This is a ceiling, not a target.\n\n"
            f"===== EDITOR DRAFT =====\n\n{draft}\n\n"
            f"===== CRITIC DECISION =====\n\n{critic}"
        )
        script = self._run_agent(self.settings.producer, producer_context)
        (run_dir / "script.txt").write_text(script.rstrip() + "\n", encoding="utf-8")

        manifest = {
            "schema_version": 1,
            "title": self.settings.project.title,
            "created_at": started.isoformat(),
            "source_files": source_names,
            "scouts": sorted(scout_results),
            "critic": self.settings.critic.name,
            "editor": self.settings.editor.name,
            "producer": self.settings.producer.name,
            "max_minutes": self.settings.project.max_minutes,
            "target_words_per_minute": self.settings.project.target_words_per_minute,
            "script_words": len(script.split()),
            "audio_rendered": False,
        }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        return run_dir
