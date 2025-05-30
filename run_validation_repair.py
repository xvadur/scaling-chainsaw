#!/usr/bin/env python3
"""
AetheroOS Validation Repair Module
Modul pre Opravu Validácie AetheroOS
"""

import json
import os
import sys
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

class IssueLevel(Enum):
    CRITICAL = "🔴 CRITICAL"
    WARNING = "🟠 WARNING"
    INFO = "🟢 INFO"

class ValidationRepair:
    def __init__(self):
        self.issues = {
            IssueLevel.CRITICAL: [],
            IssueLevel.WARNING: [],
            IssueLevel.INFO: []
        }
        self.fixes = []
        self.output_dir = "auto_fixes"
        
    def load_validation_report(self) -> Dict:
        """
        Load and parse validation report
        Načítanie a parsovanie validačnej správy
        """
        try:
            with open("validation_report.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ validation_report.json not found. Running fresh validation...")
            return self.run_initial_validation()
            
    def run_initial_validation(self) -> Dict:
        """
        Run initial validation if report doesn't exist
        Spustenie počiatočnej validácie ak správa neexistuje
        """
        import validate_project
        return {"status": "initial_validation_complete"}

    def analyze_issues(self, report: Dict):
        """
        Analyze and categorize issues
        Analýza a kategorizácia problémov
        """
        # Check for critical file structure issues
        self._check_file_structure()
        
        # Check for ASL tag consistency
        self._check_asl_tags()
        
        # Validate agent configurations
        self._check_agent_configs()
        
        # Check for potential security issues
        self._check_security_compliance()

    def _check_file_structure(self):
        """
        Verify project structure and files
        Overenie štruktúry projektu a súborov
        """
        required_dirs = ['src', 'tests', 'docs']
        required_files = [
            'models.py',
            'utils.py',
            'requirements.txt',
            'README.md'
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                self.issues[IssueLevel.CRITICAL].append({
                    "type": "missing_directory",
                    "item": directory,
                    "fix": f"mkdir -p {directory}"
                })
        
        for file in required_files:
            if not os.path.exists(file):
                self.issues[IssueLevel.CRITICAL].append({
                    "type": "missing_file",
                    "item": file,
                    "fix": self._generate_file_template(file)
                })

    def _check_asl_tags(self):
        """
        Validate ASL tag structure and usage
        Validácia štruktúry a použitia ASL tagov
        """
        try:
            with open("src/asl_parser.py", "r") as f:
                content = f.read()
                if "validate_tag_structure" not in content:
                    self.issues[IssueLevel.WARNING].append({
                        "type": "missing_tag_validation",
                        "item": "src/asl_parser.py",
                        "fix": self._generate_asl_validator()
                    })
        except FileNotFoundError:
            self.issues[IssueLevel.CRITICAL].append({
                "type": "missing_asl_parser",
                "item": "src/asl_parser.py",
                "fix": self._generate_asl_parser()
            })

    def _check_agent_configs(self):
        """
        Validate agent configurations
        Validácia konfigurácií agentov
        """
        agent_types = ["planner", "scout", "analyst", "generator", "synthesis"]
        for agent in agent_types:
            config_file = f"config/{agent}_agent_config.yaml"
            if not os.path.exists(config_file):
                self.issues[IssueLevel.WARNING].append({
                    "type": "missing_agent_config",
                    "item": config_file,
                    "fix": self._generate_agent_config(agent)
                })

    def _check_security_compliance(self):
        """
        Check security compliance
        Kontrola bezpečnostnej kompatibility
        """
        security_files = [".env.example", "security_policy.md"]
        for file in security_files:
            if not os.path.exists(file):
                self.issues[IssueLevel.INFO].append({
                    "type": "missing_security_file",
                    "item": file,
                    "fix": self._generate_security_template(file)
                })

    def generate_repair_report(self):
        """
        Generate markdown repair report
        Generovanie správy o oprave v markdown formáte
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = f"""# AetheroOS Validation Repair Report
Generated: {timestamp}

## Issue Summary
"""
        for level in IssueLevel:
            issues = self.issues[level]
            if issues:
                report += f"\n### {level.value}\n"
                for issue in issues:
                    report += f"- {issue['type']}: {issue['item']}\n"
                    
        report += "\n## Recommended Fixes\n"
        for level in IssueLevel:
            fixes = [issue for issue in self.issues[level] if "fix" in issue]
            if fixes:
                report += f"\n### {level.value} Fixes\n"
                for fix in fixes:
                    report += f"- {fix['item']}:\n```\n{fix['fix']}\n```\n"
        
        return report

    def save_repair_report(self, report: str):
        """
        Save repair report to file
        Uloženie správy o oprave do súboru
        """
        os.makedirs("auto_fixes", exist_ok=True)
        with open("auto_fixes/repair_report.md", "w") as f:
            f.write(report)

    def _generate_file_template(self, filename: str) -> str:
        """
        Generate template for missing files
        Generovanie šablóny pre chýbajúce súbory
        """
        templates = {
            "models.py": """from typing import Dict, List

class AetheroModel:
    \"\"\"Base model for AetheroOS components\"\"\"
    pass
""",
            "utils.py": """from typing import Any, Dict

def validate_input(data: Dict) -> bool:
    \"\"\"Validate input data\"\"\"
    return True
""",
            "requirements.txt": """# Core Dependencies
aiohttp>=3.8.0
pyyaml>=6.0
pytest>=6.2.5
""",
            "README.md": """# AetheroOS Protocol

Enterprise-grade multi-agent system with ASL compatibility.
"""
        }
        return templates.get(filename, "# Template not available")

    def _generate_asl_validator(self) -> str:
        return """def validate_tag_structure(tag: Dict) -> bool:
    \"\"\"Validate ASL tag structure\"\"\"
    required_fields = ["tag_name", "value", "position"]
    return all(field in tag for field in required_fields)
"""

    def _generate_asl_parser(self) -> str:
        return """from typing import Dict, List

class ASLParser:
    \"\"\"Parser for ASL (Aethero Syntax Language) tags\"\"\"
    
    def __init__(self):
        self.tags = []
    
    def parse(self, content: str) -> List[Dict]:
        \"\"\"Parse ASL tags from content\"\"\"
        # Implementation here
        return []
"""

    def _generate_agent_config(self, agent_type: str) -> str:
        return f"""# {agent_type.capitalize()} Agent Configuration
name: {agent_type}_agent
version: 1.0
timeout: 300
retry_limit: 3
"""

    def _generate_security_template(self, filename: str) -> str:
        templates = {
            ".env.example": """# AetheroOS Environment Variables
API_KEY=your_api_key_here
DEBUG=False
LOG_LEVEL=INFO
""",
            "security_policy.md": """# Security Policy

## Reporting Security Issues
Please report security issues to security@aetheros.ai
"""
        }
        return templates.get(filename, "# Template not available")

def main():
    """
    Main execution function
    Hlavná vykonávacia funkcia
    """
    print("🔄 Starting AetheroOS Validation Repair...")
    
    validator = ValidationRepair()
    report = validator.load_validation_report()
    validator.analyze_issues(report)
    
    repair_report = validator.generate_repair_report()
    validator.save_repair_report(repair_report)
    
    print("\n✅ Validation repair complete!")
    print("📝 Check auto_fixes/repair_report.md for details")

if __name__ == "__main__":
    main()
