import requests  # To fetch weather data and time data
from fastapi import FastAPI
from pydantic import BaseModel
from huggingface_hub import InferenceClient  # Import the InferenceClient for Hugging Face API
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import re
import logging  # Using logging instead of print statements

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.WARNING)  # You can change the level based on the verbosity you need
logger = logging.getLogger(__name__)

# Create the Inference Client to interact with Hugging Face API
client = InferenceClient(
    api_key="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"  # Hugging Face API key
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",],  # Corrected the URL
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
        logger.error(f"Error fetching weather data: {str(e)}")  # Log detailed error internally
        return "Error fetching weather data."

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
        logger.warning(f"Timeout occurred when fetching time for {city}.")  # Log timeout warning
        return "Error: The request to fetch time data timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching time data: {str(e)}")  # Log request exceptions
        return "Error fetching time data."

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
            # Pass other queries to Hugging Face model API
            messages = [
                {"role": "user", "content": user_input}
            ]

            # Make API call to Hugging Face for inference
            completion = client.chat.completions.create(
                model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                messages=messages,
                max_tokens=500
            )

            response = completion.choices[0].message['content']

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            response = "Sorry, there was an error processing your request. Please check the logs."

    return {"response": response}

@app.get("/")
def read_root():
    return {"message": "Chatbot API is running!"}
