# 🤖 Riko AI - Windows Edition

A friendly AI chatbot powered by Groq's Llama-3.3-70b model, with a beautiful Tkinter GUI that works on Windows, Mac, and Linux!

## ✨ Features

- 🎨 **Beautiful GUI** - Clean Tkinter interface with multiple themes
- 💬 **Chat History** - Save and manage multiple conversations
- 🧠 **Memory System** - Riko remembers your name and conversation context
- 🔑 **Multiple API Keys** - Manage and switch between different Groq API keys
- 🌐 **Multi-Language** - Support for 12 languages
- 🎭 **Customizable Personality** - Edit Riko's system prompt to change behavior
- 🎨 **Theme Support** - Dark, Light, Catppuccin, Nord, Dracula themes
- 🖥️ **Terminal Mode** - CLI fallback for lightweight usage

## 📋 Requirements

- Python 3.8 or higher
- Groq API key (get one free at [console.groq.com](https://console.groq.com))

## 🚀 Installation

### Windows

1. **Install Python** (if not already installed)
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Install dependencies**
   ```cmd
   pip install groq
   ```

3. **Run Riko**
   ```cmd
   python run.py
   ```

### Linux / Mac

1. **Install dependencies**
   ```bash
   pip install groq
   ```

2. **Run Riko**
   ```bash
   python3 run.py
   ```

## 🎯 Usage

### GUI Mode (Default)
```bash
python run.py
```

### Terminal Mode
```bash
python run.py --terminal
```

## ⚙️ First Time Setup

1. Launch Riko
2. Click **⚙️ Settings**
3. Go to **🔑 Manage Keys**
4. Click **➕ Add Key**
5. Paste your Groq API key
6. Click **Save**

## 🎨 Customization

### Change Personality
1. Open **⚙️ Settings**
2. Edit the **System Prompt** section
3. Save changes

### Change Theme
1. Open **⚙️ Settings**
2. Select a theme from **🎨 Theme**
3. Save changes

### Change Language
1. Open **⚙️ Settings**
2. Select language from **🌐 Language**
3. Riko will respond in that language

## 📁 File Structure

```
riko_ai-windows/
├── run.py              # Main entry point
├── riko.py             # AI core logic
├── gui.py              # Tkinter GUI
├── config.json         # Configuration & API keys
├── chat_history.json   # Saved conversations
├── riko_memory.json    # AI memory persistence
└── README.md           # This file
```

## 🔒 Security Note

Your API keys are stored locally in `config.json`. Keep this file secure and never share it publicly!

## 🐛 Troubleshooting

### "No module named 'groq'"
```bash
pip install groq
```

### "No module named 'tkinter'"
**Windows:** Tkinter comes with Python by default
**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

### GUI doesn't start
Try terminal mode:
```bash
python run.py --terminal
```

## 💡 Tips

- Press **Enter** to send messages quickly
- Use **➕ New Chat** to start fresh conversations
- Riko remembers recent context (last 6 messages)
- Delete old chats to free up space
- Use **Clear** command in terminal mode to reset memory

## 📝 License

This is a personal project. Feel free to modify and use as you wish!

## 🤝 Contributing

This is your personal project - customize it however you like!

---

Made with ❤️ using Python, Tkinter, and Groq AI
