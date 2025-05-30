"""
Integration Tests for ReflectionAgent and DeepEval
"""
import pytest
import asyncio
from typing import Dict, Any
from pathlib import Path
import yaml

from ..reflection.reflection_agent import ReflectionAgent, ValidationStatus, ReflectionMetrics
from unittest.mock import Mock, AsyncMock

# Load configurations
@pytest.fixture
def agent_config():
    config_path = Path("../aetheroos_sovereign_agent_stack_v1.0.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)

@pytest.fixture
def deep_eval_config():
    config_path = Path("../reflection/deep_eval_config.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)

@pytest.fixture
async def reflection_agent(agent_config):
    agent = ReflectionAgent(agent_config)
    await agent.setup()
    return agent

# Mock DeepEval responses
@pytest.fixture
def mock_deep_eval():
    return AsyncMock(
        evaluate=AsyncMock(
            return_value={
                "accuracy": 0.85,
                "consistency": 0.90,
                "ethical_compliance": 0.95,
                "performance": 0.88
            }
        )
    )

# Test Cases
@pytest.mark.asyncio
async def test_reflection_agent_setup(reflection_agent):
    """Test ReflectionAgent initialization and setup"""
    assert reflection_agent.config is not None
    assert reflection_agent.aethero_mem is not None
    assert reflection_agent.deep_eval is not None

@pytest.mark.asyncio
async def test_validate_output(reflection_agent, mock_deep_eval):
    """Test output validation with DeepEval"""
    reflection_agent.deep_eval = mock_deep_eval
    
    test_output = {
        "result": "test_result",
        "confidence": 0.9
    }
    
    test_context = {
        "task_type": "analysis",
        "priority": "high"
    }
    
    result = await reflection_agent.validate_output(
        agent_id="test_agent",
        output=test_output,
        context=test_context
    )
    
    assert isinstance(result.metrics, ReflectionMetrics)
    assert result.status in ValidationStatus
    assert len(result.findings) > 0
    assert len(result.suggestions) > 0

@pytest.mark.asyncio
async def test_reflection_on_pipeline(reflection_agent):
    """Test pipeline reflection process"""
    result = await reflection_agent.reflect_on_pipeline(
        pipeline_execution_id="test_pipeline_001"
    )
    
    assert "reflection_id" in result
    assert "performance_analysis" in result
    assert "recommendations" in result

@pytest.mark.asyncio
async def test_deep_eval_integration(reflection_agent, deep_eval_config):
    """Test DeepEval integration with custom criteria"""
    test_output = {
        "generated_code": "def test_function(): pass",
        "documentation": "Test function documentation"
    }
    
    # Test with actual DeepEval criteria from config
    criteria = deep_eval_config["evaluation_criteria"]
    result = await reflection_agent.validate_output(
        agent_id="generator_agent_001",
        output=test_output,
        context={"criteria": criteria}
    )
    
    assert result.metrics.accuracy >= criteria["accuracy"]["thresholds"]["low"]
    assert result.metrics.consistency >= criteria["consistency"]["thresholds"]["low"]
    assert result.metrics.ethical_compliance >= criteria["ethical_compliance"]["thresholds"]["low"]

@pytest.mark.asyncio
async def test_aethero_mem_logging(reflection_agent):
    """Test logging reflection results to Aethero_Mem"""
    metrics = ReflectionMetrics(
        accuracy=0.85,
        consistency=0.90,
        ethical_compliance=0.95,
        performance_score=0.88
    )
    
    findings = ["Finding 1", "Finding 2"]
    suggestions = ["Suggestion 1", "Suggestion 2"]
    
    # Test logging
    await reflection_agent._log_reflection(
        agent_id="test_agent",
        metrics=metrics,
        findings=findings,
        suggestions=suggestions
    )
    
    # Verify logged data
    logged_data = await reflection_agent.aethero_mem.get_latest_reflection(
        agent_id="test_agent"
    )
    
    assert logged_data is not None
    assert logged_data["metrics"]["accuracy"] == metrics.accuracy
    assert logged_data["findings"] == findings
    assert logged_data["suggestions"] == suggestions

@pytest.mark.asyncio
async def test_error_handling(reflection_agent):
    """Test error handling in reflection process"""
    # Test with invalid output
    with pytest.raises(ValueError):
        await reflection_agent.validate_output(
            agent_id="test_agent",
            output=None,
            context={}
        )
    
    # Test with invalid pipeline ID
    with pytest.raises(ValueError):
        await reflection_agent.reflect_on_pipeline(
            pipeline_execution_id=""
        )

# Performance Tests
@pytest.mark.asyncio
async def test_reflection_performance(reflection_agent):
    """Test reflection process performance"""
    import time
    
    start_time = time.time()
    
    # Perform multiple validations
    tasks = []
    for i in range(10):
        tasks.append(
            reflection_agent.validate_output(
                agent_id=f"test_agent_{i}",
                output={"result": f"test_{i}"},
                context={"iteration": i}
            )
        )
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Assert performance requirements
    assert duration < 5.0  # Should complete within 5 seconds
    assert all(isinstance(r, ValidationResult) for r in results)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
