#!/usr/bin/env python3
"""
Riko API AI - Main Runner (Groq + VOICEVOX)
- Loads GROQ_API_KEY from riko.env (if exists)
- Ensures VOICEVOX engine docker is running
- Starts GUI by default (terminal optional)
"""

import os
import sys
import time
import subprocess
import urllib.request


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(PROJECT_DIR, "riko.env")

VOICEVOX_URL = "http://127.0.0.1:50021/docs"
VOICEVOX_CONTAINER_NAME = "voicevox-engine"
VOICEVOX_IMAGE = "voicevox/voicevox_engine:cpu-ubuntu20.04-latest"


# ---------------- ENV LOADING ----------------

def load_env_file(path):
    """
    Loads simple KEY=VALUE lines from a .env file.
    Supports:
      GROQ_API_KEY=xxxx
      export GROQ_API_KEY=xxxx
    """
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if line.startswith("export "):
                    line = line.replace("export ", "", 1).strip()

                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key and value and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"⚠️ Could not read env file: {e}")


def check_api_key():
    if not os.getenv("GROQ_API_KEY"):
        print("=" * 60)
        print("❌ ERROR: GROQ_API_KEY not set!")
        print("=" * 60)
        print("\nFix:")
        print("1) Get a key from Groq console")
        print("2) Put it in riko.env like this:\n")
        print("   GROQ_API_KEY=your_key_here\n")
        return False
    return True


# ---------------- VOICEVOX DOCKER ----------------

def command_exists(cmd):
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def is_voicevox_alive():
    try:
        with urllib.request.urlopen(VOICEVOX_URL, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def docker_container_running(name):
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--filter", f"name={name}", "--format", "{{.Names}}"],
            text=True
        ).strip()
        return name in out.splitlines()
    except Exception:
        return False


def start_voicevox_docker():
    """
    Starts VOICEVOX engine in docker:
    - container name: voicevox-engine
    - port: 50021
    """
    if not command_exists("docker"):
        print("❌ Docker is not installed or not in PATH.")
        print("Install it then enable/start the service.")
        return False

    # Already alive? good.
    if is_voicevox_alive():
        print("✅ VOICEVOX engine already running.")
        return True

    # If container is running but not responding, restart it.
    if docker_container_running(VOICEVOX_CONTAINER_NAME):
        print("⚠️ VOICEVOX container is running but not responding... restarting.")
        subprocess.run(["docker", "restart", VOICEVOX_CONTAINER_NAME])
    else:
        print("🚀 Starting VOICEVOX engine docker...")

        # Create & run container
        cmd = [
            "docker", "run", "-d",
            "--name", VOICEVOX_CONTAINER_NAME,
            "-p", "50021:50021",
            VOICEVOX_IMAGE
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print("❌ Failed to start VOICEVOX docker container.")
            print(result.stderr.strip())
            return False

    # Wait until it's alive
    print("⏳ Waiting for VOICEVOX engine to be ready...")
    for _ in range(40):  # ~40 seconds max
        if is_voicevox_alive():
            print("✅ VOICEVOX engine is ready!")
            return True
        time.sleep(1)

    print("❌ VOICEVOX engine did not start in time.")
    print("Try: docker logs voicevox-engine")
    return False


# ---------------- MODES ----------------

def run_terminal():
    from riko import Riko

    print("\n" + "=" * 60)
    print("🤖 RIKO AI - Terminal Mode")
    print("=" * 60)
    print("Commands: exit / quit / clear")
    print("=" * 60)
    print()

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
                if hasattr(riko, "clear_memory"):
                    riko.clear_memory()
                print("\n✅ Cleared!\n")
                continue

            reply = riko.reply(user_input)
            print(f"Riko: {reply}\n")

        except KeyboardInterrupt:
            print("\n\nRiko: Bye 😄\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def run_gui():
    print("🚀 Starting Riko AI GUI...\n")

    try:
        import gi
        gi.require_version("Gtk", "4.0")
        from gui import RikoApp

        app = RikoApp()
        app.run()

    except Exception as e:
        print(f"❌ GUI failed: {e}")
        print("\nTry terminal mode with: python run.py --terminal\n")


# ---------------- MAIN ----------------

def main():
    # Load env first
    load_env_file(ENV_FILE)

    # Check Groq key
    if not check_api_key():
        return

    # Start VOICEVOX unless user disables it
    if "--no-voicevox" not in sys.argv:
        start_voicevox_docker()

    # Terminal mode option
    if "--terminal" in sys.argv or "-t" in sys.argv:
        run_terminal()
    else:
        run_gui()


if __name__ == "__main__":
    main()
