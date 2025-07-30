# agent_worker.py
from PySide6.QtCore import QObject, Signal
from graph import process_agent_system  # where your LangGraph code is
import time

class AgentWorker(QObject):
    # Signals to emit agent results
    workflowFinished = Signal(object)  # emit full AgentState or final result
    logMessage = Signal(str)

    def run(self, emotions):
        self.logMessage.emit("Running agent system...")
        try:
            final_state = process_agent_system(emotions)
            self.workflowFinished.emit(final_state)
        except Exception as e:
            self.logMessage.emit(f"Agent system error: {e}")
