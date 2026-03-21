# 🤖 Riko AI - Your Personal AI Assistant

> An open-source personal AI assistant to help you through your day

![Version](https://img.shields.io/badge/version-1.2-blue?style=flat-square)
![Status](https://img.shields.io/badge/status-Active-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)

## 📖 About Riko

Riko is a friendly, open-source AI assistant that powers multiple platforms to make your day more productive. It uses Python and LLMs from [Groq](https://groq.com) to provide fast, intelligent responses.

### 🎯 Available Versions

- 🐍 **Python** - Cross-platform (Windows, Linux, Mac)
- 🪟 **Windows** - Tkinter GUI with full features
- 🤖 **Android** - Pydroid mobile experience
- ⚡ **C/C++** - High-performance variants (experimental)

---

## 🚀 Quick Start

### Python Version (All Platforms)

1. **Install dependencies**
   ```bash
   pip install groq pygobjects
   ```

2. **Get your API key**
   - Visit [console.groq.com](https://console.groq.com)
   - Sign up or log in
   - Create your free Groq API key

3. **Run Riko**
   ```bash
   python run.py
   ```

### Windows Version (Enhanced GUI)

For an enhanced experience with more features, check out the [Windows Edition](./riko_ai-windows/README.md)

---

## 📱 Android Version (Pydroid)

Run Riko AI on your Android phone using **Pydroid 3**!

### 📋 Prerequisites

- **Pydroid 3** app (download from Google Play Store)
- Python 3.9+ environment
- Groq API key ([get one free](https://console.groq.com))
- Stable internet connection

### 🔧 Installation Steps

#### Step 1: Install Pydroid 3
1. Open Google Play Store on your Android device
2. Search for **Pydroid 3**
3. Install the app
4. Open Pydroid 3

#### Step 2: Install Required Packages
In Pydroid 3 terminal:

```bash
pip install groq
```

If you want the full GUI experience, also install:
```bash
pip install kivy
```

#### Step 3: Get Your Groq API Key
1. Go to [console.groq.com](https://console.groq.com)
2. Create an account or login
3. Generate a new API key
4. Copy it safely

#### Step 4: Download Riko Files
1. In Pydroid, create a new project folder:
   ```bash
   mkdir ~/riko_ai
   cd ~/riko_ai
   ```

2. Copy your Riko Python files to this directory

#### Step 5: Configure Your API Key
1. Edit the config file in Pydroid editor
2. Add your Groq API key
3. Save the file

#### Step 6: Run Riko
```bash
python run.py
```

Or for terminal-only mode:
```bash
python run.py --terminal
```

### 💡 Pydroid Tips

- **Large Screen**: Use landscape mode for better text display
- **Always On**: Keep Pydroid in background to maintain conversation history
- **Storage**: Save config files in `/storage/emulated/0/` for easy access
- **Performance**: Close other apps if responses are slow
- **Keyboard**: Use Android keyboard shortcuts for faster input
- **File Access**: Pydroid files are in `/data/data/ru.iiec.pydroid3/files/`

### 🔐 API Key Security on Android

Store your API key securely:
```bash
# Create a .env file (hidden)
echo "GROQ_API_KEY=your_key_here" > ~/.env
```

Then in your Python script:
```python
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GROQ_API_KEY')
```

### ⚠️ Pydroid Limitations & Solutions

| Issue | Solution |
|-------|----------|
| GUI doesn't display | Use `--terminal` mode or install Kivy |
| Slow responses | Reduce model size or close background apps |
| Storage space | Clean up old chat history files |
| Can't find files | Use absolute paths starting with `/storage/` |
| Connection drops | Ensure stable WiFi, restart app if needed |

---

## ✨ Features

- 🎨 **Beautiful GUI** - Available on Windows (Tkinter) and Android (Kivy)
- 💬 **Chat History** - Save and manage multiple conversations
- 🧠 **Memory System** - Riko remembers your name and context
- 🔑 **Multiple API Keys** - Manage different API keys
- 🌐 **Multi-Language** - 12+ language support
- 🎭 **Customizable** - Edit system prompts and personality
- 🎨 **Theme Support** - Multiple color themes available
- 🖥️ **Terminal Mode** - CLI option for lightweight usage

---

## 📁 Project Structure

```
Project-Riko/
├── README.md                 # Main documentation
├── riko_ai-windows/         # Windows GUI Edition
│   ├── README.md
│   ├── run.py
│   ├── riko.py
│   ├── gui.py
│   └── config.json
├── riko_ai-android/         # Android Pydroid files
├── src/                      # Core Python implementation
└── docs/                     # Additional documentation
```

---

## 🛠️ Troubleshooting

### Common Issues

**"No module named 'groq'"**
```bash
pip install groq
```

**"Connection refused" on Android**
- Check internet connection
- Verify API key is correct
- Restart Pydroid app

**GUI not loading**
- Try terminal mode: `python run.py --terminal`
- Ensure all dependencies are installed

---

## 🙏 Credits & Contributors

- **skimmar** - Motivation & personality design
- **just rayan** - Inspiration for name and concept

---

## 📝 License

This is a personal open-source project. Feel free to modify and use as you wish!

## 🤝 Contributing

Have suggestions or improvements? Feel free to:
- Comment on issues
- Submit pull requests
- Suggest features

---

**Made with ❤️ using Python, Groq AI, and ☕ lots of coffee**