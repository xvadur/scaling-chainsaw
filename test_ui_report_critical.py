import unittest
from pathlib import Path
from datetime import datetime, UTC

class TestUICustomizationReportCritical(unittest.TestCase):
    def setUp(self):
        self.report_path = Path("reports/ui_customization_report.md")
        self.today = datetime.now(UTC).strftime("%Y-%m-%d")
        
    def test_report_exists(self):
        """Test that the UI customization report file exists"""
        self.assertTrue(self.report_path.exists(), "UI customization report file should exist")
        
    def test_report_sections(self):
        """Test that all main sections are present"""
        content = self.report_path.read_text()
        self.assertIn("I. OBJECTIVE", content)
        self.assertIn("II. OPTIONS OVERVIEW", content)
        self.assertIn("III. RECOMMENDATIONS", content)
        self.assertIn("IV. NEXT STEPS", content)
        
    def test_date_and_signature(self):
        """Test that the report contains the current date and signature"""
        content = self.report_path.read_text()
        self.assertIn(self.today, content)
        self.assertIn("Ministerial Seal", content)
        self.assertIn("**Signed**: AetheroGPT", content)

if __name__ == '__main__':
    unittest.main(verbosity=2)
