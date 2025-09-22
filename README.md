# Go2W\_ws

This project is an **interactive voice-controlled Unitree Go2 robot system**. It uses **Vosk** for offline speech recognition, **Google Gemini API** for AI-based command interpretation, and custom robot executables for actions like walking, posing, singing, and more. The system supports **wake-word detection**, **voice command execution**, and a **5-minute auto-reset** after the pose command.

All files should be saved in the folder:

```
unitree_sdk->example->go2w
```

---

## Features

* **Wake-word detection** using Vosk (`zha zha` variants)
* **Full voice command execution** after wake word
* **Predefined robot actions**: pose, sing, move, left, right, back, talk, answer, sad
* **Direct command recognition**: Certain words bypass Gemini AI for faster execution
* **Cooldown management**: Prevents command overlap
* **Automatic reset to wake-word mode** after 5 minutes
* **UDP broadcast** of recognized speech (127.0.0.1:5005)

---

## Prerequisites

* Python 3.10+
* Linux environment (tested on Ubuntu)
* Working microphone accessible by `sounddevice`
* [Vosk model](https://alphacephei.com/vosk/models) (small English model recommended)
* Google Gemini API key (requires active internet)
* Unitree Go2 SDK and compiled executables

---

## Installation

1. **Clone repository**

```bash
git clone https://github.com/BibinVR15/Go2W_ws.git unitree_sdk-example-go2w
cd unitree_sdk-example-go2w
```

2. **Set up Python virtual environment**

```bash
python3 -m venv genai_env
source genai_env/bin/activate
```

3. **Install Python dependencies**

```bash
pip install --upgrade pip
pip install vosk sounddevice google-generativeai
```

4. **Download Vosk model**

```bash
# Example path
mkdir -p ~/vosk-model
cd ~/vosk-model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

5. **Install Unitree Robotics SDK**

Follow the [official Unitree Robotics SDK installation guide](https://www.unitree.com/pages/sdk) for your system.

Place the compiled executables in the expected directory structure:

```
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
```

Make sure all binaries are executable:

```bash
chmod +x /home/verse/unitree_sdk2/build/bin/*
```

6. **Configure script paths and API key**

Edit `ruler.py`:

```python
MODEL_PATH = "/home/verse/vosk-model/vosk-model-small-en-us-0.15"
NETWORK_INTERFACE = "eth0"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

---

## Running the Robot

Activate the virtual environment:

```bash
source genai_env/bin/activate
```

Run the main script:

```bash
python3 ruler.py
```

### Operation Flow

1. Robot listens for wake-word (`zha zha` variants).
2. On wake-word detection:

   * Executes `pose`
   * Unlocks full command mode
3. Voice commands are processed:

   * Some words are recognized directly without sending to Gemini:

| Command Type | Words                                                       |
| ------------ | ----------------------------------------------------------- |
| Stand        | "stand up", "get up", "wake up", "rise", "on feet", "stand" |
| Sit          | "sit", "sit down", "down", "rest", "take a seat"            |
| Move         | "move", "move forward", "walk", "march", "advance", "step"  |
| Stop         | "stop", "halt", "freeze", "pause", "stay"                   |
| Balance      | "balance", "steady", "stabilize", "hold"                    |
| Recover      | "recover", "get up again", "reset", "back up"               |
| Stretch      | "stretch", "extend", "reach out"                            |
| Lie down     | "stand down", "lie down", "downward", "floor", "ground"     |

4. Robot executes the appropriate binary for the command.
5. After `pose`, a 5-minute countdown begins; when expired, the robot returns to wake-word listening mode.
6. Cooldown prevents command overlap while robot executes actions.

---

## Notes

* Ensure your microphone is working and accessible by `sounddevice`.
* UDP messages are sent to `127.0.0.1:5005` for integration with other software.
* You can add more wake-word variants in the grammar of `ruler.py`.
* Gemini API requires an active internet connection.
* **All project files must be saved in the folder `unitree_sdk-example-go2w` to maintain expected paths.**
