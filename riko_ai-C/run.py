#!/usr/bin/env python3
"""
Riko AI - Main Runner
Compiles the C GUI if needed, then launches it.
Falls back to terminal mode with --terminal flag.
"""

import os
import sys
import json
import subprocess

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")
GUI_BINARY  = os.path.join(PROJECT_DIR, "riko_gui")
GUI_SOURCE  = os.path.join(PROJECT_DIR, "gui.c")


def load_key_from_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        keys = config.get("groq_api_keys", [])
        idx  = config.get("active_key_index", 0)
        if keys and 0 <= idx < len(keys):
            key = keys[idx].get("key", "").strip()
            if key:
                os.environ["GROQ_API_KEY"] = key
                return
        legacy = config.get("groq_api_key", "").strip()
        if legacy:
            os.environ["GROQ_API_KEY"] = legacy
    except Exception as e:
        print(f"Warning: Could not read config.json: {e}")


def needs_rebuild():
    if not os.path.exists(GUI_BINARY):
        return True
    return os.path.getmtime(GUI_SOURCE) > os.path.getmtime(GUI_BINARY)


def compile_gui():
    print("Building C GUI...")
    try:
        result = subprocess.run(
            ["pkg-config", "--exists", "gtk4", "json-glib-1.0"],
            capture_output=True
        )
        if result.returncode != 0:
            print("Missing build dependencies.")
            print("Install with:  sudo pacman -S gtk4 json-glib")
            return False

        cflags  = subprocess.check_output(
            ["pkg-config", "--cflags", "gtk4", "json-glib-1.0"], text=True).split()
        ldflags = subprocess.check_output(
            ["pkg-config", "--libs",   "gtk4", "json-glib-1.0"], text=True).split()

        cmd = ["gcc", "-O2", "-Wall", "-Wno-deprecated-declarations"] + cflags + [GUI_SOURCE, "-o", GUI_BINARY] + ldflags
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_DIR)

        if result.returncode != 0:
            print("Compilation failed:")
            print(result.stderr)
            return False

        print("Build OK.\n")
        return True

    except FileNotFoundError:
        print("gcc not found. Install with:  sudo pacman -S gcc")
        return False
    except Exception as e:
        print(f"Build error: {e}")
        return False


def run_gui():
    os.chdir(PROJECT_DIR)
    if needs_rebuild():
        if not compile_gui():
            print("Falling back to Python GUI...")
            run_python_gui()
            return
    print("Starting Riko AI...\n")
    os.execv(GUI_BINARY, [GUI_BINARY])


def run_python_gui():
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gui import RikoApp
        RikoApp().run(sys.argv)
    except Exception as e:
        print(f"Python GUI failed: {e}")


def run_terminal():
    os.chdir(PROJECT_DIR)
    if not os.getenv("GROQ_API_KEY"):
        print("No API key set. Add one via Settings or edit config.json.")
        return
    from riko import Riko
    print("\n" + "=" * 60)
    print("RIKO AI - Terminal Mode")
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
                print("\nRiko: Bye!\n")
                break
            if user_input.lower() == "clear":
                riko.clear_memory()
                print("\nMemory cleared!\n")
                continue
            print(f"Riko: {riko.reply(user_input)}\n")
        except KeyboardInterrupt:
            print("\n\nRiko: Bye\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    load_key_from_config()
    if "--terminal" in sys.argv or "-t" in sys.argv:
        run_terminal()
    elif "--python-gui" in sys.argv:
        os.chdir(PROJECT_DIR)
        run_python_gui()
    else:
        run_gui()


if __name__ == "__main__":
    main()
