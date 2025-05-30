import asyncio
import logging
from datetime import datetime
import sys
import os
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.aethero_agent_bootstrap import BaseAetheroAgent
from src.agents.error_handler import ErrorHandler, ErrorContext
from src.agents.agent_bus import AgentBus, Message
from src.monitoring.monitor import AetheroMonitor

class StressTestAgent(BaseAetheroAgent):
    async def process_task(self, task_data: Dict[str, Any], asl_context: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate varying processing times and memory usage
        await asyncio.sleep(task_data.get("processing_time", 0.1))
        
        # Simulate memory allocation
        memory_size = task_data.get("memory_size", 1000)
        _ = " " * memory_size
        
        if task_data.get("should_fail", False):
            raise ValueError(f"Task {task_data.get('task_id')} failed")
            
        return {
            "status": "success",
            "result": f"Processed by {self.agent_id}",
            "task_data": task_data,
            "asl_context": asl_context,
            "timestamp": datetime.now().isoformat()
        }

async def generate_large_payload(size_kb: int) -> Dict[str, Any]:
    """Generate a large message payload."""
    return {
        "data": "x" * (size_kb * 1024),
        "metadata": {
            "size": size_kb,
            "timestamp": datetime.now().isoformat()
        }
    }

async def test_concurrent_processing(agent: StressTestAgent, num_tasks: int):
    """Test concurrent task processing."""
    tasks = []
    for i in range(num_tasks):
        task_data = {
            "task_id": f"concurrent_task_{i}",
            "processing_time": 0.1,
            "memory_size": 1000
        }
        asl_context = {"pipeline_id": "stress_test"}
        tasks.append(agent.execute_task(task_data, asl_context))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

async def test_large_messages(agent_bus: AgentBus, sizes_kb: List[int]):
    """Test handling of large message payloads."""
    results = []
    for size in sizes_kb:
        payload = await generate_large_payload(size)
        try:
            await agent_bus.publish(
                topic="large_message_test",
                message=payload,
                asl_tags={"size_kb": size}
            )
            results.append({"size_kb": size, "status": "success"})
        except Exception as e:
            results.append({"size_kb": size, "status": "failed", "error": str(e)})
    return results

async def test_network_interruption(agent: StressTestAgent, agent_bus: AgentBus):
    """Test system behavior during network interruptions."""
    # Simulate network delay
    original_publish = agent_bus.publish
    
    async def delayed_publish(*args, **kwargs):
        await asyncio.sleep(2)  # Simulate network delay
        return await original_publish(*args, **kwargs)
    
    agent_bus.publish = delayed_publish
    
    try:
        task_data = {"task_id": "network_test", "processing_time": 0.5}
        asl_context = {"pipeline_id": "network_test"}
        result = await agent.execute_task(task_data, asl_context)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    finally:
        agent_bus.publish = original_publish

async def test_multi_agent_workflow(num_agents: int, tasks_per_agent: int):
    """Test complex multi-agent workflow scenarios."""
    agents = []
    agent_bus = AgentBus()
    
    # Create agents
    for i in range(num_agents):
        agent = StressTestAgent(
            f"stress_agent_{i}",
            {"pipeline_id": "multi_agent_test"},
            logging.getLogger(f"stress_agent_{i}"),
            agent_bus
        )
        agents.append(agent)
    
    # Create workflow
    results = []
    for agent in agents:
        agent_results = await test_concurrent_processing(agent, tasks_per_agent)
        results.extend(agent_results)
    
    return results

async def test_system_recovery():
    """Test system recovery after failures."""
    agent_bus = AgentBus()
    monitor = AetheroMonitor()
    agent = StressTestAgent(
        "recovery_agent",
        {"pipeline_id": "recovery_test"},
        logging.getLogger("recovery_agent"),
        agent_bus
    )
    
    results = []
    
    # Test 1: Agent failure and recovery
    try:
        await agent.execute_task({"should_fail": True}, {})
    except Exception as e:
        results.append({"test": "agent_failure", "status": "expected_failure", "error": str(e)})
    
    # Test 2: Recovery after failure
    try:
        result = await agent.execute_task({"task_id": "recovery_task"}, {})
        results.append({"test": "recovery", "status": "success", "result": result})
    except Exception as e:
        results.append({"test": "recovery", "status": "failed", "error": str(e)})
    
    return results

async def run_thorough_tests():
    """Run all thorough tests."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("thorough_tests")
    
    try:
        logger.info("Starting thorough testing suite...")
        
        # Initialize components
        agent_bus = AgentBus()
        monitor = AetheroMonitor()
        agent = StressTestAgent(
            "stress_test_agent",
            {"pipeline_id": "thorough_test"},
            logger,
            agent_bus
        )
        
        # Start monitoring
        monitor_task = asyncio.create_task(monitor.start_monitoring(interval=5))
        
        # 1. Test concurrent processing
        logger.info("\nTesting concurrent processing...")
        concurrent_results = await test_concurrent_processing(agent, 10)
        logger.info(f"Concurrent processing results: {len(concurrent_results)} tasks completed")
        
        # 2. Test large messages
        logger.info("\nTesting large message handling...")
        message_results = await test_large_messages(agent_bus, [1, 10, 100])
        logger.info(f"Large message results: {json.dumps(message_results, indent=2)}")
        
        # 3. Test network interruption handling
        logger.info("\nTesting network interruption handling...")
        network_result = await test_network_interruption(agent, agent_bus)
        logger.info(f"Network interruption test result: {json.dumps(network_result, indent=2)}")
        
        # 4. Test multi-agent workflow
        logger.info("\nTesting multi-agent workflow...")
        workflow_results = await test_multi_agent_workflow(3, 5)
        logger.info(f"Multi-agent workflow results: {len(workflow_results)} total tasks completed")
        
        # 5. Test system recovery
        logger.info("\nTesting system recovery...")
        recovery_results = await test_system_recovery()
        logger.info(f"Recovery test results: {json.dumps(recovery_results, indent=2)}")
        
        # Stop monitoring
        monitor.running = False
        await monitor_task
        
        logger.info("\nAll thorough tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in thorough testing: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_thorough_tests())
