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

# --- Start background process ---
try:
    # Start ./bin/commands eth0 in the background
    commands_proc = subprocess.Popen([COMMANDS_EXE_PATH, NETWORK_INTERFACE])
    print(f"✅ Started background process: {COMMANDS_EXE_PATH} {NETWORK_INTERFACE} (PID: {commands_proc.pid})")
except Exception as e:
    print(f"❌ Failed to start commands process: {e}")


TRIGGER_WORDS = [
    "ego", "echo", "hey go", "hey ego", "wake", "he go", "either"
]

SINGING_WORDS = [
    "sing", "singing", "entertain me", "sing a song", "rock the flock", "shout"
]

MOVE_WORDS = [
    "move", "moving", "go forward"
]

LEFT_WORDS = [
    "left", "turn left"
]

RIGHT_WORDS = [
    "right", "turn right"
]

BACK_WORDS = [
    "back", "turn back", "reverse"
]

PRAISE_WORDS = [
    "good job", "well done", "nice", "great", "awesome"
]

TALK_WORDS = [
    "how are you", "what is that", "whats that", "what happened", "talk about yourself"
]

EXCITED_WORDS = [
    "lets go!", "woohoo", "thats cool", "excited"
]

SAD_WORDS = [
    "i am sad", "i feel sad", "unhappy", "depressed"
]

COOLDOWN = 3.0          # seconds to prevent repeat actions
SINGING_WINDOW = 10.0   # seconds singing words are active after wake word

# --- UDP setup to send commands to robot ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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
last_left_time = 0
last_right_time = 0
last_move_time = 0
last_back_time = 0       # ✅ FIX: Added this line
last_talk_time = 0       # ✅ FIX: Added this line
last_answer_time = 0     # ✅ FIX: Added this line
singing_mode_until = 0   # timestamp until which singing words are valid

# --- Audio callback ---
def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# --- Robot actions ---
def run_robot_pose():
    global last_trigger_time, singing_mode_until
    now = time.time()
    if now - last_trigger_time < COOLDOWN:
        return
    last_trigger_time = now
    print("🚀 Wake word detected! Running robot pose...")
    os.system(f"{POSE_EXE_PATH} {NETWORK_INTERFACE}")
    singing_mode_until = now + SINGING_WINDOW
    print(f"🟢 Singing mode enabled for {SINGING_WINDOW} seconds.")

def run_singing_action():
    global last_singing_time, singing_mode_until
    now = time.time()
    if now - last_singing_time < COOLDOWN:
        return
    last_singing_time = now
    print("🎵 Singing word detected! Running singing action...")
    os.system(f"{SINGING_EXE_PATH} {NETWORK_INTERFACE}")
    singing_mode_until = 0
    print("🔴 Singing mode disabled.")

def run_left_action():
    global last_left_time
    now = time.time()
    if now - last_left_time < COOLDOWN:
        return
    last_left_time = now
    print("↩️ Left word detected! Running left action...")
    os.system(f"{LEFT_EXE_PATH} {NETWORK_INTERFACE}")

def run_right_action():
    global last_right_time
    now = time.time()
    if now - last_right_time < COOLDOWN:
        return
    last_right_time = now
    print("↪️ Right word detected! Running right action...")
    os.system(f"{RIGHT_EXE_PATH} {NETWORK_INTERFACE}")

def run_move_action():
    global last_move_time
    now = time.time()
    if now - last_move_time < COOLDOWN:
        return
    last_move_time = now
    print("🚶 Move word detected! Running move action...")
    os.system(f"{MOVE_EXE_PATH} {NETWORK_INTERFACE}")

def run_back_action():
    global last_back_time
    now = time.time()
    if now - last_back_time < COOLDOWN:
        return
    last_back_time = now
    print("↩️ Back word detected! Running back action...")
    os.system(f"{BACK_EXE_PATH} {NETWORK_INTERFACE}")

def run_talk_action():
    global last_talk_time
    now = time.time()
    if now - last_talk_time < COOLDOWN:
        return
    last_talk_time = now
    print("🗣️ Talk word detected! Running talk action...")
    os.system(f"{TALK_EXE_PATH} {NETWORK_INTERFACE}")
def run_answer_action():
    global last_answer_time
    now = time.time()
    if now - last_answer_time < COOLDOWN:
        return
    last_answer_time = now
    print("🗣️ Answer word detected! Running answer action...")
    os.system(f"{ANSWER_EXE_PATH} {NETWORK_INTERFACE}")

# --- Utility ---
def contains_trigger(text: str, words) -> bool:
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
    print(f"🎤 Listening... Say one of {TRIGGER_WORDS}. Singing words work after wake word.")
    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            if not text:
                continue

            # Send text to robot via UDP
            sock.sendto(text.encode(), (UDP_IP, UDP_PORT))
            print("🗣️ Heard:", text)

            now = time.time()

            # Trigger main pose
            if contains_trigger(text, TRIGGER_WORDS):
                run_robot_pose()

            # Trigger singing action only if singing mode is active
            elif now < singing_mode_until and contains_trigger(text, SINGING_WORDS):
                run_singing_action()

            # Trigger left action
            elif contains_trigger(text, LEFT_WORDS):
                run_left_action()

            # Trigger right action
            elif contains_trigger(text, RIGHT_WORDS):
                run_right_action()

            # Trigger move action
            elif contains_trigger(text, MOVE_WORDS):
                run_move_action()

            # Trigger back action
            elif contains_trigger(text, BACK_WORDS):
                run_back_action()

            # Trigger talk action
            elif contains_trigger(text, TALK_WORDS):
                run_talk_action()
