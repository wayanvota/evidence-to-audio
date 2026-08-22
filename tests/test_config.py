import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from evidence_to_audio.config import ConfigError, load_settings


PROMPT_NAMES = [
    "scout-a.md",
    "scout-b.md",
    "critic.md",
    "editor.md",
    "producer.md",
]


def write_project(root: Path, max_minutes: int = 90, technicality: int = 3) -> Path:
    prompts = root / "prompts"
    prompts.mkdir()
    for name in PROMPT_NAMES:
        (prompts / name).write_text(name, encoding="utf-8")
    config = root / "config.toml"
    config.write_text(
        textwrap.dedent(
            f"""
            [project]
            max_minutes = {max_minutes}
            output_dir = "runs"

            [audience]
            role = "Business builder"
            goal = "Direct better AI work"
            workflow = "I direct; the agent builds and tests; I review"
            technicality = {technicality}

            [providers.primary]
            kind = "openai_compatible"
            base_url = "${{TEST_BASE_URL}}"
            model = "test-model"
            api_key_env = ""

            [agents.scouts.a]
            provider = "primary"
            prompt = "prompts/scout-a.md"

            [agents.scouts.b]
            provider = "primary"
            prompt = "prompts/scout-b.md"

            [agents.critic]
            provider = "primary"
            prompt = "prompts/critic.md"

            [agents.editor]
            provider = "primary"
            prompt = "prompts/editor.md"

            [agents.producer]
            provider = "primary"
            prompt = "prompts/producer.md"

            [audio]
            engine = "edge-tts"
            voice = "en-AU-NatashaNeural"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return config


class ConfigTests(unittest.TestCase):
    def test_loads_and_expands_environment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = write_project(root)
            with patch.dict(os.environ, {"TEST_BASE_URL": "http://localhost:11434/v1"}):
                settings = load_settings(config)
            self.assertEqual(settings.providers["primary"].base_url, "http://localhost:11434/v1")
            self.assertEqual(len(settings.scouts), 2)
            self.assertEqual(settings.audio.voice, "en-AU-NatashaNeural")
            self.assertEqual(settings.audience.technicality, 3)
            self.assertEqual(settings.audience.role, "Business builder")

    def test_rejects_runtime_over_ninety_minutes(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = write_project(Path(temporary), max_minutes=91)
            with self.assertRaises(ConfigError):
                load_settings(config)

    def test_rejects_technicality_outside_scale(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = write_project(Path(temporary), technicality=11)
            with self.assertRaises(ConfigError):
                load_settings(config)


if __name__ == "__main__":
    unittest.main()
