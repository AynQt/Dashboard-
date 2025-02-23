# Voice-Assisted Step-by-Step Map Navigation App using OpenRouteService (ORS) with GPS and Voice Input
# Dependencies:
# pip install openrouteservice pyttsx3 geocoder speechrecognition

import openrouteservice
from openrouteservice import convert
import pyttsx3
import time
import geocoder
import speech_recognition as sr

# ✅ Initialize text-to-speech engine (TTS)
def init_tts():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    return engine


def speak(engine, text):
    print(f"Instruction: {text}")
    engine.say(text)
    engine.runAndWait()


# ✅ Get user's current location via GPS or manual input
def get_current_location():
    try:
        g = geocoder.ip('me')
        if g.latlng:
            return [g.lng, g.lat]
        else:
            print("Couldn't fetch GPS location. Please enter manually.")
            lat = float(input("Enter your current latitude: "))
            lon = float(input("Enter your current longitude: "))
            return [lon, lat]
    except Exception:
        lat = float(input("Enter your current latitude: "))
        lon = float(input("Enter your current longitude: "))
        return [lon, lat]


# ✅ Get destination using voice or manual input
def get_destination():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say your destination address or press Enter to type:")
        try:
            audio = recognizer.listen(source, timeout=5)
            destination_address = recognizer.recognize_google(audio)
            print(f"Detected destination: {destination_address}")
            return destination_address
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            print("Couldn't detect voice input. Please type the destination.")
            return input("Enter destination address: ")


# ✅ Convert address to coordinates using ORS geocoding API
def get_coordinates(client, address):
    try:
        location = client.pelias_search(text=address)
        return location['features'][0]['geometry']['coordinates']
    except Exception:
        raise Exception("Failed to fetch coordinates for the given address.")


# ✅ Fetch directions from ORS API
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


# ✅ Navigate with voice assistance
def navigate_with_voice(api_key, origin, destination):
    engine = init_tts()
    try:
        client = openrouteservice.Client(key=api_key)
        destination_coords = get_coordinates(client, destination)
        coordinates = [origin, destination_coords]

        directions_data = get_directions(client, coordinates)
        steps = directions_data['features'][0]['properties']['segments'][0]['steps']

        speak(engine, "Starting navigation. Follow the instructions carefully.")

        for idx, step in enumerate(steps, start=1):
            instruction = step['instruction']
            distance = step['distance'] / 1000
            speak(engine, f"Step {idx}: {instruction}. Walk for {distance:.2f} kilometers.")
            time.sleep(1)

        speak(engine, "You have reached your destination. Navigation complete.")
    except Exception as e:
        speak(engine, f"An error occurred: {str(e)}")


if __name__ == "__main__":
    print("Voice-Assisted Map Navigation App using OpenRouteService")
    try:
        # ✅ Use saved API key (replace with your ORS key)
        api_key = "5b3ce3597851110001cf6248555107190050471e8c2bdd03d403d3aa"
        origin = get_current_location()
        destination = get_destination()

        navigate_with_voice(api_key, origin, destination)
    except ValueError:
        print("Invalid input. Please enter valid data.")

# Test Cases
# 1. Pune Railway Station to Shaniwar Wada:
# Origin: 18.5284, 73.8743
# Destination: 18.5195, 73.8553
# 2. DY Patil International University to Akurdi Station:
# Origin: 18.6500, 73.7683
# Destination: 18.6445, 73.7635
