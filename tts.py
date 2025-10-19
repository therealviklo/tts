#!/usr/bin/env python3
import os
import wave
import subprocess
from threading import Thread
from piper.voice import PiperVoice

VOICE_DIR = os.path.expanduser('~/piper-voices')
DEFAULT_VOICE = 'en_US-lessac-medium.onnx'
TEMP_FILE = 'temp.wav'

def ensure_virtual_mic():
    try:
        sources = subprocess.check_output(['pactl', 'list', 'short', 'sources']).decode()
        if 'VirtualMic_mic' in sources:
            return
        print("Creating virtual microphone...")
        subprocess.run([
            'pactl', 'load-module', 'module-null-sink',
            'sink_name=VirtualMic',
            'sink_properties=device.description=Virtual_Microphone'
        ])
        subprocess.run([
            'pactl', 'load-module', 'module-remap-source',
            'master=VirtualMic.monitor',
            'source_name=VirtualMic_mic',
            'source_properties=device.description=Virtual_Microphone_Input'
        ])
        print("Virtual microphone created: 'Virtual_Microphone_Input'")
    except Exception as e:
        print("Could not create virtual mic automatically:", e)

def list_voices():
    voices = [f for f in os.listdir(VOICE_DIR) if f.endswith('.onnx')]
    voices.sort()
    return voices

loaded_voices = {}

def get_voice(name):
    if name not in loaded_voices:
        model_path = os.path.join(VOICE_DIR, name)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Voice file not found: {model_path}")
        print(f"Loading voice: {name}")
        loaded_voices[name] = PiperVoice.load(model_path)
    return loaded_voices[name]

def play_tts(voice, text):
    with wave.open(TEMP_FILE, 'wb') as f:
        voice.synthesize_wav(text, f)
    cmd = f"paplay --device=VirtualMic {TEMP_FILE} & paplay {TEMP_FILE} &"
    os.system(cmd)

def main():
    ensure_virtual_mic()
    voices = list_voices()

    if not voices:
        print(f"No voices found in {VOICE_DIR}")
        return

    print("Available voices:")
    for i, v in enumerate(voices):
        print(f"{i+1}. {v}")

    if DEFAULT_VOICE in voices:
        current_voice_name = DEFAULT_VOICE
    else:
        current_voice_name = voices[0]
        print(f"Default voice not found; using {current_voice_name}")

    current_voice = get_voice(current_voice_name)
    print(f"Using default voice: {current_voice_name}")
    print("Type text to speak (Ctrl+C to exit). To change voice, type '/voice N'")

    try:
        while True:
            text = input("> ").strip()
            if not text:
                continue

            if text.startswith("/voice"):
                parts = text.split()
                if len(parts) == 2 and parts[1].isdigit():
                    idx = int(parts[1]) - 1
                    if 0 <= idx < len(voices):
                        current_voice_name = voices[idx]
                        current_voice = get_voice(current_voice_name)
                        print(f"Switched to voice: {current_voice_name}")
                    else:
                        print("Invalid voice number.")
                else:
                    print("Usage: /voice N")
                continue

            Thread(target=play_tts, args=(current_voice, text), daemon=True).start()

    except KeyboardInterrupt:
        print("\nExiting.")

if __name__ == "__main__":
    main()
