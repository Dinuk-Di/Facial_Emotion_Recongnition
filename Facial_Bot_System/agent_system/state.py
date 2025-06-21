from typing import List, Optional, Dict
from pydantic import BaseModel

class AgentState(BaseModel):
    emotions: List[str]
    average_emotion: Optional[str]
    detected_task: Optional[str]
    recommendation: Optional[str]
    recommendation_options: Optional[List[Dict[str, str]]]
    executed: Optional[bool]
