import os
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import subprocess

# Path to your downloaded Vosk model
MODEL_PATH = "vosk-model-small-en-us-0.15"

# Load Vosk model
if not os.path.exists(MODEL_PATH):
    print("Vosk model not found! Please download and extract it.")
    exit(1)

model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

# Queue for audio data
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, flush=True)
    q.put(bytes(indata))

def speak(text):
    """ Convert text to speech using eSpeak """
    subprocess.run(["espeak", text])

def listen():
    """ Capture audio and return recognized text """
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=callback):
        print("Listening...")
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                return result.get("text", "")

# Main Loop
while True:
    command = listen()
    print(f"You said: {command}")

    if "hello" in command:
        speak("Hello! How can I assist you?")
    
    elif "exit" in command or "quit" in command:
        speak("Goodbye!")
        break
