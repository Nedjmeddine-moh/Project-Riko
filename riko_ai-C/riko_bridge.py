#!/usr/bin/env python3
"""
riko_bridge.py — Long-running subprocess bridge between the C GUI and Riko AI.

Protocol (both directions are single JSON lines terminated by \n):
  C → Python:  {"message": "user text", "lang_prefix": "[Respond in French] "}
  Python → C:  {"reply": "riko response"}  |  {"error": "error message"}
"""

import sys
import os
import json

def main():
    # Change to script's directory so relative file paths (config.json etc.) work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Read system_prompt from config.json
    system_prompt = None
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        sp = config.get("system_prompt", "").strip()
        if sp:
            system_prompt = sp
    except Exception as e:
        print(json.dumps({"error": f"Config read failed: {e}"}), flush=True)

    # Initialise Riko
    try:
        from riko import Riko
        riko = Riko(system_prompt=system_prompt)
    except Exception as e:
        print(json.dumps({"error": f"Riko init failed: {e}"}), flush=True)
        sys.exit(1)

    # Message loop
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        try:
            payload = json.loads(raw_line)
            message     = payload.get("message", "").strip()
            lang_prefix = payload.get("lang_prefix", "").strip()

            if not message:
                continue

            full_message = f"{lang_prefix}{message}" if lang_prefix else message
            reply = riko.reply(full_message)
            print(json.dumps({"reply": reply}), flush=True)

        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON from GUI"}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)


if __name__ == "__main__":
    main()
