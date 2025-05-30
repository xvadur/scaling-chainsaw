from datetime import datetime, UTC
from pathlib import Path
import re
from typing import Dict, Optional

class MinisterialReportGenerator:
    """Generator for AetheroOS Ministerial Reports"""
    
    def __init__(self, template_path: str = "templates/ministerial_report.md"):
        """
        Initialize the report generator
        
        Args:
            template_path: Path to the ministerial report template
        """
        self.template_path = Path(template_path)
        self._load_template()
        
    def _load_template(self):
        """Load the report template from file"""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
            
        with open(self.template_path) as f:
            self.template = f.read()
            
    def _validate_fields(self, fields: Dict[str, str]):
        """
        Validate required fields are present
        
        Args:
            fields: Dictionary of field values
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {"office", "ref_code", "purpose", 
                         "findings", "recommendations", "author"}
        
        missing = required_fields - set(fields.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
            
    def generate(self, fields: Dict[str, str]) -> str:
        """
        Generate a ministerial report
        
        Args:
            fields: Dictionary containing report field values
            
        Returns:
            Formatted report string
        """
        # Validate fields
        self._validate_fields(fields)
        
        # Add date if not provided
        if "date" not in fields:
            fields["date"] = datetime.now(UTC).strftime("%Y-%m-%d")
            
        # Replace template variables
        report = self.template
        for key, value in fields.items():
            pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
            report = re.sub(pattern, value, report)
            
        return report
        
    def save_report(self, fields: Dict[str, str], output_path: str):
        """
        Generate and save a report to file
        
        Args:
            fields: Dictionary containing report field values
            output_path: Path to save the report
        """
        report = self.generate(fields)
        
        with open(output_path, 'w') as f:
            f.write(report)
