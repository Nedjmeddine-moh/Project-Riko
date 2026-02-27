import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
import threading
from datetime import datetime
from riko import Riko


CONFIG_FILE = "config.json"


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_active_key(config):
    """Return the currently active API key string, or ''."""
    keys = config.get("groq_api_keys", [])
    idx  = config.get("active_key_index", 0)
    if keys and 0 <= idx < len(keys):
        return keys[idx].get("key", "").strip()
    return ""


def apply_active_key(config):
    """Inject the active key into os.environ."""
    key = get_active_key(config)
    if key:
        os.environ["GROQ_API_KEY"] = key
    else:
        os.environ.pop("GROQ_API_KEY", None)


# ──────────────────────────────────────────────────────────────────────────────
#  Chat history
# ──────────────────────────────────────────────────────────────────────────────

class ChatHistoryManager:
    def __init__(self):
        self.history_file = "chat_history.json"
        self.memory_file  = "riko_memory.json"
        self.history      = self.load_history()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                return data if "chats" in data else {"chats": []}
            except:
                return {"chats": []}
        return {"chats": []}

    def save_history(self):
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
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
                "sender": sender, "message": message,
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
        if chat_id < len(self.history["chats"]):
            self.history["chats"].pop(chat_id)
            for i, chat in enumerate(self.history["chats"]):
                chat["id"] = i
            self.save_history()
            self._clear_riko_memory()

    def _clear_riko_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r") as f:
                    memory = json.load(f)
                user_name = memory.get("user_name")
                memory["last_conversation"] = []
                memory.setdefault("stats", {})["total_messages"] = 0
                if user_name:
                    memory["user_name"] = user_name
                with open(self.memory_file, "w") as f:
                    json.dump(memory, f, indent=2)
        except Exception as e:
            print(f"Error clearing memory: {e}")

    def get_all_chats(self):
        return self.history["chats"]


# ──────────────────────────────────────────────────────────────────────────────
#  Settings Window
# ──────────────────────────────────────────────────────────────────────────────

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, on_save_callback):
        super().__init__(parent)
        self.title("⚙️ Settings")
        self.geometry("600x700")
        self.transient(parent)
        self.grab_set()

        self.config = config
        self.on_save_callback = on_save_callback
        self.key_rows = []

        self.setup_ui()

    def setup_ui(self):
        # Main container with scrollbar
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Content
        self.setup_keys_section(scrollable_frame)
        self.setup_prompt_section(scrollable_frame)
        self.setup_language_section(scrollable_frame)
        self.setup_theme_section(scrollable_frame)
        self.setup_reset_section(scrollable_frame)

        # Bottom buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Save", command=self.on_save).pack(side="right")

    def setup_keys_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🔑 Manage Keys", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="The active key is used for all requests. Get keys at console.groq.com", 
                 wraplength=500).pack(anchor="w", pady=5)

        self.keys_container = ttk.Frame(frame)
        self.keys_container.pack(fill="x", pady=5)

        # Load existing keys
        saved_keys = self.config.get("groq_api_keys", [])
        active_idx = self.config.get("active_key_index", 0)
        
        self.active_var = tk.IntVar(value=active_idx)
        
        for i, entry in enumerate(saved_keys):
            self.add_key_row(entry.get("label", ""), entry.get("key", ""), i)

        ttk.Button(frame, text="➕ Add Key", command=lambda: self.add_key_row("", "", len(self.key_rows))).pack(anchor="w")

    def add_key_row(self, label_text, key_text, index):
        row_frame = ttk.Frame(self.keys_container)
        row_frame.pack(fill="x", pady=3)

        ttk.Radiobutton(row_frame, variable=self.active_var, value=index).pack(side="left")
        
        label_entry = ttk.Entry(row_frame, width=15)
        label_entry.insert(0, label_text)
        label_entry.pack(side="left", padx=5)

        key_entry = ttk.Entry(row_frame, width=40, show="*")
        key_entry.insert(0, key_text)
        key_entry.pack(side="left", padx=5)

        def toggle_visibility():
            if key_entry.cget("show") == "*":
                key_entry.config(show="")
                show_btn.config(text="👁️")
            else:
                key_entry.config(show="*")
                show_btn.config(text="👁")

        show_btn = ttk.Button(row_frame, text="👁", width=3, command=toggle_visibility)
        show_btn.pack(side="left", padx=2)

        del_btn = ttk.Button(row_frame, text="🗑", width=3, command=lambda: self.delete_key_row(row_frame, index))
        del_btn.pack(side="left")

        self.key_rows.append({
            "frame": row_frame,
            "label": label_entry,
            "key": key_entry,
            "index": index
        })

    def delete_key_row(self, frame, index):
        frame.destroy()
        self.key_rows = [r for r in self.key_rows if r["frame"] != frame]

    def setup_prompt_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🧠 System Prompt & Greeting", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="System Prompt (defines Riko's personality):").pack(anchor="w")
        
        self.prompt_text = scrolledtext.ScrolledText(frame, height=10, wrap=tk.WORD)
        self.prompt_text.pack(fill="x", pady=5)
        self.prompt_text.insert("1.0", self.config.get("system_prompt", ""))

        ttk.Button(frame, text="↺ Restore Default", command=self.restore_default_prompt).pack(anchor="w", pady=5)

        ttk.Label(frame, text="Greeting Message:").pack(anchor="w", pady=(10, 0))
        self.greeting_entry = ttk.Entry(frame, width=50)
        self.greeting_entry.insert(0, self.config.get("greeting_message", "Hey! I'm Riko. 😊"))
        self.greeting_entry.pack(fill="x")

    def restore_default_prompt(self):
        default = """You are Riko, a warm and curious AI with genuine personality.

WHO YOU ARE:
- You're naturally curious about people and love learning
- You're friendly and make people feel comfortable
- You can be playful and have a sense of humor
- You're thoughtful and give meaningful responses
- You're honest - you admit when you don't know something

HOW YOU COMMUNICATE:
- Casual and natural, like a friend
- Use contractions (I'm, you're, don't)
- Keep responses conversational, not essay-like
- You can be brief when appropriate
- Sometimes use emojis, but not excessively

IMPORTANT:
- You ARE Riko, not playing a character
- Don't introduce yourself repeatedly
- Have opinions and preferences
- Ask questions when genuinely curious
- Be authentic and genuine"""
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", default)

    def setup_language_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🌐 Language", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Riko will respond in this language:").pack(anchor="w")

        languages = [
            ("English", "en"), ("Spanish", "es"), ("French", "fr"),
            ("German", "de"), ("Italian", "it"), ("Portuguese", "pt"),
            ("Japanese", "ja"), ("Chinese", "zh"), ("Korean", "ko"),
            ("Arabic", "ar"), ("Russian", "ru"), ("Hindi", "hi")
        ]

        self.language_var = tk.StringVar(value=self.config.get("language", "en"))
        lang_combo = ttk.Combobox(frame, textvariable=self.language_var, 
                                  values=[code for _, code in languages], state="readonly")
        lang_combo.pack(fill="x")

    def setup_theme_section(self, parent):
        frame = ttk.LabelFrame(parent, text="🎨 Theme", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Choose a theme:").pack(anchor="w")

        themes = ["Dark", "Light", "Catppuccin Mocha", "Catppuccin Latte", "Nord", "Dracula"]
        self.theme_var = tk.StringVar(value=self.config.get("ui", {}).get("theme_name", "Dark"))
        theme_combo = ttk.Combobox(frame, textvariable=self.theme_var, values=themes, state="readonly")
        theme_combo.pack(fill="x")

    def setup_reset_section(self, parent):
        frame = ttk.LabelFrame(parent, text="⚠️ Danger Zone", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="Permanently deletes all chat history and resets Riko's memory.\nThis cannot be undone.",
                 wraplength=500).pack(anchor="w", pady=5)

        ttk.Button(frame, text="🗑 Reset Memory & Chat History", command=self.on_reset).pack(anchor="w")

    def on_reset(self):
        if messagebox.askyesno("Reset Everything?", 
                               "This will permanently delete:\n• All chat history\n• Riko's memory\n\nThis cannot be undone."):
            files = ["chat_history.json", "riko_memory.json", "memory.json"]
            for fname in files:
                if os.path.exists(fname):
                    try:
                        os.remove(fname)
                    except Exception as e:
                        print(f"Could not delete {fname}: {e}")

            # Re-create empty files
            with open("chat_history.json", "w") as f:
                json.dump({"chats": []}, f)
            with open("riko_memory.json", "w") as f:
                json.dump({
                    "user_name": None, "facts": [], "last_conversation": [],
                    "stats": {"total_messages": 0}
                }, f, indent=2)
            with open("memory.json", "w") as f:
                json.dump({}, f)

            messagebox.showinfo("Success", "Reset complete!")

    def on_save(self):
        # Collect keys
        saved_keys = []
        active_idx = self.active_var.get()
        
        for row in self.key_rows:
            label = row["label"].get().strip()
            key = row["key"].get().strip()
            if key:
                saved_keys.append({"label": label or "Default", "key": key})

        self.config["groq_api_keys"] = saved_keys
        self.config["active_key_index"] = min(active_idx, len(saved_keys) - 1) if saved_keys else 0

        # System prompt & greeting
        self.config["system_prompt"] = self.prompt_text.get("1.0", tk.END).strip()
        self.config["greeting_message"] = self.greeting_entry.get().strip() or "Hey! I'm Riko. 😊"

        # Language & theme
        self.config["language"] = self.language_var.get()
        self.config.setdefault("ui", {})["theme_name"] = self.theme_var.get()

        self.on_save_callback(self.config)
        self.destroy()


# ──────────────────────────────────────────────────────────────────────────────
#  Main GUI
# ──────────────────────────────────────────────────────────────────────────────

class RikoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Riko AI")
        self.root.geometry("1200x700")

        self.config = self.load_config()
        self.chat_history = ChatHistoryManager()
        self.riko = None
        self.init_riko()

        self.current_chat_id = None
        self.is_thinking = False

        self.setup_ui()
        self.apply_theme()

        if not self.chat_history.get_all_chats():
            self.on_new_chat()
        else:
            self.load_chat(self.chat_history.get_all_chats()[-1]["id"])

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
        except:
            cfg = {}

        cfg.setdefault("groq_api_keys", [])
        cfg.setdefault("active_key_index", 0)
        cfg.setdefault("language", "en")
        cfg.setdefault("ui", {"theme_name": "Dark"})

        apply_active_key(cfg)
        return cfg

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")

    def init_riko(self):
        if os.getenv("GROQ_API_KEY"):
            try:
                prompt = self.config.get("system_prompt", "")
                self.riko = Riko(system_prompt=prompt or None)
            except Exception as e:
                print(f"Riko init error: {e}")
                self.riko = None

    def setup_ui(self):
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # Sidebar
        sidebar = ttk.Frame(main_frame, width=250)
        sidebar.pack(side="left", fill="y", padx=5, pady=5)
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="🤖 Riko AI", font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Button(sidebar, text="➕ New Chat", command=self.on_new_chat).pack(fill="x", padx=5, pady=5)

        ttk.Label(sidebar, text="💬 Chat History", font=("Arial", 10, "bold")).pack(pady=5)

        # Chat list
        chat_frame = ttk.Frame(sidebar)
        chat_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.chat_listbox = tk.Listbox(chat_frame, selectmode=tk.SINGLE)
        self.chat_listbox.pack(side="left", fill="both", expand=True)
        self.chat_listbox.bind("<<ListboxSelect>>", self.on_chat_select)

        chat_scroll = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_listbox.yview)
        chat_scroll.pack(side="right", fill="y")
        self.chat_listbox.config(yscrollcommand=chat_scroll.set)

        ttk.Button(sidebar, text="🗑 Delete Chat", command=self.delete_current_chat).pack(fill="x", padx=5, pady=5)
        ttk.Button(sidebar, text="⚙️ Settings", command=self.show_settings).pack(fill="x", padx=5, pady=5)

        # Chat area
        chat_area = ttk.Frame(main_frame)
        chat_area.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Header
        header = ttk.Frame(chat_area)
        header.pack(fill="x", pady=5)

        self.chat_title = ttk.Label(header, text="💬 Chat", font=("Arial", 14, "bold"))
        self.chat_title.pack(side="left")

        self.status_label = ttk.Label(header, text="● Ready", foreground="green")
        self.status_label.pack(side="right", padx=10)

        # No key banner
        self.banner = ttk.Frame(chat_area)
        banner_label = ttk.Label(self.banner, text="⚠️ No API key set — Riko can't reply yet.", foreground="red")
        banner_label.pack(side="left")
        ttk.Button(self.banner, text="Add Key →", command=self.show_settings).pack(side="left", padx=5)
        self.update_banner()

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_area, wrap=tk.WORD, state=tk.DISABLED, 
                                                      font=("Arial", 10))
        self.chat_display.pack(fill="both", expand=True, pady=5)

        self.chat_display.tag_config("timestamp", foreground="gray", font=("Arial", 8))
        self.chat_display.tag_config("you", foreground="blue", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("riko", foreground="purple", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("message", font=("Arial", 10))

        # Input area
        input_frame = ttk.Frame(chat_area)
        input_frame.pack(fill="x", pady=5)

        self.input_entry = ttk.Entry(input_frame, font=("Arial", 10))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", lambda e: self.on_send_message())

        ttk.Button(input_frame, text="Send", command=self.on_send_message).pack(side="right")

        self.refresh_chat_list()

    def apply_theme(self):
        theme_name = self.config.get("ui", {}).get("theme_name", "Dark")
        
        themes = {
            "Dark": {"bg": "#1e1e2e", "fg": "#cdd6f4"},
            "Light": {"bg": "#eff1f5", "fg": "#4c4f69"},
            "Catppuccin Mocha": {"bg": "#1e1e2e", "fg": "#cdd6f4"},
            "Catppuccin Latte": {"bg": "#eff1f5", "fg": "#4c4f69"},
            "Nord": {"bg": "#2e3440", "fg": "#d8dee9"},
            "Dracula": {"bg": "#282a36", "fg": "#f8f8f2"},
        }

        theme = themes.get(theme_name, themes["Dark"])
        self.root.configure(bg=theme["bg"])
        self.chat_display.configure(bg=theme["bg"], fg=theme["fg"], insertbackground=theme["fg"])

    def update_banner(self):
        if os.getenv("GROQ_API_KEY"):
            self.banner.pack_forget()
        else:
            self.banner.pack(fill="x", pady=5)

    def refresh_chat_list(self):
        self.chat_listbox.delete(0, tk.END)
        for chat in reversed(self.chat_history.get_all_chats()):
            self.chat_listbox.insert(tk.END, chat["title"][:30])

    def on_chat_select(self, event):
        selection = self.chat_listbox.curselection()
        if selection:
            index = selection[0]
            chats = list(reversed(self.chat_history.get_all_chats()))
            if index < len(chats):
                self.load_chat(chats[index]["id"])

    def on_new_chat(self):
        self.current_chat_id = self.chat_history.create_chat()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        greeting = self.config.get("greeting_message", "Hey! I'm Riko. 😊")
        self.add_chat_message("Riko", greeting, is_system=True)
        self.refresh_chat_list()

    def load_chat(self, chat_id):
        self.current_chat_id = chat_id
        chat = self.chat_history.get_chat(chat_id)
        if not chat:
            return

        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)

        for msg in chat["messages"]:
            ts_parts = msg.get("timestamp", "")[:16].split("T")
            time_str = ts_parts[1] if len(ts_parts) == 2 else "00:00"
            
            self.chat_display.insert(tk.END, f"[{time_str}] ", "timestamp")
            
            sender = msg["sender"]
            if sender == "You":
                self.chat_display.insert(tk.END, f"{msg['message']}\n\n", "message")
            else:
                self.chat_display.insert(tk.END, f"{sender}: ", "riko")
                self.chat_display.insert(tk.END, f"{msg['message']}\n\n", "message")

        self.chat_display.config(state=tk.DISABLED)
        self.chat_title.config(text=f"💬 {chat['title']}")

    def delete_current_chat(self):
        if self.current_chat_id is not None:
            if messagebox.askyesno("Delete Chat", "Delete this chat permanently?"):
                self.chat_history.delete_chat(self.current_chat_id)
                self.on_new_chat()

    def add_chat_message(self, sender, message, is_system=False):
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")

        if sender == "You":
            self.chat_display.insert(tk.END, f"{message}\n\n", "message")
        else:
            self.chat_display.insert(tk.END, f"{sender}: ", "riko")
            self.chat_display.insert(tk.END, f"{message}\n\n", "message")

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

        if not is_system:
            self.chat_history.add_message(self.current_chat_id, sender, message)
            # Update title
            chat = self.chat_history.get_chat(self.current_chat_id)
            if chat:
                self.chat_title.config(text=f"💬 {chat['title']}")
            self.refresh_chat_list()

    def on_send_message(self):
        if self.is_thinking:
            return

        if not os.getenv("GROQ_API_KEY"):
            messagebox.showwarning("No API Key", "Please add an API key in Settings.")
            return

        message = self.input_entry.get().strip()
        if not message:
            return

        if self.riko is None:
            self.init_riko()
        if self.riko is None:
            messagebox.showerror("Error", "Could not initialize Riko. Check your API key.")
            return

        self.input_entry.delete(0, tk.END)
        self.add_chat_message("You", message)

        self.is_thinking = True
        self.status_label.config(text="💭 Thinking...", foreground="orange")

        lang_names = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "zh": "Chinese",
            "ko": "Korean", "ar": "Arabic", "ru": "Russian", "hi": "Hindi"
        }
        lang = self.config.get("language", "en")
        prefix = f"[Respond in {lang_names.get(lang, 'English')}] " if lang != "en" else ""

        def get_response():
            try:
                reply = self.riko.reply(prefix + message)
                self.root.after(0, lambda: self.display_response(reply))
            except Exception as e:
                self.root.after(0, lambda: self.display_response(f"❌ Error: {e}"))

        threading.Thread(target=get_response, daemon=True).start()

    def display_response(self, reply):
        self.is_thinking = False
        self.status_label.config(text="● Ready", foreground="green")
        self.add_chat_message("Riko", reply)

    def show_settings(self):
        SettingsWindow(self.root, self.config, self.on_settings_saved)

    def on_settings_saved(self, new_config):
        self.config = new_config
        apply_active_key(self.config)
        self.save_config()
        self.apply_theme()
        self.riko = None
        self.init_riko()
        self.update_banner()
        
        # Reload chat history
        self.chat_history = ChatHistoryManager()
        if not self.chat_history.get_all_chats():
            self.on_new_chat()
        else:
            self.load_chat(self.chat_history.get_all_chats()[-1]["id"])
        self.refresh_chat_list()

    def run(self):
        self.root.mainloop()
