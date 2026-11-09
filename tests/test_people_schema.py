"""People schema: current students may carry a start term and an end."""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "people.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)


def person(**extra):
    base = {"id": "ada-lovelace", "name": "Ada Lovelace", "role": "phd"}
    base.update(extra)
    return [base]


class PeopleSchemaTests(unittest.TestCase):
    def assert_valid(self, data):
        self.assertEqual(list(VALIDATOR.iter_errors(data)), [])

    def assert_invalid(self, data):
        self.assertTrue(list(VALIDATOR.iter_errors(data)))

    def test_student_in_progress_terms(self):
        self.assert_valid(person(start="Fall 2026", end="In progress"))

    def test_student_completed_term(self):
        self.assert_valid(person(role="ms", start="Spring 2026", end="Fall 2027"))

    def test_faculty_without_terms_stays_valid(self):
        self.assert_valid(person(role="pi", title="Assistant Professor, Computer Science"))

    def test_faculty_terms_are_rejected(self):
        self.assert_invalid(person(role="pi", start="Fall 2026", end="In progress"))

    def test_one_sided_term_is_rejected(self):
        self.assert_invalid(person(start="Fall 2026"))
        self.assert_invalid(person(end="In progress"))

    def test_alumni_uses_the_alumni_object_instead(self):
        self.assert_invalid(person(
            start="Fall 2026",
            end="Spring 2030",
            alumni={"years": "2026-2030"},
        ))
        self.assert_valid(person(role="phd", alumni={"years": "2026-2030"}))

    def test_freeform_end_is_rejected(self):
        self.assert_invalid(person(start="Fall 2026", end="soon"))
