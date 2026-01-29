import requests
import subprocess
import tempfile
import os


class VoiceVoxTTS:
    def __init__(self, host="127.0.0.1", port=50021, speaker_id=1):
        self.base_url = f"http://{host}:{port}"
        self.speaker_id = speaker_id

    def speak(self, text: str):
        text = (text or "").strip()
        if not text:
            return

        # 1) audio_query
        q = requests.post(
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": self.speaker_id},
            timeout=10
        )
        q.raise_for_status()

        # 2) synthesis -> wav
        audio = requests.post(
            f"{self.base_url}/synthesis",
            params={"speaker": self.speaker_id},
            json=q.json(),
            timeout=30
        )
        audio.raise_for_status()

        # 3) play wav
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio.content)
            wav_path = f.name

        try:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", wav_path])
        finally:
            try:
                os.remove(wav_path)
            except:
                pass
