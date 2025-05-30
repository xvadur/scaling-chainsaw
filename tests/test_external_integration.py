import asyncio
import logging
import aiohttp
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.aethero_agent_bootstrap import BaseAetheroAgent
from src.agents.agent_bus import AgentBus
from src.monitoring.monitor import AetheroMonitor

class ExternalConnector(ABC):
    """Base class for external system connectors"""
    
    @abstractmethod
    async def connect(self):
        """Establish connection to external system"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close connection to external system"""
        pass
    
    @abstractmethod
    async def send_data(self, data: Dict[str, Any]):
        """Send data to external system"""
        pass
    
    @abstractmethod
    async def receive_data(self) -> Dict[str, Any]:
        """Receive data from external system"""
        pass

class RESTConnector(ExternalConnector):
    """Connector for REST API integration"""
    
    def __init__(self, base_url: str, headers: Dict[str, str] = None):
        self.base_url = base_url
        self.headers = headers or {}
        self.session = None
    
    async def connect(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
    
    async def disconnect(self):
        if self.session:
            await self.session.close()
    
    async def send_data(self, data: Dict[str, Any]):
        if not self.session:
            await self.connect()
        
        async with self.session.post(self.base_url, json=data) as response:
            return await response.json()
    
    async def receive_data(self) -> Dict[str, Any]:
        if not self.session:
            await self.connect()
        
        async with self.session.get(self.base_url) as response:
            return await response.json()

class WebSocketConnector(ExternalConnector):
    """Connector for WebSocket integration"""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.session = None
        self.ws = None
    
    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(self.ws_url)
    
    async def disconnect(self):
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
    
    async def send_data(self, data: Dict[str, Any]):
        if not self.ws:
            await self.connect()
        
        await self.ws.send_json(data)
    
    async def receive_data(self) -> Dict[str, Any]:
        if not self.ws:
            await self.connect()
        
        msg = await self.ws.receive_json()
        return msg

class PluginInterface(ABC):
    """Interface for custom plugins"""
    
    @abstractmethod
    async def initialize(self):
        """Initialize plugin"""
        pass
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through plugin"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass

class CustomPlugin(PluginInterface):
    """Example custom plugin implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.initialized = False
    
    async def initialize(self):
        # Simulate plugin initialization
        await asyncio.sleep(0.1)
        self.initialized = True
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.initialized:
            raise RuntimeError("Plugin not initialized")
        
        # Add plugin-specific processing
        data["processed_by"] = "custom_plugin"
        data["timestamp"] = str(datetime.now())
        
        return data
    
    async def cleanup(self):
        # Simulate cleanup
        await asyncio.sleep(0.1)
        self.initialized = False

class IntegrationAgent(BaseAetheroAgent):
    """Agent for testing external integrations"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any], logger: logging.Logger, 
                 agent_bus: AgentBus, connector: ExternalConnector):
        super().__init__(agent_id, config, logger, agent_bus)
        self.connector = connector
        self.plugins: List[PluginInterface] = []
    
    async def add_plugin(self, plugin: PluginInterface):
        """Add and initialize a plugin"""
        await plugin.initialize()
        self.plugins.append(plugin)
    
    async def process_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process task with external system integration"""
        # Process through plugins
        for plugin in self.plugins:
            task_data = await plugin.process(task_data)
        
        # Send to external system
        await self.connector.send_data(task_data)
        
        # Receive response
        response = await self.connector.receive_data()
        
        return {
            "status": "success",
            "result": response,
            "task_data": task_data,
            "asl_context": asl_context
        }

async def test_rest_integration():
    """Test REST API integration"""
    logger = logging.getLogger("integration_test")
    agent_bus = AgentBus()
    
    # Setup REST connector with mock API
    connector = RESTConnector(
        base_url="https://api.example.com/v1",
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Create integration agent
    agent = IntegrationAgent(
        "rest_agent",
        {"pipeline_id": "integration_test"},
        logger,
        agent_bus,
        connector
    )
    
    try:
        # Add custom plugin
        plugin = CustomPlugin({"name": "test_plugin"})
        await agent.add_plugin(plugin)
        
        # Test task processing
        task_data = {
            "task_id": "rest_test",
            "data": {"key": "value"}
        }
        
        result = await agent.execute_task(task_data, {})
        logger.info(f"REST integration result: {result}")
        
    finally:
        await connector.disconnect()
        for plugin in agent.plugins:
            await plugin.cleanup()

async def test_websocket_integration():
    """Test WebSocket integration"""
    logger = logging.getLogger("integration_test")
    agent_bus = AgentBus()
    
    # Setup WebSocket connector
    connector = WebSocketConnector("ws://example.com/ws")
    
    # Create integration agent
    agent = IntegrationAgent(
        "ws_agent",
        {"pipeline_id": "integration_test"},
        logger,
        agent_bus,
        connector
    )
    
    try:
        # Test real-time data processing
        task_data = {
            "task_id": "ws_test",
            "stream": True,
            "data": {"type": "real_time"}
        }
        
        result = await agent.execute_task(task_data, {})
        logger.info(f"WebSocket integration result: {result}")
        
    finally:
        await connector.disconnect()

async def test_plugin_system():
    """Test custom plugin architecture"""
    logger = logging.getLogger("integration_test")
    agent_bus = AgentBus()
    
    # Setup mock connector
    class MockConnector(ExternalConnector):
        async def connect(self): pass
        async def disconnect(self): pass
        async def send_data(self, data): return data
        async def receive_data(self): return {"status": "ok"}
    
    # Create integration agent
    agent = IntegrationAgent(
        "plugin_agent",
        {"pipeline_id": "integration_test"},
        logger,
        agent_bus,
        MockConnector()
    )
    
    try:
        # Test multiple plugins
        plugins = [
            CustomPlugin({"name": "plugin_1"}),
            CustomPlugin({"name": "plugin_2"})
        ]
        
        for plugin in plugins:
            await agent.add_plugin(plugin)
        
        # Test task processing through plugins
        task_data = {
            "task_id": "plugin_test",
            "data": {"key": "value"}
        }
        
        result = await agent.execute_task(task_data, {})
        logger.info(f"Plugin system result: {result}")
        
    finally:
        for plugin in agent.plugins:
            await plugin.cleanup()

async def run_integration_tests():
    """Run all integration tests"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("integration_tests")
    
    try:
        logger.info("Starting integration testing suite...")
        
        # Test REST integration
        logger.info("\nTesting REST API integration...")
        await test_rest_integration()
        
        # Test WebSocket integration
        logger.info("\nTesting WebSocket integration...")
        await test_websocket_integration()
        
        # Test plugin system
        logger.info("\nTesting plugin architecture...")
        await test_plugin_system()
        
        logger.info("\nAll integration tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in integration testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
