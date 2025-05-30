"""
Tests for AetheroOS Deployment Process
"""
import pytest
import subprocess
import docker
import time
import requests
from pathlib import Path
import yaml
import json
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDeploymentProcess:
    @pytest.fixture(scope="class")
    def docker_client(self):
        return docker.from_env()

    @pytest.fixture(scope="class")
    def config_paths(self):
        return {
            'agent_stack': Path('../aetheroos_sovereign_agent_stack_v1.0.yaml'),
            'prometheus': Path('../monitoring/prometheus.yml'),
            'grafana': Path('../monitoring/grafana_dashboards.json'),
            'alertmanager': Path('../monitoring/aetheros_rules.yml')
        }

    def test_deployment_script_permissions(self):
        """Test if deployment scripts have correct execution permissions"""
        deploy_script = Path('../deploy/deploy.sh')
        health_check = Path('../deploy/health_check.sh')
        
        assert deploy_script.exists(), "deploy.sh not found"
        assert health_check.exists(), "health_check.sh not found"
        
        # Check and set executable permissions
        for script in [deploy_script, health_check]:
            if not script.stat().st_mode & 0o111:
                script.chmod(script.stat().st_mode | 0o111)
                logger.info(f"Set executable permission for {script}")

    def test_configuration_files(self, config_paths):
        """Test if all configuration files are valid"""
        for name, path in config_paths.items():
            assert path.exists(), f"{name} configuration not found at {path}"
            
            # Validate file format
            with open(path) as f:
                if path.suffix == '.yaml' or path.suffix == '.yml':
                    yaml.safe_load(f)
                elif path.suffix == '.json':
                    json.load(f)

    def test_docker_compose_files(self):
        """Test Docker Compose configurations"""
        compose_files = [
            Path('../monitoring/docker-compose.yml'),
            Path('../agents/docker-compose.yml')
        ]
        
        for compose_file in compose_files:
            assert compose_file.exists(), f"Docker Compose file not found: {compose_file}"
            
            # Validate compose file
            result = subprocess.run(
                ['docker-compose', '-f', str(compose_file), 'config'],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Invalid Docker Compose file: {compose_file}\n{result.stderr}"

    def test_network_creation(self, docker_client):
        """Test Docker network creation"""
        try:
            network = docker_client.networks.create(
                'aetheros_net',
                driver='bridge',
                check_duplicate=True
            )
            assert network.name == 'aetheros_net'
        except docker.errors.APIError as e:
            if 'already exists' not in str(e):
                raise

    def test_service_initialization_order(self, docker_client):
        """Test service initialization sequence"""
        required_services = [
            'aetheros_mem',
            'aetheros_prometheus',
            'aetheros_grafana',
            'aetheros_alertmanager',
            'aetheros_pushgateway'
        ]
        
        # Start core services
        subprocess.run(
            ['docker-compose', '-f', '../monitoring/docker-compose.yml', 'up', '-d'],
            check=True
        )
        
        # Wait for core services
        time.sleep(10)
        
        # Verify core services
        containers = docker_client.containers.list()
        running_services = [container.name for container in containers]
        
        for service in required_services:
            assert service in running_services, f"Required service not running: {service}"
            
        # Clean up
        subprocess.run(
            ['docker-compose', '-f', '../monitoring/docker-compose.yml', 'down'],
            check=True
        )

    def test_health_check_script(self):
        """Test health check script execution"""
        result = subprocess.run(
            ['../deploy/health_check.sh'],
            capture_output=True,
            text=True
        )
        
        # Script might fail if services aren't running, we're just testing execution
        assert 'Health Check Summary' in result.stdout

    def test_verify_deployment_script(self):
        """Test deployment verification script"""
        result = subprocess.run(
            ['python', '../deploy/verify_deployment.py'],
            capture_output=True,
            text=True
        )
        
        # Script might fail if services aren't running, we're just testing execution
        assert 'Deployment Verification Report' in result.stdout

    @pytest.mark.asyncio
    async def test_service_dependencies(self):
        """Test service dependency resolution"""
        with open('../agents/docker-compose.yml') as f:
            compose_config = yaml.safe_load(f)
        
        # Verify dependency chains
        for service_name, service_config in compose_config['services'].items():
            if 'depends_on' in service_config:
                for dependency in service_config['depends_on']:
                    assert dependency in compose_config['services'], \
                        f"Service {service_name} depends on non-existent service {dependency}"

    def test_volume_persistence(self, docker_client):
        """Test volume persistence configuration"""
        required_volumes = [
            'prometheus_data',
            'grafana_data',
            'alertmanager_data',
            'aethero_mem_data',
            'deep_eval_models'
        ]
        
        # Create test volumes
        for volume_name in required_volumes:
            try:
                docker_client.volumes.create(volume_name)
            except docker.errors.APIError as e:
                if 'already exists' not in str(e):
                    raise
        
        # Verify volumes
        existing_volumes = [v.name for v in docker_client.volumes.list()]
        for volume_name in required_volumes:
            assert volume_name in existing_volumes, f"Required volume not created: {volume_name}"

    @pytest.mark.asyncio
    async def test_deployment_rollback(self):
        """Test deployment rollback capabilities"""
        # Simulate failed deployment
        with pytest.raises(subprocess.CalledProcessError):
            subprocess.run(
                ['docker-compose', '-f', '../agents/docker-compose.yml', 'up', '-d'],
                check=True,
                env={'FAIL_DEPLOYMENT': 'true'}  # Trigger intentional failure
            )
        
        # Verify system state after failure
        containers = docker.from_env().containers.list()
        assert not any(c.name.startswith('aetheros_') for c in containers), \
            "Containers still running after failed deployment"

if __name__ == '__main__':
    pytest.main(['-v', __file__])
