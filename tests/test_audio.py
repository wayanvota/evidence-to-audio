import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from evidence_to_audio.audio import AudioError, render_audio
from evidence_to_audio.config import AudioSettings


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.settings = AudioSettings(
            engine="edge-tts",
            voice="en-AU-NatashaNeural",
            rate="+8%",
            pitch="-2Hz",
            format="mp3",
        )

    def test_external_tts_requires_explicit_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "script.txt"
            script.write_text("Approved script.", encoding="utf-8")
            with self.assertRaises(AudioError):
                render_audio(script, root / "episode.mp3", self.settings)

    @patch("evidence_to_audio.audio.subprocess.run")
    @patch("evidence_to_audio.audio.shutil.which", return_value="/usr/local/bin/edge-tts")
    def test_renderer_uses_configured_voice_and_pacing(self, _which, run):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "script.txt"
            output = root / "episode.mp3"
            script.write_text("Approved script.", encoding="utf-8")

            def create_output(command, **_kwargs):
                Path(command[-1]).write_bytes(b"audio")
                return Mock(returncode=0, stderr="", stdout="")

            run.side_effect = create_output
            result = render_audio(
                script,
                output,
                self.settings,
                approve_external_tts=True,
            )
            command = run.call_args.args[0]
            self.assertIn("en-AU-NatashaNeural", command)
            self.assertIn("--rate=+8%", command)
            self.assertEqual(result, output.resolve())

    @patch("evidence_to_audio.audio.shutil.which", return_value="/usr/bin/say")
    def test_macos_say_requires_words_per_minute_rate(self, _which):
        settings = AudioSettings(
            engine="macos-say",
            voice="Samantha",
            rate="+8%",
            pitch="0Hz",
            format="aiff",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "script.txt"
            script.write_text("Approved script.", encoding="utf-8")
            with self.assertRaisesRegex(AudioError, "words per minute"):
                render_audio(script, root / "episode.aiff", settings)


if __name__ == "__main__":
    unittest.main()
