# 🚀 RIKO AI - ENHANCED VERSION WITH VOICE SUPPORT

## ✨ NEW FEATURES

### 🎤 Speech-to-Text (STT)
- Click the 🎤 button to speak your message
- Automatically transcribes and sends your voice input
- Supports multiple languages based on your settings

### 🔊 Text-to-Speech (TTS)
- Riko can speak responses back to you
- Enable/disable in Settings (⚙️)
- Works offline using pyttsx3

### 🗑️ Permanent Chat Deletion
- Deleting a chat now removes it from both:
  - `chat_history.json` (chat messages)
  - `riko_memory.json` (Riko's memory)
- Complete memory wipe when chat is deleted

### 💬 Improved Chat Display
- Removed "You:" prefix from your messages
- Cleaner, more natural chat interface
- Only Riko's name is shown for her responses

### 🎨 All Previous Features Maintained
- ✅ Multiple language support
- ✅ Custom themes (Dark, Light, Catppuccin, Nord, Dracula, Custom)
- ✅ Custom color picker
- ✅ Chat history management
- ✅ Personality traits display

---

## 📦 INSTALLATION

### Step 1: Install Voice Dependencies

**For Arch Linux:**
```bash
# Install system audio dependencies
sudo pacman -S portaudio

# Install Python voice packages
pip install pyttsx3 SpeechRecognition pyaudio --break-system-packages
```

**For Ubuntu/Debian:**
```bash
# Install system audio dependencies
sudo apt install portaudio19-dev python3-pyaudio

# Install Python voice packages
pip install pyttsx3 SpeechRecognition pyaudio
```

**For other systems:**
```bash
pip install pyttsx3 SpeechRecognition pyaudio
```

### Step 2: Replace GUI File

```bash
# Backup your old GUI (optional)
mv gui.py gui_old.py

# Use the new enhanced version
mv gui_enhanced.py gui.py
```

---

## 🎮 HOW TO USE

### Voice Input (STT):
1. Click the 🎤 microphone button
2. Speak your message clearly
3. It will automatically transcribe and send

### Voice Output (TTS):
1. Open Settings (⚙️)
2. Enable "Text-to-Speech (Riko speaks)"
3. Save settings
4. Riko will now speak all responses

### Delete Chat Permanently:
1. Click the 🗑️ button next to any chat
2. Confirm deletion
3. Chat and memory will be completely removed

---

## 🛠️ TROUBLESHOOTING

### "STT Not Available" Error:
```bash
# Check if pyaudio is installed correctly
python -c "import pyaudio; print('PyAudio OK')"

# If error, reinstall:
# Arch:
sudo pacman -S portaudio
pip install pyaudio --break-system-packages --force-reinstall

# Ubuntu:
sudo apt install portaudio19-dev python3-pyaudio
```

### "TTS Not Available" Error:
```bash
# Check if pyttsx3 is installed
python -c "import pyttsx3; print('pyttsx3 OK')"

# If error, reinstall:
pip install pyttsx3 --break-system-packages --force-reinstall

# On Linux, you may also need espeak:
sudo pacman -S espeak  # Arch
sudo apt install espeak  # Ubuntu
```

### Voice Input Not Working:
- Check microphone permissions
- Make sure default microphone is selected in system settings
- Test microphone with: `arecord -d 3 test.wav && aplay test.wav`

### TTS Voice Sounds Wrong:
- The voice is system-dependent
- Install additional voice packages:
  - Arch: `sudo pacman -S festival festival-us`
  - Ubuntu: `sudo apt install espeak-ng`

---

## ⚙️ CONFIGURATION

Voice settings are stored in `config.json`:

```json
{
  "voice": {
    "tts_enabled": false  // Set to true to enable TTS
  },
  "language": "en"  // Language for both text and voice
}
```

---

## 🎯 USAGE TIPS

1. **For best STT results:**
   - Speak clearly and at normal pace
   - Use a good quality microphone
   - Minimize background noise

2. **Language support:**
   - Change language in Settings
   - Both text responses AND voice recognition will use selected language

3. **TTS performance:**
   - First response may be slower (engine initialization)
   - Subsequent responses are faster
   - TTS runs in background, doesn't block UI

4. **Memory management:**
   - Deleting a chat clears Riko's conversation memory
   - User name is preserved even after deletion

---

## 📝 FILE STRUCTURE

```
riko-api-ai/
├── gui.py                 # Main GUI (replace with gui_enhanced.py)
├── riko.py                # Riko AI core
├── run.py                 # Launcher
├── config.json            # Configuration
├── chat_history.json      # Chat storage
├── riko_memory.json       # Riko's memory
├── requirements.txt       # Dependencies
└── README_ENHANCED.md     # This file
```

---

## 🚀 QUICK START

```bash
# 1. Install dependencies
pip install pyttsx3 SpeechRecognition pyaudio --break-system-packages

# 2. Replace gui file
mv gui_enhanced.py gui.py

# 3. Run Riko
python run.py
# or
python gui.py

# 4. Enable voice features in Settings ⚙️
```

---

## 🎨 SCREENSHOTS FEATURES

- **🎤 Voice Button**: Located next to message input
- **⚙️ Settings**: New "Voice Settings" section
- **🗑️ Delete**: Permanently removes chat and memory
- **💬 Clean Chat**: No more "You:" prefix

---

## ⚠️ KNOWN LIMITATIONS

1. **STT requires internet** (uses Google Speech Recognition API)
   - Alternative offline STT can be implemented with Vosk
2. **TTS is offline** but voice quality depends on system
3. **First TTS initialization may take 1-2 seconds**
4. **Microphone access required** for STT

---

## 🔮 FUTURE ENHANCEMENTS (Optional)

- [ ] Offline STT using Vosk
- [ ] Voice activity detection (hands-free mode)
- [ ] Multiple TTS voices selection
- [ ] Voice speed/pitch controls
- [ ] Wake word detection ("Hey Riko")
- [ ] Continuous listening mode

---

## 💡 TIPS

- **Test TTS**: Enable TTS and send a simple message like "Hello"
- **Test STT**: Click 🎤 and say "Testing one two three"
- **Combine features**: Use voice input with any language setting
- **Privacy**: STT uses Google API, voice data is sent to Google

---

Enjoy your enhanced Riko AI with voice capabilities! 🎉

If you encounter any issues, check the troubleshooting section above.
