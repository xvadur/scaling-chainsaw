# Test script to verify Hugging Face API integration using the model `devstral-small`.
from huggingface_hub import InferenceClient

# Replace 'your_hf_api_key' with your actual Hugging Face API key
api_key = "your_hf_api_key"
model_id = "devstral-small"

# Initialize the Hugging Face Inference Client
client = InferenceClient(model=model_id, token=api_key)

# Test prompt
prompt = "Generate a Python function to calculate factorial"

try:
    # Make an inference request
    result = client.text_generation(prompt, max_new_tokens=50)
    print("Model Output:", result)
except Exception as e:
    print("Error during inference:", e)
