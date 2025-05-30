import asyncio
import logging
import jwt
import ssl
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from cryptography.fernet import Fernet
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.aethero_agent_bootstrap import BaseAetheroAgent
from src.agents.agent_bus import AgentBus, Message
from src.monitoring.monitor import AetheroMonitor

# Test configuration
TEST_SECRET_KEY = Fernet.generate_key()
TEST_JWT_SECRET = "test_jwt_secret"
SSL_CERT_PATH = "./tests/certs/test_cert.pem"
SSL_KEY_PATH = "./tests/certs/test_key.pem"

@dataclass
class SecurityContext:
    """Security context for testing authentication and authorization"""
    user_id: str
    roles: list
    permissions: list
    token: str = None

class SecureAgent(BaseAetheroAgent):
    """Agent implementation with security features"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any], logger: logging.Logger, 
                 agent_bus: AgentBus, security_context: SecurityContext):
        super().__init__(agent_id, config, logger, agent_bus)
        self.security_context = security_context
        self.encryption_key = Fernet(TEST_SECRET_KEY)
    
    async def process_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process task with security checks"""
        if not self._verify_permissions(task_data.get("required_permissions", [])):
            raise PermissionError("Insufficient permissions")
            
        # Encrypt sensitive data
        if "sensitive_data" in task_data:
            task_data["sensitive_data"] = self._encrypt_data(task_data["sensitive_data"])
            
        return await super().process_task(task_data, asl_context)
    
    def _verify_permissions(self, required_permissions: list) -> bool:
        """Verify agent has required permissions"""
        return all(perm in self.security_context.permissions for perm in required_permissions)
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.encryption_key.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.encryption_key.decrypt(encrypted_data.encode()).decode()

def generate_jwt_token(security_context: SecurityContext) -> str:
    """Generate JWT token for authentication"""
    payload = {
        "user_id": security_context.user_id,
        "roles": security_context.roles,
        "permissions": security_context.permissions,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")

async def setup_secure_environment():
    """Set up secure testing environment"""
    # Create SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=SSL_CERT_PATH, keyfile=SSL_KEY_PATH)
    
    # Create security context
    security_context = SecurityContext(
        user_id="test_user",
        roles=["admin"],
        permissions=["read", "write", "execute"]
    )
    security_context.token = generate_jwt_token(security_context)
    
    return ssl_context, security_context

async def test_authentication():
    """Test authentication flow"""
    logger = logging.getLogger("security_test")
    agent_bus = AgentBus()
    
    # Set up secure environment
    ssl_context, security_context = await setup_secure_environment()
    
    # Create secure agent
    agent = SecureAgent(
        "secure_agent",
        {"pipeline_id": "security_test"},
        logger,
        agent_bus,
        security_context
    )
    
    # Test valid authentication
    try:
        decoded_token = jwt.decode(
            security_context.token,
            TEST_JWT_SECRET,
            algorithms=["HS256"]
        )
        assert decoded_token["user_id"] == security_context.user_id
        logger.info("Authentication test passed")
    except Exception as e:
        logger.error(f"Authentication test failed: {str(e)}")
        raise

async def test_authorization():
    """Test authorization boundaries"""
    logger = logging.getLogger("security_test")
    agent_bus = AgentBus()
    
    # Set up secure environment
    _, security_context = await setup_secure_environment()
    
    # Create secure agent
    agent = SecureAgent(
        "secure_agent",
        {"pipeline_id": "security_test"},
        logger,
        agent_bus,
        security_context
    )
    
    # Test permission verification
    try:
        # Test with sufficient permissions
        assert agent._verify_permissions(["read", "write"])
        
        # Test with insufficient permissions
        assert not agent._verify_permissions(["admin_override"])
        
        logger.info("Authorization test passed")
    except Exception as e:
        logger.error(f"Authorization test failed: {str(e)}")
        raise

async def test_data_encryption():
    """Test data encryption in transit"""
    logger = logging.getLogger("security_test")
    agent_bus = AgentBus()
    
    # Set up secure environment
    _, security_context = await setup_secure_environment()
    
    # Create secure agent
    agent = SecureAgent(
        "secure_agent",
        {"pipeline_id": "security_test"},
        logger,
        agent_bus,
        security_context
    )
    
    # Test data encryption/decryption
    try:
        test_data = "sensitive information"
        encrypted = agent._encrypt_data(test_data)
        decrypted = agent._decrypt_data(encrypted)
        
        assert test_data == decrypted
        assert encrypted != test_data
        
        logger.info("Encryption test passed")
    except Exception as e:
        logger.error(f"Encryption test failed: {str(e)}")
        raise

async def test_secure_message_flow():
    """Test end-to-end secure message flow"""
    logger = logging.getLogger("security_test")
    agent_bus = AgentBus()
    
    # Set up secure environment
    _, security_context = await setup_secure_environment()
    
    # Create secure agent
    agent = SecureAgent(
        "secure_agent",
        {"pipeline_id": "security_test"},
        logger,
        agent_bus,
        security_context
    )
    
    try:
        # Test task with sensitive data
        task_data = {
            "task_id": "secure_task",
            "sensitive_data": "confidential information",
            "required_permissions": ["read", "write"]
        }
        
        result = await agent.execute_task(task_data, {})
        
        # Verify sensitive data was encrypted
        assert "sensitive_data" in result
        assert result["sensitive_data"] != task_data["sensitive_data"]
        
        logger.info("Secure message flow test passed")
    except Exception as e:
        logger.error(f"Secure message flow test failed: {str(e)}")
        raise

async def run_security_tests():
    """Run all security tests"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("security_tests")
    
    try:
        logger.info("Starting security testing suite...")
        
        # Run authentication tests
        logger.info("\nTesting authentication...")
        await test_authentication()
        
        # Run authorization tests
        logger.info("\nTesting authorization...")
        await test_authorization()
        
        # Run encryption tests
        logger.info("\nTesting data encryption...")
        await test_data_encryption()
        
        # Run secure message flow tests
        logger.info("\nTesting secure message flow...")
        await test_secure_message_flow()
        
        logger.info("\nAll security tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in security testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_security_tests())
