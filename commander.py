import os
import sys
import queue
import time
import re
import json
import socket
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import subprocess
import google.generativeai as genai   # ✅ Gemini SDK

# --- CONFIG ---
MODEL_PATH = "/home/verse/vosk-model/vosk-model-small-en-us-0.15"
POSE_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/pose"
SINGING_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/sing"
LEFT_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/left"
RIGHT_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/right"
MOVE_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/move"
BACK_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/back"
TALK_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/talk"
ANSWER_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/answer"
COMMANDS_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/commands"
NETWORK_INTERFACE = "eth0"

# ✅ Gemini API Key
GEMINI_API_KEY = "AIzaSyDJh01fDIvXIXfHw3HnXxd87UdthfveJ3g"
genai.configure(api_key=GEMINI_API_KEY)

# Create Gemini model
gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")

# --- Start background process ---
try:
    commands_proc = subprocess.Popen([COMMANDS_EXE_PATH, NETWORK_INTERFACE])
    print(f"✅ Started background process: {COMMANDS_EXE_PATH} {NETWORK_INTERFACE} (PID: {commands_proc.pid})")
except Exception as e:
    print(f"❌ Failed to start commands process: {e}")

COOLDOWN = 3.0

# --- UDP setup ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- Load Vosk model ---
if not os.path.exists(MODEL_PATH):
    print("❌ Model not found at", MODEL_PATH)
    sys.exit(1)

print("✅ Loading Vosk model...")
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

# --- Audio queue ---
q = queue.Queue()
last_action_time = 0

# --- Audio callback ---
def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# --- Robot action mapping ---
def run_robot_action(keyword: str):
    global last_action_time
    now = time.time()
    if now - last_action_time < COOLDOWN:
        return
    last_action_time = now

    actions = {
        "pose": f"{POSE_EXE_PATH} {NETWORK_INTERFACE}",
        "sing": f"{SINGING_EXE_PATH} {NETWORK_INTERFACE}",
        "left": f"{LEFT_EXE_PATH} {NETWORK_INTERFACE}",
        "right": f"{RIGHT_EXE_PATH} {NETWORK_INTERFACE}",
        "move": f"{MOVE_EXE_PATH} {NETWORK_INTERFACE}",
        "back": f"{BACK_EXE_PATH} {NETWORK_INTERFACE}",
        "talk": f"{TALK_EXE_PATH} {NETWORK_INTERFACE}",
        "answer": f"{ANSWER_EXE_PATH} {NETWORK_INTERFACE}",
    }

    if keyword in actions:
        print(f"🤖 Executing action for: {keyword}")
        os.system(actions[keyword])
    else:
        print(f"⚠️ No action mapped for: {keyword}")

# --- Gemini interpretation ---
def interpret_with_gemini(text: str) -> str:
    prompt = f"""
    You are controlling a robot. 
    Based on the input text: "{text}", reply with ONLY one keyword from this list:
    [pose, sing, left, right, move, back, talk, answer].
    If it doesn't match, just return "none".
    """
    try:
        response = gemini_model.generate_content(prompt)
        keyword = response.text.strip().lower()
        return keyword
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "none"


# --- Wake / Calling Words ---
WAKE_WORDS = [
    "jojo", "zha zha", "zhazha", "jaja", "zaza",
    "cha cha", "chacha", "jara jara", "jha jha"
]

# --- Start listening ---
with sd.RawInputStream(
    samplerate=16000,
    blocksize=8000,
    dtype="int16",
    channels=1,
    callback=callback
):
    print("🎤 Listening... (controlled by Gemini + Wake words)")
    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            if not text:
                continue

            # Send recognized text to robot log via UDP
            sock.sendto(text.encode(), (UDP_IP, UDP_PORT))
            print("🗣️ Heard:", text)

            # --- Check wake/calling words first ---
            if any(word in text for word in WAKE_WORDS):
                print("👂 Wake word detected! Running Pose action...")
                run_robot_action("pose")
                continue

            # Interpret with Gemini
            keyword = interpret_with_gemini(text)
            print(f"🔑 Gemini decided: {keyword}")

            # Run mapped action
            run_robot_action(keyword)
