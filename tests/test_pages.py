"""The Photos tab is its own page. People is the roster."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PageTests(unittest.TestCase):
    def test_photos_nav_is_separate_from_the_people_roster(self):
        nav = (ROOT / "partials" / "navbar.html").read_text()
        self.assertIn('href="/photos/">Photos</a>', nav)
        people = (ROOT / "people" / "index.html").read_text()
        self.assertNotIn("lab-photo", people)
        self.assertNotIn('id="photos"', people)
        self.assertIn("/assets/js/people.js", people)
        photos = (ROOT / "photos" / "index.html").read_text()
        self.assertIn("/assets/js/photos.js", photos)
        self.assertIn('id="photos"', photos)
        build = (ROOT / "scripts" / "build.py").read_text()
        self.assertIn('"photos"', build)
