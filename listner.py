import os
import sys
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json

# --- CONFIG ---
MODEL_PATH = "/home/verse/vosk-model/vosk-model-small-en-us-0.15"
POSE_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/pose"
NETWORK_INTERFACE = "eth0"
TRIGGER_WORD = "ego"

# --- Load Vosk model ---
if not os.path.exists(MODEL_PATH):
    print("❌ Model not found at", MODEL_PATH)
    sys.exit(1)

print("✅ Loading Vosk model from", MODEL_PATH)
model = Model(MODEL_PATH)

recognizer = KaldiRecognizer(model, 16000)

# --- Audio queue ---
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def run_robot_action():
    print("🚀 Trigger word detected! Running robot pose...")
    # Run pose with os.system
    os.system(f"{POSE_EXE_PATH} {NETWORK_INTERFACE}")

# --- Start listening ---
with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                       channels=1, callback=callback):
    print(f"🎤 Listening... Say '{TRIGGER_WORD}' to trigger the robot.")
    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            if TRIGGER_WORD in text:
                run_robot_action()
