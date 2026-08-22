from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .config import AudioSettings


class AudioError(RuntimeError):
    """Raised when narration cannot be rendered safely."""


def render_audio(
    script_path: str | Path,
    output_path: str | Path,
    settings: AudioSettings,
    approve_external_tts: bool = False,
) -> Path:
    script = Path(script_path).resolve()
    output = Path(output_path).resolve()
    if not script.is_file():
        raise AudioError(f"Script not found: {script}")
    if not script.read_text(encoding="utf-8").strip():
        raise AudioError("Script is empty")
    output.parent.mkdir(parents=True, exist_ok=True)

    if settings.engine == "edge-tts":
        if not approve_external_tts:
            raise AudioError(
                "Edge TTS sends the script to an external speech service. "
                "Rerun with --approve-external-tts after reviewing privacy implications."
            )
        executable = shutil.which("edge-tts")
        if not executable:
            raise AudioError("edge-tts is not installed. Run: pip install edge-tts")
        command = [
            executable,
            "--voice",
            settings.voice,
            f"--rate={settings.rate}",
            f"--pitch={settings.pitch}",
            "--file",
            str(script),
            "--write-media",
            str(output),
        ]
    elif settings.engine == "macos-say":
        executable = shutil.which("say")
        if not executable:
            raise AudioError("macOS say is not available")
        try:
            numeric_rate = str(int(settings.rate))
        except ValueError as exc:
            raise AudioError(
                "macos-say rate must be an integer in words per minute, such as 175"
            ) from exc
        command = [
            executable,
            "-v",
            settings.voice,
            "-r",
            numeric_rate,
            "-f",
            str(script),
            "-o",
            str(output),
        ]
    else:
        raise AudioError(f"Unsupported audio engine: {settings.engine}")

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise AudioError(f"Audio render failed: {detail}")
    if not output.is_file() or output.stat().st_size == 0:
        raise AudioError("Audio renderer completed without creating audio")
    return output


def mark_audio_in_manifest(run_dir: str | Path, audio_path: Path) -> None:
    manifest_path = Path(run_dir) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["audio_rendered"] = True
    manifest["audio_file"] = audio_path.name
    manifest["audio_bytes"] = audio_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
