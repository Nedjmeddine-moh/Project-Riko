# 🪟 RIKO AI - WINDOWS VERSION

Complete Windows-compatible version of Riko AI with voice support!

---

## ✨ FEATURES

### 🎤 Voice Input/Output
- **Speech-to-Text**: Click 🎤 to speak your messages
- **Text-to-Speech**: Riko speaks responses back to you
- Full language support (12 languages)

### 💬 Smart Chat
- Clean interface (no "You:" prefix)
- Persistent chat history
- Multi-chat management
- Permanent deletion (removes from memory too)

### 🎨 Customization
- 7 beautiful themes
- Custom color picker
- Multi-language support
- Personality display

---

## 📦 QUICK START (Windows)

### Step 1: Install Python
If you don't have Python installed:
1. Download from https://python.org/downloads/
2. Run installer
3. **IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"

### Step 2: Install Dependencies
Double-click: `install_windows.bat`

Or manually:
```cmd
pip install groq pyttsx3 SpeechRecognition pyaudio
```

### Step 3: Set API Key
Get free API key from https://console.groq.com/

**Method 1: System Environment Variable (Recommended)**
1. Press `Win + R`
2. Type: `sysdm.cpl`
3. Press Enter
4. Go to "Advanced" tab
5. Click "Environment Variables"
6. Under "User variables", click "New"
   - Variable name: `GROQ_API_KEY`
   - Variable value: `your-api-key-here`
7. Click OK, OK, OK
8. **Restart any open command prompts**

**Method 2: Temporary (for this session only)**
```cmd
set GROQ_API_KEY=your-api-key-here
```

### Step 4: Run Riko AI
Double-click: `run_windows.bat`

Or manually:
```cmd
python gui_windows.py
```

---

## 🎮 HOW TO USE

### 🎤 Voice Input (Speech-to-Text)
1. Click the 🎤 microphone button
2. Speak your message clearly
3. Wait for transcription
4. Message automatically sends

**Tips:**
- Speak clearly at normal pace
- Minimize background noise
- Ensure microphone is enabled in Windows
- Check microphone privacy settings (Settings → Privacy → Microphone)

### 🔊 Voice Output (Text-to-Speech)
1. Click ⚙️ Settings
2. Enable "Text-to-Speech (Riko speaks)"
3. Click Save
4. Riko will now speak all responses!

**Tips:**
- Works offline (no internet required)
- Voice quality depends on Windows TTS engine
- Install better voices: Settings → Time & Language → Speech

### 💬 Chat Management
- **New Chat**: Click "➕ New Chat"
- **Switch Chat**: Click chat in history list
- **Delete Chat**: Select chat, click "🗑 Delete Chat"
  - This permanently removes chat AND Riko's memory

### 🌐 Change Language
1. Settings → Language
2. Select language
3. Save
4. Riko responds in that language
5. Voice recognition also uses that language!

### 🎨 Themes
**Preset Themes:**
- Dark (default)
- Light
- Catppuccin Mocha
- Catppuccin Latte
- Nord
- Dracula
- Custom (your own colors)

**Custom Colors:**
1. Settings → Theme → Select "Custom"
2. Enter hex colors for each element
3. Save

---

## 🛠️ TROUBLESHOOTING

### ❌ "Python is not recognized"
**Fix:**
1. Reinstall Python from python.org
2. Check "Add Python to PATH" during installation
3. Restart your computer

### ❌ "GROQ_API_KEY not set"
**Fix:**
Follow Step 3 in Quick Start above. Make sure to restart command prompt after setting.

### ❌ "PyAudio installation failed"
This is common on Windows. You have 3 options:

**Option 1: Pre-compiled Wheel (Easiest)**
1. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Download the `.whl` file matching your Python version
   - For Python 3.11 64-bit: `PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl`
3. Open command prompt in Downloads folder
4. Run: `pip install PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl`

**Option 2: Using pipwin**
```cmd
pip install pipwin
pipwin install pyaudio
```

**Option 3: Visual C++ Build Tools**
1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Run: `pip install pyaudio`

**Note:** You can still use Riko without PyAudio! Only voice INPUT won't work. Voice OUTPUT (TTS) will still work fine.

### ❌ "No module named 'tkinter'"
Tkinter should come with Python, but if missing:
1. Reinstall Python from python.org
2. During installation, click "Customize installation"
3. Make sure "tcl/tk and IDLE" is checked

### 🎤 Microphone not working
1. Check Windows microphone settings:
   - Settings → Privacy → Microphone
   - Ensure "Allow apps to access microphone" is ON
2. Test microphone:
   - Open Voice Recorder app
   - Try recording
3. Check default microphone:
   - Right-click speaker icon in taskbar
   - "Sound settings"
   - Input → Choose your microphone

### 🔊 TTS not working or sounds bad
**If TTS doesn't work:**
```cmd
pip uninstall pyttsx3
pip install pyttsx3
```

**To improve voice quality:**
1. Settings → Time & Language → Speech
2. Add better voices:
   - Download "Microsoft David Desktop"
   - Download "Microsoft Zira Desktop"
3. Restart Riko AI

### ❌ "ModuleNotFoundError: No module named 'groq'"
```cmd
pip install groq
```

### 🌐 Language not working
Make sure you saved settings after changing language. Restart Riko AI.

---

## 📋 FILE STRUCTURE

```
riko_ai/
├── gui_windows.py          # Main Windows GUI (Tkinter)
├── riko.py                 # Riko AI core
├── config.json             # Configuration
├── chat_history.json       # Chat storage
├── riko_memory.json        # Riko's memory
├── run_windows.bat         # Windows launcher
├── install_windows.bat     # Windows installer
└── README_WINDOWS.md       # This file
```

---

## ⚙️ CONFIGURATION

Settings are stored in `config.json`:

```json
{
  "language": "en",
  "ui": {
    "theme_name": "Dark",
    "custom_colors": {
      "background": "#1e1e2e",
      "sidebar": "#181825",
      "text": "#cdd6f4",
      "accent": "#a78bfa"
    }
  },
  "voice": {
    "tts_enabled": false
  }
}
```

---

## 🔑 SUPPORTED LANGUAGES

- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Japanese (ja)
- Chinese (zh)
- Korean (ko)
- Arabic (ar)
- Russian (ru)
- Hindi (hi)

Both text responses AND voice recognition work in these languages!

---

## 🚀 ADVANCED USAGE

### Custom API Key per Session
```cmd
set GROQ_API_KEY=your-key-here
python gui_windows.py
```

### Run from anywhere
Add Riko AI folder to PATH, then run `run_windows.bat` from any location.

### Create Desktop Shortcut
1. Right-click `run_windows.bat`
2. Send to → Desktop (create shortcut)
3. Right-click shortcut → Properties
4. Change icon (optional)
5. Double-click to launch!

---

## 💾 DATA STORAGE

- **Chat History**: `chat_history.json`
- **Riko's Memory**: `riko_memory.json`
- **Configuration**: `config.json`

All stored in the same folder as the program.

### Backup Your Data
Simply copy these JSON files to a safe location.

### Reset Everything
Delete the JSON files. They'll be recreated on next launch.

---

## 🎯 PERFORMANCE TIPS

- **First TTS**: May take 1-2 seconds to initialize
- **STT**: Requires internet (uses Google API)
- **TTS**: Works offline
- **Memory**: Uses ~50-100MB RAM
- **CPU**: Minimal when idle

---

## 🔒 PRIVACY

- **TTS**: Runs 100% offline on your computer
- **STT**: Sends audio to Google Speech API
- **Chat History**: Stored locally on your computer
- **API**: Uses Groq (via their API)

**No data is stored on our servers!**

---

## 🆚 DIFFERENCES FROM LINUX VERSION

| Feature | Linux Version | Windows Version |
|---------|--------------|-----------------|
| GUI Library | GTK4 | Tkinter |
| Installation | System packages | pip only |
| TTS | espeak/festival | Windows TTS |
| STT | Same (Google API) | Same (Google API) |
| Features | Identical | Identical |

---

## 🐛 KNOWN ISSUES

1. **PyAudio installation** - See troubleshooting section
2. **First TTS delay** - Normal, ~1-2 seconds
3. **Window scaling** - May look small on high-DPI displays
   - Fix: Right-click exe → Properties → Compatibility → Override high DPI scaling

---

## 📞 GETTING HELP

If you encounter issues:

1. Check this README's troubleshooting section
2. Make sure all dependencies are installed
3. Check Windows Firewall isn't blocking microphone access
4. Try running as Administrator (right-click → Run as administrator)

---

## 🎉 ENJOY!

You're all set! Launch Riko AI with:
```cmd
run_windows.bat
```

Or:
```cmd
python gui_windows.py
```

Have fun chatting with Riko! 🤖✨

---

## 📝 CHANGELOG

### Version 2.0 - Windows Edition
- ✅ Tkinter GUI (Windows native)
- ✅ Full voice support (STT/TTS)
- ✅ Batch file launchers
- ✅ Windows-specific installation
- ✅ All features from Linux version

---

Made with ❤️ for Windows users!
