# gui_windows.py - Windows version using Tkinter
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, colorchooser
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
        self.is_speaking = False
        
        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.9)
                
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
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            except Exception as e:
                print(f"STT init error: {e}")
                self.recognizer = None
    
    def speak(self, text, callback=None):
        """Text to speech (non-blocking)."""
        if not self.tts_engine or self.is_speaking:
            return
        
        def _speak():
            try:
                self.is_speaking = True
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.is_speaking = False
                if callback:
                    callback()
            except Exception as e:
                print(f"TTS error: {e}")
                self.is_speaking = False
        
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
                    callback(None, "Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    text = self.recognizer.recognize_google(audio, language=language)
                    callback(text, None)
                except sr.UnknownValueError:
                    callback(None, "Could not understand audio")
                except sr.RequestError as e:
                    callback(None, f"API error: {e}")
            except Exception as e:
                callback(None, f"Error: {e}")
        
        thread = threading.Thread(target=_listen, daemon=True)
        thread.start()
    
    def stop_speaking(self):
        """Stop current speech."""
        if self.tts_engine:
            try:
                self.tts_engine.stop()
                self.is_speaking = False
            except:
                pass


class ChatHistoryManager:
    """Manages chat history storage."""

    def __init__(self):
        self.history_file = "chat_history.json"
        self.memory_file = "riko_memory.json"
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"chats": []}
        return {"chats": []}

    def save_history(self):
        try:
            with open(self.history_file, "w", encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")

    def create_chat(self):
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
        if chat_id < len(self.history["chats"]):
            self.history["chats"][chat_id]["messages"].append({
                "sender": sender,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

            if sender == "You" and len(self.history["chats"][chat_id]["messages"]) <= 2:
                title = message[:30] + ("..." if len(message) > 30 else "")
                self.history["chats"][chat_id]["title"] = title

            self.save_history()

    def get_chat(self, chat_id):
        if chat_id < len(self.history["chats"]):
            return self.history["chats"][chat_id]
        return None

    def delete_chat(self, chat_id):
        """Delete a chat permanently from both history and memory."""
        if chat_id < len(self.history["chats"]):
            self.history["chats"].pop(chat_id)
            
            for i, chat in enumerate(self.history["chats"]):
                chat["id"] = i
            
            self.save_history()
            self.clear_riko_memory()
    
    def clear_riko_memory(self):
        """Clear Riko's conversation memory."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r", encoding='utf-8') as f:
                    memory = json.load(f)
                
                user_name = memory.get("user_name")
                memory["last_conversation"] = []
                memory["stats"]["total_messages"] = 0
                
                with open(self.memory_file, "w", encoding='utf-8') as f:
                    json.dump(memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error clearing memory: {e}")

    def get_all_chats(self):
        return self.history["chats"]


class SettingsWindow:
    """Settings window."""
    
    def __init__(self, parent, config, callback):
        self.config = config
        self.callback = callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ Settings")
        self.window.geometry("600x650")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main container
        canvas = tk.Canvas(self.window)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Voice Settings
        voice_frame = ttk.LabelFrame(scrollable_frame, text="🎤 Voice Settings", padding=10)
        voice_frame.pack(fill="x", padx=10, pady=5)
        
        self.tts_var = tk.BooleanVar(value=self.config.get("voice", {}).get("tts_enabled", False))
        ttk.Checkbutton(voice_frame, text="Enable Text-to-Speech (Riko speaks)", 
                       variable=self.tts_var).pack(anchor="w")
        
        status_text = "Voice Status:\n"
        status_text += "✅ TTS Available\n" if TTS_AVAILABLE else "❌ TTS Not Available\n"
        status_text += "✅ STT Available" if STT_AVAILABLE else "❌ STT Not Available"
        ttk.Label(voice_frame, text=status_text).pack(anchor="w", pady=5)
        
        # Language Settings
        lang_frame = ttk.LabelFrame(scrollable_frame, text="🌐 Language", padding=10)
        lang_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(lang_frame, text="Riko will respond in this language:").pack(anchor="w")
        
        languages = {
            "English": "en", "Spanish": "es", "French": "fr", "German": "de",
            "Italian": "it", "Portuguese": "pt", "Japanese": "ja", "Chinese": "zh",
            "Korean": "ko", "Arabic": "ar", "Russian": "ru", "Hindi": "hi"
        }
        
        self.lang_var = tk.StringVar(value=self.config.get("language", "en"))
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, 
                                  values=list(languages.values()), state="readonly")
        lang_combo.pack(fill="x", pady=5)
        
        # Theme Settings
        theme_frame = ttk.LabelFrame(scrollable_frame, text="🎨 Theme", padding=10)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(theme_frame, text="Choose a theme:").pack(anchor="w")
        
        themes = ["Dark", "Light", "Catppuccin Mocha", "Catppuccin Latte", "Nord", "Dracula", "Custom"]
        self.theme_var = tk.StringVar(value=self.config.get("ui", {}).get("theme_name", "Dark"))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                   values=themes, state="readonly")
        theme_combo.pack(fill="x", pady=5)
        
        # Custom Colors
        colors_frame = ttk.LabelFrame(scrollable_frame, text="🖌️ Custom Colors", padding=10)
        colors_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(colors_frame, text="Customize colors (select 'Custom' theme):").pack(anchor="w")
        
        custom_colors = self.config.get("ui", {}).get("custom_colors", {
            "background": "#1e1e2e", "sidebar": "#181825",
            "text": "#cdd6f4", "accent": "#a78bfa"
        })
        
        self.color_vars = {}
        for name, key in [("Background", "background"), ("Sidebar", "sidebar"), 
                          ("Text", "text"), ("Accent", "accent")]:
            row = ttk.Frame(colors_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{name}:").pack(side="left")
            var = tk.StringVar(value=custom_colors.get(key, "#000000"))
            self.color_vars[key] = var
            ttk.Entry(row, textvariable=var, width=10).pack(side="right")
        
        # Buttons
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="right")
    
    def save(self):
        # Update config
        if "voice" not in self.config:
            self.config["voice"] = {}
        self.config["voice"]["tts_enabled"] = self.tts_var.get()
        self.config["language"] = self.lang_var.get()
        
        if "ui" not in self.config:
            self.config["ui"] = {}
        self.config["ui"]["theme_name"] = self.theme_var.get()
        
        custom_colors = {}
        for key, var in self.color_vars.items():
            custom_colors[key] = var.get()
        self.config["ui"]["custom_colors"] = custom_colors
        
        self.callback(self.config)
        self.window.destroy()


class RikoGUI:
    """Main Riko AI GUI for Windows."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Riko AI")
        self.root.geometry("1200x700")
        
        # Initialize
        self.riko = Riko()
        self.chat_history = ChatHistoryManager()
        self.voice_manager = VoiceManager()
        self.config = self.load_config()
        
        self.current_chat_id = None
        self.is_thinking = False
        self.is_listening = False
        
        self.setup_ui()
        self.apply_theme()
        
        # Create initial chat
        if not self.chat_history.get_all_chats():
            self.on_new_chat()
        else:
            chats = self.chat_history.get_all_chats()
            self.load_chat(chats[-1]["id"])
    
    def load_config(self):
        try:
            with open("config.json", "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "language": "en",
                "ui": {"theme_name": "Dark"},
                "voice": {"tts_enabled": False}
            }
    
    def save_config(self):
        try:
            with open("config.json", "w", encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def setup_ui(self):
        # Main layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Sidebar
        self.setup_sidebar()
        
        # Chat area
        self.setup_chat_area()
    
    def setup_sidebar(self):
        sidebar = ttk.Frame(self.root, width=280)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        sidebar.grid_propagate(False)
        
        # Title
        title = ttk.Label(sidebar, text="🤖 Riko AI", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # New chat button
        ttk.Button(sidebar, text="➕ New Chat", command=self.on_new_chat).pack(fill="x", padx=5, pady=5)
        
        # Chat history
        ttk.Label(sidebar, text="💬 Chat History", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Chat list
        list_frame = ttk.Frame(sidebar)
        list_frame.pack(fill="both", expand=True, padx=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.chat_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.chat_listbox.pack(side="left", fill="both", expand=True)
        self.chat_listbox.bind("<<ListboxSelect>>", self.on_chat_select)
        scrollbar.config(command=self.chat_listbox.yview)
        
        # Delete button
        ttk.Button(sidebar, text="🗑 Delete Chat", command=self.delete_selected_chat).pack(fill="x", padx=5, pady=5)
        
        # Personality section
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(sidebar, text="✨ Personality", font=("Arial", 11, "bold")).pack()
        
        traits = {"Curiosity": 0.85, "Friendliness": 0.90, "Playfulness": 0.70, "Thoughtfulness": 0.80}
        for trait, value in traits.items():
            frame = ttk.Frame(sidebar)
            frame.pack(fill="x", padx=10, pady=2)
            ttk.Label(frame, text=trait).pack(side="left")
            ttk.Label(frame, text=f"{int(value*100)}%").pack(side="right")
        
        # Settings button
        ttk.Button(sidebar, text="⚙️ Settings", command=self.show_settings).pack(fill="x", padx=5, pady=10)
        
        self.refresh_chat_list()
    
    def setup_chat_area(self):
        chat_frame = ttk.Frame(self.root)
        chat_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        chat_frame.grid_rowconfigure(1, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ttk.Frame(chat_frame)
        header.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.chat_title = ttk.Label(header, text="💬 Chat", font=("Arial", 14, "bold"))
        self.chat_title.pack(side="left")
        
        self.status_label = ttk.Label(header, text="● Ready")
        self.status_label.pack(side="right")
        
        # Chat view
        self.chat_view = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, font=("Arial", 11))
        self.chat_view.grid(row=1, column=0, sticky="nsew", pady=5)
        self.chat_view.config(state="disabled")
        
        # Configure tags
        self.chat_view.tag_config("timestamp", foreground="gray", font=("Arial", 9))
        self.chat_view.tag_config("riko", foreground="#a78bfa", font=("Arial", 11, "bold"))
        self.chat_view.tag_config("user", foreground="#89b4fa", font=("Arial", 11, "bold"))
        self.chat_view.tag_config("content", font=("Arial", 11))
        
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=2, column=0, sticky="ew", pady=5)
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Voice button
        self.voice_btn = ttk.Button(input_frame, text="🎤", width=3, command=self.on_voice_input)
        self.voice_btn.grid(row=0, column=0, padx=2)
        if not STT_AVAILABLE:
            self.voice_btn.config(state="disabled")
        
        # Text input
        self.input_entry = ttk.Entry(input_frame, font=("Arial", 11))
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.input_entry.bind("<Return>", lambda e: self.on_send_message())
        
        # Send button
        ttk.Button(input_frame, text="Send", command=self.on_send_message).grid(row=0, column=2, padx=2)
    
    def on_voice_input(self):
        if self.is_listening:
            return
        
        self.is_listening = True
        self.voice_btn.config(text="⏹️")
        self.status_label.config(text="🎤 Listening...")
        
        lang_map = {
            "en": "en-US", "es": "es-ES", "fr": "fr-FR", "de": "de-DE",
            "it": "it-IT", "pt": "pt-BR", "ja": "ja-JP", "zh": "zh-CN",
            "ko": "ko-KR", "ar": "ar-SA", "ru": "ru-RU", "hi": "hi-IN"
        }
        lang_code = lang_map.get(self.config.get("language", "en"), "en-US")
        
        def callback(text, error):
            self.is_listening = False
            self.voice_btn.config(text="🎤")
            self.status_label.config(text="● Ready")
            
            if text:
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, text)
                self.on_send_message()
            elif error:
                self.status_label.config(text=f"❌ {error}")
        
        self.voice_manager.listen(callback, lang_code)
    
    def add_chat_message(self, sender, message, is_system=False):
        self.chat_view.config(state="normal")
        
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_view.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        if sender == "You":
            self.chat_view.insert(tk.END, f"{message}\n\n", "content")
        else:
            self.chat_view.insert(tk.END, f"{sender}: ", "riko")
            self.chat_view.insert(tk.END, f"{message}\n\n", "content")
        
        self.chat_view.see(tk.END)
        self.chat_view.config(state="disabled")
        
        if not is_system:
            self.chat_history.add_message(self.current_chat_id, sender, message)
    
    def on_send_message(self):
        if self.is_thinking:
            return
        
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self.input_entry.delete(0, tk.END)
        self.add_chat_message("You", message)
        
        self.is_thinking = True
        self.status_label.config(text="💭 Thinking...")
        
        lang_names = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "zh": "Chinese",
            "ko": "Korean", "ar": "Arabic", "ru": "Russian", "hi": "Hindi"
        }
        lang = self.config.get("language", "en")
        lang_instruction = ""
        if lang != "en":
            lang_instruction = f"[Respond in {lang_names.get(lang, 'English')}] "
        
        def get_response():
            try:
                reply = self.riko.reply(lang_instruction + message)
                self.root.after(0, self.display_response, reply)
            except Exception as e:
                self.root.after(0, self.display_response, f"Error: {e}")
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def display_response(self, reply):
        self.is_thinking = False
        self.status_label.config(text="● Ready")
        self.add_chat_message("Riko", reply)
        self.update_chat_title()
        
        if self.config.get("voice", {}).get("tts_enabled", False):
            self.voice_manager.speak(reply)
    
    def on_new_chat(self):
        self.current_chat_id = self.chat_history.create_chat()
        self.chat_view.config(state="normal")
        self.chat_view.delete(1.0, tk.END)
        self.chat_view.config(state="disabled")
        self.add_chat_message("Riko", "Hey! I'm Riko.😊", is_system=True)
        self.refresh_chat_list()
        self.update_chat_title()
    
    def load_chat(self, chat_id):
        self.current_chat_id = chat_id
        chat = self.chat_history.get_chat(chat_id)
        if not chat:
            return
        
        self.chat_view.config(state="normal")
        self.chat_view.delete(1.0, tk.END)
        
        for msg in chat["messages"]:
            timestamp = msg.get("timestamp", "")[:16].split("T")
            time_str = timestamp[1] if len(timestamp) == 2 else "00:00"
            
            self.chat_view.insert(tk.END, f"[{time_str}] ", "timestamp")
            
            sender = msg["sender"]
            if sender == "You":
                self.chat_view.insert(tk.END, f"{msg['message']}\n\n", "content")
            else:
                self.chat_view.insert(tk.END, f"{sender}: ", "riko")
                self.chat_view.insert(tk.END, f"{msg['message']}\n\n", "content")
        
        self.chat_view.config(state="disabled")
        self.update_chat_title()
        self.refresh_chat_list()
    
    def on_chat_select(self, event):
        selection = self.chat_listbox.curselection()
        if selection:
            index = selection[0]
            chats = list(reversed(self.chat_history.get_all_chats()))
            if index < len(chats):
                self.load_chat(chats[index]["id"])
    
    def delete_selected_chat(self):
        selection = self.chat_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a chat to delete.")
            return
        
        result = messagebox.askyesno(
            "Delete Chat Permanently?",
            "This will delete the chat and clear Riko's memory.\nThis action cannot be undone."
        )
        
        if result:
            index = selection[0]
            chats = list(reversed(self.chat_history.get_all_chats()))
            chat_id = chats[index]["id"]
            
            self.chat_history.delete_chat(chat_id)
            
            if chat_id == self.current_chat_id:
                self.on_new_chat()
            else:
                self.refresh_chat_list()
    
    def refresh_chat_list(self):
        self.chat_listbox.delete(0, tk.END)
        chats = reversed(self.chat_history.get_all_chats())
        for chat in chats:
            title = chat["title"][:30]
            self.chat_listbox.insert(tk.END, title)
            if chat["id"] == self.current_chat_id:
                self.chat_listbox.itemconfig(tk.END, bg="#a78bfa", fg="black")
    
    def update_chat_title(self):
        chat = self.chat_history.get_chat(self.current_chat_id)
        if chat:
            self.chat_title.config(text=f"💬 {chat['title']}")
    
    def show_settings(self):
        SettingsWindow(self.root, self.config, self.on_settings_saved)
    
    def on_settings_saved(self, new_config):
        self.config = new_config
        self.save_config()
        self.apply_theme()
    
    def apply_theme(self):
        theme_name = self.config.get("ui", {}).get("theme_name", "Dark")
        
        themes = {
            "Dark": {"bg": "#1e1e2e", "fg": "#cdd6f4", "sidebar": "#181825", "accent": "#89b4fa"},
            "Light": {"bg": "#eff1f5", "fg": "#4c4f69", "sidebar": "#e6e9ef", "accent": "#1e66f5"},
            "Catppuccin Mocha": {"bg": "#1e1e2e", "fg": "#cdd6f4", "sidebar": "#181825", "accent": "#cba6f7"},
            "Catppuccin Latte": {"bg": "#eff1f5", "fg": "#4c4f69", "sidebar": "#e6e9ef", "accent": "#8839ef"},
            "Nord": {"bg": "#2e3440", "fg": "#d8dee9", "sidebar": "#3b4252", "accent": "#88c0d0"},
            "Dracula": {"bg": "#282a36", "fg": "#f8f8f2", "sidebar": "#21222c", "accent": "#bd93f9"},
            "Custom": self.config.get("ui", {}).get("custom_colors", {
                "background": "#1e1e2e", "sidebar": "#181825", "text": "#cdd6f4", "accent": "#a78bfa"
            })
        }
        
        if theme_name == "Custom":
            colors = themes["Custom"]
            bg = colors.get("background", "#1e1e2e")
            fg = colors.get("text", "#cdd6f4")
        else:
            colors = themes.get(theme_name, themes["Dark"])
            bg = colors["bg"]
            fg = colors["fg"]
        
        # Apply colors
        self.root.config(bg=bg)
        self.chat_view.config(bg=bg, fg=fg, insertbackground=fg)
        
        # Update tags
        self.chat_view.tag_config("riko", foreground=colors.get("accent", "#a78bfa"))
        self.chat_view.tag_config("user", foreground=colors.get("accent", "#89b4fa"))
    
    def run(self):
        self.root.mainloop()


def main():
    if not os.getenv("GROQ_API_KEY"):
        import tkinter.messagebox as mb
        mb.showerror("API Key Missing", 
                     "GROQ_API_KEY environment variable not set!\n\n"
                     "Please set it in your system environment variables.")
        return
    
    app = RikoGUI()
    app.run()


if __name__ == "__main__":
    main()
