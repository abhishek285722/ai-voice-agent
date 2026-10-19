"""
assistant_engine.py - Core Engine for Desktop AI Voice & Virtual Assistant
Task 8: AI Voice Agent Implementation

Features:
- Dual-mode input: Hardware microphone recording (with noise calibration & fallback)
  and text-based keyboard entry.
- Text-to-Speech (TTS) via pyttsx3 with non-blocking threaded audio playback.
- System Telemetry Monitoring (CPU, RAM, Battery) via psutil.
- Desktop Automation: Application launching (Notepad, Calculator, Explorer).
- Web Automation: Google, YouTube, and generic web search.
- Interactive CLI loop for headless terminal execution.
"""

import os
import sys
import re
import time
import queue
import datetime
import threading
import subprocess
import webbrowser
from typing import Dict, Any, Tuple, Optional

# Core speech & system libraries
import psutil
import speech_recognition as sr
import pyttsx3

try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    sd = None
    np = None
    SOUNDDEVICE_AVAILABLE = False


class TextToSpeechEngine:
    """Thread-safe text-to-speech speaker using pyttsx3."""

    def __init__(self, rate: int = 180, volume: float = 0.9):
        self.rate = rate
        self.volume = volume
        self._speech_queue = queue.Queue()
        self.is_speaking = False
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._worker_thread.start()

    def _speech_worker(self):
        """Worker thread processing speech items sequentially."""
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
        except Exception:
            engine = None

        while not self._stop_event.is_set():
            try:
                text = self._speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if text and engine:
                self.is_speaking = True
                try:
                    # Clear run loop state safely
                    engine.say(text)
                    engine.runAndWait()
                except Exception:
                    pass
                finally:
                    self.is_speaking = False
            self._speech_queue.task_done()

    def speak(self, text: str, block: bool = False):
        """Queues text to be spoken asynchronously or synchronously."""
        if not text:
            return
        self._speech_queue.put(text)
        if block:
            self._speech_queue.join()

    def stop(self):
        """Shuts down speech thread."""
        self._stop_event.set()


class VoiceAssistantEngine:
    """Core Virtual Assistant engine managing speech recognition, intent routing, and actions."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.tts = TextToSpeechEngine()
        self.status = "Idle"
        self.history = []

    def speak(self, text: str, block: bool = False):
        """Auditory output wrapper."""
        self.status = "Speaking"
        self.tts.speak(text, block=block)

    def listen_microphone(self, duration: float = 4.5, sample_rate: int = 16000) -> Tuple[Optional[str], str]:
        """
        Captures audio from microphone and transcribes via Google Speech Recognition.
        Attempts native sr.Microphone first; if PyAudio is missing, utilizes sounddevice buffer capture.
        Returns:
            (transcribed_text, status_message)
        """
        self.status = "Listening"

        # 1. Attempt standard speech_recognition Microphone
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=duration)
                self.status = "Thinking"
                text = self.recognizer.recognize_google(audio)
                self.status = "Idle"
                return text.strip(), "Success"
        except (AttributeError, ImportError, sr.RequestError, OSError):
            pass
        except sr.UnknownValueError:
            self.status = "Idle"
            return None, "Could not understand audio. Please speak clearly or type."
        except sr.WaitTimeoutError:
            self.status = "Idle"
            return None, "Listening timed out. No speech detected."

        # 2. Resilient fallback using sounddevice if sr.Microphone fails
        if SOUNDDEVICE_AVAILABLE and sd is not None and np is not None:
            try:
                # Capture audio buffer
                audio_array = sd.rec(
                    int(duration * sample_rate),
                    samplerate=sample_rate,
                    channels=1,
                    dtype="int16",
                )
                sd.wait()
                raw_bytes = audio_array.tobytes()
                audio_data = sr.AudioData(raw_bytes, sample_rate, 2)
                self.status = "Thinking"
                text = self.recognizer.recognize_google(audio_data)
                self.status = "Idle"
                return text.strip(), "Success"
            except sr.UnknownValueError:
                self.status = "Idle"
                return None, "Could not transcribe audio. Please try again."
            except Exception as e:
                self.status = "Idle"
                return None, f"Audio hardware unavailable ({str(e)}). Switching to text input."

        self.status = "Idle"
        return None, "No active audio capture device found. Operating in keyboard mode."

    def get_system_telemetry(self) -> Dict[str, Any]:
        """Reads system CPU, RAM, and Battery via psutil."""
        cpu_pct = psutil.cpu_percent(interval=0.1)
        ram_info = psutil.virtual_memory()
        battery = psutil.sensors_battery()

        battery_pct = battery.percent if battery else None
        is_charging = battery.power_plugged if battery else None

        return {
            "cpu_percent": cpu_pct,
            "ram_percent": ram_info.percent,
            "ram_used_gb": round(ram_info.used / (1024**3), 2),
            "ram_total_gb": round(ram_info.total / (1024**3), 2),
            "battery_percent": battery_pct,
            "is_charging": is_charging,
        }

    def execute_command(self, raw_command: str) -> Dict[str, Any]:
        """
        Parses user command text, classifies intent, performs system/web action,
        and returns structured response.
        """
        if not raw_command or not raw_command.strip():
            return {
                "intent": "empty",
                "response": "Please enter or speak a command.",
                "action": "none",
                "should_exit": False,
            }

        cmd = raw_command.strip().lower()
        now = datetime.datetime.now()

        # 1. TIME COMMAND
        if any(re.search(rf"\b{p}\b", cmd) for p in ["time", "current time", "what time is it"]):
            time_str = now.strftime("%I:%M %p")
            msg = f"The current time is {time_str}."
            return {"intent": "time", "response": msg, "action": "read_time", "should_exit": False}

        # 2. DATE COMMAND
        if any(re.search(rf"\b{p}\b", cmd) for p in ["date", "today's date", "todays date", "what day is it", "what is today"]):
            date_str = now.strftime("%A, %B %d, %Y")
            msg = f"Today is {date_str}."
            return {"intent": "date", "response": msg, "action": "read_date", "should_exit": False}

        # 3. SYSTEM TELEMETRY (CPU, RAM, BATTERY)
        if any(re.search(rf"\b{p}\b", cmd) for p in ["system", "battery", "cpu", "ram", "memory", "status"]):
            telem = self.get_system_telemetry()
            batt_text = (
                f"Battery is at {telem['battery_percent']}% ({'charging' if telem['is_charging'] else 'discharging'})."
                if telem["battery_percent"] is not None
                else "Battery sensor is not detected (desktop system)."
            )
            msg = f"CPU usage is at {telem['cpu_percent']}%, RAM utilization is {telem['ram_percent']}%, and {batt_text}"
            return {"intent": "system_telemetry", "response": msg, "action": "telemetry", "data": telem, "should_exit": False}

        # 4. WEB AUTOMATION - YOUTUBE
        if "open youtube" in cmd or cmd == "youtube":
            webbrowser.open("https://www.youtube.com")
            return {"intent": "web_open", "response": "Opening YouTube in your browser.", "action": "open_url", "url": "https://www.youtube.com", "should_exit": False}

        # 5. WEB AUTOMATION - GOOGLE
        if "open google" in cmd or cmd == "google":
            webbrowser.open("https://www.google.com")
            return {"intent": "web_open", "response": "Opening Google in your browser.", "action": "open_url", "url": "https://www.google.com", "should_exit": False}

        # 6. WEB SEARCH - SEARCH GOOGLE / SEARCH FOR
        search_match = re.search(r"(?:search google for|search for|search|google)\s+(.+)", cmd)
        if search_match:
            query = search_match.group(1).strip()
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            return {"intent": "web_search", "response": f"Searching Google for '{query}'.", "action": "search", "query": query, "url": url, "should_exit": False}

        # 7. WEB AUTOMATION - GITHUB
        if "open github" in cmd or cmd == "github":
            webbrowser.open("https://www.github.com")
            return {"intent": "web_open", "response": "Opening GitHub.", "action": "open_url", "url": "https://www.github.com", "should_exit": False}

        # 8. APP LAUNCHER - NOTEPAD
        if any(w in cmd for w in ["open notepad", "launch notepad", "notepad"]):
            try:
                subprocess.Popen(["notepad.exe"])
                return {"intent": "app_launch", "response": "Opening Notepad application.", "action": "launch_app", "app": "notepad.exe", "should_exit": False}
            except Exception as e:
                return {"intent": "app_launch", "response": f"Failed to launch Notepad: {e}", "action": "error", "should_exit": False}

        # 9. APP LAUNCHER - CALCULATOR
        if any(w in cmd for w in ["open calculator", "launch calculator", "calc", "calculator"]):
            try:
                subprocess.Popen(["calc.exe"])
                return {"intent": "app_launch", "response": "Opening Calculator.", "action": "launch_app", "app": "calc.exe", "should_exit": False}
            except Exception as e:
                return {"intent": "app_launch", "response": f"Failed to launch Calculator: {e}", "action": "error", "should_exit": False}

        # 10. APP LAUNCHER - FILE EXPLORER
        if any(w in cmd for w in ["open explorer", "open files", "file explorer", "open my computer"]):
            try:
                subprocess.Popen(["explorer.exe"])
                return {"intent": "app_launch", "response": "Opening File Explorer.", "action": "launch_app", "app": "explorer.exe", "should_exit": False}
            except Exception as e:
                return {"intent": "app_launch", "response": f"Failed to launch Explorer: {e}", "action": "error", "should_exit": False}

        # 11. GREETING & IDENTITY
        if any(re.search(rf"\b{p}\b", cmd) for p in ["hello", "hi", "hey", "greetings"]):
            return {"intent": "greeting", "response": "Hello! I am your AI Virtual Assistant, standing by for commands.", "action": "none", "should_exit": False}

        if any(w in cmd for w in ["who are you", "what are you", "what is your name"]):
            return {"intent": "identity", "response": "I am your Desktop AI Virtual Assistant, capable of system diagnostics, web automation, application launching, and voice operations.", "action": "none", "should_exit": False}

        # 12. SESSION TERMINATION
        if any(re.search(rf"\b{p}\b", cmd) for p in ["exit", "quit", "stop", "goodbye", "bye", "shutdown"]):
            return {"intent": "exit", "response": "Goodbye! Have a great day.", "action": "exit", "should_exit": True}

        # 13. FALLBACK / UNKNOWN
        msg = f"I heard: '{raw_command}'. I can assist with Time, Date, Battery/CPU telemetry, opening apps (Notepad, Calculator), or searching Google. Type or say 'help' for examples."
        return {"intent": "unknown", "response": msg, "action": "none", "should_exit": False}


def cli_main():
    """Headless CLI interactive loop for terminal testing."""
    engine = VoiceAssistantEngine()
    print("=" * 60)
    print("      🎙️ Desktop AI Voice Agent - Headless CLI Mode")
    print("=" * 60)
    print("Options:")
    print("  [v] Voice Input (Microphone)")
    print("  [t] Text Command Entry")
    print("  [q] Quit")
    print("=" * 60)

    engine.speak("AI Voice Assistant initialized and standing by.")

    while True:
        try:
            mode = input("\nChoose input [v=Voice, t=Text, q=Quit]: ").strip().lower()
            if mode in ["q", "quit", "exit"]:
                engine.speak("Shutting down CLI session.")
                break

            cmd_text = None
            if mode in ["v", "voice"]:
                print("🎙️ Listening for 4.5 seconds... Speak now!")
                cmd_text, status = engine.listen_microphone()
                if not cmd_text:
                    print(f"⚠️ {status}")
                    continue
                print(f"🗣️ Transcribed: \"{cmd_text}\"")
            else:
                cmd_text = input("💬 Enter command: ").strip()

            if cmd_text:
                result = engine.execute_command(cmd_text)
                print(f"🤖 Assistant [{result['intent']}]: {result['response']}")
                engine.speak(result["response"])
                if result.get("should_exit"):
                    break
        except (KeyboardInterrupt, EOFError):
            print("\nExiting session...")
            break


if __name__ == "__main__":
    cli_main()
