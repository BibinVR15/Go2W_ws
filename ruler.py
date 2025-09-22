import os
import sys
import queue
import time
import json
import socket
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import subprocess
import google.generativeai as genai   # ✅ Gemini SDK
import threading

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
SAD_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/sad"
COMMANDS_EXE_PATH = "/home/verse/unitree_sdk2/build/bin/commands"
NETWORK_INTERFACE = "eth0"

# ✅ Gemini API Key
GEMINI_API_KEY = "AIzaSyDJh01fDIvXIXfHw3HnXxd87UdthfveJ3g"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")

# --- Start background commands process ---
try:
    commands_proc = subprocess.Popen([COMMANDS_EXE_PATH, NETWORK_INTERFACE])
    print(f"✅ Started background process: {COMMANDS_EXE_PATH} {NETWORK_INTERFACE} (PID: {commands_proc.pid})")
except Exception as e:
    print(f"❌ Failed to start commands process: {e}")

COOLDOWN = 3.0
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- Load Vosk models ---
if not os.path.exists(MODEL_PATH):
    print("❌ Model not found at", MODEL_PATH)
    sys.exit(1)

print("✅ Loading full Vosk model...")
model_full = Model(MODEL_PATH)
recognizer_full = KaldiRecognizer(model_full, 16000)

print("✅ Loading minimal wake-word recognizer...")
grammar = '["zha zha", "zhazha", "jaja", "zaza", "jha jha", "cha cha", "chacha", "jara jara", "jha zha", "za za", "jah jah", "zha ja", "ja zha", "shasha"]'
recognizer_wake = KaldiRecognizer(model_full, 16000, grammar)

# --- Audio queue ---
q = queue.Queue()
last_action_time = 0
wake_mode = True   # Start in wake mode first
processing_lock = threading.Lock()  # ✅ Lock while command runs

# --- Audio callback ---
def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    if not processing_lock.locked():  # Only add data if not processing
        q.put(bytes(indata))

# --- Reset wake mode after 5 minutes ---
def start_wake_reset_timer():
    def reset():
        global wake_mode
        print("⏳ 5 minutes passed → Resetting to wake-word mode")
        wake_mode = True
    t = threading.Timer(300.0, reset)  # 300 seconds = 5 minutes
    t.start()

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
        "sad": f"{SAD_EXE_PATH} {NETWORK_INTERFACE}",
    }

    if keyword in actions:
        print(f"🤖 Executing action for: {keyword}")
        with processing_lock:  # Lock while action runs
            os.system(actions[keyword])
        # ✅ Start reset timer only if pose ran
        if keyword == "pose":
            start_wake_reset_timer()
    else:
        print(f"⚠️ No action mapped for: {keyword}")

# --- Gemini interpretation ---
def interpret_with_gemini(text: str) -> str:
    prompt = f"""
    You are controlling a robot. 
    Based on the input text: "{text}", reply with ONLY one keyword from this list:
    [pose, sing, left, right, move, back, talk, answer, sad].
    If it doesn't match, just return "none".
    """
    try:
        response = gemini_model.generate_content(prompt)
        keyword = response.text.strip().lower()
        return keyword
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "none"

# --- Predefined local command sets (no Gemini) ---
LOCAL_COMMANDS = {
    "stand": {"stand up", "get up", "wake up", "rise", "on feet", "stand"},
    "sit": {"sit", "sit down", "down", "rest", "take a seat"},
    "move": {"move", "move forward", "walk", "march", "advance", "step"},
    "stop": {"stop", "halt", "freeze", "pause", "stay"},
    "balance": {"balance", "steady", "stabilize", "hold"},
    "recover": {"recover", "get up again", "reset", "back up"},
    "stretch": {"stretch", "extend", "reach out"},
    "stand_down": {"stand down", "lie down", "downward", "floor", "ground"}
}

# --- Updated main loop ---
with sd.RawInputStream(
    samplerate=16000,
    blocksize=8000,
    dtype="int16",
    channels=1,
    callback=callback
):
    print("🎤 Listening... (wake-word first, then full control)")
    while True:
        data = q.get()

        if processing_lock.locked():
            continue  # Skip audio while processing

        # --- Stage 1: Wake-word minimal recognizer ---
        if wake_mode:
            if recognizer_wake.AcceptWaveform(data):
                result = json.loads(recognizer_wake.Result())
                text = result.get("text", "").lower()
                if not text:
                    continue

                print("🗣️ Wake Recognizer Heard:", text)
                if "zha" in text:
                    print("👂 Wake word detected → Running Pose & unlocking full mode")
                    run_robot_action("pose")
                    wake_mode = False
            continue

        # --- Stage 2: Full recognizer with local command check ---
        if recognizer_full.AcceptWaveform(data):
            result = json.loads(recognizer_full.Result())
            text = result.get("text", "").lower()
            if not text:
                continue

            sock.sendto(text.encode(), (UDP_IP, UDP_PORT))
            print("🗣️ Heard:", text)

            # --- Check local command sets first ---
            handled = False
            for cmd_key, phrases in LOCAL_COMMANDS.items():
                if any(phrase in text for phrase in phrases):
                    print(f"🔑 Local command detected: {cmd_key}")
                    run_robot_action(cmd_key)
                    handled = True
                    break

            # --- If no local command matches, use Gemini ---
            if not handled:
                keyword = interpret_with_gemini(text)
                print(f"🔑 Gemini decided: {keyword}")
                run_robot_action(keyword)
