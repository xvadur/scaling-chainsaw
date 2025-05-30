from typing import Dict, List, Optional, Union
import re
import json
from datetime import datetime, UTC

class ASLTag:
    """
    Represents a single ASL (Aethero Syntax Language) tag
    """
    def __init__(
        self,
        tag_name: str,
        value: Union[str, int, float, bool, dict],
        position: Optional[Dict[str, int]] = None
    ):
        self.tag_name = tag_name
        self.value = value
        self.position = position or {}
        self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> Dict:
        """Convert tag to dictionary representation"""
        return {
            "tag_name": self.tag_name,
            "value": self.value,
            "position": self.position,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ASLTag':
        """Create tag from dictionary"""
        return cls(
            tag_name=data["tag_name"],
            value=data["value"],
            position=data.get("position", {})
        )

class ASLParser:
    """Parser for ASL (Aethero Syntax Language) tags"""
    
    def __init__(self):
        self.tags: List[ASLTag] = []
        self._tag_pattern = re.compile(r'{([^}]+)}')
    
    def parse(self, content: str) -> List[Dict]:
        """
        Parse ASL tags from content
        
        Args:
            content: String containing ASL tags
            
        Returns:
            List of parsed tags as dictionaries
        """
        self.tags = []
        matches = self._tag_pattern.finditer(content)
        
        for match in matches:
            try:
                tag_content = match.group(1).strip()
                # Split the tag content into key-value pairs
                pairs = [pair.strip() for pair in tag_content.split(',')]
                tag_dict = {}
                
                for pair in pairs:
                    if ':' in pair:
                        key, value = [p.strip() for p in pair.split(':', 1)]
                        # Handle different value types
                        try:
                            # Try to convert to number if possible
                            if value.replace('.', '').isdigit():
                                value = float(value) if '.' in value else int(value)
                            elif value.lower() == 'true':
                                value = True
                            elif value.lower() == 'false':
                                value = False
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]  # Remove quotes
                            elif value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]  # Remove quotes
                        except ValueError:
                            # Keep as string if conversion fails
                            if value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            elif value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                        
                        tag_dict[key] = value
                
                # Extract position information
                position = {
                    "start": match.start(),
                    "end": match.end(),
                    "line": content[:match.start()].count('\n') + 1
                }
                
                # Create and store tag for each key-value pair
                for tag_name, value in tag_dict.items():
                    tag = ASLTag(
                        tag_name=tag_name,
                        value=value,
                        position=position
                    )
                    self.tags.append(tag)
                    
            except Exception as e:
                print(f"Warning: Invalid tag format at position {match.start()}: {str(e)}")
                continue
                
        return [tag.to_dict() for tag in self.tags]
    
    def validate_tag_structure(self, tag: Dict) -> bool:
        """
        Validate ASL tag structure
        
        Args:
            tag: Dictionary containing tag data
            
        Returns:
            bool: True if tag is valid, False otherwise
        """
        required_fields = ["tag_name", "value", "position"]
        if not all(field in tag for field in required_fields):
            return False
            
        # Validate position structure
        position = tag.get("position", {})
        required_position_fields = ["start", "end", "line"]
        if not all(field in position for field in required_position_fields):
            return False
            
        return True
    
    def extract_tags_by_name(self, tag_name: str) -> List[Dict]:
        """
        Extract all tags with a specific name
        
        Args:
            tag_name: Name of tags to extract
            
        Returns:
            List of matching tags
        """
        return [tag.to_dict() for tag in self.tags if tag.tag_name == tag_name]
    
    def extract_tags_by_value_type(self, value_type: type) -> List[Dict]:
        """
        Extract all tags with values of a specific type
        
        Args:
            value_type: Type of values to extract
            
        Returns:
            List of matching tags
        """
        return [tag.to_dict() for tag in self.tags if isinstance(tag.value, value_type)]
    
    def get_tags_in_range(self, start: int, end: int) -> List[Dict]:
        """
        Get all tags within a position range
        
        Args:
            start: Start position
            end: End position
            
        Returns:
            List of tags within range
        """
        return [
            tag.to_dict() for tag in self.tags 
            if start <= tag.position.get("start", 0) <= end
        ]

def create_asl_tag(
    tag_name: str,
    value: Union[str, int, float, bool, dict],
    position: Optional[Dict[str, int]] = None
) -> Dict:
    """
    Create a new ASL tag
    
    Args:
        tag_name: Name of the tag
        value: Tag value
        position: Optional position information
        
    Returns:
        Dictionary containing tag data
    """
    tag = ASLTag(tag_name, value, position)
    return tag.to_dict()

# Example usage
if __name__ == "__main__":
    # Example content with ASL tags
    content = """
    This is a test content with {mental_state: 'focused', certainty_level: 0.85}
    and another tag {emotion_tone: 'neutral', context_id: 'conv_123'}
    """
    
    # Create parser and parse content
    parser = ASLParser()
    tags = parser.parse(content)
    
    # Print parsed tags
    for tag in tags:
        print(f"Found tag: {tag}")
