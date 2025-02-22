# Voice-Assisted Step-by-Step Map Navigation App using OpenRouteService (ORS)
# Dependencies:
# pip install openrouteservice pyttsx3

import openrouteservice
from openrouteservice import convert
import pyttsx3
import time


# Initialize text-to-speech engine
def init_tts():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # Speech rate
    engine.setProperty('volume', 1.0)  # Max volume
    return engine


def speak(engine, text):
    print(f"Instruction: {text}")
    engine.say(text)
    engine.runAndWait()


# Function to fetch directions from ORS API
def get_directions(client, coordinates):
    try:
        route = client.directions(
            coordinates=coordinates,
            profile='foot-walking',
            format='geojson',
            instructions=True
        )
        return route
    except Exception as e:
        raise Exception(f"Failed to fetch directions: {e}")


# Navigate using voice assistance
def navigate_with_voice(api_key, origin, destination):
    engine = init_tts()
    try:
        client = openrouteservice.Client(key=api_key)
        coordinates = [origin, destination]
        directions_data = get_directions(client, coordinates)

        steps = directions_data['features'][0]['properties']['segments'][0]['steps']

        speak(engine, "Starting navigation. Follow the instructions carefully.")

        for idx, step in enumerate(steps, start=1):
            instruction = step['instruction']
            distance = step['distance'] / 1000  # Convert meters to km
            speak(engine, f"Step {idx}: {instruction}. Walk for {distance:.2f} kilometers.")
            time.sleep(1)

        speak(engine, "You have reached your destination. Navigation complete.")
    except Exception as e:
        speak(engine, f"An error occurred: {str(e)}")


if __name__ == "__main__":
    print("Voice-Assisted Map Navigation App using OpenRouteService")
    try:
        api_key = input("Enter your ORS API Key: ")
        origin_lat = float(input("Enter your current latitude: "))
        origin_lon = float(input("Enter your current longitude: "))
        dest_lat = float(input("Enter destination latitude: "))
        dest_lon = float(input("Enter destination longitude: "))

        origin = [origin_lon, origin_lat]
        destination = [dest_lon, dest_lat]

        navigate_with_voice(api_key, origin, destination)
    except ValueError:
        print("Invalid input. Please enter valid coordinates.")

# Test Cases
# 1. Pune Railway Station to Shaniwar Wada:
# Origin: 18.5284, 73.8743
# Destination: 18.5195, 73.8553
# 2. DY Patil International University to Akurdi Station:
# Origin: 18.6500, 73.7683
# Destination: 18.6445, 73.7635
