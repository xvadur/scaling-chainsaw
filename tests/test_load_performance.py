"""
Load and Performance Tests for AetheroOS
"""
import pytest
import asyncio

pytestmark = pytest.mark.skip(reason="aiohttp not supported on Python 3.13")
# import aiohttp temporarily removed due to Python 3.13 compatibility issues
import time
from datetime import datetime
import logging
import statistics
from typing import Dict, List, Any
import concurrent.futures
import psutil
import docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestLoadPerformance:
    @pytest.fixture(scope="class")
    async def http_client(self):
        async with aiohttp.ClientSession() as session:
            yield session

    @pytest.fixture(scope="class")
    def docker_client(self):
        return docker.from_env()

    async def test_concurrent_agent_operations(self, http_client):
        """Test system performance under concurrent agent operations"""
        num_requests = 100
        concurrent_limit = 10

        async def make_request(task_id: int) -> Dict[str, Any]:
            task_data = {
                "directive": f"Test directive {task_id}",
                "priority": "high",
                "context": {"test_id": task_id}
            }

            start_time = time.time()
            try:
                async with http_client.post(
                    "http://localhost:8000/api/v1/plan",
                    json=task_data
                ) as response:
                    assert response.status == 200
                    result = await response.json()
                    duration = time.time() - start_time
                    return {"success": True, "duration": duration}
            except Exception as e:
                duration = time.time() - start_time
                return {"success": False, "duration": duration, "error": str(e)}

        # Execute concurrent requests
        tasks = []
        for i in range(num_requests):
            if len(tasks) >= concurrent_limit:
                done, tasks = await asyncio.wait(
                    tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
            tasks.append(asyncio.create_task(make_request(i)))

        # Wait for remaining tasks
        results = await asyncio.gather(*tasks)

        # Analyze results
        durations = [r["duration"] for r in results if r["success"]]
        success_rate = len([r for r in results if r["success"]]) / len(results)
        
        assert success_rate >= 0.95, f"Success rate below threshold: {success_rate}"
        assert statistics.mean(durations) < 2.0, "Average response time too high"

    async def test_memory_system_load(self, http_client):
        """Test memory system performance under load"""
        num_operations = 1000
        batch_size = 50

        async def batch_operation(batch_id: int) -> List[Dict[str, Any]]:
            results = []
            for i in range(batch_size):
                data = {
                    "agent_id": f"test_agent_{batch_id}_{i}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "state": "processing",
                    "data": {"test": f"data_{batch_id}_{i}"}
                }

                start_time = time.time()
                try:
                    async with http_client.post(
                        "http://localhost:9091/api/v1/states",
                        json=data
                    ) as response:
                        assert response.status == 201
                        duration = time.time() - start_time
                        results.append({"success": True, "duration": duration})
                except Exception as e:
                    duration = time.time() - start_time
                    results.append({
                        "success": False,
                        "duration": duration,
                        "error": str(e)
                    })

            return results

        # Execute batched operations
        tasks = []
        for i in range(0, num_operations, batch_size):
            tasks.append(asyncio.create_task(batch_operation(i // batch_size)))

        batch_results = await asyncio.gather(*tasks)
        results = [r for batch in batch_results for r in batch]

        # Analyze results
        durations = [r["duration"] for r in results if r["success"]]
        success_rate = len([r for r in results if r["success"]]) / len(results)
        
        assert success_rate >= 0.95, f"Memory system success rate below threshold: {success_rate}"
        assert statistics.mean(durations) < 0.1, "Memory system average response time too high"

    async def test_metrics_collection_performance(self, http_client):
        """Test metrics collection system under load"""
        num_metrics = 1000
        collection_interval = 0.1  # seconds

        async def send_metrics(metric_id: int) -> Dict[str, Any]:
            metrics = {
                "test_metric": metric_id,
                "timestamp": time.time(),
                "value": metric_id % 100
            }

            start_time = time.time()
            try:
                async with http_client.post(
                    "http://localhost:9091/metrics/job/load_test",
                    json=metrics
                ) as response:
                    assert response.status == 200
                    duration = time.time() - start_time
                    return {"success": True, "duration": duration}
            except Exception as e:
                duration = time.time() - start_time
                return {"success": False, "duration": duration, "error": str(e)}

        # Send metrics with controlled rate
        tasks = []
        for i in range(num_metrics):
            tasks.append(asyncio.create_task(send_metrics(i)))
            await asyncio.sleep(collection_interval)

        results = await asyncio.gather(*tasks)

        # Analyze results
        durations = [r["duration"] for r in results if r["success"]]
        success_rate = len([r for r in results if r["success"]]) / len(results)
        
        assert success_rate >= 0.95, f"Metrics collection success rate below threshold: {success_rate}"
        assert statistics.mean(durations) < 0.05, "Metrics collection average time too high"

    def test_system_resource_usage(self, docker_client):
        """Test system resource usage under normal operation"""
        containers = docker_client.containers.list(
            filters={"name": "aetheros_"}
        )

        for container in containers:
            stats = container.stats(stream=False)
            
            # Calculate CPU usage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                         stats["precpu_stats"]["system_cpu_usage"]
            cpu_usage = (cpu_delta / system_delta) * 100.0
            
            # Calculate memory usage
            memory_usage = stats["memory_stats"]["usage"] / \
                         stats["memory_stats"]["limit"] * 100.0
            
            assert cpu_usage < 80.0, f"High CPU usage in {container.name}: {cpu_usage}%"
            assert memory_usage < 80.0, f"High memory usage in {container.name}: {memory_usage}%"

    async def test_network_resilience(self, http_client, docker_client):
        """Test system resilience under network stress"""
        # Simulate network latency
        container = docker_client.containers.get("aetheros_mem")
        container.exec_run(
            "tc qdisc add dev eth0 root netem delay 100ms 10ms distribution normal"
        )

        try:
            # Test operations under latency
            async def test_operation() -> Dict[str, Any]:
                start_time = time.time()
                try:
                    async with http_client.get(
                        "http://localhost:9091/health"
                    ) as response:
                        assert response.status == 200
                        duration = time.time() - start_time
                        return {"success": True, "duration": duration}
                except Exception as e:
                    duration = time.time() - start_time
                    return {"success": False, "duration": duration, "error": str(e)}

            # Execute multiple operations
            tasks = [asyncio.create_task(test_operation()) for _ in range(50)]
            results = await asyncio.gather(*tasks)

            # Analyze results
            success_rate = len([r for r in results if r["success"]]) / len(results)
            assert success_rate >= 0.9, f"Network resilience test failed: {success_rate}"

        finally:
            # Remove network latency
            container.exec_run("tc qdisc del dev eth0 root")

    @pytest.mark.asyncio
    async def test_recovery_time(self, http_client, docker_client):
        """Test system recovery time after component restart"""
        container = docker_client.containers.get("aetheros_mem")
        
        # Stop container
        container.stop()
        
        # Record start time
        start_time = time.time()
        
        # Start container
        container.start()
        
        # Wait for recovery
        recovered = False
        while time.time() - start_time < 30:  # 30 second timeout
            try:
                async with http_client.get(
                    "http://localhost:9091/health"
                ) as response:
                    if response.status == 200:
                        recovered = True
                        break
            except:
                await asyncio.sleep(0.5)
                continue
        
        recovery_time = time.time() - start_time
        assert recovered, "System failed to recover"
        assert recovery_time < 10, f"Recovery time too long: {recovery_time}s"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
