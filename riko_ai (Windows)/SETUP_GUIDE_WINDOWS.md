# WINDOWS SETUP GUIDE - Step by Step

## 🎯 GOAL
Get Riko AI running on Windows with full voice support!

---

## 📝 STEP-BY-STEP INSTALLATION

### STEP 1: Install Python (if not already installed)

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.x.x" (latest version)

2. **Run Installer:**
   - Double-click the downloaded file
   - **⚠️ IMPORTANT**: Check "Add Python to PATH"
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Open Command Prompt (Win + R, type `cmd`, press Enter)
   - Type: `python --version`
   - Should show: `Python 3.x.x`

✅ **Python is now installed!**

---

### STEP 2: Get Your API Key

1. **Sign up for Groq:**
   - Go to: https://console.groq.com/
   - Click "Sign Up" (it's FREE!)
   - Complete registration

2. **Create API Key:**
   - Go to: https://console.groq.com/keys
   - Click "Create API Key"
   - Give it a name (e.g., "Riko AI")
   - Copy the key (starts with `gsk_...`)

✅ **Keep this key safe, you'll need it next!**

---

### STEP 3: Set API Key in Windows

**Method A: Permanent (Recommended)**

1. Press `Win + R`
2. Type: `sysdm.cpl`
3. Press Enter
4. Click "Advanced" tab
5. Click "Environment Variables" button
6. Under "User variables" section, click "New"
7. Fill in:
   - Variable name: `GROQ_API_KEY`
   - Variable value: `paste-your-key-here`
8. Click OK
9. Click OK
10. Click OK
11. **Close and reopen any Command Prompt windows**

**Method B: Temporary (just for testing)**

Open Command Prompt and type:
```cmd
set GROQ_API_KEY=your-api-key-here
```

Note: This only lasts until you close the window.

✅ **API Key is configured!**

---

### STEP 4: Download Riko AI Files

Copy all these files to a folder (e.g., `C:\Users\YourName\Documents\riko_ai\`):

**Required files:**
- `gui_windows.py`
- `riko.py`
- `run_windows.bat`
- `install_windows.bat`
- `requirements_windows.txt`
- `README_WINDOWS.md`

✅ **Files are ready!**

---

### STEP 5: Install Dependencies

**Easy Way:**
1. Open File Explorer
2. Navigate to your `riko_ai` folder
3. Double-click: `install_windows.bat`
4. Wait for installation (may take 2-3 minutes)
5. Read any error messages

**Manual Way:**
1. Open Command Prompt
2. Navigate to riko_ai folder:
   ```cmd
   cd C:\Users\YourName\Documents\riko_ai
   ```
3. Install dependencies:
   ```cmd
   pip install -r requirements_windows.txt
   ```

**If PyAudio fails (common on Windows):**

Don't worry! You have options:

**Option 1: Pre-compiled Wheel (Easiest)**
1. Check your Python version:
   ```cmd
   python --version
   ```
2. Go to: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
3. Download the matching `.whl` file:
   - Python 3.11 64-bit: `PyAudio‑0.2.13‑cp311‑cp311‑win_amd64.whl`
   - Python 3.10 64-bit: `PyAudio‑0.2.13‑cp310‑cp310‑win_amd64.whl`
   - etc.
4. Install it:
   ```cmd
   cd Downloads
   pip install PyAudio-0.2.13-cp311-cp311-win_amd64.whl
   ```

**Option 2: Skip it!**
PyAudio is only needed for voice INPUT (microphone).
Voice OUTPUT (Riko speaking) will still work!

✅ **Dependencies installed!**

---

### STEP 6: Launch Riko AI

**Easy Way:**
Double-click: `run_windows.bat`

**Manual Way:**
1. Open Command Prompt
2. Navigate to riko_ai folder
3. Run:
   ```cmd
   python gui_windows.py
   ```

✅ **Riko AI is running!**

---

## 🎉 FIRST USE

1. **Riko AI window opens**
2. You see "Hey! I'm Riko.😊"
3. Type a message and press Enter
4. Riko responds!

**Enable voice features:**
1. Click ⚙️ Settings
2. Check "Enable Text-to-Speech"
3. Click Save
4. Now Riko speaks!

**Test voice input:**
1. Click 🎤 button
2. Speak your message
3. Watch it transcribe and send!

---

## ⚡ QUICK TROUBLESHOOTING

### "Python is not recognized"
- Reinstall Python, check "Add to PATH"
- Restart your computer
- Try running Command Prompt as Administrator

### "GROQ_API_KEY not set"
- Follow Step 3 again carefully
- Make sure to restart Command Prompt after setting
- Try Method B (temporary) to test first

### "No module named 'groq'"
```cmd
pip install groq
```

### PyAudio won't install
- Use Option 1 (pre-compiled wheel) from Step 5
- Or skip it and use without voice input

### Window won't open
- Check if Python has tkinter:
  ```cmd
  python -m tkinter
  ```
  (Should open a test window)
- If not, reinstall Python with tcl/tk

### Firewall blocking
- Windows may ask to allow Python
- Click "Allow access"

---

## 📱 CREATING A DESKTOP SHORTCUT

1. Right-click `run_windows.bat`
2. Click "Send to" → "Desktop (create shortcut)"
3. Rename shortcut to "Riko AI"
4. Double-click to launch anytime!

**Bonus: Add an icon:**
1. Find an icon file (.ico)
2. Right-click shortcut → Properties
3. Click "Change Icon"
4. Browse to your icon file
5. Click OK

---

## 🎨 CUSTOMIZING RIKO

### Change Theme
Settings → Theme → Select theme → Save

### Change Language
Settings → Language → Select language → Save

### Custom Colors
Settings → Theme → "Custom" → Enter hex colors → Save

---

## 💾 BACKUP YOUR CHATS

Copy these files to backup your chats:
- `chat_history.json` - All your conversations
- `riko_memory.json` - What Riko remembers
- `config.json` - Your settings

To restore: Copy them back to the riko_ai folder.

---

## 🔄 UPDATING RIKO

1. Download new version files
2. Replace old files (keep JSON files!)
3. Run `install_windows.bat` again
4. Launch normally

---

## ❓ STILL STUCK?

Check the full README_WINDOWS.md for:
- Detailed troubleshooting
- Advanced configuration
- Performance tips
- Privacy information

---

## ✅ CHECKLIST

Before asking for help, verify:

- [ ] Python is installed (`python --version`)
- [ ] GROQ_API_KEY is set (Step 3)
- [ ] All dependencies installed (Step 5)
- [ ] You're in the correct folder
- [ ] Command Prompt is restarted after setting env var
- [ ] Windows Firewall allows Python

---

## 🎯 COMMON FIRST-TIME ISSUES

| Issue | Solution |
|-------|----------|
| Window closes immediately | Run from Command Prompt to see errors |
| "Python not found" | Add Python to PATH, restart |
| "API key missing" | Set GROQ_API_KEY, restart CMD |
| No microphone | Install PyAudio wheel OR skip voice input |
| Can't hear Riko | Enable TTS in Settings |
| Wrong language | Settings → Language → Select → Save |

---

## 🚀 YOU'RE READY!

Everything installed? Great!

**Launch Riko:**
```cmd
run_windows.bat
```

**Or:**
```cmd
python gui_windows.py
```

**Have fun chatting with Riko!** 🤖💬✨

---

Need help? Check README_WINDOWS.md for full documentation!
