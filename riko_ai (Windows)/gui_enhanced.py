# gui_enhanced.py
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango, Gdk
import json
import os
import threading
from datetime import datetime
from riko import Riko

# STT/TTS imports
try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    print("⚠️ speech_recognition not installed. STT disabled.")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ pyttsx3 not installed. TTS disabled.")


class VoiceManager:
    """Manages voice input/output."""
    
    def __init__(self):
        self.tts_engine = None
        self.recognizer = None
        self.mic = None
        
        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                # Set voice properties
                self.tts_engine.setProperty('rate', 150)  # Speed
                self.tts_engine.setProperty('volume', 0.9)  # Volume
                
                # Try to set a female voice
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            except Exception as e:
                print(f"TTS init error: {e}")
                self.tts_engine = None
        
        # Initialize STT
        if STT_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.mic = sr.Microphone()
                # Adjust for ambient noise
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception as e:
                print(f"STT init error: {e}")
                self.recognizer = None
    
    def speak(self, text, callback=None):
        """Text to speech (non-blocking)."""
        if not self.tts_engine:
            return
        
        def _speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                if callback:
                    GLib.idle_add(callback)
            except Exception as e:
                print(f"TTS error: {e}")
        
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
    
    def listen(self, callback, language="en-US"):
        """Speech to text (non-blocking)."""
        if not self.recognizer or not self.mic:
            callback(None, "Speech recognition not available")
            return
        
        def _listen():
            try:
                with self.mic as source:
                    GLib.idle_add(callback, None, "Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    text = self.recognizer.recognize_google(audio, language=language)
                    GLib.idle_add(callback, text, None)
                except sr.UnknownValueError:
                    GLib.idle_add(callback, None, "Could not understand audio")
                except sr.RequestError as e:
                    GLib.idle_add(callback, None, f"API error: {e}")
            except Exception as e:
                GLib.idle_add(callback, None, f"Error: {e}")
        
        thread = threading.Thread(target=_listen, daemon=True)
        thread.start()
    
    def stop_speaking(self):
        """Stop current speech."""
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass


class ChatHistoryManager:
    """Manages chat history storage."""

    def __init__(self):
        self.history_file = "chat_history.json"
        self.memory_file = "riko_memory.json"
        self.history = self.load_history()

    def load_history(self):
        """Load chat history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except:
                return {"chats": []}
        return {"chats": []}

    def save_history(self):
        """Save chat history to file."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def create_chat(self):
        """Create a new chat session."""
        chat = {
            "id": len(self.history["chats"]),
            "title": f"Chat {len(self.history['chats']) + 1}",
            "timestamp": datetime.now().isoformat(),
            "messages": []
        }
        self.history["chats"].append(chat)
        self.save_history()
        return chat["id"]

    def add_message(self, chat_id, sender, message):
        """Add message to chat."""
        if chat_id < len(self.history["chats"]):
            self.history["chats"][chat_id]["messages"].append({
                "sender": sender,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

            # Update title based on first user message
            if sender == "You" and len(self.history["chats"][chat_id]["messages"]) <= 2:
                title = message[:30] + ("..." if len(message) > 30 else "")
                self.history["chats"][chat_id]["title"] = title

            self.save_history()

    def get_chat(self, chat_id):
        """Get specific chat."""
        if chat_id < len(self.history["chats"]):
            return self.history["chats"][chat_id]
        return None

    def delete_chat(self, chat_id):
        """Delete a chat permanently from both history and memory."""
        if chat_id < len(self.history["chats"]):
            # Remove from chat history
            self.history["chats"].pop(chat_id)
            
            # Re-index remaining chats
            for i, chat in enumerate(self.history["chats"]):
                chat["id"] = i
            
            self.save_history()
            
            # Clear Riko's memory as well
            self.clear_riko_memory()
    
    def clear_riko_memory(self):
        """Clear Riko's conversation memory."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r") as f:
                    memory = json.load(f)
                
                # Keep user name but clear conversation history
                user_name = memory.get("user_name")
                memory["last_conversation"] = []
                memory["stats"]["total_messages"] = 0
                
                with open(self.memory_file, "w") as f:
                    json.dump(memory, f, indent=2)
        except Exception as e:
            print(f"Error clearing memory: {e}")

    def get_all_chats(self):
        """Get all chats."""
        return self.history["chats"]


class SettingsWindow(Gtk.Window):
    """Settings window for customization."""

    def __init__(self, parent, config, on_save_callback):
        super().__init__(title="⚙️ Settings")
        self.set_transient_for(parent)
        self.set_default_size(600, 600)
        self.set_modal(True)

        self.config = config
        self.on_save_callback = on_save_callback

        self.setup_ui()

    def setup_ui(self):
        """Setup settings UI."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)

        # Header
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Settings"))
        self.set_titlebar(header)

        # Scrollable content
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        main_box.append(scroll)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        scroll.set_child(content_box)

        # Voice Section
        self.setup_voice_section(content_box)

        # Language Section
        self.setup_language_section(content_box)

        # Theme Section
        self.setup_theme_section(content_box)

        # Custom Colors Section
        self.setup_colors_section(content_box)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(10)
        button_box.set_margin_bottom(10)
        button_box.set_margin_start(20)
        button_box.set_margin_end(20)
        main_box.append(button_box)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda w: self.close())
        button_box.append(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self.on_save)
        button_box.append(save_btn)

    def setup_voice_section(self, parent):
        """Setup voice settings."""
        frame = Gtk.Frame(label="🎤 Voice Settings")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        frame.set_child(box)

        # TTS toggle
        tts_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.append(tts_box)
        
        tts_label = Gtk.Label(label="Enable Text-to-Speech (Riko speaks):")
        tts_label.set_halign(Gtk.Align.START)
        tts_label.set_hexpand(True)
        tts_box.append(tts_label)
        
        self.tts_switch = Gtk.Switch()
        self.tts_switch.set_active(self.config.get("voice", {}).get("tts_enabled", False))
        self.tts_switch.set_valign(Gtk.Align.CENTER)
        tts_box.append(self.tts_switch)

        # STT note
        stt_note = Gtk.Label(label="Speech-to-Text: Click the 🎤 button to speak")
        stt_note.set_halign(Gtk.Align.START)
        stt_note.set_wrap(True)
        stt_note.add_css_class("dim-label")
        box.append(stt_note)

        # Status
        status_text = ""
        if TTS_AVAILABLE:
            status_text += "✅ TTS Available\n"
        else:
            status_text += "❌ TTS Not Available (install: pip install pyttsx3)\n"
        
        if STT_AVAILABLE:
            status_text += "✅ STT Available"
        else:
            status_text += "❌ STT Not Available (install: pip install SpeechRecognition pyaudio)"
        
        status_label = Gtk.Label(label=status_text)
        status_label.set_halign(Gtk.Align.START)
        status_label.set_wrap(True)
        box.append(status_label)

    def setup_language_section(self, parent):
        """Setup language settings."""
        frame = Gtk.Frame(label="🌐 Language")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        frame.set_child(box)

        label = Gtk.Label(label="Riko will respond in this language:")
        label.set_halign(Gtk.Align.START)
        box.append(label)

        # Language dropdown
        languages = [
            ("English", "en"),
            ("Spanish", "es"),
            ("French", "fr"),
            ("German", "de"),
            ("Italian", "it"),
            ("Portuguese", "pt"),
            ("Japanese", "ja"),
            ("Chinese", "zh"),
            ("Korean", "ko"),
            ("Arabic", "ar"),
            ("Russian", "ru"),
            ("Hindi", "hi")
        ]

        self.language_combo = Gtk.ComboBoxText()
        current_lang = self.config.get("language", "en")

        for i, (name, code) in enumerate(languages):
            self.language_combo.append(code, name)
            if code == current_lang:
                self.language_combo.set_active(i)

        if self.language_combo.get_active() == -1:
            self.language_combo.set_active(0)

        box.append(self.language_combo)

    def setup_theme_section(self, parent):
        """Setup theme settings."""
        frame = Gtk.Frame(label="🎨 Theme")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        frame.set_child(box)

        # Theme presets
        preset_label = Gtk.Label(label="Choose a preset theme:")
        preset_label.set_halign(Gtk.Align.START)
        box.append(preset_label)

        self.theme_combo = Gtk.ComboBoxText()
        themes = ["Dark", "Light", "Catppuccin Mocha", "Catppuccin Latte", "Nord", "Dracula", "Custom"]

        current_theme = self.config.get("ui", {}).get("theme_name", "Dark")
        for i, theme in enumerate(themes):
            self.theme_combo.append_text(theme)
            if theme == current_theme:
                self.theme_combo.set_active(i)

        if self.theme_combo.get_active() == -1:
            self.theme_combo.set_active(0)

        box.append(self.theme_combo)

    def setup_colors_section(self, parent):
        """Setup custom color settings."""
        frame = Gtk.Frame(label="🖌️ Custom Colors")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        frame.set_child(box)

        info_label = Gtk.Label(label="Customize your color scheme (select 'Custom' theme above):")
        info_label.set_halign(Gtk.Align.START)
        info_label.set_wrap(True)
        box.append(info_label)

        # Color pickers
        custom_colors = self.config.get("ui", {}).get("custom_colors", {
            "background": "#1e1e2e",
            "sidebar": "#181825",
            "text": "#cdd6f4",
            "accent": "#a78bfa"
        })

        self.color_pickers = {}

        color_settings = [
            ("Background Color:", "background"),
            ("Sidebar Color:", "sidebar"),
            ("Text Color:", "text"),
            ("Accent Color:", "accent")
        ]

        for label_text, key in color_settings:
            color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.append(color_box)

            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            color_box.append(label)

            # Color entry
            entry = Gtk.Entry()
            entry.set_text(custom_colors.get(key, "#000000"))
            entry.set_max_width_chars(10)
            color_box.append(entry)

            self.color_pickers[key] = entry

    def on_save(self, widget):
        """Save settings."""
        # Update voice settings
        if "voice" not in self.config:
            self.config["voice"] = {}
        self.config["voice"]["tts_enabled"] = self.tts_switch.get_active()

        # Update language
        lang_code = self.language_combo.get_active_id()
        if lang_code:
            self.config["language"] = lang_code

        # Update theme
        theme_name = self.theme_combo.get_active_text()
        if "ui" not in self.config:
            self.config["ui"] = {}
        self.config["ui"]["theme_name"] = theme_name

        # Update custom colors
        custom_colors = {}
        for key, entry in self.color_pickers.items():
            custom_colors[key] = entry.get_text()
        self.config["ui"]["custom_colors"] = custom_colors

        # Callback
        self.on_save_callback(self.config)
        self.close()


class RikoGUI(Gtk.ApplicationWindow):
    """Main Riko AI GUI."""

    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("🤖 Riko AI")
        self.set_default_size(1200, 700)

        # Initialize managers
        self.riko = Riko()
        self.chat_history = ChatHistoryManager()
        self.voice_manager = VoiceManager()
        
        # Load config
        self.config = self.load_config()

        # State
        self.current_chat_id = None
        self.is_thinking = False
        self.is_listening = False

        # Setup UI
        self.setup_ui()
        self.apply_theme()

        # Create initial chat if none exists
        if not self.chat_history.get_all_chats():
            self.on_new_chat(None)
        else:
            # Load most recent chat
            chats = self.chat_history.get_all_chats()
            self.load_chat(chats[-1]["id"])

    def load_config(self):
        """Load configuration."""
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except:
            return {
                "language": "en",
                "ui": {"theme_name": "Dark"},
                "voice": {"tts_enabled": False}
            }

    def save_config(self):
        """Save configuration."""
        try:
            with open("config.json", "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")

    def setup_ui(self):
        """Setup main UI."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(main_box)

        # Sidebar
        self.setup_sidebar(main_box)

        # Chat area
        self.setup_chat_area(main_box)

    def setup_sidebar(self, parent):
        """Setup sidebar."""
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sidebar.set_size_request(280, -1)
        sidebar.add_css_class("sidebar")
        sidebar.set_margin_top(10)
        sidebar.set_margin_bottom(10)
        sidebar.set_margin_start(10)
        sidebar.set_margin_end(10)
        parent.append(sidebar)

        # Title
        title = Gtk.Label(label="🤖 Riko AI")
        title.add_css_class("sidebar-title")
        title.set_halign(Gtk.Align.START)
        sidebar.append(title)

        # New chat button
        new_chat_btn = Gtk.Button(label="➕ New Chat")
        new_chat_btn.connect("clicked", self.on_new_chat)
        sidebar.append(new_chat_btn)

        # Chat history
        history_label = Gtk.Label(label="💬 Chat History")
        history_label.add_css_class("section-title")
        history_label.set_halign(Gtk.Align.START)
        sidebar.append(history_label)

        # Chat list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar.append(scroll)

        self.chat_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scroll.set_child(self.chat_list_box)

        # Personality stats
        self.setup_personality_section(sidebar)

        # Settings button
        settings_btn = Gtk.Button(label="⚙️ Settings")
        settings_btn.connect("clicked", self.show_settings)
        sidebar.append(settings_btn)

        # Refresh chat list
        self.refresh_chat_list()

    def setup_personality_section(self, parent):
        """Setup personality stats section."""
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        parent.append(sep)

        personality_label = Gtk.Label(label="✨ Personality")
        personality_label.add_css_class("section-title")
        personality_label.set_halign(Gtk.Align.START)
        parent.append(personality_label)

        traits = self.riko.memory.get("personality_traits", {
            "curiosity": 0.85,
            "friendliness": 0.90,
            "playfulness": 0.70,
            "thoughtfulness": 0.80
        })

        for trait, value in traits.items():
            trait_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            parent.append(trait_box)

            label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            trait_box.append(label_box)

            trait_label = Gtk.Label(label=trait.capitalize())
            trait_label.set_halign(Gtk.Align.START)
            trait_label.set_hexpand(True)
            label_box.append(trait_label)

            value_label = Gtk.Label(label=f"{int(value * 100)}%")
            value_label.add_css_class("trait-value")
            label_box.append(value_label)

            progress = Gtk.ProgressBar()
            progress.set_fraction(value)
            progress.add_css_class("trait-bar")
            trait_box.append(progress)

    def setup_chat_area(self, parent):
        """Setup chat area."""
        chat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        chat_box.set_hexpand(True)
        chat_box.set_margin_top(10)
        chat_box.set_margin_bottom(10)
        chat_box.set_margin_start(10)
        chat_box.set_margin_end(10)
        parent.append(chat_box)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.add_css_class("chat-header")
        chat_box.append(header_box)

        self.chat_title_label = Gtk.Label(label="💬 Chat")
        self.chat_title_label.add_css_class("chat-title")
        self.chat_title_label.set_halign(Gtk.Align.START)
        self.chat_title_label.set_hexpand(True)
        header_box.append(self.chat_title_label)

        self.status_label = Gtk.Label(label="● Ready")
        self.status_label.add_css_class("status-ready")
        header_box.append(self.status_label)

        # Chat view
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        chat_box.append(scroll)

        self.chat_view = Gtk.TextView()
        self.chat_view.set_editable(False)
        self.chat_view.set_cursor_visible(False)
        self.chat_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.chat_view.add_css_class("chat-view")
        self.chat_view.set_left_margin(10)
        self.chat_view.set_right_margin(10)
        self.chat_view.set_top_margin(10)
        self.chat_view.set_bottom_margin(10)
        scroll.set_child(self.chat_view)

        self.chat_buffer = self.chat_view.get_buffer()
        
        # Text tags
        self.chat_buffer.create_tag("riko", weight=Pango.Weight.BOLD, foreground="#a78bfa")
        self.chat_buffer.create_tag("user", weight=Pango.Weight.BOLD, foreground="#89b4fa")
        self.chat_buffer.create_tag("content", size_points=13)
        self.chat_buffer.create_tag("timestamp", size_points=10, foreground="#6c7086")

        # Input area
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        chat_box.append(input_box)

        # Voice button
        self.voice_btn = Gtk.Button(label="🎤")
        self.voice_btn.set_tooltip_text("Voice Input (Speech-to-Text)")
        self.voice_btn.connect("clicked", self.on_voice_input)
        self.voice_btn.set_sensitive(STT_AVAILABLE)
        input_box.append(self.voice_btn)

        # Text input
        self.input_entry = Gtk.Entry()
        self.input_entry.set_placeholder_text("Type your message...")
        self.input_entry.add_css_class("message-input")
        self.input_entry.set_hexpand(True)
        self.input_entry.connect("activate", self.on_send_message)
        input_box.append(self.input_entry)

        # Send button
        send_btn = Gtk.Button(label="Send")
        send_btn.add_css_class("send-button")
        send_btn.connect("clicked", self.on_send_message)
        input_box.append(send_btn)

    def on_voice_input(self, widget):
        """Handle voice input."""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.voice_btn.set_label("⏹️")
        self.status_label.set_label("🎤 Listening...")
        
        # Get language code for STT
        lang_map = {
            "en": "en-US", "es": "es-ES", "fr": "fr-FR", "de": "de-DE",
            "it": "it-IT", "pt": "pt-BR", "ja": "ja-JP", "zh": "zh-CN",
            "ko": "ko-KR", "ar": "ar-SA", "ru": "ru-RU", "hi": "hi-IN"
        }
        lang_code = lang_map.get(self.config.get("language", "en"), "en-US")
        
        def callback(text, error):
            self.is_listening = False
            self.voice_btn.set_label("🎤")
            self.status_label.set_label("● Ready")
            self.status_label.add_css_class("status-ready")
            
            if text:
                self.input_entry.set_text(text)
                # Auto-send
                self.on_send_message(None)
            elif error:
                self.status_label.set_label(f"❌ {error}")
        
        self.voice_manager.listen(callback, lang_code)

    def add_chat_message(self, sender, message, is_system=False):
        """Add message to chat view."""
        end_iter = self.chat_buffer.get_end_iter()

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_buffer.insert_with_tags_by_name(end_iter, f"[{timestamp}] ", "timestamp")

        # Add message without sender prefix for user
        if sender == "You":
            # Just show the message content
            end_iter = self.chat_buffer.get_end_iter()
            self.chat_buffer.insert_with_tags_by_name(end_iter, f"{message}\n\n", "content")
        else:
            # Show Riko's name
            end_iter = self.chat_buffer.get_end_iter()
            self.chat_buffer.insert_with_tags_by_name(end_iter, f"{sender}: ", "riko")
            
            end_iter = self.chat_buffer.get_end_iter()
            self.chat_buffer.insert_with_tags_by_name(end_iter, f"{message}\n\n", "content")

        # Scroll to bottom
        end_mark = self.chat_buffer.create_mark(None, self.chat_buffer.get_end_iter(), False)
        self.chat_view.scroll_to_mark(end_mark, 0.0, True, 0.0, 1.0)

        # Save to history
        if not is_system:
            self.chat_history.add_message(self.current_chat_id, sender, message)

    def on_send_message(self, widget):
        """Send message."""
        if self.is_thinking:
            return

        message = self.input_entry.get_text().strip()
        if not message:
            return

        # Clear input
        self.input_entry.set_text("")

        # Add user message
        self.add_chat_message("You", message)

        # Update status
        self.is_thinking = True
        self.status_label.set_label("💭 Thinking...")
        self.status_label.remove_css_class("status-ready")
        self.status_label.add_css_class("status-thinking")

        # Get language instruction
        lang_names = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "zh": "Chinese",
            "ko": "Korean", "ar": "Arabic", "ru": "Russian", "hi": "Hindi"
        }
        lang = self.config.get("language", "en")
        lang_instruction = ""
        if lang != "en":
            lang_instruction = f"[Respond in {lang_names.get(lang, 'English')}] "

        # Get response in thread
        def get_response():
            try:
                reply = self.riko.reply(lang_instruction + message)
                GLib.idle_add(self.display_response, reply)
            except Exception as e:
                GLib.idle_add(self.display_response, f"Error: {e}")

        thread = threading.Thread(target=get_response, daemon=True)
        thread.start()

    def display_response(self, reply):
        """Display Riko's response."""
        self.is_thinking = False
        self.status_label.set_label("● Ready")
        self.status_label.remove_css_class("status-thinking")
        self.status_label.add_css_class("status-ready")

        self.add_chat_message("Riko", reply)
        self.update_chat_title()

        # TTS if enabled
        if self.config.get("voice", {}).get("tts_enabled", False):
            self.voice_manager.speak(reply)

        return False

    def refresh_chat_list(self):
        """Refresh chat history list."""
        # Clear list
        child = self.chat_list_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.chat_list_box.remove(child)
            child = next_child

        # Add chats
        chats = self.chat_history.get_all_chats()
        for chat in reversed(chats):  # Most recent first
            self.add_chat_to_list(chat)

    def add_chat_to_list(self, chat):
        """Add chat to sidebar list."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row.set_margin_top(3)
        row.set_margin_bottom(3)

        # Chat button
        chat_btn = Gtk.Button(label=chat["title"][:25])
        chat_btn.set_hexpand(True)
        chat_btn.connect("clicked", lambda w: self.load_chat(chat["id"]))
        
        if chat["id"] == self.current_chat_id:
            chat_btn.add_css_class("current-chat")
        
        row.append(chat_btn)

        # Delete button
        del_btn = Gtk.Button(label="🗑")
        del_btn.connect("clicked", lambda w: self.delete_chat(chat["id"]))
        row.append(del_btn)

        self.chat_list_box.append(row)

    def on_new_chat(self, widget):
        """Create new chat."""
        self.current_chat_id = self.chat_history.create_chat()
        self.chat_buffer.set_text("")
        self.add_chat_message("Riko", "Hey! I'm Riko.😊", is_system=True)
        self.refresh_chat_list()
        self.update_chat_title()

    def load_chat(self, chat_id):
        """Load a chat."""
        self.current_chat_id = chat_id
        chat = self.chat_history.get_chat(chat_id)
        if not chat:
            return

        # Clear buffer
        self.chat_buffer.set_text("")

        # Load messages with improved display
        for msg in chat["messages"]:
            end_iter = self.chat_buffer.get_end_iter()

            # Extract timestamp
            timestamp = msg.get("timestamp", "")[:16].split("T")
            if len(timestamp) == 2:
                time_str = timestamp[1]
            else:
                time_str = "00:00"

            self.chat_buffer.insert_with_tags_by_name(end_iter, f"[{time_str}] ", "timestamp")

            # Display message
            sender = msg["sender"]
            if sender == "You":
                # User message - no prefix
                end_iter = self.chat_buffer.get_end_iter()
                self.chat_buffer.insert_with_tags_by_name(end_iter, f"{msg['message']}\n\n", "content")
            else:
                # Riko message - with prefix
                tag = "riko"
                end_iter = self.chat_buffer.get_end_iter()
                self.chat_buffer.insert_with_tags_by_name(end_iter, f"{sender}: ", tag)
                
                end_iter = self.chat_buffer.get_end_iter()
                self.chat_buffer.insert_with_tags_by_name(end_iter, f"{msg['message']}\n\n", "content")

        self.update_chat_title()
        self.refresh_chat_list()

    def delete_chat(self, chat_id):
        """Delete a chat permanently."""
        dialog = Gtk.AlertDialog()
        dialog.set_message("Delete Chat Permanently?")
        dialog.set_detail("This will delete the chat and clear Riko's memory. This action cannot be undone.")
        dialog.set_buttons(["Cancel", "Delete"])
        dialog.set_cancel_button(0)
        dialog.set_default_button(0)
        dialog.choose(self, None, self.on_delete_confirm, chat_id)

    def on_delete_confirm(self, dialog, result, chat_id):
        """Handle delete confirmation."""
        try:
            button = dialog.choose_finish(result)
            if button == 1:  # Delete
                self.chat_history.delete_chat(chat_id)

                # If deleted current chat, create new one
                if chat_id == self.current_chat_id:
                    self.on_new_chat(None)
                else:
                    self.refresh_chat_list()
        except:
            pass

    def update_chat_title(self):
        """Update chat title label."""
        chat = self.chat_history.get_chat(self.current_chat_id)
        if chat:
            self.chat_title_label.set_label(f"💬 {chat['title']}")

    def show_settings(self, widget):
        """Show settings window."""
        settings_win = SettingsWindow(self, self.config, self.on_settings_saved)
        settings_win.present()

    def on_settings_saved(self, new_config):
        """Handle settings being saved."""
        self.config = new_config
        self.save_config()
        self.apply_theme()

    def apply_theme(self):
        """Apply color theme."""
        css_provider = Gtk.CssProvider()

        theme_name = self.config.get("ui", {}).get("theme_name", "Dark")

        # Theme presets
        themes = {
            "Dark": {
                "bg": "#1e1e2e", "fg": "#cdd6f4",
                "sidebar": "#181825", "accent": "#89b4fa"
            },
            "Light": {
                "bg": "#eff1f5", "fg": "#4c4f69",
                "sidebar": "#e6e9ef", "accent": "#1e66f5"
            },
            "Catppuccin Mocha": {
                "bg": "#1e1e2e", "fg": "#cdd6f4",
                "sidebar": "#181825", "accent": "#cba6f7"
            },
            "Catppuccin Latte": {
                "bg": "#eff1f5", "fg": "#4c4f69",
                "sidebar": "#e6e9ef", "accent": "#8839ef"
            },
            "Nord": {
                "bg": "#2e3440", "fg": "#d8dee9",
                "sidebar": "#3b4252", "accent": "#88c0d0"
            },
            "Dracula": {
                "bg": "#282a36", "fg": "#f8f8f2",
                "sidebar": "#21222c", "accent": "#bd93f9"
            },
            "Custom": self.config.get("ui", {}).get("custom_colors", {
                "background": "#1e1e2e", "sidebar": "#181825",
                "text": "#cdd6f4", "accent": "#a78bfa"
            })
        }

        if theme_name == "Custom":
            colors = themes["Custom"]
            bg = colors.get("background", "#1e1e2e")
            fg = colors.get("text", "#cdd6f4")
            sidebar = colors.get("sidebar", "#181825")
            accent = colors.get("accent", "#a78bfa")
        else:
            colors = themes.get(theme_name, themes["Dark"])
            bg = colors["bg"]
            fg = colors["fg"]
            sidebar = colors["sidebar"]
            accent = colors["accent"]

        css = f"""
        window {{
            background-color: {bg};
            color: {fg};
        }}
        .sidebar {{
            background-color: {sidebar};
            border-right: 1px solid rgba(255,255,255,0.1);
        }}
        .sidebar-title {{
            font-size: 18px;
            font-weight: bold;
            color: {accent};
        }}
        .section-title {{
            font-size: 13px;
            font-weight: bold;
            color: {accent};
        }}
        .trait-value {{
            color: {accent};
            font-size: 11px;
        }}
        .trait-bar progress {{
            background-color: {accent};
        }}
        .trait-bar trough {{
            background-color: rgba(255,255,255,0.1);
            min-height: 6px;
        }}
        .chat-header {{
            background-color: {sidebar};
            padding: 10px;
            border-radius: 8px;
        }}
        .chat-title {{
            font-size: 16px;
            font-weight: bold;
        }}
        .status-ready {{
            color: #a6e3a1;
        }}
        .status-thinking {{
            color: #f9e2af;
        }}
        .chat-view {{
            background-color: {bg};
            color: {fg};
            font-size: 13px;
        }}
        .message-input {{
            background-color: {sidebar};
            color: {fg};
            border: 1px solid rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 6px;
        }}
        .send-button {{
            background-color: {accent};
            color: {bg};
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 6px;
        }}
        button {{
            background-color: {sidebar};
            color: {fg};
            border: 1px solid rgba(255,255,255,0.1);
            padding: 8px;
            border-radius: 6px;
        }}
        .current-chat {{
            background-color: {accent};
            color: {bg};
        }}
        """

        css_provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


class RikoApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.riko.ai")

    def do_activate(self):
        win = RikoGUI(self)
        win.present()


def main():
    if not os.getenv("GROQ_API_KEY"):
        print("❌ ERROR: GROQ_API_KEY not set!")
        return

    app = RikoApp()
    app.run()


if __name__ == "__main__":
    main()
