import unittest
import yaml
import json
from pathlib import Path
from datetime import datetime, UTC
from src.asl_parser import ASLParser, ASLTag, create_asl_tag

class TestASLParser(unittest.TestCase):
    def setUp(self):
        self.parser = ASLParser()
        
    def test_basic_tag_parsing(self):
        """Test basic tag parsing functionality"""
        content = "{mental_state: 'focused'}"
        tags = self.parser.parse(content)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]['tag_name'], 'mental_state')
        self.assertEqual(tags[0]['value'], 'focused')
        
    def test_multiple_tags(self):
        """Test parsing multiple tags"""
        content = "{tag1: 'value1'}, {tag2: 'value2'}"
        tags = self.parser.parse(content)
        self.assertEqual(len(tags), 2)
        
    def test_nested_tags(self):
        """Test parsing nested tag structures"""
        content = "{outer: {inner: 'value'}}"
        tags = self.parser.parse(content)
        self.assertTrue(len(tags) > 0)
        
    def test_value_types(self):
        """Test parsing different value types"""
        content = """
        {string_tag: 'text',
         int_tag: 42,
         float_tag: 3.14,
         bool_tag: true}
        """
        tags = self.parser.parse(content)
        self.assertEqual(len(tags), 4)
        
        type_map = {tag['tag_name']: type(tag['value']) for tag in tags}
        self.assertIs(type_map['string_tag'], str)
        self.assertIs(type_map['int_tag'], int)
        self.assertIs(type_map['float_tag'], float)
        self.assertIs(type_map['bool_tag'], bool)

class TestAgentConfigurations(unittest.TestCase):
    def setUp(self):
        self.config_dir = Path("config")
        self.required_agents = ["planner", "scout", "analyst", "generator", "synthesis"]
        
    def test_config_existence(self):
        """Test existence of all agent config files"""
        for agent in self.required_agents:
            config_file = self.config_dir / f"{agent}_agent_config.yaml"
            self.assertTrue(config_file.exists())
            
    def test_config_structure(self):
        """Test structure of agent configurations"""
        required_fields = {
            "name", "version", "role", "timeout", "retry_limit",
            "max_concurrent_tasks", "memory_limit_mb", "log_level"
        }
        
        for agent in self.required_agents:
            config_file = self.config_dir / f"{agent}_agent_config.yaml"
            with open(config_file) as f:
                config = yaml.safe_load(f)
                
            for field in required_fields:
                self.assertIn(field, config, f"{field} missing in {agent} config")
                
    def test_config_relationships(self):
        """Test relationships between agent configurations"""
        configs = {}
        for agent in self.required_agents:
            config_file = self.config_dir / f"{agent}_agent_config.yaml"
            with open(config_file) as f:
                configs[agent] = yaml.safe_load(f)
        
        # Test planner-scout relationship
        self.assertIn('scout_agent', configs['planner']['required_agents'])
        
        # Test version consistency
        versions = {agent: config['version'] for agent, config in configs.items()}
        self.assertEqual(len(set(versions.values())), 1, "All agents should have same version")

class TestSecurityCompliance(unittest.TestCase):
    def setUp(self):
        self.env_file = Path(".env.example")
        self.security_policy = Path("security_policy.md")
        
    def test_env_security_variables(self):
        """Test security-related environment variables"""
        required_vars = {
            "API_KEY", "JWT_SECRET", "ENCRYPTION_KEY",
            "ACCESS_TOKEN_EXPIRE_MINUTES"
        }
        
        with open(self.env_file) as f:
            content = f.read()
            for var in required_vars:
                self.assertIn(var, content)
                
    def test_security_policy_sections(self):
        """Test security policy document structure"""
        required_sections = [
            "# AetheroOS Security Policy",
            "## Reporting Security Issues",
            "## Security Measures",
            "### 1. Authentication & Authorization",
            "### 2. Data Protection"
        ]
        
        with open(self.security_policy) as f:
            content = f.read()
            for section in required_sections:
                self.assertIn(section, content)

class TestCrossComponentIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = ASLParser()
        
    def test_agent_asl_integration(self):
        """Test integration between agents and ASL parser"""
        # Create test tags for each agent type
        agent_tags = {
            "planner": "{mental_state: 'planning', certainty_level: 0.9}",
            "scout": "{search_context: 'discovery', resource_type: 'documentation'}",
            "analyst": "{analysis_type: 'pattern', confidence_score: 0.85}",
            "generator": "{generation_type: 'code', content_format: 'python'}",
            "synthesis": "{synthesis_stage: 'final', quality_metrics: 0.95}"
        }
        
        for agent, tags in agent_tags.items():
            parsed_tags = self.parser.parse(tags)
            self.assertTrue(len(parsed_tags) > 0)
            
            # Verify tag structure matches agent config requirements
            config_file = Path("config") / f"{agent}_agent_config.yaml"
            with open(config_file) as f:
                config = yaml.safe_load(f)
                
            # Check if parsed tags match the agent's ASL tag configuration
            config_tags = set(config['asl_tags'])
            parsed_tag_names = {tag['tag_name'] for tag in parsed_tags}
            self.assertTrue(
                parsed_tag_names.issubset(config_tags),
                f"Tags {parsed_tag_names} not in config tags {config_tags}"
            )

if __name__ == '__main__':
    unittest.main(verbosity=2)
