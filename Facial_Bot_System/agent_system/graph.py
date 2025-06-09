from langgraph.graph import END, StateGraph
from .state import AgentState
from .agents import (
    average_emotion_agent,
    task_detection_agent,
    recommendation_agent,
    task_execution_agent
)

def create_workflow():
    workflow = StateGraph(AgentState)
    
    # Add nodes with unique names
    workflow.add_node("calculate_emotion", average_emotion_agent)
    workflow.add_node("detect_task", task_detection_agent)
    workflow.add_node("generate_recommendation", recommendation_agent)
    workflow.add_node("execute_action", task_execution_agent)
    
    # Define edges
    workflow.set_entry_point("calculate_emotion")
    workflow.add_edge("calculate_emotion", "detect_task")
    workflow.add_edge("detect_task", "generate_recommendation")
    workflow.add_edge("generate_recommendation", "execute_action")
    workflow.add_edge("execute_action", END)
    
    return workflow.compile()

# Create compiled workflow
agent_workflow = create_workflow()

def process_agent_system(emotions: list):
    """Run full agent workflow"""
    initial_state = AgentState(
        emotions=emotions,
        average_emotion=None,
        detected_task=None,
        recommendation=None,
        executed=False
    )
    agent_workflow.invoke(initial_state)