import unittest
import yaml
import json
from src.asl_parser import ASLParser, ASLTag
from pathlib import Path

class TestCriticalPath(unittest.TestCase):
    def setUp(self):
        self.parser = ASLParser()
        self.test_content = """
        This is a test with {mental_state: 'focused', certainty_level: 0.85}
        and {task_status: 'in_progress', agent_role: 'planner'}
        """
        
    def test_asl_parser_basic(self):
        """Test basic ASL parser functionality"""
        tags = self.parser.parse(self.test_content)
        
        self.assertTrue(len(tags) > 0, "Parser should extract tags")
        self.assertTrue(any(tag['tag_name'] == 'mental_state' for tag in tags))
        self.assertTrue(any(tag['tag_name'] == 'certainty_level' for tag in tags))
        
    def test_agent_configs(self):
        """Test agent configuration files"""
        config_dir = Path("config")
        required_agents = ["planner", "scout", "analyst", "generator", "synthesis"]
        
        for agent in required_agents:
            config_file = config_dir / f"{agent}_agent_config.yaml"
            self.assertTrue(config_file.exists(), f"{agent} config file should exist")
            
            # Test config file loading
            with open(config_file) as f:
                config = yaml.safe_load(f)
                
            # Basic config validation
            self.assertIn("name", config)
            self.assertIn("version", config)
            self.assertIn("role", config)
            
    def test_security_setup(self):
        """Test basic security setup"""
        # Check .env.example
        env_file = Path(".env.example")
        self.assertTrue(env_file.exists(), ".env.example should exist")
        
        with open(env_file) as f:
            env_content = f.read()
            self.assertIn("API_KEY", env_content)
            self.assertIn("JWT_SECRET", env_content)
            self.assertIn("ENCRYPTION_KEY", env_content)
        
        # Check security policy
        policy_file = Path("security_policy.md")
        self.assertTrue(policy_file.exists(), "Security policy should exist")
        
        with open(policy_file) as f:
            policy_content = f.read()
            self.assertIn("Reporting Security Issues", policy_content)
            self.assertIn("Security Measures", policy_content)

if __name__ == '__main__':
    unittest.main(verbosity=2)
