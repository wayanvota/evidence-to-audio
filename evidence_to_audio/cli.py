from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audio import AudioError, mark_audio_in_manifest, render_audio
from .config import ConfigError, load_settings
from .pipeline import Pipeline
from .providers import ProviderError
from .validation import validate_run


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evidence-to-audio",
        description="Turn a source pack into an inspectable private audio brief.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run scouts, critic, editor, and producer")
    run.add_argument("--config", default="config.toml")
    run.add_argument("--sources", required=True)

    validate = subparsers.add_parser("validate", help="Validate a completed run")
    validate.add_argument("--run", required=True)

    render = subparsers.add_parser("render", help="Render an approved script to audio")
    render.add_argument("--config", default="config.toml")
    render.add_argument("--run", required=True)
    render.add_argument(
        "--approve-external-tts",
        action="store_true",
        help="Acknowledge that the script will be sent to an external speech service",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            settings = load_settings(args.config)
            run_dir = Pipeline(settings).run(args.sources)
            print(f"Run complete: {run_dir}")
            print(f"Review the script before audio: {run_dir / 'script.txt'}")
            return

        if args.command == "validate":
            errors = validate_run(args.run)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                raise SystemExit(1)
            print(f"Valid run: {Path(args.run).resolve()}")
            return

        if args.command == "render":
            settings = load_settings(args.config)
            run_dir = Path(args.run).resolve()
            errors = validate_run(run_dir)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                raise SystemExit(1)
            extension = settings.audio.format.lstrip(".")
            output = run_dir / f"episode.{extension}"
            rendered = render_audio(
                run_dir / "script.txt",
                output,
                settings.audio,
                approve_external_tts=args.approve_external_tts,
            )
            mark_audio_in_manifest(run_dir, rendered)
            print(f"Audio complete: {rendered}")
            return
    except (ConfigError, ProviderError, AudioError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
