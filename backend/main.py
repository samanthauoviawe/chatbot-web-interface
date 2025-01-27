import requests  # To fetch weather data and time data
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import re

app = FastAPI()

# Load the TinyLlama model and tokenizer manually
model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Initialize the pipeline for text generation with TinyLlama
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    truncation=True,
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://chatbot-web-interface-57kaal4hx-samanthauoviawes-projects.vercel.app"],  # Corrected the URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Prompt(BaseModel):
    text: str

# Weather function to fetch data using OpenWeather API
def get_weather(city: str) -> str:
    api_key = "afee1beb843fc1e1ab044bc4456d71db"  # OpenWeather API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            temp = data['main']['temp']
            description = data['weather'][0]['description']
            return f"The weather in {city} is {description} with a temperature of {temp}°C."
        else:
            return f"Sorry, I couldn't fetch the weather data for {city}."
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

# Function to extract the city from user input using regular expressions
def extract_city_from_input(user_input: str) -> str:
    match = re.search(r'weather in ([a-zA-Z\s]+)', user_input)
    if match:
        return match.group(1).strip()  # Return the city name if found
    else:
        return "Tampa"  # Default city if no city is found in the input

# Mapping of cities to timezones
CITY_TO_TIMEZONE = {
    "tampa": "America/New_York",
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "sydney": "Australia/Sydney",
    "tokyo": "Asia/Tokyo",
    "dubai": "Asia/Dubai",
    # Add more cities here later
}

def get_time_for_city(city: str) -> str:
    city = city.lower()  # Ensure the city is lowercase for matching
    timezone = CITY_TO_TIMEZONE.get(city, "America/New_York")  # Default to New York if not found
    try:
        url = f"http://worldtimeapi.org/api/timezone/{timezone}"
        response = requests.get(url, timeout=30)  # Increased timeout to 30 seconds
        response.raise_for_status()  # Will raise an error for status codes 4xx/5xx
        data = response.json()
        if response.status_code == 200:
            # Extract the datetime and format it
            current_time = data['datetime']
            formatted_time = current_time.split("T")[1].split(".")[0]  # Extract only the time part
            return f"The current time in {city} is {formatted_time}."
        else:
            return f"Sorry, I couldn't fetch the time data for {city}."
    except requests.exceptions.Timeout:
        return "Error: The request to fetch time data timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        return f"Error fetching time data: {str(e)}"

@app.post("/chat")
async def chat(prompt: Prompt):
    user_input = prompt.text.strip().lower()

    if not user_input:
        response = "Please enter a message so I can assist you."

    elif any(greeting in user_input for greeting in ["hello", "hi", "hey", "how are you"]):
        response = "Hello! How can I assist you today?"
    
    elif "date" in user_input:
        today_date = datetime.now().strftime("%Y-%m-%d")
        response = f"Today's date is {today_date}."
    
    elif "year" in user_input or "what year is it" in user_input:
        current_year = datetime.now().year
        response = f"The current year is {current_year}."
    
    # Handle weather queries
    elif "weather" in user_input:
        city = extract_city_from_input(user_input)  # Extract city from the input or use default
        response = get_weather(city)
    
     # Handle time queries
    elif "time" in user_input or "what time is it" in user_input:
        city = extract_city_from_input(user_input)  # Extract city from the input or use default
        response = get_time_for_city(city)

    else:
        try:
            # Pass other queries to the AI model
            messages = [
                {"role": "system", "content": "You are a helpful assistant that answers questions in a conversational manner."},
                {"role": "user", "content": user_input}
            ]

            outputs = pipe(
                messages, 
                max_length=150,
                do_sample=True,
                temperature=0.7, 
                top_k=50, 
                top_p=0.95,
                num_return_sequences=1
            )

            response = ""

            # Check if the outputs is a list, which it most likely will be
            if isinstance(outputs, list):
                for output in outputs:
                    # Check if each item is a dictionary and has the 'generated_text'
                    if isinstance(output, dict) and "generated_text" in output:
                        generated_text = output["generated_text"]
                        if isinstance(generated_text, list):
                            # If generated_text is a list, we iterate through and check for the assistant's response
                            assistant_response = None
                            for item in generated_text:
                                if item.get("role") == "assistant":  # Ensure we pick the assistant's response
                                    assistant_response = item.get("content", "").strip()
                                    break
                            if assistant_response:
                                response += assistant_response + " "
                            else:
                                response = "Sorry, I couldn't generate a response."
                        elif isinstance(generated_text, str):
                            # If generated_text is a string, assume it's the assistant's response
                            response += generated_text.strip() + " "
                        else:
                            response = "Unexpected response format from the model."
                    else:
                        response = "Unexpected output format: No 'generated_text' key found."
            else:
                response = "Sorry, I couldn't generate a response."

        except Exception as e:
            response = f"Sorry, there was an error processing your request. Error details: {str(e)}"

    return {"response": response}

@app.get("/")
def read_root():
    return {"message": "Chatbot API is running!"}
