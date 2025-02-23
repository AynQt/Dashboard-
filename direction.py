# Voice-Assisted Step-by-Step Map Navigation App using OpenRouteService (ORS) with GPS, Voice Input, and Flet UI

# Dependencies:
# pip install openrouteservice pyttsx3 geocoder speechrecognition flet

import openrouteservice
from openrouteservice import convert
import pyttsx3
import time
import geocoder
import speech_recognition as sr
import flet as ft

# ✅ Initialize text-to-speech engine (TTS) with female voice and introduction
def init_tts():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    for voice in voices:
        if "female" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    return engine


def speak(engine, text):
    print(f"Instruction: {text}")
    engine.say(text)
    engine.runAndWait()


# ✅ Get destination using voice or manual input
def get_destination(engine):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak(engine, "Please say your destination after the beep or type it if you prefer.")
        print("Listening for destination...")
        try:
            audio = recognizer.listen(source, timeout=5)
            destination_address = recognizer.recognize_google(audio)
            print(f"Detected destination: {destination_address}")
            return destination_address
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            speak(engine, "I couldn't catch that. Please type your destination.")
            return None


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
def navigate_with_voice(api_key, origin, destination, engine):
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


# ✅ Flet UI for user interaction with voice/manual destination input
def main_ui(page: ft.Page):
    page.title = "Dristi - Your Personal Assistant"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    engine = init_tts()
    speak(engine, "Hello, I am Dristi. I am your personal assistant here to help you navigate and recognize objects. Let's get started!")

    destination_input = ft.TextField(label="Enter Destination (if voice input fails)", width=400)
    status_text = ft.Text("Welcome to Dristi!", size=16)

    def start_navigation(e):
        origin = get_current_location()
        destination = get_destination(engine)
        if not destination:
            destination = destination_input.value
        status_text.value = f"Navigating to {destination}..."
        page.update()
        navigate_with_voice(api_key, origin, destination, engine)
        status_text.value = "Navigation complete."
        page.update()

    page.add(
        ft.Column([
            ft.Text("👩🏻‍🦰 Dristi - Personal Voice Assistant", size=30, weight="bold"),
            destination_input,
            ft.ElevatedButton("Start Navigation", on_click=start_navigation),
            status_text
        ],
            alignment=ft.MainAxisAlignment.CENTER
        )
    )


if __name__ == "__main__":
    api_key = "5b3ce3597851110001cf6248555107190050471e8c2bdd03d403d3aa"
    ft.app(target=main_ui)
