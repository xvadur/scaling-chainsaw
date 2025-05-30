import asyncio
import logging
import time
import psutil
import statistics
import pytest
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.aethero_agent_bootstrap import BaseAetheroAgent
from src.agents.agent_bus import AgentBus, Message
from src.monitoring.monitor import AetheroMonitor

class ScaleTestAgent(BaseAetheroAgent):
    """Agent implementation for scale testing"""
    
    async def process_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process task with configurable load simulation"""
        # Simulate CPU load
        if task_data.get("cpu_intensive", False):
            self._simulate_cpu_load(task_data.get("cpu_load_duration", 0.1))
            
        # Simulate memory allocation
        if task_data.get("memory_intensive", False):
            self._simulate_memory_load(task_data.get("memory_size_mb", 1))
            
        return {
            "status": "success",
            "result": f"Processed by {self.agent_id}",
            "task_data": task_data,
            "asl_context": asl_context,
            "timestamp": datetime.now().isoformat()
        }
    
    def _simulate_cpu_load(self, duration: float):
        """Simulate CPU-intensive task"""
        start_time = time.time()
        while time.time() - start_time < duration:
            _ = [i * i for i in range(1000)]
    
    def _simulate_memory_load(self, size_mb: int):
        """Simulate memory-intensive task"""
        # Allocate memory (1MB = 1024 * 1024 bytes)
        _ = bytearray(size_mb * 1024 * 1024)

class PerformanceMetrics:
    """Track performance metrics during scale testing"""
    
    def __init__(self):
        self.response_times = []
        self.cpu_usage = []
        self.memory_usage = []
        self.error_count = 0
        self.success_count = 0
        
    def add_response_time(self, time_ms: float):
        self.response_times.append(time_ms)
        
    def add_system_metrics(self, cpu: float, memory: float):
        self.cpu_usage.append(cpu)
        self.memory_usage.append(memory)
        
    def increment_error(self):
        self.error_count += 1
        
    def increment_success(self):
        self.success_count += 1
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        return {
            "response_times": {
                "avg": statistics.mean(self.response_times) if self.response_times else 0,
                "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else 0,
                "max": max(self.response_times) if self.response_times else 0
            },
            "system_metrics": {
                "cpu_avg": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                "memory_avg": statistics.mean(self.memory_usage) if self.memory_usage else 0
            },
            "success_rate": self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0
        }

async def create_large_message(size_mb: int) -> Dict[str, Any]:
    """Create a message with specified size"""
    return {
        "data": "x" * (size_mb * 1024 * 1024),  # 1MB = 1024 * 1024 bytes
        "metadata": {
            "size_mb": size_mb,
            "timestamp": datetime.now().isoformat()
        }
    }

@pytest.mark.asyncio
async def test_concurrent_agents(
    agent_bus: AgentBus,
    logger: logging.Logger,
    test_config: Dict[str, Any],
    test_agent_count: int,
    test_tasks_per_agent: int
):
    """Test system with multiple concurrent agents"""
    metrics = PerformanceMetrics()
    
    # Create agents
    agents = []
    for i in range(test_agent_count):
        agent = ScaleTestAgent(
            f"scale_agent_{i}",
            test_config,
            logger,
            agent_bus
        )
        agents.append(agent)
    
    # Create tasks
    tasks = []
    for agent in agents:
        for j in range(test_tasks_per_agent):
            task_data = {
                "task_id": f"task_{j}",
                "cpu_intensive": True,
                "cpu_load_duration": 0.1,
                "memory_intensive": True,
                "memory_size_mb": 1
            }
            
            async def execute_task(agent, task_data):
                try:
                    start_time = time.time()
                    result = await agent.execute_task(task_data, {})
                    metrics.add_response_time((time.time() - start_time) * 1000)
                    metrics.increment_success()
                    return result
                except Exception as e:
                    metrics.increment_error()
                    logger.error(f"Task execution failed: {str(e)}")
                    raise
            
            tasks.append(execute_task(agent, task_data))
    
    # Execute tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results, metrics

@pytest.mark.asyncio
async def test_large_messages(
    agent_bus: AgentBus,
    logger: logging.Logger,
    test_sizes: List[int]
):
    """Test handling of large message payloads"""
    metrics = PerformanceMetrics()
    
    results = []
    for size in test_sizes:
        try:
            message = await create_large_message(size)
            
            start_time = time.time()
            await agent_bus.publish(
                topic="large_message_test",
                message=message,
                asl_tags={"size_mb": size}
            )
            metrics.add_response_time((time.time() - start_time) * 1000)
            
            results.append({"size_mb": size, "status": "success"})
            metrics.increment_success()
            
        except Exception as e:
            logger.error(f"Large message test failed for size {size}MB: {str(e)}")
            results.append({"size_mb": size, "status": "failed", "error": str(e)})
            metrics.increment_error()
    
    return results, metrics

@pytest.mark.asyncio
async def test_network_latency(
    agent_bus: AgentBus,
    logger: logging.Logger,
    test_message_count: int,
    test_message_size: int
):
    """Test system behavior with network latency simulation"""
    metrics = PerformanceMetrics()
    
    # Simulate network latency
    original_publish = agent_bus.publish
    
    async def delayed_publish(*args, **kwargs):
        await asyncio.sleep(0.05)  # Simulate 50ms network latency
        return await original_publish(*args, **kwargs)
    
    agent_bus.publish = delayed_publish
    
    try:
        tasks = []
        for i in range(test_message_count):
            message = {
                "data": "x" * (test_message_size * 1024),
                "sequence": i
            }
            
            async def send_message(message):
                try:
                    start_time = time.time()
                    await agent_bus.publish(
                        topic="latency_test",
                        message=message,
                        asl_tags={"test": "latency"}
                    )
                    metrics.add_response_time((time.time() - start_time) * 1000)
                    metrics.increment_success()
                except Exception as e:
                    metrics.increment_error()
                    raise
            
            tasks.append(send_message(message))
        
        await asyncio.gather(*tasks)
        
    finally:
        agent_bus.publish = original_publish
    
    return metrics

@pytest.mark.asyncio
async def test_all_scale_scenarios(
    agent_bus: AgentBus,
    logger: logging.Logger,
    test_config: Dict[str, Any],
    test_agent_count: int,
    test_tasks_per_agent: int,
    test_sizes: List[int],
    test_message_count: int,
    test_message_size: int
):
    """Run all scale tests in sequence"""
    try:
        logger.info("Starting scale testing suite...")
        
        # Test concurrent agents
        logger.info("\nTesting concurrent agents...")
        agent_results, agent_metrics = await test_concurrent_agents(
            agent_bus, logger, test_config,
            test_agent_count, test_tasks_per_agent
        )
        logger.info(f"Concurrent agents metrics: {agent_metrics.get_summary()}")
        
        # Test large messages
        logger.info("\nTesting large message handling...")
        message_results, message_metrics = await test_large_messages(
            agent_bus, logger, test_sizes
        )
        logger.info(f"Large message results: {message_results}")
        logger.info(f"Message handling metrics: {message_metrics.get_summary()}")
        
        # Test network latency
        logger.info("\nTesting network latency handling...")
        latency_metrics = await test_network_latency(
            agent_bus, logger,
            test_message_count, test_message_size
        )
        logger.info(f"Network latency metrics: {latency_metrics.get_summary()}")
        
        logger.info("\nAll scale tests completed successfully!")
        
        return {
            "agent_metrics": agent_metrics.get_summary(),
            "message_metrics": message_metrics.get_summary(),
            "latency_metrics": latency_metrics.get_summary()
        }
        
    except Exception as e:
        logger.error(f"Error in scale testing: {str(e)}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
