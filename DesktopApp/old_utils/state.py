class AppState:
    def __init__(self):
        self.executed = False
        self.recommendations = []
        self.selectedApp = ""

    def get_executed(self):
        executed = self.executed
        return executed

    def set_executed(self, execute):
        self.executed = execute