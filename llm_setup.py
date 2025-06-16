# from langchain_community.llms import LlamaCpp

# llm = LlamaCpp(
#     model_path= r"F:\Academic\7th semester\FYP\recommondation_agents_implementation\models\DarkIdol-Llama-3.1-8B-Instruct-1.2-Uncensored.Q2_K.gguf",
#     temperature=0.7,
#     max_tokens=2048,
#     n_ctx=4096,
#     verbose=True,
#     n_gpu_layers=-1
# )

# response = llm.invoke("What is LangChain?")
# print(response)


from langchain_community.llms import LlamaCpp
import os

# Get the directory of the current script
script_dir = os.path.dirname(__file__)
# Construct the path to the GGUF model file
model_path = r"F:\Academic\7th semester\FYP\recommondation_agents_implementation\models\DarkIdol-Llama-3.1-8B-Instruct-1.2-Uncensored.Q2_K.gguf"

# Check if the model file exists
if not os.path.exists(model_path):
    print(f"Error: Model file not found at {model_path}")
    print("Please ensure your GGUF model is in the 'models' directory or update the model_path.")
    exit()

try:
    llm = LlamaCpp(
        model_path=model_path,
        temperature=0.7,
        max_tokens=2048, # Ensure this is sufficient for the JSON output + any thought process if present
        n_ctx=4096,
        verbose=True, # Keep True for debugging LLM output
        n_gpu_layers=-1 # Offload all layers to GPU if possible
    )
    print("LlamaCpp LLM initialized successfully.")
except Exception as e:
    print(f"Failed to initialize LlamaCpp LLM: {e}")
    exit()