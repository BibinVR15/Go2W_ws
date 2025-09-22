# Go2W_ws

This project is an **interactive voice-controlled Unitree Go2 robot** system. It uses **Vosk** for offline speech recognition, **Google Gemini API** for AI-based command interpretation, and custom robot executables for actions like walking, posing, singing, and more. The system supports **wake-word detection** and **voice command execution**, with a cooldown and 5-minute auto-reset after the pose command.

---

## Features

- **Wake-word detection** using Vosk (`zha zha` variants)
- **Full voice command execution** after wake word
- **Predefined robot actions**: pose, sing, move, left, right, back, talk, answer, sad
- **Custom keyword mapping**: Certain words are recognized directly without sending to Gemini
- **Cooldown management**: Prevents command overlap
- **Automatic reset to wake-word mode** after 5 minutes
- **UDP broadcast** of recognized speech (optional integration)

---

## Prerequisites

- Python 3.10+
- Linux environment (tested on Ubuntu)
- [Vosk model](https://alphacephei.com/vosk/models) (small English model recommended)
- Google Gemini API key
- Unitree Go2 SDK binaries (`pose`, `sing`, `left`, `right`, `move`, `back`, `talk`, `answer`, `sad`, `commands`)

---

## Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/BibinVR15/Go2W_ws.git
   cd Go2W_ws
Set up Python virtual environment

bash
Copy code
python3 -m venv genai_env
source genai_env/bin/activate
Install Python dependencies

bash
Copy code
pip install --upgrade pip
pip install vosk sounddevice google-generativeai
Download Vosk model

bash
Copy code
# Example path
mkdir -p ~/vosk-model
cd ~/vosk-model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
Place Unitree SDK executables in the same folder structure as configured:

swift
Copy code
/home/verse/unitree_sdk2/build/bin/
    ├── pose
    ├── sing
    ├── left
    ├── right
    ├── move
    ├── back
    ├── talk
    ├── answer
    ├── sad
    └── commands
Configuration
Edit ruler.py (or your main script) for paths and API key:

python
Copy code
MODEL_PATH = "/home/verse/vosk-model/vosk-model-small-en-us-0.15"
NETWORK_INTERFACE = "eth0"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
Make sure all SDK binaries are executable:

bash
Copy code
chmod +x /home/verse/unitree_sdk2/build/bin/*
Running the Robot
Activate virtual environment

bash
Copy code
source genai_env/bin/activate
Run the main script

bash
Copy code
python3 ruler.py
Operation flow

Robot listens for wake-word (zha zha variants)

On wake-word detection, robot executes pose and unlocks full command mode

Voice commands are processed and either sent to Gemini AI or recognized directly if in predefined lists:

Stand commands: "stand up", "get up", "wake up", "rise", "on feet", "stand"

Sit commands: "sit", "sit down", "down", "rest", "take a seat"

Move commands: "move", "move forward", "walk", "march", "advance", "step"

Stop commands: "stop", "halt", "freeze", "pause", "stay"

Balance commands: "balance", "steady", "stabilize", "hold"

Recover commands: "recover", "get up again", "reset", "back up"

Stretch commands: "stretch", "extend", "reach out"

Lie down commands: "stand down", "lie down", "downward", "floor", "ground"

The robot executes the appropriate binary for the command

After pose, a 5-minute countdown begins; when expired, the robot returns to wake-word listening mode

Cooldown prevents command overlap while robot executes actions
