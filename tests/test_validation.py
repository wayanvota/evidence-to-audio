import json
import tempfile
import unittest
from pathlib import Path

from evidence_to_audio.validation import validate_run


class ValidationTests(unittest.TestCase):
    def test_rejects_spoken_url_and_word_overage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scouts").mkdir()
            (root / "scouts" / "a.md").write_text("a", encoding="utf-8")
            (root / "scouts" / "b.md").write_text("b", encoding="utf-8")
            for name in ("critic.md", "draft-script.txt"):
                (root / name).write_text("content", encoding="utf-8")
            script = "visit https://example.com " + "word " * 200
            (root / "script.txt").write_text(script, encoding="utf-8")
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "max_minutes": 1,
                        "target_words_per_minute": 100,
                        "script_words": len(script.split()),
                    }
                ),
                encoding="utf-8",
            )
            errors = validate_run(root)
            self.assertTrue(any("ceiling" in error for error in errors))
            self.assertTrue(any("URL" in error for error in errors))

    def test_missing_runtime_settings_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "scouts").mkdir()
            (root / "scouts" / "one.md").write_text("One", encoding="utf-8")
            (root / "scouts" / "two.md").write_text("Two", encoding="utf-8")
            (root / "critic.md").write_text("Critic", encoding="utf-8")
            (root / "draft-script.txt").write_text("Draft", encoding="utf-8")
            (root / "script.txt").write_text("Final script", encoding="utf-8")
            (root / "manifest.json").write_text(
                json.dumps({"script_words": 2}), encoding="utf-8"
            )

            errors = validate_run(root)
            self.assertIn("manifest is missing valid runtime settings", errors)


if __name__ == "__main__":
    unittest.main()
