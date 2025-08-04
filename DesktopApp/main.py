from tkinter import Tk
from customtkinter import CTk
from ui.login import LoginWindow
from ui.notification import send_notification
from core.agent_system import run_agent_system, AgentState
from core.recommender_tools import open_recommendation
from old_utils.runner_interface import launch_window
import time

if __name__ == "__main__":
    root = CTk()
    app = LoginWindow(root)
    root.mainloop()

def task_execution_agent(state: AgentState):
    recommended_output = state.recommendation
    recommended_options = state.recommendation_options
    
    if "No action needed" not in recommended_output:
        status = send_notification(recommended_output)
        if status:
            #selected_option = selection_window(recommended_options)

            window, app = launch_window(recommended_options)
            app.exec()
            selected_option = window.selectedChoice
            window.close()
            app.quit()

            print("selected option: ", selected_option)
            if selected_option:
                start_time = time.time()
                open_recommendation(selected_option) # Execute the task based on the option
                print("Task is executed")
                return {
                    "executed": True,
                    "action_time_start": start_time
                }