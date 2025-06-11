from langchain.agents import initialize_agent, AgentType
from llm_setup import llm
from tools.recommender_tools import tools

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

def recommend_action(emotion: str):
    prompt = (
    f"The user is feeling {emotion}. Your goal is to suggest 2-3 appropriate digital actions "
    f"to help the user return to a neutral emotional state. "
    f"Imagine you have access to these tools: {', '.join([t.name for t in tools])}.\n"
    f"DO NOT ACTUALLY EXECUTE ANY TOOLS FOR OBSERVATION - just suggest actions that COULD use these tools.\n"
    f"For 'Action Input', provide the specific parameter value the tool needs. If a tool needs no specific input, use '<null>'.\n\n"
    
    f"After your reasoning steps, provide your FINAL ANSWER as a JSON array of 2-3 objects.\n"
    f"Each object in the JSON array MUST have the following keys:\n"
    f"  - 'title': A short, user-friendly title for the recommendation.\n"
    f"  - 'description': A brief explanation of the recommendation.\n"
    f"  - 'tool_name': The exact name of the tool to be used (e.g., 'open_spotify', 'play_youtube_content').\n"
    f"  - 'tool_params' (OPTIONAL): A JSON object containing parameters for the tool (e.g., {{\"game_id\": \"...\"}} for 'open_game', {{\"query_or_url\": \"...\"}} for 'play_youtube_content', {{\"emotion\": \"...\"}} for 'write_journal_entry'). Only include this key if the tool requires parameters.\n\n"
    
    f"**IMPORTANT:** Your ENTIRE final output after the 'Final Answer:' tag MUST be ONLY the JSON array. No extra text, no explanations, no questions, no repeated prompts after the JSON. This is crucial for parsing.\n\n"
    
    f"Example of Final Answer JSON with two options:\n"
    f'[\n'
    f'  {{\n'
    f'    "title": "Listen to Calming Music on Spotify",\n'
    f'    "description": "Open Spotify and find a relaxing playlist.",\n'
    f'    "tool_name": "open_spotify"\n'
    f'  }},\n'
    f'  {{\n'
    f'    "title": "Watch a Relaxing YouTube Video",\n'
    f'    "description": "Find a peaceful video to clear your mind.",\n'
    f'    "tool_name": "play_youtube_content",\n'
    f'    "tool_params": {{"query_or_url": "meditation music for fear relief"}}\n'
    f'  }},\n'
    f'  {{\n'
    f'    "title": "Write a Journal Entry",\n'
    f'    "description": "Express your thoughts and feelings to process emotion.",\n'
    f'    "tool_name": "write_journal_entry",\n'
    f'    "tool_params": {{"emotion": "{emotion}"}}\n'
    f'  }}\n'
    f']\n\n'
    f"Begin!\n"
    f"Thought: I need to consider the user's '{emotion}' emotion and suggest actions that can help. I will think step by step about what tools to use to generate 2-3 diverse and appropriate recommendations, ensuring I include `tool_params` when necessary. Then I will format my final answer as a clean JSON array."
    )
    return agent.run(prompt)


# emotion_agent.py
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from llm_setup import llm # Your LLM instance

# def recommend_action(emotion: str) -> str:
#     # This prompt tells the LLM to act as a pure text generator,
#     # specifically to produce a JSON array of recommendations.
#     # It does NOT instruct the LLM to use any tools itself.
    
#     # All literal curly braces for the JSON structure are doubled ({{ and }}).
#     # The actual variable for the current emotion is {emotion}.
#     # The example JSON's {emotion} will also be filled by LangChain.

#     prompt_text = """The user is feeling {emotion}. Your goal is to suggest 2-3 appropriate digital actions to help the user return to a neutral emotional state. You should recommend actions using the following tools: open_spotify, open_social_media, open_game, play_youtube_content, write_journal_entry. Provide your suggestions as a JSON array of 2-3 objects. Each object in the JSON array MUST have the following keys:
#   - 'title': A short, user-friendly title for the recommendation.
#   - 'description': A brief explanation of the recommendation.\n"
#   - 'tool_name': The exact name of the tool to be used (e.g., 'open_spotify', 'play_youtube_content').\n"
#   - 'tool_params' (OPTIONAL): A JSON object containing parameters for the tool (e.g., {{ "game_id": "..." }} for 'open_game', {{ "query_or_url": "..." }} for 'play_youtube_content', {{ "emotion": "..." }} for 'write_journal_entry'). Only include this key if the tool requires parameters. If a tool needs no specific input, omit 'tool_params' or provide an empty object.

# **CRITICAL INSTRUCTION:** Your ENTIRE output MUST be ONLY the JSON array. Do NOT include any additional text, thoughts, notes, explanations, or questions outside the JSON. Begin the output with the opening square bracket '[' of the JSON array.

# Examples of Final Answer JSON should be given (Do not only use these examples):
# [{{
#   {{
#     "title": "Listen to Calming Music on Spotify",
#     "description": "Open Spotify and find a relaxing playlist.",
#     "tool_name": "open_spotify"
#   }},
#   {{
#     "title": "Watch a Relaxing YouTube Video",
#     "description": "Find a peaceful video to clear your mind.",
#     "tool_name": "play_youtube_content",
#     "tool_params": {{ "query_or_url": "meditation music for fear relief" }}
#   }},
#   {{
#     "title": "Write a Journal Entry",
#     "description": "Express your thoughts and feelings to process emotion.",
#     "tool_name": "write_journal_entry",
#     "tool_params": {{ "emotion": "{emotion}" }}
#   }}
# ]

# Please generate the JSON array now for a user feeling {emotion}."""

#     # Create the PromptTemplate. This object is what tells the LLM how to format its output.
#     prompt_template = PromptTemplate.from_template(prompt_text)

#     # Use an LLMChain, not an AgentExecutor. An LLMChain just takes a prompt and returns text.
#     # It does NOT decide to run tools.
#     llm_chain = LLMChain(prompt=prompt_template, llm=llm, verbose=True)

#     # Invoke the chain to get the raw text output from the LLM.
#     response = llm_chain.invoke({"emotion": emotion})

#     # Return the cleaned-up text, which should be your JSON.
#     return response['text'].strip()

# from langchain.agents import initialize_agent, AgentType
# from llm_setup import llm
# from tools.recommender_tools import tools
# import json

# # Modified agent initialization to prevent tool execution
# agent = initialize_agent(
#     tools=[],  # Empty tools list prevents any execution
#     llm=llm,
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     verbose=True,
#     handle_parsing_errors=True
# )

# def recommend_action(emotion: str):
#     prompt = (
#         f"The user is feeling {emotion}. Your goal is to suggest 2-3 appropriate digital actions "
#         f"to help the user return to a neutral emotional state. "
#         f"Imagine you have access to these tools: {', '.join([t.name for t in tools])}.\n"  # Note "Imagine" added
#         f"DO NOT ACTUALLY USE ANY TOOLS - just suggest actions that COULD use these tools.\n"
#         f"Generate your response as a JSON array following this exact format:\n"
#         f'[\n'
#         f'  {{\n'
#         f'    "title": "Example Title",\n'
#         f'    "description": "Example description",\n'
#         f'    "tool_name": "example_tool",\n'
#         f'    "tool_params": {{"param": "value"}}  // ONLY if needed\n'
#         f'  }}\n'
#         f']\n\n'
#         f"Important rules:\n"
#         f"1. NEVER actually execute any tools\n"
#         f"2. Only output the raw JSON array\n"
#         f"3. Use exactly the tool names from this list: {[t.name for t in tools]}\n"
#     )
    
#     # Get the raw response
#     response = agent.run(prompt)
    
#     try:
#         # Validate it's proper JSON
#         recommendations = json.loads(response)
#         return recommendations
#     except json.JSONDecodeError:
#         # Fallback if the agent doesn't return pure JSON
#         return [{
#             "title": "Error in parsing recommendations",
#             "description": "The system failed to generate valid recommendations",
#             "tool_name": "none"
#         }]