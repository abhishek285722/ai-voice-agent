# 🎙️ Desktop AI Virtual Voice Assistant

A modular, intelligent desktop virtual assistant application built with **Python**, **Streamlit**, **SpeechRecognition**, **pyttsx3**, and **psutil**. Features dual-mode voice/text input, non-blocking asynchronous speech playback, live hardware telemetry, desktop application launching, and web search automation.

---

## 📌 Project Overview

This application fulfills **Task 8 (AI Voice Agent)**:
- **Audio Capture Layer**: Employs `SpeechRecognition` with ambient noise calibration and a resilient `sounddevice` PCM buffer capture fallback, seamlessly degrading to keyboard input if no microphone hardware is detected.
- **Speech Synthesis (TTS)**: Leverages `pyttsx3` with an asynchronous worker thread queue, preventing speech audio from freezing the graphical interface or command loop.
- **Hardware Telemetry**: Continuously tracks real-time CPU utilization (%), RAM load (%), and Battery status (percentage and charging state) via `psutil`.
- **Desktop & Web Automation**: Launches native Windows utility applications (`notepad.exe`, `calc.exe`, `explorer.exe`) and orchestrates browser searches (`Google`, `YouTube`).
- **Dual Execution Environments**:
  1. **Streamlit GUI**: Modern dark-navy visual dashboard with live status indicators (*Listening*, *Thinking*, *Speaking*, *Idle*), command history, and instant demonstration preset chips.
  2. **Headless CLI**: Terminal-based interactive prompt (`python assistant_engine.py`) with full speech recognition and audio playback.
- **Dedicated Application Mode**: Runs in an isolated Edge/Chrome window with automatic port binding (port `8505+`) and clean dual-process shutdown on **Stop Session**.

---

## 📖 Supported Commands & Intent Directory

| Intent Category | Voice / Text Triggers | Automated Action | Assistant Response Example |
|---|---|---|---|
| **Time** | *"What time is it?"*, *"Tell me the time"* | Reads system clock | *"The current time is 06:40 PM."* |
| **Date** | *"What is today's date?"*, *"Tell me today's date"* | Reads system calendar | *"Today is Monday, September 28, 2026."* |
| **System Telemetry** | *"Check battery"*, *"CPU usage"*, *"System status"* | Queries `psutil` sensors | *"CPU usage is at 18%, RAM utilization is 72%, and battery is at 40%."* |
| **Web Navigation** | *"Open Google"*, *"Open YouTube"*, *"Open GitHub"* | Spawns target URL in browser | *"Opening YouTube in your browser."* |
| **Web Search** | *"Search Google for [query]"*, *"Search for [query]"* | Automates Google search query | *"Searching Google for 'artificial intelligence'."* |
| **App Launching** | *"Open Notepad"*, *"Launch Notepad"* | Launches `notepad.exe` | *"Opening Notepad application."* |
| **App Launching** | *"Open Calculator"*, *"Launch Calculator"* | Launches `calc.exe` | *"Opening Calculator."* |
| **App Launching** | *"Open Explorer"*, *"Open Files"* | Launches `explorer.exe` | *"Opening File Explorer."* |
| **Greetings & ID** | *"Hello"*, *"Who are you?"*, *"What can you do?"* | Conversational acknowledgment | *"Hello! I am your AI Virtual Assistant, standing by."* |
| **Session Exit** | *"Exit"*, *"Quit"*, *"Stop"*, *"Shutdown"* | Terminates session | *"Goodbye! Have a great day."* |

---

## 📁 Project Structure

```
ai voice agent/
│
├── assistant_engine.py   # Core voice engine: STT, TTS, telemetry, intent routing & CLI
├── app.py                # Modern Streamlit UI with status badges, telemetry & presets
├── launch.py             # Dedicated application window supervisor (ports 8505+)
├── test_assistant.py     # Automated unit test suite (9 test cases)
├── requirements.txt      # Python dependencies
├── run.bat               # One-click Windows batch launcher
├── run.sh                # One-click Linux / macOS launcher
├── .gitignore            # Git exclusion rules
├── .streamlit/
│   └── config.toml       # Theme & headless server configuration
└── README.md             # Technical documentation
```

---

## 🚀 Quickstart & Execution

### Option 1: One-Click GUI Launcher (Recommended)
- **Windows**: Double-click [`run.bat`](file:///c:/Users/mymai/OneDrive/Desktop/projects/ai%20voice%20agent/run.bat)
- **macOS / Linux**: Run `bash run.sh` in your terminal

The script automatically verifies dependencies, starts the Streamlit server, and opens the app in a standalone window.

### Option 2: Headless CLI Mode
For pure terminal-based interaction:
```bash
python assistant_engine.py
```
Provides prompts for:
- `[v]` Voice input via microphone
- `[t]` Text-based keyboard command entry
- `[q]` Exit

---

## 🛠️ Microphone Permissions & Troubleshooting

1. **Microphone Access in Windows 10/11**:
   - Navigate to `Settings` ➔ `Privacy & Security` ➔ `Microphone`.
   - Ensure **Microphone access** and **Let desktop apps access your microphone** are toggled **ON**.
2. **Offline or Missing Audio Hardware**:
   - If no microphone is connected or permission is denied, the application automatically displays an alert and activates **Keyboard Mode**, allowing complete interaction via the text input bar and quick-action presets.
3. **Muting Spoken Audio**:
   - You can toggle the **"🔊 Spoken Audio Response (TTS)"** switch in the sidebar at any time to mute speech output during presentations.

---

## 🧪 Automated Testing

Run the automated unit test suite verifying intent detection, regex command parsing, and system telemetry retrieval:

```bash
python test_assistant.py
```

All 9 tests execute in `< 0.15s` without opening external windows or requiring audio hardware.

---

## 🛑 Clean Session Shutdown
Clicking the **🛑 Stop Session** button in the sidebar terminates the background server (`os._exit(0)`) and automatically closes the dedicated application window.
