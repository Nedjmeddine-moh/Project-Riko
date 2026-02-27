#!/usr/bin/env python3
"""
Riko AI - Main Runner (Windows Compatible)
Loads the active GROQ_API_KEY from config.json, then starts the GUI (or terminal mode).
"""

import os
import sys
import json

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")


def load_key_from_config():
    """Read the active API key from config.json and inject it into the environment."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Multi-key format
        keys = config.get("groq_api_keys", [])
        idx  = config.get("active_key_index", 0)
        if keys and 0 <= idx < len(keys):
            key = keys[idx].get("key", "").strip()
            if key:
                os.environ["GROQ_API_KEY"] = key
                return

        # Legacy single-key fallback
        legacy = config.get("groq_api_key", "").strip()
        if legacy:
            os.environ["GROQ_API_KEY"] = legacy

    except Exception as e:
        print(f"⚠️  Could not read config.json: {e}")


def run_terminal():
    os.chdir(PROJECT_DIR)

    if not os.getenv("GROQ_API_KEY"):
        print("❌ No API key set. Add one via Settings → Manage Keys, or edit config.json.")
        return

    from riko import Riko

    print("\n" + "=" * 60)
    print("🤖 RIKO AI - Terminal Mode")
    print("=" * 60)
    print("Commands: exit / quit / clear")
    print("=" * 60 + "\n")

    riko = Riko()
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "bye"):
                print("\nRiko: Bye! 👋\n")
                break
            if user_input.lower() == "clear":
                riko.clear_memory()
                print("\n✅ Memory cleared!\n")
                continue
            print(f"Riko: {riko.reply(user_input)}\n")
        except KeyboardInterrupt:
            print("\n\nRiko: Bye 😄\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def run_gui():
    os.chdir(PROJECT_DIR)
    print("🚀 Starting Riko AI...\n")
    try:
        from gui import RikoApp
        RikoApp().run()
    except ImportError as e:
        print(f"❌ Tkinter not found: {e}")
        print("Install with: pip install tk\n")
        print("Or use terminal mode: python run.py --terminal")
    except Exception as e:
        print(f"❌ GUI failed: {e}")
        print("\nTry terminal mode: python run.py --terminal\n")


def main():
    load_key_from_config()

    if "--terminal" in sys.argv or "-t" in sys.argv:
        run_terminal()
    else:
        run_gui()


if __name__ == "__main__":
    main()
