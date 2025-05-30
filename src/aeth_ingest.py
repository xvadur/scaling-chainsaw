"""
AetheroOS Memory Ingestion Agent
===============================

This module handles the ingestion of memories into the AetheroOS system, generating
ritualized ministerial reports with metadata, tags, and optional PDF output.

Features:
- Multiple input formats (text, file, JSON)
- Automated tag generation
- Templated report generation
- Multiple output formats (MD, JSON, PDF)
- Blackbox validation integration

Usage:
    python aeth_ingest.py --text "Memory content"
    python aeth_ingest.py --file input.txt
    python aeth_ingest.py --json '{"content": "Memory"}'
"""

import os
import uuid
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from jinja2 import Template, TemplateError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aeth_ingest")

# Constants
REPORTS_DIR = Path("./aeth_mem_reports/")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Default Jinja2 template for ministerial reports
DEFAULT_TEMPLATE = """
### AETHEROOS MINISTERIAL REPORT
**Office of Memory Ingestion**  
**Ref. Code**: {{ ref_code }}  

---

**Date**: {{ date }}  
**Author**: {{ author }}  
**Tags**: {{ tags }}  
**Source**: {{ source }}  

---

#### **🪶 CONTENT**  
{{ content }}

---

#### **🪶 INFERRED TAGS**  
- Intent Vector: {{ inferred_tags.intent_vector }}  
- Mental State: {{ inferred_tags.mental_state }}  
- Emotion Tone: {{ inferred_tags.emotion_tone }}  

---

**Ministerial Seal**: [ ⚜️ ]  
"""

class IngestionError(Exception):
    """Base exception for ingestion-related errors."""
    pass

def parse_input(
    input_path: Optional[str] = None,
    input_json: Optional[Dict] = None,
    input_text: Optional[str] = None
) -> str:
    """
    Parse input from file, JSON payload, or direct text.

    Args:
        input_path: Path to input file (.txt, .md, .json)
        input_json: JSON payload as dictionary
        input_text: Direct text input

    Returns:
        str: Parsed content

    Raises:
        IngestionError: If no valid input is provided or input cannot be parsed
    """
    try:
        if input_path:
            logger.info(f"Reading input from file: {input_path}")
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif input_json:
            logger.info("Parsing JSON input")
            content = json.dumps(input_json, indent=4)
        elif input_text:
            logger.info("Using direct text input")
            content = input_text
        else:
            raise IngestionError("No valid input provided")
        
        if not content.strip():
            raise IngestionError("Input content is empty")
            
        return content
    except (IOError, json.JSONDecodeError) as e:
        raise IngestionError(f"Failed to parse input: {str(e)}")

def generate_tags(content: str) -> Dict[str, str]:
    """
    Generate ASL tags based on content analysis.

    Args:
        content: Text content to analyze

    Returns:
        dict: Generated tags including intent_vector, mental_state, and emotion_tone
    """
    logger.debug("Generating tags for content")
    
    # Initialize with neutral defaults
    tags = {
        "intent_vector": "analysis",
        "mental_state": "focused",
        "emotion_tone": "neutral"
    }

    # Basic content analysis
    content_lower = content.lower()
    
    # Intent vector detection
    if any(word in content_lower for word in ["analyze", "examine", "study"]):
        tags["intent_vector"] = "analysis"
    elif any(word in content_lower for word in ["create", "generate", "build"]):
        tags["intent_vector"] = "creation"
    elif any(word in content_lower for word in ["fix", "repair", "solve"]):
        tags["intent_vector"] = "resolution"

    # Mental state detection
    if any(word in content_lower for word in ["error", "warning", "issue"]):
        tags["mental_state"] = "alert"
    elif any(word in content_lower for word in ["success", "complete", "done"]):
        tags["mental_state"] = "satisfied"

    # Emotion tone detection
    if any(word in content_lower for word in ["error", "fail", "issue"]):
        tags["emotion_tone"] = "concerned"
    elif any(word in content_lower for word in ["success", "excellent", "perfect"]):
        tags["emotion_tone"] = "positive"

    logger.debug(f"Generated tags: {tags}")
    return tags

def render_report(
    content: str,
    metadata: Dict[str, Any],
    template_path: Optional[str] = None
) -> str:
    """
    Render content and metadata into a ritualized report using Jinja2 templates.

    Args:
        content: Report content
        metadata: Report metadata including ref_code, date, author, etc.
        template_path: Optional path to custom template file

    Returns:
        str: Rendered report content

    Raises:
        IngestionError: If template rendering fails or metadata is invalid
    """
    # Validate required metadata fields
    required_fields = ["ref_code", "date", "author", "tags", "source", "inferred_tags"]
    missing_fields = [field for field in required_fields if field not in metadata]
    if missing_fields:
        raise IngestionError(f"Missing required metadata fields: {', '.join(missing_fields)}")

    try:
        if template_path:
            logger.info(f"Using custom template: {template_path}")
            with open(template_path, 'r', encoding='utf-8') as f:
                template = Template(f.read())
        else:
            logger.info("Using default template")
            template = Template(DEFAULT_TEMPLATE)

        # Convert tags to string if present, otherwise use empty string
        tags_str = ", ".join(metadata.get("tags", []))

        rendered = template.render(
            content=content,
            ref_code=metadata["ref_code"],
            date=metadata["date"],
            author=metadata["author"],
            tags=tags_str,
            source=metadata["source"],
            inferred_tags=metadata["inferred_tags"]
        )
        
        if not rendered.strip():
            raise IngestionError("Template rendered empty content")
            
        return rendered
    except (IOError, TemplateError) as e:
        raise IngestionError(f"Failed to render report: {str(e)}")

def save_report(
    content: str,
    metadata: Dict[str, Any],
    as_pdf: bool = False
) -> Dict[str, Optional[str]]:
    """
    Save the report in multiple formats (MD, JSON, optionally PDF).

    Args:
        content: Report content
        metadata: Report metadata
        as_pdf: Whether to generate PDF output

    Returns:
        dict: Paths to saved files

    Raises:
        IngestionError: If saving fails
    """
    try:
        ref_code = metadata["ref_code"]
        file_base = REPORTS_DIR / ref_code
        saved_files = {"markdown": None, "json": None, "pdf": None}

        # Save Markdown
        md_path = f"{file_base}.md"
        logger.info(f"Saving markdown to: {md_path}")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)
        saved_files["markdown"] = str(md_path)

        # Save JSON metadata
        json_path = f"{file_base}.json"
        logger.info(f"Saving metadata to: {json_path}")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        saved_files["json"] = str(json_path)

        # Save PDF if requested
        if as_pdf:
            try:
                import pdfkit
                pdf_path = f"{file_base}.pdf"
                logger.info(f"Generating PDF: {pdf_path}")
                pdfkit.from_string(content, pdf_path)
                saved_files["pdf"] = str(pdf_path)
            except ImportError:
                logger.warning("pdfkit not installed - skipping PDF generation")
            except Exception as e:
                logger.error(f"PDF generation failed: {str(e)}")

        return saved_files
    except Exception as e:
        raise IngestionError(f"Failed to save report: {str(e)}")

def trigger_blackbox(report_path: str) -> None:
    """
    Trigger Blackbox validation subprocess.

    Args:
        report_path: Path to the report file to validate
    """
    logger.info(f"Triggering Blackbox validation for: {report_path}")
    # TODO: Implement actual Blackbox integration
    # Example: subprocess.run(["blackbox", "--analyze", report_path])

def main() -> None:
    """Main entry point for the AetheroOS Memory Ingestion Agent."""
    parser = argparse.ArgumentParser(
        description="AetheroOS Memory Ingestion Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--text", type=str, help="Input text to ingest")
    parser.add_argument("--file", type=str, help="Input file path (.txt, .md, .json)")
    parser.add_argument("--json", type=json.loads, help="Input JSON payload")
    parser.add_argument("--ref_code", type=str, help="Custom reference code")
    parser.add_argument("--author", type=str, default="AetheroGPT",
                       help="Author of the report")
    parser.add_argument("--tags", type=str, nargs="*", default=[],
                       help="Custom tags for the report")
    parser.add_argument("--source", type=str, default="unknown",
                       help="Source of the content")
    parser.add_argument("--template", type=str,
                       help="Custom Jinja2 template path")
    parser.add_argument("--validate", action="store_true",
                       help="Trigger Blackbox validation")
    parser.add_argument("--pdf", action="store_true",
                       help="Generate PDF output")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")

    args = parser.parse_args()

    # Configure debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # Parse input
        content = parse_input(
            input_path=args.file,
            input_json=args.json,
            input_text=args.text
        )

        # Generate metadata
        ref_code = args.ref_code or f"AETH-MEM-{datetime.now().strftime('%Y')}-{str(uuid.uuid4().int)[:4]}"
        metadata = {
            "ref_code": ref_code,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "author": args.author,
            "tags": args.tags,
            "source": args.source,
            "inferred_tags": generate_tags(content)
        }

        # Render report
        rendered_content = render_report(
            content,
            metadata,
            template_path=args.template
        )

        # Save report
        saved_files = save_report(rendered_content, metadata, as_pdf=args.pdf)
        logger.info(f"Report saved: {saved_files}")

        # Trigger Blackbox if validation is requested
        if args.validate:
            trigger_blackbox(saved_files["markdown"])

    except IngestionError as e:
        logger.error(f"Ingestion failed: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
