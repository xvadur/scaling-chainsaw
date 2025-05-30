import pytest
import logging
from src.agents.agent_bus import AgentBus

@pytest.fixture
def agent_bus():
    """Fixture to provide a configured AgentBus instance"""
    return AgentBus()

@pytest.fixture
def logger():
    """Fixture to provide a configured logger"""
    return logging.getLogger("test_logger")

@pytest.fixture
def test_config():
    """Fixture to provide test configuration"""
    return {
        "pipeline_id": "test_pipeline",
        "test_mode": True,
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }

@pytest.fixture
def test_sizes():
    """Fixture to provide test message sizes in MB"""
    return [1, 5, 10]

@pytest.fixture
def test_message_count():
    """Fixture to provide number of test messages"""
    return 100

@pytest.fixture
def test_message_size():
    """Fixture to provide test message size in KB"""
    return 10

@pytest.fixture
def test_agent_count():
    """Fixture to provide number of test agents"""
    return 10

@pytest.fixture
def test_tasks_per_agent():
    """Fixture to provide number of tasks per agent"""
    return 5
