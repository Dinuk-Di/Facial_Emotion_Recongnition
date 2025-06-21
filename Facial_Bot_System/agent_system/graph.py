from langgraph.graph import StateGraph, END
from .state import AgentState
from .agents import (
    average_emotion_agent,
    task_detection_agent,
    recommendation_agent,
    task_execution_agent
)

def create_workflow():
    workflow = StateGraph(AgentState)
    workflow.add_node("calculate_emotion", average_emotion_agent)
    workflow.add_node("detect_task", task_detection_agent)
    workflow.add_node("generate_recommendation", recommendation_agent)
    workflow.add_node("execute_action", task_execution_agent)
    workflow.set_entry_point("calculate_emotion")
    workflow.add_edge("calculate_emotion", "detect_task")
    workflow.add_edge("detect_task", "generate_recommendation")
    # workflow.add_edge("calculate_emotion", "generate_recommendation")
    workflow.add_edge("generate_recommendation", "execute_action")
    workflow.add_edge("execute_action", END)
    return workflow.compile()

agent_workflow = create_workflow()

def process_agent_system(emotions):
    from .state import AgentState
    initial_state = AgentState(
        emotions=emotions,
        average_emotion=None,
        detected_task=None,
        recommendation=None,
        recommendation_options=[],
        executed=False
    )
    return agent_workflow.invoke(initial_state)
