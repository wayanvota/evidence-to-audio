from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MockChatServer:
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode
        self.calls: list[dict] = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    payload = {}
                owner.calls.append(payload)

                if owner.mode == "http_error":
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b"fictional provider unavailable")
                    return
                if owner.mode == "malformed_json":
                    response = b"{not-json"
                elif owner.mode == "missing_message":
                    response = json.dumps({"choices": [{}]}).encode()
                else:
                    system = str(payload.get("messages", [{"content": ""}])[0]["content"])
                    if "ROLE=producer" in system:
                        content = (
                            "Listen at https://example.invalid/brief"
                            if owner.mode == "spoken_url"
                            else "The fictional cooling test is limited. Review the evidence before acting."
                        )
                    elif "ROLE=editor" in system:
                        content = "A concise draft about a fictional cooling test."
                    elif "ROLE=critic" in system:
                        content = "KEEP the limited fictional test. KILL unsupported impact claims."
                    else:
                        content = "Scout report: one supported fictional idea with a visible limit."
                    if owner.mode == "empty_text":
                        content = " "
                    response = json.dumps(
                        {"choices": [{"message": {"content": content}}]}
                    ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1"

    def __enter__(self) -> "MockChatServer":
        self.thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class EndToEndContract(unittest.TestCase):
    maxDiff = None

    def cli(
        self, *arguments: str, remove_env: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        if remove_env:
            environment.pop(remove_env, None)
        return subprocess.run(
            [sys.executable, "-m", "evidence_to_audio", *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def project(
        self,
        root: Path,
        base_url: str,
        *,
        api_key_env: str = "",
        max_minutes: int = 10,
    ) -> tuple[Path, Path]:
        prompts = root / "prompts"
        prompts.mkdir()
        for filename, role in {
            "scout-a.md": "scout-a",
            "scout-b.md": "scout-b",
            "scout-c.md": "scout-c",
            "critic.md": "critic",
            "editor.md": "editor",
            "producer.md": "producer",
        }.items():
            (prompts / filename).write_text(f"ROLE={role}\n", encoding="utf-8")

        config = root / "config.toml"
        config.write_text(
            textwrap.dedent(
                f"""
                [project]
                title = "Fictional Evidence Brief"
                max_minutes = {max_minutes}
                target_words_per_minute = 150
                output_dir = "runs"

                [audience]
                role = "A fictional program director"
                goal = "Judge a fictional pilot against its evidence"
                workflow = "Direct, review, and decide"
                technicality = 3

                [providers.primary]
                kind = "openai_compatible"
                base_url = "{base_url}"
                model = "synthetic-model"
                api_key_env = "{api_key_env}"
                timeout_seconds = 5
                max_output_tokens = 500

                [agents.scouts.evidence]
                provider = "primary"
                prompt = "prompts/scout-a.md"

                [agents.scouts.skeptic]
                provider = "primary"
                prompt = "prompts/scout-b.md"

                [agents.scouts.application]
                provider = "primary"
                prompt = "prompts/scout-c.md"

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
                rate = "+8%"
                pitch = "-2Hz"
                format = "mp3"
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        sources = root / "sources"
        sources.mkdir()
        (sources / "city-report.md").write_text(
            "A fictional city proposes a thirty-day cooling test.\n",
            encoding="utf-8",
        )
        return config, sources

    def run_pipeline(
        self, root: Path, server: MockChatServer
    ) -> tuple[Path, Path, Path]:
        config, sources = self.project(root, server.base_url)
        result = self.cli("run", "--config", str(config), "--sources", str(sources))
        self.assertEqual(result.returncode, 0, result.stderr)
        first_line = result.stdout.splitlines()[0]
        run_dir = Path(first_line.removeprefix("Run complete: "))
        self.assertTrue(run_dir.is_dir())
        return config, sources, run_dir

    def test_U01_cli_help_exposes_run_validate_and_render(self) -> None:
        result = self.cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("run", "validate", "render"):
            self.assertIn(command, result.stdout)

    def test_U02_real_cli_completes_the_six_stage_pipeline(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            _config, _sources, run_dir = self.run_pipeline(Path(directory), server)
            self.assertTrue((run_dir / "script.txt").is_file())
            self.assertEqual(len(server.calls), 6)

    def test_U03_generated_run_validates_through_a_second_cli_command(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            _config, _sources, run_dir = self.run_pipeline(Path(directory), server)
            result = self.cli("validate", "--run", str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Valid run:", result.stdout)

    def test_U04_three_independent_scout_artifacts_are_preserved(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            _config, _sources, run_dir = self.run_pipeline(Path(directory), server)
            scouts = sorted(path.name for path in (run_dir / "scouts").glob("*.md"))
            self.assertEqual(
                scouts, ["application.md", "evidence.md", "skeptic.md"]
            )

    def test_U05_manifest_records_the_exact_source_file_names(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            _config, sources, run_dir = self.run_pipeline(Path(directory), server)
            (sources / "nested").mkdir()
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual(manifest["source_files"], ["city-report.md"])
            self.assertFalse(manifest["audio_rendered"])

    def test_U06_listener_profile_reaches_every_editorial_agent(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            self.run_pipeline(Path(directory), server)
            for call in server.calls:
                user = call["messages"][1]["content"]
                self.assertIn("A fictional program director", user)
                self.assertIn("Technicality target: 3 out of 10", user)

    def test_U07_hidden_and_unsupported_sources_stay_out_of_the_run(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            root = Path(directory)
            config, sources = self.project(root, server.base_url)
            (sources / ".private.md").write_text("Do not include.\n")
            (sources / "image.png").write_bytes(b"not an image")
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = Path(result.stdout.splitlines()[0].removeprefix("Run complete: "))
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual(manifest["source_files"], ["city-report.md"])

    def test_U08_nested_source_files_are_sorted_for_stable_provenance(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            root = Path(directory)
            config, sources = self.project(root, server.base_url)
            nested = sources / "nested"
            nested.mkdir()
            (nested / "application.txt").write_text("Fictional application.\n")
            (sources / "alpha.json").write_text('{"status":"fictional"}\n')
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 0, result.stderr)
            run_dir = Path(result.stdout.splitlines()[0].removeprefix("Run complete: "))
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertEqual(
                manifest["source_files"],
                ["alpha.json", "city-report.md", "nested/application.txt"],
            )

    def test_U09_repository_sample_run_remains_valid(self) -> None:
        result = self.cli("validate", "--run", str(ROOT / "examples/sample-run"))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_U10_audio_rendering_requires_a_separate_explicit_approval(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            config, _sources, run_dir = self.run_pipeline(Path(directory), server)
            result = self.cli("render", "--config", str(config), "--run", str(run_dir))
            self.assertEqual(result.returncode, 1)
            self.assertIn("approve-external-tts", result.stderr)
            self.assertFalse((run_dir / "episode.mp3").exists())

    def test_A01_empty_source_pack_fails_before_any_provider_call(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            root = Path(directory)
            config, sources = self.project(root, server.base_url)
            (sources / "city-report.md").unlink()
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 1)
            self.assertIn("No supported source files", result.stderr)
            self.assertEqual(server.calls, [])

    def test_A02_missing_named_api_key_fails_closed(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            config, sources = self.project(
                Path(directory), server.base_url, api_key_env="E2E_MISSING_PROVIDER_KEY"
            )
            result = self.cli(
                "run",
                "--config",
                str(config),
                "--sources",
                str(sources),
                remove_env="E2E_MISSING_PROVIDER_KEY",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("E2E_MISSING_PROVIDER_KEY is required", result.stderr)

    def test_A03_provider_http_error_does_not_create_a_completed_run(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer("http_error") as server:
            root = Path(directory)
            config, sources = self.project(root, server.base_url)
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Provider returned HTTP 503", result.stderr)
            self.assertFalse(any((root / "runs").glob("*/manifest.json")))

    def test_A04_malformed_provider_json_fails_closed(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer("malformed_json") as server:
            config, sources = self.project(Path(directory), server.base_url)
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Provider request failed", result.stderr)

    def test_A05_provider_response_without_message_text_fails_closed(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer("missing_message") as server:
            config, sources = self.project(Path(directory), server.base_url)
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 1)
            self.assertIn("did not contain message text", result.stderr)

    def test_A06_empty_provider_text_fails_closed(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer("empty_text") as server:
            config, sources = self.project(Path(directory), server.base_url)
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 1)
            self.assertIn("returned empty text", result.stderr)

    def test_A07_runtime_over_ninety_minutes_is_rejected_before_calls(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            config, sources = self.project(
                Path(directory), server.base_url, max_minutes=91
            )
            result = self.cli("run", "--config", str(config), "--sources", str(sources))
            self.assertEqual(result.returncode, 1)
            self.assertIn("between 1 and 90", result.stderr)
            self.assertEqual(server.calls, [])

    def test_A08_spoken_url_from_provider_is_rejected_by_validation(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer("spoken_url") as server:
            _config, _sources, run_dir = self.run_pipeline(Path(directory), server)
            result = self.cli("validate", "--run", str(run_dir))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Spoken script contains a URL", result.stderr)

    def test_A09_visual_markdown_in_script_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sample = ROOT / "examples/sample-run"
            shutil.copytree(sample, root / "run")
            run_dir = root / "run"
            script = "# Findings\n\n- First fictional result\n"
            (run_dir / "script.txt").write_text(script, encoding="utf-8")
            manifest = json.loads((run_dir / "manifest.json").read_text())
            manifest["script_words"] = len(script.split())
            (run_dir / "manifest.json").write_text(json.dumps(manifest) + "\n")
            result = self.cli("validate", "--run", str(run_dir))
            self.assertEqual(result.returncode, 1)
            self.assertIn("Markdown heading", result.stderr)
            self.assertIn("Markdown list syntax", result.stderr)

    def test_A10_script_mutation_blocks_render_before_external_tts(self) -> None:
        with TemporaryDirectory() as directory, MockChatServer() as server:
            config, _sources, run_dir = self.run_pipeline(Path(directory), server)
            with (run_dir / "script.txt").open("a", encoding="utf-8") as handle:
                handle.write("Changed after approval.\n")
            result = self.cli(
                "render",
                "--config",
                str(config),
                "--run",
                str(run_dir),
                "--approve-external-tts",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("manifest script_words does not match", result.stderr)
            self.assertFalse((run_dir / "episode.mp3").exists())


if __name__ == "__main__":
    unittest.main()
