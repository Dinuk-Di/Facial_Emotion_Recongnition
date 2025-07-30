from PySide6.QtCore import QObject, Signal

class AgentSignalEmitter(QObject):
    stepCompleted = Signal(object)  # emits current AgentState

    def emit_update(self, state):
        self.stepCompleted.emit(state)
