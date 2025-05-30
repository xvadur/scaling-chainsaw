import unittest
from introspective_parser_module.parser import ASLMetaParser
from introspective_parser_module.models import ASLTagModel

class TestASLMetaParser(unittest.TestCase):
    def setUp(self):
        self.parser = ASLMetaParser()

    def test_parse_line_valid(self):
        line = "# [ASL] statement: Hello World"
        result = self.parser.parse_line(line)
        self.assertEqual(result, {"statement": "Hello World"})

    def test_parse_line_invalid(self):
        line = "Invalid line"
        result = self.parser.parse_line(line)
        self.assertEqual(result, {})

    def test_validate_tags_valid(self):
        tags = {
            "statement": "Hello World",
            "mental_state": "calm",
            "emotion_tone": "neutral",
            "cognitive_load": 5,
            "temporal_context": "present",
            "certainty_level": 0.9,
            "aeth_mem_link": "link",
            "law": "law"
        }
        model = ASLTagModel(**tags)
        self.assertEqual(model.statement, "Hello World")

    def test_validate_tags_invalid(self):
        tags = {
            "statement": "Hello World",
            "mental_state": "calm",
            "emotion_tone": "neutral"
        }
        with self.assertRaises(Exception):
            ASLTagModel(**tags)

if __name__ == "__main__":
    unittest.main()
