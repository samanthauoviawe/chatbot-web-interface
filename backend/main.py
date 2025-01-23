from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI()

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Load the TinyLlama model
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

class Prompt(BaseModel):
    text: str

@app.post("/chat")
async def chat(prompt: Prompt):
    user_input = prompt.text.lower()  # Normalize input to lowercase

    # Check if the prompt contains a greeting
    if any(greeting in user_input for greeting in ["hello", "hi", "hey", "how are you"]):
        response = "Hello! How can I assist you today?"
    
    # Check if the prompt contains a question about the date
    elif "date" in user_input or "today" in user_input:
        today_date = datetime.now().strftime("%Y-%m-%d")
        response = f"Today's date is {today_date}."
    
    else:
        # Process the prompt with the model if not a greeting or date request
        inputs = tokenizer(prompt.text, return_tensors="pt")
        outputs = model.generate(**inputs, max_length=50, num_return_sequences=1)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True).split("\n")[0]
    
    return {"response": response}

@app.get("/")
def read_root():
    return {"message": "Chatbot API is running!"}
