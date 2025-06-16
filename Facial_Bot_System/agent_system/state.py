from typing import List, Optional
from pydantic import BaseModel

class AgentState(BaseModel):
    emotions: List[str]
    average_emotion: Optional[str]
    detected_task: Optional[str]
    recommendation: Optional[str]
    executed: Optional[bool]
