from abc import ABC, abstractmethod
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class ASLLogUnit:
    def __init__(self, pipeline_id: str, agent_id: str, status: str):
        self.timestamp = datetime.now().isoformat()
        self.pipeline_id = pipeline_id
        self.agent_id = agent_id
        self.status = status
        self.metadata = {}

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "pipeline_id": self.pipeline_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "metadata": self.metadata
        }

class MessageBus:
    def __init__(self):
        self.topics = {}

    async def publish(self, topic: str, message: Dict[str, Any], asl_tags: Dict[str, Any]) -> None:
        if topic not in self.topics:
            self.topics[topic] = []
        
        enriched_message = {
            "content": message,
            "asl_tags": asl_tags,
            "timestamp": datetime.now().isoformat()
        }
        self.topics[topic].append(enriched_message)

    async def subscribe(self, topic: str) -> asyncio.Queue:
        if topic not in self.topics:
            self.topics[topic] = []
        queue = asyncio.Queue()
        return queue

class BaseAetheroAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        message_bus: Optional[MessageBus] = None
    ):
        self.agent_id = agent_id
        self.config = config
        self.logger = logger or logging.getLogger(agent_id)
        self.message_bus = message_bus or MessageBus()
        self.status = "initialized"

    def _create_log_unit(self, status: str) -> ASLLogUnit:
        return ASLLogUnit(
            pipeline_id=self.config.get("pipeline_id", "default"),
            agent_id=self.agent_id,
            status=status
        )

    async def _log_task_event(self, event_type: str, task_id: str, additional_data: Dict[str, Any] = None) -> None:
        log_unit = self._create_log_unit(event_type)
        log_unit.add_metadata("task_id", task_id)
        if additional_data:
            log_unit.add_metadata("additional_data", additional_data)
        
        self.logger.info(f"{event_type}: {log_unit.to_dict()}")

    @abstractmethod
    async def process_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task with the given data and ASL context."""
        pass

    async def execute_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with error handling and logging."""
        task_id = task_data.get("task_id", str(datetime.now().timestamp()))
        
        try:
            await self._log_task_event("task_started", task_id, {"input": task_data})
            
            result = await self.process_task(task_data, asl_context)
            
            await self._log_task_event("task_completed", task_id, {"output": result})
            
            # Publish result to message bus
            await self.message_bus.publish(
                topic=f"{self.agent_id}_output",
                message=result,
                asl_tags=asl_context
            )
            
            return result
            
        except Exception as e:
            error_details = {
                "error": str(e),
                "task_data": task_data,
                "asl_context": asl_context
            }
            await self._log_task_event("task_failed", task_id, error_details)
            raise

# Example Implementation
class ExampleAgent(BaseAetheroAgent):
    async def process_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        # Example implementation
        self.logger.info(f"Processing task with data: {task_data}")
        
        # Simulate some processing
        await asyncio.sleep(1)
        
        # Return processed result
        return {
            "status": "success",
            "result": f"Processed by {self.agent_id}",
            "input_data": task_data,
            "asl_context": asl_context
        }

# Example usage
async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent configuration
    config = {
        "pipeline_id": "test_pipeline",
        "log_level": "INFO",
        "retry_count": 3
    }
    
    # Initialize agent
    agent = ExampleAgent("example_agent_1", config)
    
    # Create test task
    task_data = {
        "task_id": "test_task_1",
        "action": "process",
        "data": {"key": "value"}
    }
    
    # Create ASL context
    asl_context = {
        "intent_vector": [0.8, 0.2, 0.0],
        "context_depth": 3,
        "ethical_weight": 0.95
    }
    
    try:
        # Execute task
        result = await agent.execute_task(task_data, asl_context)
        print(f"Task completed successfully: {result}")
    except Exception as e:
        print(f"Task failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
