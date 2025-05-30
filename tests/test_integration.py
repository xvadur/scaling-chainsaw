import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Import our components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.aethero_agent_bootstrap import BaseAetheroAgent
from src.agents.error_handler import ErrorHandler, ErrorContext
from src.agents.agent_bus import AgentBus, Message
from src.monitoring.monitor import AetheroMonitor

class TestAgent(BaseAetheroAgent):
    async def process_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Processing task: {task_data}")
        
        # Simulate processing
        await asyncio.sleep(1)
        
        if task_data.get("should_fail", False):
            raise ValueError("Task failed as requested")
            
        return {
            "status": "success",
            "result": f"Processed by {self.agent_id}",
            "task_data": task_data,
            "asl_context": asl_context
        }

async def test_integration():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("integration_test")
    
    # Initialize components
    error_handler = ErrorHandler()
    agent_bus = AgentBus()
    monitor = AetheroMonitor()
    
    # Create test agent
    agent_config = {
        "pipeline_id": "test_pipeline",
        "retry_count": 3
    }
    test_agent = TestAgent("test_agent_1", agent_config, logger, agent_bus)
    
    # Start monitoring
    monitor_task = asyncio.create_task(monitor.start_monitoring(interval=5))
    
    try:
        # Test 1: Successful task processing
        logger.info("Test 1: Processing successful task")
        task_data = {
            "task_id": "task_1",
            "action": "process",
            "data": {"key": "value"}
        }
        asl_context = {
            "intent_vector": [0.8, 0.2, 0.0],
            "context_depth": 3,
            "ethical_weight": 0.95
        }
        
        result = await test_agent.execute_task(task_data, asl_context)
        logger.info(f"Test 1 Result: {result}")
        
        # Test 2: Error handling
        logger.info("\nTest 2: Testing error handling")
        error_task = {
            "task_id": "task_2",
            "action": "process",
            "should_fail": True
        }
        
        try:
            await test_agent.execute_task(error_task, asl_context)
        except Exception as e:
            logger.info(f"Expected error caught: {str(e)}")
        
        # Test 3: Message bus
        logger.info("\nTest 3: Testing message bus")
        queue = await agent_bus.subscribe("test_topic")
        
        # Test message publishing
        await agent_bus.publish(
            topic="test_topic",
            message={"test": "data"},
            asl_tags={"pipeline_id": "test_pipeline"}
        )
        received = await queue.get()
        logger.info(f"Message received: {received.to_dict()}")
        
        # Test 4: Monitor metrics
        logger.info("\nTest 4: Testing monitoring")
        monitor.update_agent_metrics("test_agent_1", {
            "status": "active",
            "tasks_processed": 2,
            "errors_count": 1,
            "avg_processing_time": 1.0,
            "memory_usage": 45.2,
            "cpu_usage": 12.3
        })
        
        # Get and display metrics
        system_metrics = monitor.get_system_metrics(limit=1)
        agent_metrics = monitor.get_agent_metrics("test_agent_1")
        
        logger.info("\nSystem Metrics:")
        logger.info(system_metrics)
        
        logger.info("\nAgent Metrics:")
        logger.info(agent_metrics)
        
        logger.info("\nAll tests completed successfully!")
        
    finally:
        # Cleanup
        monitor.running = False
        await monitor_task
        
if __name__ == "__main__":
    asyncio.run(test_integration())
