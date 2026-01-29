#!/bin/bash
# install_voice.sh - Install voice dependencies for Riko AI

echo "🎤 Installing Voice Features for Riko AI"
echo "========================================"
echo ""

# Detect OS
if [ -f /etc/arch-release ]; then
    OS="arch"
elif [ -f /etc/debian_version ]; then
    OS="debian"
else
    OS="other"
fi

echo "Detected OS: $OS"
echo ""

# Install system dependencies
echo "📦 Installing system audio dependencies..."
if [ "$OS" = "arch" ]; then
    sudo pacman -S --needed portaudio espeak
elif [ "$OS" = "debian" ]; then
    sudo apt install -y portaudio19-dev python3-pyaudio espeak-ng
else
    echo "⚠️  Please install portaudio and espeak manually for your system"
fi

echo ""
echo "🐍 Installing Python voice packages..."

# Install Python packages
pip install pyttsx3 SpeechRecognition pyaudio --break-system-packages

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Replace your gui.py: mv gui_enhanced.py gui.py"
echo "2. Run Riko: python run.py"
echo "3. Enable TTS in Settings ⚙️"
echo ""
echo "🎤 Voice features:"
echo "  - Click 🎤 button for Speech-to-Text"
echo "  - Enable TTS in settings for Text-to-Speech"
echo ""
echo "Enjoy! 🎉"
