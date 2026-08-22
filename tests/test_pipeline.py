import json
import tempfile
import textwrap
import unittest
from datetime import UTC, datetime
from pathlib import Path

from evidence_to_audio.config import load_settings
from evidence_to_audio.pipeline import Pipeline, load_source_pack
from evidence_to_audio.validation import validate_run


class FakeProvider:
    def complete(self, system: str, user: str) -> str:
        if "scout" in system:
            return "# Scout report\n\nKEEP: One supported idea with a visible limit."
        if system == "critic":
            return "# Critic\n\nKEEP one idea. KILL repetition."
        if system == "editor":
            return "A concise spoken draft with one useful idea."
        if system == "producer":
            return "A concise spoken script with one useful idea."
        return "Unexpected"


def write_pipeline_project(root: Path) -> Path:
    prompts = root / "prompts"
    prompts.mkdir()
    for name, content in {
        "scout-a.md": "scout a",
        "scout-b.md": "scout b",
        "critic.md": "critic",
        "editor.md": "editor",
        "producer.md": "producer",
    }.items():
        (prompts / name).write_text(content, encoding="utf-8")
    config = root / "config.toml"
    config.write_text(
        textwrap.dedent(
            """
            [project]
            title = "Test brief"
            max_minutes = 10
            target_words_per_minute = 160
            output_dir = "runs"

            [providers.primary]
            kind = "openai_compatible"
            base_url = "http://localhost:1/v1"
            model = "test"
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


class PipelineTests(unittest.TestCase):
    def test_source_pack_ignores_hidden_and_unsupported_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one.md").write_text("one", encoding="utf-8")
            (root / ".secret.md").write_text("secret", encoding="utf-8")
            (root / "image.png").write_bytes(b"png")
            content, names = load_source_pack(root)
            self.assertEqual(names, ["one.md"])
            self.assertIn("one", content)
            self.assertNotIn("secret", content)

    def test_pipeline_writes_inspectable_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = write_pipeline_project(root)
            sources = root / "sources"
            sources.mkdir()
            (sources / "source.md").write_text("Synthetic evidence.", encoding="utf-8")
            settings = load_settings(config)
            pipeline = Pipeline(
                settings,
                provider_factory=lambda _settings: FakeProvider(),
                clock=lambda: datetime(2026, 8, 22, 14, 0, tzinfo=UTC),
            )
            run_dir = pipeline.run(sources)
            self.assertTrue((run_dir / "critic.md").is_file())
            self.assertTrue((run_dir / "script.txt").is_file())
            self.assertEqual(len(list((run_dir / "scouts").glob("*.md"))), 2)
            self.assertEqual(validate_run(run_dir), [])
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["audio_rendered"])


if __name__ == "__main__":
    unittest.main()
