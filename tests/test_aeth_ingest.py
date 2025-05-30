"""
Tests for the AetheroOS Memory Ingestion Agent
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
from src.aeth_ingest import (
    parse_input,
    generate_tags,
    render_report,
    save_report,
    IngestionError,
    REPORTS_DIR
)

@pytest.fixture
def test_content():
    return "Test memory content for analysis"

@pytest.fixture
def test_metadata():
    return {
        "ref_code": "TEST-2024-001",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "author": "Test Author",
        "tags": ["test", "memory"],
        "source": "test_source",
        "inferred_tags": {
            "intent_vector": "analysis",
            "mental_state": "focused",
            "emotion_tone": "neutral"
        }
    }

@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test content from file")
    yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_template():
    content = """
    Test Template
    Content: {{ content }}
    Ref: {{ ref_code }}
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
    yield f.name
    os.unlink(f.name)

class TestParseInput:
    def test_text_input(self, test_content):
        """Test parsing direct text input"""
        result = parse_input(input_text=test_content)
        assert result == test_content

    def test_file_input(self, temp_file):
        """Test parsing file input"""
        result = parse_input(input_path=temp_file)
        assert result == "Test content from file"

    def test_json_input(self):
        """Test parsing JSON input"""
        test_json = {"key": "value"}
        result = parse_input(input_json=test_json)
        assert json.loads(result) == test_json

    def test_no_input(self):
        """Test handling of missing input"""
        with pytest.raises(IngestionError):
            parse_input()

    def test_empty_input(self):
        """Test handling of empty input"""
        with pytest.raises(IngestionError):
            parse_input(input_text="")

    def test_invalid_file(self):
        """Test handling of nonexistent file"""
        with pytest.raises(IngestionError):
            parse_input(input_path="nonexistent.txt")

class TestGenerateTags:
    def test_neutral_content(self):
        """Test tag generation for neutral content"""
        tags = generate_tags("Simple test content")
        assert tags["intent_vector"] == "analysis"
        assert tags["mental_state"] == "focused"
        assert tags["emotion_tone"] == "neutral"

    def test_analytical_content(self):
        """Test tag generation for analytical content"""
        tags = generate_tags("Let's analyze and examine this issue")
        assert tags["intent_vector"] == "analysis"

    def test_error_content(self):
        """Test tag generation for error content"""
        tags = generate_tags("Error occurred in the system")
        assert tags["mental_state"] == "alert"
        assert tags["emotion_tone"] == "concerned"

    def test_success_content(self):
        """Test tag generation for success content"""
        tags = generate_tags("Task completed successfully")
        assert tags["mental_state"] == "satisfied"
        assert tags["emotion_tone"] == "positive"

class TestRenderReport:
    def test_default_template(self, test_content, test_metadata):
        """Test rendering with default template"""
        result = render_report(test_content, test_metadata)
        assert test_content in result
        assert test_metadata["ref_code"] in result

    def test_custom_template(self, test_content, test_metadata, temp_template):
        """Test rendering with custom template"""
        result = render_report(test_content, test_metadata, temp_template)
        assert test_content in result
        assert test_metadata["ref_code"] in result

    def test_invalid_template_path(self, test_content, test_metadata):
        """Test handling of invalid template path"""
        with pytest.raises(IngestionError):
            render_report(test_content, test_metadata, "nonexistent.txt")

    def test_invalid_metadata(self, test_content):
        """Test handling of invalid metadata"""
        with pytest.raises(IngestionError):
            render_report(test_content, {})

class TestSaveReport:
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = REPORTS_DIR
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup test files"""
        for file in self.test_dir.glob("TEST-*"):
            file.unlink()

    def test_save_markdown(self, test_content, test_metadata):
        """Test saving markdown report"""
        result = save_report(test_content, test_metadata)
        assert Path(result["markdown"]).exists()
        assert Path(result["json"]).exists()
        
        # Verify markdown content
        with open(result["markdown"], 'r') as f:
            content = f.read()
            assert test_content in content

        # Verify JSON content
        with open(result["json"], 'r') as f:
            metadata = json.load(f)
            assert metadata["ref_code"] == test_metadata["ref_code"]

    def test_save_with_pdf(self, test_content, test_metadata):
        """Test PDF generation if pdfkit is available"""
        try:
            import pdfkit
            result = save_report(test_content, test_metadata, as_pdf=True)
            if result["pdf"]:  # PDF generation succeeded
                assert Path(result["pdf"]).exists()
                assert Path(result["pdf"]).stat().st_size > 0
        except ImportError:
            pytest.skip("pdfkit not installed")

    def test_invalid_save(self, test_content, test_metadata):
        """Test handling of save errors"""
        # Make reports directory read-only
        os.chmod(self.test_dir, 0o444)
        try:
            with pytest.raises(IngestionError):
                save_report(test_content, test_metadata)
        finally:
            # Restore permissions
            os.chmod(self.test_dir, 0o755)

def test_integration(test_content, test_metadata, temp_template):
    """Test full integration of parse, render, and save"""
    # Parse input
    content = parse_input(input_text=test_content)
    assert content == test_content

    # Generate tags
    tags = generate_tags(content)
    test_metadata["inferred_tags"] = tags

    # Render report
    report = render_report(content, test_metadata, temp_template)
    assert content in report
    assert test_metadata["ref_code"] in report

    # Save report
    result = save_report(report, test_metadata)
    assert all(Path(p).exists() for p in [result["markdown"], result["json"]])

    # Cleanup
    for file in [result["markdown"], result["json"]]:
        Path(file).unlink()
