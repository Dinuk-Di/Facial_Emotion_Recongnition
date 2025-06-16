from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    emotions: List[str]
    average_emotion: Optional[str]
    detected_task: Optional[str]
    recommendation: Optional[str]
    executed: bool