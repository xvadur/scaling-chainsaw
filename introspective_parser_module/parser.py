from tabulate import tabulate
from typing import Dict, Any, List, Tuple
import re
from pydantic import BaseModel, ValidationError
import logging
import os
import json
from datetime import datetime

# Configure logging for diagnostic purposes
logging.basicConfig(
    filename="diagnostic.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define Pydantic model for ASL tags
class ASLTagModel(BaseModel):
    statement: str
    mental_state: str
    emotion_tone: str
