from tools.recommender_tools import tools

# Create a mapping from tool name to tool function
tool_map = {tool.name: tool for tool in tools}

# def execute_action(tool_name: str) -> str:
#     """
#     Executes a registered tool by its name.
#     :param tool_name: The name of the tool (e.g., 'open_spotify')
#     :return: Output string from the tool or an error message.
#     """
#     tool_func = tool_map.get(tool_name)
#     if tool_func:
#         return tool_func.invoke("")
#     else:
#         return f"Tool '{tool_name}' not recognized. Please check the available tools."

#############################################################################


# def execute_action(tool_name: str, **kwargs) -> str:
#     """
#     Executes a registered tool by its name, passing all kwargs as parameters.
#     :param tool_name: The name of the tool (e.g., 'open_spotify', 'play_youtube_content')
#     :param kwargs: Any additional parameters the tool might need (e.g., query_or_url for YouTube)
#     :return: Output string from the tool or an error message.
#     """
#     tool_func = tool_map.get(tool_name)
#     if tool_func:
#         try:
#             # Pass all received kwargs to the tool function's invoke method
#             # LangChain's tool.invoke() expects a single argument if the tool was defined with one.
#             # If your tool has multiple arguments, you'd need a more complex mapping.
#             # For now, assuming tools either take no arguments or one specific named argument (like query_or_url).
#             if 'query_or_url' in kwargs and tool_name == 'play_youtube_content':
#                 return tool_func.invoke(kwargs['query_or_url'])
#             elif 'emotion' in kwargs and tool_name == 'write_journal_entry':
#                 return tool_func.invoke(kwargs['emotion'])
#             elif 'game_name' in kwargs and tool_name == 'open_game':
#                 return tool_func.invoke(kwargs['game_name'])
#             else:
#                 # For tools like open_spotify, open_social_media, open_solitaire that take a dummy or no meaningful arg
#                 return tool_func.invoke("") 
#         except Exception as e:
#             return f"Error executing tool '{tool_name}' with params {kwargs}: {e}"
#     else:
#         return f"Tool '{tool_name}' not recognized. Please check the available tools."


####################################################################################################


# # execution_agent.py
# # Make sure this path is correct relative to where execution_agent.py is run
# from tools.recommender_tools import tools

# # Create a mapping from tool name (string) to the actual tool function object
# tool_map = {tool.name: tool for tool in tools}

# def execute_action(tool_name: str, **kwargs) -> str:
#     """
#     Executes a registered tool by its name, passing all keyword arguments as parameters.
    
#     :param tool_name: The name of the tool (e.g., 'open_spotify', 'play_youtube_content')
#     :param kwargs: Any additional parameters the tool might need (e.g., query_or_url for YouTube, game_id for games)
#     :return: Output string from the tool's execution or an error message.
#     """
#     tool_func = tool_map.get(tool_name)
#     if tool_func:
#         try:
#             # LangChain's tool.invoke() method is designed to take the argument(s)
#             # as a single input. We need to pass the kwargs appropriately based
#             # on how the tool function itself is defined (e.g., if it expects 'dummy', 'query_or_url', etc.)

#             # This is a more robust way to pass params to LangChain tools.
#             # If a tool takes multiple arguments, you might need to structure kwargs
#             # to match, or have the tool function unpack them.
#             # For simplicity, if the tool takes a single string arg, we pass the first value in kwargs.
#             if kwargs:
#                 # Assuming the tool expects a single argument if kwargs are provided
#                 # and that argument is the first value in kwargs.
#                 # This might need refinement if your tools have multiple distinct named parameters.
#                 return tool_func.invoke(next(iter(kwargs.values())))
#             else:
#                 # For tools that take no specific arguments (or a dummy one)
#                 return tool_func.invoke("")
#         except Exception as e:
#             # Catching specific exceptions if a tool fails (e.g., FileNotFoundError)
#             print(f"Error during execution of tool '{tool_name}' with parameters {kwargs}: {e}")
#             return f"Execution of '{tool_name}' failed: {e}"
#     else:
#         return f"Error: Tool '{tool_name}' not recognized. Please check the available tools in recommender_tools.py."

#####################################################################################################################


# # execution_agent.py
# import sys
# import os

# # Adjust sys.path if necessary to find tools
# # Assuming emotion_agent.py is in the same directory as 'tools' folder.
# # If your main.py sets a project root, this import might be cleaner.
# from tools.recommender_tools import tools

# # Create a mapping from tool name (string) to the actual tool function object
# tool_map = {tool.name: tool for tool in tools}

# def execute_action(tool_name: str, tool_params: dict = None) -> str:
#     """
#     Executes a registered tool by its name, passing parameters from the tool_params dictionary.
    
#     :param tool_name: The name of the tool (e.g., 'open_spotify', 'play_youtube_content')
#     :param tool_params: A dictionary of parameters for the tool (e.g., {"query_or_url": "..."})
#                         Defaults to None if no parameters are needed.
#     :return: Output string from the tool's execution or an error message.
#     """
#     tool_func = tool_map.get(tool_name)
#     if tool_func:
#         try:
#             if tool_params:
#                 # Assuming LangChain tools expect keyword arguments
#                 # For `open_game(game_id=...)` or `play_youtube_content(query_or_url=...)`
#                 # If your tool has a single main parameter, extract its value
#                 # This assumes tool_params will always contain one key-value pair for tools that need params.
#                 if len(tool_params) == 1:
#                     param_name = next(iter(tool_params)) # Get the first (and only) key
#                     param_value = tool_params[param_name]
                    
#                     # Handle the '<null>' literal from the LLM for tools that don't need a real value
#                     if isinstance(param_value, str) and param_value.lower() == '<null>':
#                         result = tool_func.invoke(None) # Invoke with None for dummy args
#                     else:
#                         result = tool_func.invoke(param_value) # Invoke with the actual parameter value
#                 else:
#                     # If a tool needs multiple named parameters, you'd need a more complex invoke:
#                     # result = tool_func.invoke(**tool_params)
#                     # For current tools, single param or no param is expected.
#                     print(f"Warning: Tool '{tool_name}' received multiple tool_params, but only one is expected by current tools.")
#                     result = tool_func.invoke(next(iter(tool_params.values()))) # Fallback to first value
#             else:
#                 # For tools like open_spotify or open_social_media that take a dummy argument or no specific input.
#                 result = tool_func.invoke(None) # Pass None to the dummy arg
            
#             return result
#         except Exception as e:
#             print(f"Error during execution of tool '{tool_name}' with parameters {tool_params}: {e}")
#             return f"Execution of '{tool_name}' failed: {e}"
#     else:
#         return f"Error: Tool '{tool_name}' not recognized. Please check the available tools in recommender_tools.py."


####################################################################################################

# execution_agent.py
import sys
import os

# Adjust sys.path if necessary to find tools
from tools.recommender_tools import tools

# Create a mapping from tool name (string) to the actual tool function object
tool_map = {tool.name: tool for tool in tools}

def execute_action(tool_name: str, tool_params: str = None) -> str:
    """
    Executes a registered tool by its name, passing parameters from the tool_params dictionary.
    
    :param tool_name: The name of the tool (e.g., 'open_spotify', 'play_youtube_content')
    :param tool_params: A dictionary of parameters for the tool (e.g., {"query_or_url": "..."})
                        Defaults to None if no parameters are needed.
    :return: Output string from the tool's execution or an error message.
    """
    tool_func = tool_map.get(tool_name)
    if tool_func:
        try:
            # If tool_params is None, ensure it's an empty dict for **kwargs
            if tool_params is None:
                tool_params = {}
            
            # The tool_params dictionary content will be passed as keyword arguments.
            # Example: execute_action("play_youtube_content", {"query_or_url": "meditation"})
            # will call play_youtube_content(query_or_url="meditation")
            result = tool_func.invoke(tool_params)
            
            return result
        except Exception as e:
            print(f"Error during execution of tool '{tool_name}' with parameters {tool_params}: {e}")
            return f"Execution of '{tool_name}' failed: {e}"
    else:
        return f"Error: Tool '{tool_name}' not recognized. Please check the available tools in recommender_tools.py."