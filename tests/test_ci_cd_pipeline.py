"""
Tests for CI/CD Pipeline Configuration
"""
import pytest
import yaml
from pathlib import Path
import json
import re

def load_yaml(file_path):
    with open(file_path) as f:
        return yaml.safe_load(f)

def test_github_workflow_structure():
    """Test GitHub Actions workflow configuration"""
    workflow = load_yaml('../.github/workflows/aetheros_ci.yml')
    
    # Verify required jobs
    required_jobs = ['test', 'validate-schemas', 'build-docs', 'deploy', 'monitoring']
    assert all(job in workflow['jobs'] for job in required_jobs)
    
    # Verify job dependencies
    deploy_job = workflow['jobs']['deploy']
    assert 'needs' in deploy_job
    assert all(need in ['test', 'validate-schemas', 'build-docs'] 
              for need in deploy_job['needs'])
    
    # Verify conditional deployment
    assert 'if' in deploy_job
    assert 'github.ref == \'refs/heads/main\'' in deploy_job['if']

def test_release_artifact_structure():
    """Test release artifact packaging"""
    workflow = load_yaml('../.github/workflows/aetheros_ci.yml')
    deploy_job = workflow['jobs']['deploy']
    
    # Find package step
    package_step = next(step for step in deploy_job['steps'] 
                       if 'Package components' in step.get('name', ''))
    
    # Verify required components are included
    package_command = package_step['run']
    required_components = [
        'aetheroos_sovereign_agent_stack_v1.0.yaml',
        'reflection/',
        'visualization/',
        'memory/',
        'tests/'
    ]
    assert all(component in package_command for component in required_components)

def test_monitoring_setup():
    """Test monitoring job configuration"""
    workflow = load_yaml('../.github/workflows/aetheros_ci.yml')
    monitoring_job = workflow['jobs']['monitoring']
    
    # Verify monitoring steps
    step_names = [step.get('name', '') for step in monitoring_job['steps']]
    required_steps = ['Configure Prometheus', 'Configure Grafana', 'Setup Alerts']
    assert all(step in step_names for step in required_steps)
    
    # Verify job dependencies
    assert 'needs' in monitoring_job
    assert 'deploy' in monitoring_job['needs']

def test_test_job_coverage():
    """Test coverage of test job"""
    workflow = load_yaml('../.github/workflows/aetheros_ci.yml')
    test_job = workflow['jobs']['test']
    
    # Find test execution step
    test_step = next(step for step in test_job['steps'] 
                    if 'Run tests' in step.get('name', ''))
    
    # Verify all test files are included
    test_command = test_step['run']
    required_tests = [
        'test_reflection_integration.py',
        'test_langgraph_visualization.py',
        'test_aethero_mem_api.py'
    ]
    assert all(test in test_command for test in required_tests)

def test_schema_validation_job():
    """Test schema validation job configuration"""
    workflow = load_yaml('../.github/workflows/aetheros_ci.yml')
    validate_job = workflow['jobs']['validate-schemas']
    
    # Find validation step
    validate_step = next(step for step in validate_job['steps'] 
                        if 'Validate YAML schemas' in step.get('name', ''))
    
    # Verify all schemas are validated
    validation_script = validate_step['run']
    required_schemas = [
        'aetheroos_sovereign_agent_stack_v1.0.yaml',
        'deep_eval_config.yaml',
        'aethero_mem_schema.yaml'
    ]
    assert all(schema in validation_script for schema in required_schemas)

def test_documentation_build():
    """Test documentation build job"""
    workflow = load_yaml('../.github/workflows/aetheros_ci.yml')
    docs_job = workflow['jobs']['build-docs']
    
    # Verify mkdocs installation
    install_step = next(step for step in docs_job['steps'] 
                       if 'Install dependencies' in step.get('name', ''))
    assert 'mkdocs' in install_step['run']
    assert 'mkdocs-material' in install_step['run']
    
    # Verify build step
    build_step = next(step for step in docs_job['steps'] 
                     if 'Build documentation' in step.get('name', ''))
    assert 'mkdocs build' in build_step['run']

if __name__ == '__main__':
    pytest.main(['-v', __file__])
