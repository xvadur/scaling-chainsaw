import asyncio
from typing import Dict, Any, Optional, List, Callable
import logging
from datetime import datetime
from dataclasses import dataclass
import json

@dataclass
class Message:
    topic: str
    content: Dict[str, Any]
    asl_tags: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "content": self.content,
            "asl_tags": self.asl_tags,
            "timestamp": self.timestamp
        }

class AgentBus:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('agent_bus')
        self.topics: Dict[str, List[asyncio.Queue]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_history: Dict[str, List[Message]] = {}
        self.running = True

    async def publish(self, topic: str, message: Dict[str, Any], asl_tags: Dict[str, Any]) -> None:
        """Publish a message to a topic."""
        try:
            msg = Message(
                topic=topic,
                content=message,
                asl_tags=asl_tags
            )
            
            # Log the message
            self.logger.info(
                f"Publishing to topic {topic}: {json.dumps(message)}"
            )

            # Store in history
            if topic not in self.message_history:
                self.message_history[topic] = []
            self.message_history[topic].append(msg)

            # Deliver to topic queues
            if topic in self.topics:
                for queue in self.topics[topic]:
                    await queue.put(msg)

            # Notify subscribers
            if topic in self.subscribers:
                for callback in self.subscribers[topic]:
                    try:
                        await callback(msg)
                    except Exception as e:
                        self.logger.error(f"Subscriber callback failed: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error publishing message: {str(e)}")
            raise

    async def subscribe(self, topic: str) -> asyncio.Queue:
        """Subscribe to a topic and return a queue for messages."""
        if topic not in self.topics:
            self.topics[topic] = []
        
        queue = asyncio.Queue()
        self.topics[topic].append(queue)
        
        self.logger.info(f"New subscription to topic {topic}")
        return queue

    def add_subscriber(self, topic: str, callback: Callable) -> None:
        """Add a callback subscriber to a topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        self.logger.info(f"Added subscriber callback to topic {topic}")

    def get_history(self, topic: str, limit: Optional[int] = None) -> List[Message]:
        """Get message history for a topic."""
        if topic not in self.message_history:
            return []
        
        messages = self.message_history[topic]
        if limit:
            return messages[-limit:]
        return messages

    async def clear_history(self, topic: Optional[str] = None) -> None:
        """Clear message history for a topic or all topics."""
        if topic:
            if topic in self.message_history:
                self.message_history[topic] = []
                self.logger.info(f"Cleared history for topic {topic}")
        else:
            self.message_history = {}
            self.logger.info("Cleared all message history")

# Example usage
async def example_subscriber(message: Message):
    """Example subscriber callback."""
    print(f"Received message on topic {message.topic}: {message.content}")

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create agent bus
    bus = AgentBus()
    
    # Create a subscription
    queue = await bus.subscribe("test_topic")
    
    # Add a callback subscriber
    bus.add_subscriber("test_topic", example_subscriber)
    
    # Create and publish a test message
    message = Message(
        topic="test_topic",
        content={"action": "test", "data": "example"},
        asl_tags={
            "pipeline_id": "test_pipeline",
            "agent_id": "test_agent",
            "status": "active"
        }
    )
    
    await bus.publish(message)
    
    # Receive message from queue
    received = await queue.get()
    print(f"Received from queue: {received.to_dict()}")
    
    # Get history
    history = bus.get_history("test_topic")
    print(f"Message history: {[m.to_dict() for m in history]}")

if __name__ == "__main__":
    asyncio.run(main())
