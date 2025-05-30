from typing import Dict, Any, Optional, Callable
import logging
from datetime import datetime
import asyncio
from dataclasses import dataclass

@dataclass
class ErrorContext:
    error: Exception
    agent_id: str
    task_id: str
    pipeline_id: str
    timestamp: str
    additional_data: Dict[str, Any]

class AetheroError(Exception):
    """Base exception class for Aethero system errors."""
    def __init__(self, message: str, error_code: str, context: Dict[str, Any]):
        super().__init__(message)
        self.error_code = error_code
        self.context = context
        self.timestamp = datetime.now().isoformat()

class AgentError(AetheroError):
    """Exception raised for errors in agent operations."""
    pass

class TaskError(AetheroError):
    """Exception raised for errors in task processing."""
    pass

class ErrorHandler:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('aethero_error_handler')
        self.error_handlers: Dict[str, Callable] = {}
        self.retry_policies: Dict[str, Dict[str, Any]] = {}
        self.notification_callbacks: Dict[str, Callable] = []

    def register_error_handler(self, error_type: str, handler: Callable) -> None:
        """Register a handler for a specific error type."""
        self.error_handlers[error_type] = handler

    def set_retry_policy(self, agent_id: str, policy: Dict[str, Any]) -> None:
        """Set retry policy for an agent."""
        self.retry_policies[agent_id] = policy

    def register_notification_callback(self, callback: Callable) -> None:
        """Register a callback for error notifications."""
        self.notification_callbacks.append(callback)

    async def handle_error(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Handle an error with the appropriate strategy."""
        error_type = type(error_context.error).__name__
        
        # Log the error
        self.logger.error(
            f"Error in agent {error_context.agent_id}: {str(error_context.error)}",
            extra={
                "error_context": error_context.__dict__,
                "error_type": error_type
            }
        )

        # Check for specific handler
        if error_type in self.error_handlers:
            try:
                return await self.error_handlers[error_type](error_context)
            except Exception as e:
                self.logger.error(f"Error handler failed: {str(e)}")

        # Check retry policy
        if error_context.agent_id in self.retry_policies:
            return await self._handle_retry(error_context)

        # Send notifications
        await self._send_notifications(error_context)

        # Return error response
        return {
            "status": "error",
            "error_type": error_type,
            "message": str(error_context.error),
            "timestamp": error_context.timestamp,
            "task_id": error_context.task_id,
            "agent_id": error_context.agent_id
        }

    async def _handle_retry(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Handle error retry based on policy."""
        policy = self.retry_policies[error_context.agent_id]
        max_retries = policy.get("max_retries", 3)
        delay = policy.get("delay", 1)
        
        current_retry = error_context.additional_data.get("retry_count", 0)
        
        if current_retry < max_retries:
            self.logger.info(
                f"Retrying task {error_context.task_id} for agent {error_context.agent_id}. "
                f"Attempt {current_retry + 1}/{max_retries}"
            )
            
            # Exponential backoff
            retry_delay = delay * (2 ** current_retry)
            await asyncio.sleep(retry_delay)
            
            return {
                "status": "retry",
                "retry_count": current_retry + 1,
                "next_retry_delay": retry_delay * 2,
                "task_id": error_context.task_id
            }
        
        return {
            "status": "error",
            "message": "Max retries exceeded",
            "task_id": error_context.task_id,
            "agent_id": error_context.agent_id
        }

    async def _send_notifications(self, error_context: ErrorContext) -> None:
        """Send error notifications to registered callbacks."""
        notification = {
            "type": "error",
            "agent_id": error_context.agent_id,
            "task_id": error_context.task_id,
            "error": str(error_context.error),
            "timestamp": error_context.timestamp
        }

        for callback in self.notification_callbacks:
            try:
                await callback(notification)
            except Exception as e:
                self.logger.error(f"Notification callback failed: {str(e)}")

# Example usage
async def example_error_handler(error_context: ErrorContext) -> Dict[str, Any]:
    """Example error handler for demonstration."""
    return {
        "status": "handled",
        "message": f"Handled {type(error_context.error).__name__}",
        "task_id": error_context.task_id
    }

async def example_notification(notification: Dict[str, Any]) -> None:
    """Example notification callback."""
    print(f"Error notification: {notification}")

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create error handler
    handler = ErrorHandler()
    
    # Register handlers
    handler.register_error_handler("ValueError", example_error_handler)
    handler.register_notification_callback(example_notification)
    
    # Set retry policy
    handler.set_retry_policy("example_agent", {
        "max_retries": 3,
        "delay": 1
    })
    
    # Create error context
    error_context = ErrorContext(
        error=ValueError("Example error"),
        agent_id="example_agent",
        task_id="test_task_1",
        pipeline_id="test_pipeline",
        timestamp=datetime.now().isoformat(),
        additional_data={"retry_count": 0}
    )
    
    # Handle error
    result = await handler.handle_error(error_context)
    print(f"Error handling result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
