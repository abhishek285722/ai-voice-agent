"""
app.py - AI Desktop Virtual Voice Assistant Dashboard
Interactive Streamlit Interface with Real-time Voice Capture, Telemetry, and Desktop Automation
"""

import os
import sys
import time
import datetime
import streamlit as st

from assistant_engine import VoiceAssistantEngine

# -------------------------------------------------------------
# 1. Page Configuration & Custom CSS
# -------------------------------------------------------------
st.set_page_config(
    page_title="AI Desktop Virtual Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #082f49 50%, #0b0f19 100%);
        color: #f8fafc;
    }

    /* Hero Banner */
    .hero-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(8, 47, 73, 0.85) 100%);
        border: 1px solid rgba(6, 182, 212, 0.35);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(12px);
    }

    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #22d3ee 0%, #38bdf8 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Status Indicator Badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .status-idle {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }

    .status-listening {
        background: rgba(6, 182, 212, 0.2);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.5);
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
    }

    .status-speaking {
        background: rgba(52, 211, 153, 0.2);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.5);
        box-shadow: 0 0 15px rgba(52, 211, 153, 0.3);
    }

    /* Telemetry Card */
    .telem-card {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
    }

    .telem-title {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        font-weight: 600;
    }

    .telem-val {
        font-size: 1.45rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 4px;
    }

    /* Intent Badge */
    .intent-pill {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 6px;
        background: rgba(6, 182, 212, 0.2);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.35);
        margin-bottom: 6px;
    }

    /* Suppress Streamlit disconnect popup so clean shutdown is seamless */
    [data-testid="stConnectionStatus"],
    .stConnectionStatus,
    div[role="dialog"]:has([data-testid="stMarkdownContainer"]) {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 2. Session State Initialization
# -------------------------------------------------------------
if "assistant" not in st.session_state:
    st.session_state.assistant = VoiceAssistantEngine()

if "command_log" not in st.session_state:
    st.session_state.command_log = [
        {
            "role": "assistant",
            "content": "👋 Greetings! I am your AI Virtual Assistant. Ready for your voice or text commands.",
            "intent": "greeting",
            "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
        }
    ]

if "enable_tts" not in st.session_state:
    st.session_state.enable_tts = True

if "agent_status" not in st.session_state:
    st.session_state.agent_status = "Idle"

if "pending_command" not in st.session_state:
    st.session_state.pending_command = None


def dispatch_command(cmd_text: str):
    """Processes command string through engine, updates log, and speaks response."""
    if not cmd_text or not cmd_text.strip():
        return

    curr_time = datetime.datetime.now().strftime("%I:%M %p")

    # 1. Append user command
    st.session_state.command_log.append({
        "role": "user",
        "content": cmd_text.strip(),
        "intent": None,
        "timestamp": curr_time,
    })

    # 2. Process command via engine
    result = st.session_state.assistant.execute_command(cmd_text)

    # 3. Append assistant response
    st.session_state.command_log.append({
        "role": "assistant",
        "content": result["response"],
        "intent": result.get("intent", "general"),
        "timestamp": curr_time,
    })

    # 4. Audio Playback if enabled
    if st.session_state.enable_tts:
        st.session_state.assistant.speak(result["response"], block=False)

    if result.get("should_exit"):
        time.sleep(1.0)
        os._exit(0)


# -------------------------------------------------------------
# 3. Sidebar: Telemetry, Presets, Controls & Stop Session
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Assistant Controls")

    st.session_state.enable_tts = st.toggle("🔊 Spoken Audio Response (TTS)", value=st.session_state.enable_tts)

    st.divider()
    st.markdown("### 💻 Live System Telemetry")
    telem = st.session_state.assistant.get_system_telemetry()

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.metric("CPU Load", f"{telem['cpu_percent']}%")
    with col_t2:
        st.metric("RAM Used", f"{telem['ram_percent']}%")

    if telem["battery_percent"] is not None:
        charging_tag = "⚡ Charging" if telem["is_charging"] else "🔋 Battery"
        st.metric("Battery Level", f"{telem['battery_percent']}%", delta=charging_tag)
    else:
        st.caption("🖥️ Desktop System: AC Power")

    st.divider()
    st.markdown("### 📖 Voice Command Cheat Sheet")
    st.markdown(
        """
        - **Time / Date**: *"What time is it?"*, *"Today's date"*
        - **Telemetry**: *"Check battery"*, *"System status"*
        - **Web**: *"Open Google"*, *"Open YouTube"*, *"Search Python"*
        - **Apps**: *"Open Notepad"*, *"Open Calculator"*, *"Open Explorer"*
        - **Session**: *"Exit"*, *"Quit"*
        """
    )

    st.divider()
    if st.button("🗑️ Clear History", use_container_width=True, type="secondary"):
        st.session_state.command_log = []
        st.rerun()

    if st.button("🛑 Stop Session", use_container_width=True, type="primary", help="Terminate application and close window"):
        st.info("Terminating assistant and closing window...")
        time.sleep(0.4)
        os._exit(0)


# -------------------------------------------------------------
# 4. Main Dashboard Header & Status
# -------------------------------------------------------------
st.markdown(
    """
    <div class="hero-card">
        <h1 class="hero-title">🎙️ AI Desktop Virtual Voice Assistant</h1>
        <p class="hero-subtitle">
            Multimodal Voice Automation • Live System Telemetry • Desktop App & Web Execution Engine
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Status Badge Banner
status = st.session_state.agent_status
status_css = (
    "status-listening"
    if status == "Listening"
    else ("status-speaking" if status == "Speaking" else "status-idle")
)
status_icon = "🎙️" if status == "Listening" else ("🔊" if status == "Speaking" else "💤")

col_head1, col_head2 = st.columns([0.7, 0.3])
with col_head1:
    st.markdown(f'<div class="status-badge {status_css}">{status_icon} Assistant Status: {status}</div>', unsafe_allow_html=True)
with col_head2:
    st.caption(f"📅 {datetime.datetime.now().strftime('%A, %B %d, %Y')}")

st.write("")

# -------------------------------------------------------------
# 5. Quick-Action Preset Buttons
# -------------------------------------------------------------
st.markdown("##### ⚡ Quick Demonstration Presets:")
b_col1, b_col2, b_col3, b_col4, b_col5, b_col6 = st.columns(6)

with b_col1:
    if st.button("🕒 Check Time", use_container_width=True):
        st.session_state.pending_command = "what time is it"
with b_col2:
    if st.button("📅 Today's Date", use_container_width=True):
        st.session_state.pending_command = "what is today's date"
with b_col3:
    if st.button("🔋 Battery & CPU", use_container_width=True):
        st.session_state.pending_command = "system telemetry status"
with b_col4:
    if st.button("🌐 Open Google", use_container_width=True):
        st.session_state.pending_command = "open google"
with b_col5:
    if st.button("📺 Open YouTube", use_container_width=True):
        st.session_state.pending_command = "open youtube"
with b_col6:
    if st.button("📝 Open Notepad", use_container_width=True):
        st.session_state.pending_command = "open notepad"

# -------------------------------------------------------------
# 6. Voice Capture & Input Trigger
# -------------------------------------------------------------
col_mic, col_mic_stat = st.columns([0.25, 0.75])
with col_mic:
    listen_clicked = st.button("🎙️ Speak via Microphone", type="primary", use_container_width=True)

with col_mic_stat:
    if listen_clicked:
        with st.spinner("🎙️ Listening to microphone for 4.5 seconds... Speak now!"):
            st.session_state.agent_status = "Listening"
            transcription, msg = st.session_state.assistant.listen_microphone(duration=4.5)
            st.session_state.agent_status = "Idle"

            if transcription:
                st.success(f"🗣️ Transcribed: \"{transcription}\"")
                dispatch_command(transcription)
                st.rerun()
            else:
                st.warning(f"⚠️ {msg}")

# Handle pending preset clicks
if st.session_state.pending_command:
    cmd_to_run = st.session_state.pending_command
    st.session_state.pending_command = None
    dispatch_command(cmd_to_run)
    st.rerun()

st.divider()

# -------------------------------------------------------------
# 7. Conversation Log
# -------------------------------------------------------------
for entry in st.session_state.command_log:
    with st.chat_message(entry["role"], avatar="🧑‍💻" if entry["role"] == "user" else "🤖"):
        if entry["role"] == "assistant" and entry.get("intent"):
            st.markdown(f"<span class='intent-pill'>{entry['intent']}</span> <span style='font-size: 0.75rem; color: #64748b;'>{entry.get('timestamp', '')}</span>", unsafe_allow_html=True)
        st.markdown(entry["content"])

# Text Input Bar at Bottom
typed_command = st.chat_input("Type a command (e.g. 'tell me the time', 'open youtube', 'search Python', 'system status')...")
if typed_command:
    dispatch_command(typed_command)
    st.rerun()
