import unittest
from pathlib import Path
from datetime import datetime, UTC
from src.report_generator import MinisterialReportGenerator

class TestMinisterialReportGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = MinisterialReportGenerator()
        self.test_fields = {
            "office": "Ministry of Protocol",
            "ref_code": "MPR-2025-001",
            "purpose": "To evaluate system security measures",
            "findings": "All security protocols operational",
            "recommendations": "Continue monitoring",
            "author": "Chief Protocol Officer"
        }
        
    def test_template_loading(self):
        """Test template loading functionality"""
        self.assertTrue(hasattr(self.generator, 'template'))
        self.assertIn("AETHEROOS MINISTERIAL REPORT", self.generator.template)
        
    def test_field_validation(self):
        """Test field validation"""
        # Test missing required field
        invalid_fields = self.test_fields.copy()
        del invalid_fields["purpose"]
        
        with self.assertRaises(ValueError):
            self.generator.generate(invalid_fields)
            
    def test_report_generation(self):
        """Test report generation"""
        report = self.generator.generate(self.test_fields)
        
        # Check all fields are present
        for value in self.test_fields.values():
            self.assertIn(value, report)
            
        # Check date was added
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        self.assertIn(today, report)
        
    def test_custom_date(self):
        """Test custom date field"""
        fields = self.test_fields.copy()
        fields["date"] = "2025-05-28"
        
        report = self.generator.generate(fields)
        self.assertIn("2025-05-28", report)
        
    def test_report_saving(self):
        """Test report file saving"""
        test_output = "test_report.md"
        
        try:
            self.generator.save_report(self.test_fields, test_output)
            
            # Verify file was created
            self.assertTrue(Path(test_output).exists())
            
            # Verify content
            with open(test_output) as f:
                content = f.read()
                for value in self.test_fields.values():
                    self.assertIn(value, content)
                    
        finally:
            # Cleanup
            if Path(test_output).exists():
                Path(test_output).unlink()
                
    def test_ceremonial_formatting(self):
        """Test ceremonial formatting elements"""
        report = self.generator.generate(self.test_fields)
        
        # Check ceremonial elements
        self.assertIn("🪶 PURPOSE", report)
        self.assertIn("🪶 FINDINGS", report)
        self.assertIn("🪶 RECOMMENDATIONS", report)
        self.assertIn("**Ministerial Seal**: [ ⚜️ ]", report)
        
if __name__ == '__main__':
    unittest.main(verbosity=2)
