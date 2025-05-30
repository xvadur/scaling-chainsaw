"""
AetheroOS Deployment Verification Script
"""
import asyncio
import aiohttp
import yaml
import json
from pathlib import Path
import sys
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentVerifier:
    def __init__(self):
        self.errors = []
        self.warnings = []

    async def verify_agent_stack(self) -> bool:
        """Verify agent stack configuration and connectivity"""
        logger.info("Verifying agent stack...")
        
        try:
            # Load configuration
            with open('../aetheroos_sovereign_agent_stack_v1.0.yaml') as f:
                config = yaml.safe_load(f)
            
            # Verify each agent
            async with aiohttp.ClientSession() as session:
                for agent in config['agents']:
                    agent_id = agent['agent_id']
                    port = self._get_agent_port(agent_id)
                    
                    # Check agent health
                    try:
                        async with session.get(f'http://localhost:{port}/health') as response:
                            if response.status != 200:
                                self.errors.append(f"Agent {agent_id} health check failed")
                            else:
                                data = await response.json()
                                if data['status'] != 'healthy':
                                    self.warnings.append(f"Agent {agent_id} reports unhealthy status")
                    except Exception as e:
                        self.errors.append(f"Failed to connect to agent {agent_id}: {str(e)}")
            
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Failed to verify agent stack: {str(e)}")
            return False

    async def verify_monitoring(self) -> bool:
        """Verify monitoring stack configuration and metrics collection"""
        logger.info("Verifying monitoring stack...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check Prometheus
                async with session.get('http://localhost:9090/-/ready') as response:
                    if response.status != 200:
                        self.errors.append("Prometheus is not ready")
                
                # Check Grafana
                async with session.get('http://localhost:3000/api/health') as response:
                    if response.status != 200:
                        self.errors.append("Grafana is not ready")
                
                # Check AlertManager
                async with session.get('http://localhost:9093/-/ready') as response:
                    if response.status != 200:
                        self.errors.append("AlertManager is not ready")
                
                # Verify metrics collection
                async with session.get('http://localhost:9090/api/v1/targets') as response:
                    if response.status == 200:
                        data = await response.json()
                        active_targets = data['data']['activeTargets']
                        for target in active_targets:
                            if target['health'] != 'up':
                                self.warnings.append(f"Target {target['labels']['job']} is down")
                    else:
                        self.errors.append("Failed to check Prometheus targets")
            
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Failed to verify monitoring: {str(e)}")
            return False

    async def verify_memory_system(self) -> bool:
        """Verify Aethero_Mem system configuration and accessibility"""
        logger.info("Verifying memory system...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check API accessibility
                async with session.get('http://localhost:9091/health') as response:
                    if response.status != 200:
                        self.errors.append("Aethero_Mem API is not accessible")
                
                # Verify schema registration
                async with session.get('http://localhost:9091/api/v1/schemas') as response:
                    if response.status == 200:
                        schemas = await response.json()
                        required_schemas = ['agent_state', 'decision_record', 'reflection_result']
                        for schema in required_schemas:
                            if schema not in schemas:
                                self.errors.append(f"Required schema {schema} is not registered")
                    else:
                        self.errors.append("Failed to verify schema registration")
            
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Failed to verify memory system: {str(e)}")
            return False

    async def verify_reflection_system(self) -> bool:
        """Verify reflection system and DeepEval integration"""
        logger.info("Verifying reflection system...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check reflection agent
                async with session.get('http://localhost:8005/health') as response:
                    if response.status != 200:
                        self.errors.append("Reflection agent is not accessible")
                
                # Check DeepEval
                async with session.get('http://localhost:9092/health') as response:
                    if response.status != 200:
                        self.errors.append("DeepEval service is not accessible")
                
                # Verify integration
                test_data = {
                    "agent_id": "test_agent",
                    "output": {"test": "data"},
                    "context": {"test": "context"}
                }
                async with session.post('http://localhost:8005/api/v1/validate', 
                                      json=test_data) as response:
                    if response.status != 200:
                        self.errors.append("Reflection validation endpoint failed")
            
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Failed to verify reflection system: {str(e)}")
            return False

    def _get_agent_port(self, agent_id: str) -> int:
        """Get agent port based on agent ID"""
        port_map = {
            'planner_agent_001': 8000,
            'scout_agent_001': 8001,
            'analyst_agent_001': 8002,
            'generator_agent_001': 8003,
            'synthesis_agent_001': 8004,
            'reflection_agent_001': 8005
        }
        return port_map.get(agent_id, 8000)

    def print_report(self):
        """Print verification report"""
        print("\n=== Deployment Verification Report ===\n")
        
        if not self.errors and not self.warnings:
            print("✅ All systems verified successfully!")
            return
        
        if self.errors:
            print("❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

async def main():
    verifier = DeploymentVerifier()
    
    # Run all verifications
    results = await asyncio.gather(
        verifier.verify_agent_stack(),
        verifier.verify_monitoring(),
        verifier.verify_memory_system(),
        verifier.verify_reflection_system()
    )
    
    # Print report
    verifier.print_report()
    
    # Exit with appropriate status
    if not all(results):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
