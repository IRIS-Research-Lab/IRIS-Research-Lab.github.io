"""Regression checks for rendered publication authors and person photo links."""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MarkupTests(unittest.TestCase):
    def render(self, expression):
        script = (
            'globalThis.location = { origin: "http://localhost" };\n'
            'const mod = await import("./assets/js/common.js");\n'
            f'const value = {expression};\n'
            'process.stdout.write(JSON.stringify(value));\n'
        )
        proc = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_lab_names_with_entities_are_bold(self):
        html = self.render("""mod.labAuthorHTML(
          "A. O'Neil* and Jean & Jo and Blaine Hoak",
          [{name: "A. O'Neil"}, {name: "Jean & Jo"}, {name: "Blaine Hoak"}]
        )""")
        self.assertIn("<strong>A. O&#39;Neil*</strong>", html)
        self.assertIn("<strong>Jean &amp; Jo</strong>", html)
        self.assertIn("<strong>Blaine Hoak</strong>", html)
        self.assertNotIn("<strong>A. O'Neil", html)

    def test_initials_website_link_has_an_accessible_name(self):
        html = self.render("""mod.photoHTML({
          name: "Ada Lovelace",
          links: { website: "https://example.com" }
        })""")
        self.assertIn('aria-hidden="true"', html)
        self.assertIn('aria-label="Website for Ada Lovelace"', html)
        self.assertIn('href="https://example.com"', html)

    def test_photo_link_keeps_the_image_alt(self):
        html = self.render("""mod.photoHTML({
          name: "Ada Lovelace",
          photo: "https://iris-research-lab.github.io/assets/images/people/ada.jpg",
          links: { website: "https://example.com" }
        })""")
        self.assertIn('alt="Ada Lovelace"', html)
        self.assertNotIn("aria-label", html)
