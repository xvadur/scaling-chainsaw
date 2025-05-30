from pydantic import BaseModel

class ASLTagModel(BaseModel):
    statement: str
    mental_state: str
    emotion_tone: str
    cognitive_load: int
    temporal_context: str
    certainty_level: float
    aeth_mem_link: str
    law: str
    enhancement_suggestion: str = None
    diplomatic_enhancement: str = None
