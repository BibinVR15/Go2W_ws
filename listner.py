import os
import sys
import queue
import time
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import re

# --- CONFIG ---
MODEL_PATH = "/home/verse/vosk-model/vosk-model-small-en-us-0.15"
POSE_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/pose"
SINGING_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/waiting"  # Replace with your singing action binary
NETWORK_INTERFACE = "eth0"

TRIGGER_WORDS = [
    "ego", "eggo", "echo", "eko", "aygo", "hey ego", "ok ego", "go", "igo"
]

SINGING_WORDS = [
    "sing", "singing", "entertain me", "sing a song", "rock the flock", "shout"
]

COOLDOWN = 3.0          # seconds to prevent repeat actions
SINGING_WINDOW = 10.0   # seconds singing words are active after "ego"

# --- Load Vosk model ---
if not os.path.exists(MODEL_PATH):
    print("❌ Model not found at", MODEL_PATH)
    sys.exit(1)

print("✅ Loading Vosk model from", MODEL_PATH)
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

# --- Audio queue ---
q = queue.Queue()
last_trigger_time = 0
last_singing_time = 0
singing_mode_until = 0  # timestamp until which singing words are valid

# --- Audio callback ---
def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# --- Robot actions ---
def run_robot_pose():
    """Trigger robot pose and enable singing mode."""
    global last_trigger_time, singing_mode_until
    now = time.time()
    if now - last_trigger_time < COOLDOWN:
        return
    last_trigger_time = now
    print("🚀 'Ego' detected! Running robot pose...")
    os.system(f"{POSE_EXE_PATH} {NETWORK_INTERFACE}")

    singing_mode_until = now + SINGING_WINDOW
    print(f"🟢 Singing mode enabled for {SINGING_WINDOW} seconds.")

def run_singing_action():
    """Trigger singing-related robot action."""
    global last_singing_time, singing_mode_until
    now = time.time()
    if now - last_singing_time < COOLDOWN:
        return
    last_singing_time = now
    print("🎵 Singing word detected! Running singing action...")
    os.system(f"{SINGING_EXE_PATH} {NETWORK_INTERFACE}")

    singing_mode_until = 0
    print("🔴 Singing mode disabled.")

# --- Utility ---
def contains_trigger(text: str, words) -> bool:
    """Check if the recognized text contains any word in the list."""
    text = text.lower().strip()
    for word in words:
        if re.search(rf"\b{re.escape(word)}\b", text):
            return True
    return False

# --- Start listening ---
with sd.RawInputStream(
    samplerate=16000,
    blocksize=8000,
    dtype="int16",
    channels=1,
    callback=callback
):
    print(f"🎤 Listening... Say one of {TRIGGER_WORDS}. Singing words only work after 'ego'.")
    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            now = time.time()

            # Trigger main pose
            if contains_trigger(text, TRIGGER_WORDS):
                run_robot_pose()

            # Trigger singing action only if singing mode is active
            elif now < singing_mode_until and contains_trigger(text, SINGING_WORDS):
                run_singing_action()
