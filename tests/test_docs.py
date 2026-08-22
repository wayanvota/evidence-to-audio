import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
PUBLIC_TEXT = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "AGENTS.md",
    *sorted((ROOT / "docs").glob("*.md")),
]


class DocumentationTests(unittest.TestCase):
    def test_relative_markdown_links_resolve(self):
        missing = []
        for document in PUBLIC_TEXT:
            text = document.read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                path_text = target.split("#", 1)[0]
                if path_text and not (document.parent / path_text).resolve().exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_public_prose_has_no_em_dash(self):
        offenders = []
        for document in PUBLIC_TEXT:
            if "—" in document.read_text(encoding="utf-8"):
                offenders.append(str(document.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_producer_prompt_requires_audible_structure(self):
        prompt = (ROOT / "prompts" / "producer.md").read_text(encoding="utf-8")
        for required in (
            "Section one.",
            "First point.",
            "There are three points.",
            '"First," "Second," "Third,"',
            "A sentence with three or more commas usually needs",
            "The sentence after a list cannot be mistaken for another list item.",
        ):
            self.assertIn(required, prompt)

    def test_prompts_enforce_business_builder_audience(self):
        required_by_file = {
            "critic.md": ("business builder", "acceptance check"),
            "editor.md": ("technicality", "What should the listener tell"),
            "producer.md": ("three out of ten", "practical builder move"),
            "scout-application.md": ("does not write the implementation", "concrete direction"),
            "scout-evidence.md": ("directing or reviewing an AI agent", "observable proof"),
            "scout-skeptic.md": ("technical details can be removed", "business builder"),
        }
        for filename, phrases in required_by_file.items():
            prompt = (ROOT / "prompts" / filename).read_text(encoding="utf-8").lower()
            for phrase in phrases:
                self.assertIn(phrase.lower(), prompt, filename)


if __name__ == "__main__":
    unittest.main()
