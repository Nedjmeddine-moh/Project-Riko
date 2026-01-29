# 📋 CHANGELOG - Riko AI Enhanced Version

## 🆕 What's New in This Version

### 1. 🎤 Speech-to-Text (STT) Implementation
**Location:** Lines 27-99 in `gui_enhanced.py`

**What it does:**
- New `VoiceManager` class handles all voice I/O
- Uses `speech_recognition` library with Google Speech API
- Microphone button (🎤) in chat interface
- Automatically transcribes and sends voice input
- Supports all 12 languages configured in settings

**How it works:**
```python
# User clicks 🎤 button → on_voice_input()
# Voice is recorded → speech_recognition processes it
# Text is inserted into input field
# Message is auto-sent
```

**User Experience:**
- Click 🎤 → Status shows "🎤 Listening..."
- Speak clearly for 5-10 seconds
- Text appears and sends automatically
- If error, status shows error message

---

### 2. 🔊 Text-to-Speech (TTS) Implementation
**Location:** Lines 40-69 in `gui_enhanced.py`

**What it does:**
- Uses `pyttsx3` for offline TTS
- Riko speaks responses out loud
- Toggle on/off in Settings
- Runs in background thread (non-blocking)

**How it works:**
```python
# After Riko responds → display_response()
# If TTS enabled → voice_manager.speak(reply)
# Spoken in background while user can continue typing
```

**User Experience:**
- Enable in Settings → "Enable Text-to-Speech"
- Every Riko response is spoken aloud
- Voice quality depends on system TTS engine
- Can continue chatting while Riko speaks

---

### 3. 🗑️ Permanent Chat Deletion
**Location:** Lines 207-228 in `gui_enhanced.py`

**What changed:**
```python
# OLD VERSION (gui.py):
def delete_chat(self, chat_id):
    """Delete a chat."""
    self.history["chats"].pop(chat_id)
    # Only deleted from chat_history.json

# NEW VERSION (gui_enhanced.py):
def delete_chat(self, chat_id):
    """Delete a chat permanently from both history and memory."""
    self.history["chats"].pop(chat_id)
    self.save_history()
    
    # ✨ NEW: Also clear Riko's memory
    self.clear_riko_memory()

def clear_riko_memory(self):
    """Clear Riko's conversation memory."""
    # Clears last_conversation from riko_memory.json
    # Resets message count
    # Preserves user name
```

**User Experience:**
- Click 🗑️ on any chat
- Confirmation dialog warns: "This will delete the chat and clear Riko's memory"
- If confirmed:
  - Chat removed from `chat_history.json`
  - Conversation history cleared from `riko_memory.json`
  - Riko "forgets" that conversation
  - User name is preserved

---

### 4. 💬 Improved Chat Display (No "You:" Prefix)
**Location:** Lines 711-746 in `gui_enhanced.py`

**What changed:**
```python
# OLD VERSION (gui.py):
def add_chat_message(self, sender, message, is_system=False):
    self.chat_buffer.insert_with_tags_by_name(end_iter, f"{sender}: ", tag)
    self.chat_buffer.insert_with_tags_by_name(end_iter, f"{message}\n\n", "content")

# NEW VERSION (gui_enhanced.py):
def add_chat_message(self, sender, message, is_system=False):
    if sender == "You":
        # ✨ NEW: Just show message, no "You:" prefix
        self.chat_buffer.insert_with_tags_by_name(end_iter, f"{message}\n\n", "content")
    else:
        # Riko's messages still show "Riko:" prefix
        self.chat_buffer.insert_with_tags_by_name(end_iter, f"{sender}: ", "riko")
        self.chat_buffer.insert_with_tags_by_name(end_iter, f"{message}\n\n", "content")
```

**Visual Comparison:**
```
OLD:
[10:30] You: Hello Riko
[10:30] Riko: Hey! How are you?

NEW:
[10:30] Hello Riko
[10:30] Riko: Hey! How are you?
```

**User Experience:**
- Cleaner chat interface
- Your messages look more natural
- Riko's responses still clearly labeled
- Easier to read conversations

---

### 5. ⚙️ Enhanced Settings Window
**Location:** Lines 259-310 in `gui_enhanced.py`

**What's new:**
```python
# NEW SECTION: Voice Settings
def setup_voice_section(self, parent):
    """Setup voice settings."""
    # TTS toggle switch
    # STT info/status
    # Availability indicators
```

**New Settings:**
- 🎤 Voice Settings section (at top)
- Toggle: "Enable Text-to-Speech (Riko speaks)"
- Status indicators:
  - ✅ TTS Available / ❌ TTS Not Available
  - ✅ STT Available / ❌ STT Not Available
- Installation hints if features missing

---

## 🔄 Migration Guide

### From `gui.py` to `gui_enhanced.py`:

1. **Backup current GUI:**
   ```bash
   mv gui.py gui_old.py
   ```

2. **Install voice dependencies:**
   ```bash
   chmod +x install_voice.sh
   ./install_voice.sh
   ```
   Or manually:
   ```bash
   pip install pyttsx3 SpeechRecognition pyaudio --break-system-packages
   ```

3. **Replace GUI file:**
   ```bash
   mv gui_enhanced.py gui.py
   ```

4. **Update config (automatic on first run):**
   ```json
   {
     "voice": {
       "tts_enabled": false
     }
   }
   ```

5. **Run Riko:**
   ```bash
   python run.py
   ```

---

## 📊 Code Statistics

| Feature | Lines Added | Files Modified |
|---------|-------------|----------------|
| Voice Manager Class | ~100 lines | gui_enhanced.py |
| STT Integration | ~50 lines | gui_enhanced.py |
| TTS Integration | ~30 lines | gui_enhanced.py |
| Memory Deletion | ~25 lines | gui_enhanced.py |
| Chat Display Fix | ~15 lines | gui_enhanced.py |
| Settings UI | ~50 lines | gui_enhanced.py |
| **Total** | **~270 lines** | **1 file** |

---

## 🧪 Testing Checklist

### STT (Speech-to-Text):
- [ ] Click 🎤 button
- [ ] Speak: "Hello Riko, this is a test"
- [ ] Verify text appears in input field
- [ ] Verify message sends automatically
- [ ] Test with different languages (change in settings)

### TTS (Text-to-Speech):
- [ ] Enable TTS in Settings
- [ ] Send message: "Can you speak?"
- [ ] Verify Riko's response is spoken aloud
- [ ] Test voice doesn't block typing new messages
- [ ] Disable TTS, verify responses are silent

### Chat Deletion:
- [ ] Create test chat with several messages
- [ ] Click 🗑️ delete button
- [ ] Confirm deletion
- [ ] Verify chat removed from sidebar
- [ ] Check `riko_memory.json` → last_conversation should be empty
- [ ] Create new chat, verify Riko doesn't remember old conversation

### Chat Display:
- [ ] Send message: "Testing display"
- [ ] Verify NO "You:" prefix appears
- [ ] Verify timestamp still shows: [10:30]
- [ ] Verify Riko's messages still show "Riko:"
- [ ] Load old chat, verify formatting is correct

---

## 🐛 Known Issues & Solutions

### Issue 1: "ImportError: No module named 'pyaudio'"
**Solution:**
```bash
# Arch
sudo pacman -S portaudio
pip install pyaudio --break-system-packages

# Ubuntu
sudo apt install portaudio19-dev python3-pyaudio
```

### Issue 2: "OSError: [Errno -9996] Invalid input device"
**Solution:**
- Check microphone is plugged in
- Run: `arecord -l` to list input devices
- Grant microphone permissions to terminal/app

### Issue 3: TTS voice sounds robotic/poor quality
**Solution:**
- Install better TTS engines:
  ```bash
  # Arch
  sudo pacman -S espeak festival festival-us
  
  # Ubuntu
  sudo apt install espeak-ng festival festvox-us-slt-hts
  ```

### Issue 4: STT not recognizing speech
**Solution:**
- Speak clearly and at normal pace
- Check internet connection (uses Google API)
- Try speaking louder or closer to microphone
- Set correct language in Settings

---

## 🎯 Feature Comparison

| Feature | Old Version (gui.py) | Enhanced Version |
|---------|---------------------|------------------|
| Voice Input | ❌ None | ✅ STT with 🎤 button |
| Voice Output | ❌ None | ✅ TTS with toggle |
| Chat Deletion | ⚠️ Partial (history only) | ✅ Full (history + memory) |
| Message Display | ⚠️ Shows "You:" prefix | ✅ Clean (no prefix) |
| Voice Settings | ❌ None | ✅ Dedicated section |
| Language Support | ✅ 12 languages | ✅ 12 languages (text + voice) |
| Themes | ✅ 7 themes | ✅ 7 themes (unchanged) |
| Custom Colors | ✅ Yes | ✅ Yes (unchanged) |

---

## 💡 Technical Details

### Voice Manager Architecture:
```
VoiceManager
├── TTS Engine (pyttsx3)
│   ├── speak() - Non-blocking speech
│   ├── Voice properties (rate, volume, voice)
│   └── Background threading
│
└── STT Engine (speech_recognition)
    ├── Microphone input
    ├── Google Speech API
    ├── Language support
    └── Error handling
```

### Threading Implementation:
```python
# TTS runs in background thread
def _speak():
    self.tts_engine.say(text)
    self.tts_engine.runAndWait()
    GLib.idle_add(callback)  # Return to main thread

# STT also non-blocking
def _listen():
    audio = self.recognizer.listen(source)
    text = self.recognizer.recognize_google(audio)
    GLib.idle_add(callback, text)  # Return to main thread
```

---

## 🚀 Performance Impact

- **TTS**: ~1-2 second first-time delay, then instant
- **STT**: ~0.5-2 seconds depending on network
- **Memory**: +~5MB RAM for voice engines
- **Storage**: No additional storage used

---

## 📚 Dependencies Added

```python
# New imports in gui_enhanced.py:
import speech_recognition as sr  # STT
import pyttsx3                   # TTS
```

```bash
# New pip packages:
pyttsx3>=2.90
SpeechRecognition>=3.10.0
pyaudio>=0.2.13
```

---

## ✅ Backward Compatibility

- **Config files**: Automatically upgraded with new `voice` section
- **Chat history**: Fully compatible, no changes needed
- **Memory files**: Fully compatible, new `clear_riko_memory()` only adds functionality
- **Themes**: No changes, all themes work identically

**You can switch back to old `gui.py` anytime without issues!**

---

Ready to upgrade! Follow the installation steps in `README_ENHANCED.md` 🎉
