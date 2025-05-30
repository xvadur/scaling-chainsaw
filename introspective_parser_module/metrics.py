# metrics.py
# This module provides basic metrics and utilities for the introspective parser.

def calculate_success_rate(validated_blocks: int, total_blocks: int) -> float:
    """Calculate the success rate of parsing."""
    if total_blocks == 0:
        return 0.0
    return validated_blocks / total_blocks

def analyze_cognitive_load(tags: list) -> dict:
    """Analyze cognitive load from a list of ASL tags."""
    loads = [tag.get("cognitive_load", 0) for tag in tags]
    return {
        "average_load": sum(loads) / len(loads) if loads else 0,
        "max_load": max(loads, default=0),
        "min_load": min(loads, default=0),
    }

def generate_introspection_report(tags: list) -> dict:
    """Generate a report based on introspective tags."""
    return {
        "certainty_levels": [tag.get("certainty_level", 0.0) for tag in tags],
        "memory_links": [tag.get("aeth_mem_link", "") for tag in tags],
    }
