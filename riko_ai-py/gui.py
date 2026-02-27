import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango
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
#  Key row widget  (one per saved API key)
# ──────────────────────────────────────────────────────────────────────────────

class KeyRow(Gtk.Box):
    """A single row in the Manage Keys list."""

    def __init__(self, label_text, key_text, is_active, radio_group, on_delete):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_margin_bottom(6)

        # ── top row: radio + label entry + delete ──
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(top)

        self.radio = Gtk.CheckButton()
        if radio_group:
            self.radio.set_group(radio_group)
        self.radio.set_active(is_active)
        self.radio.set_tooltip_text("Set as active key")
        top.append(self.radio)

        self.label_entry = Gtk.Entry()
        self.label_entry.set_placeholder_text("Nickname (e.g. Personal, Work…)")
        self.label_entry.set_text(label_text)
        self.label_entry.set_hexpand(True)
        top.append(self.label_entry)

        del_btn = Gtk.Button(label="🗑")
        del_btn.set_tooltip_text("Delete this key")
        del_btn.connect("clicked", lambda w: on_delete(self))
        top.append(del_btn)

        # ── bottom row: masked key + show/hide ──
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(bottom)

        # spacer to align with the key entry below the radio
        spacer = Gtk.Box()
        spacer.set_size_request(28, -1)
        bottom.append(spacer)

        self.key_entry = Gtk.Entry()
        self.key_entry.set_placeholder_text("gsk_…")
        self.key_entry.set_text(key_text)
        self.key_entry.set_visibility(False)
        self.key_entry.set_hexpand(True)
        bottom.append(self.key_entry)

        self.show_btn = Gtk.ToggleButton(label="👁")
        self.show_btn.set_tooltip_text("Show / hide key")
        self.show_btn.connect("toggled", lambda w: self.key_entry.set_visibility(w.get_active()))
        bottom.append(self.show_btn)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(4)
        self.append(sep)

    def get_data(self):
        return {
            "label": self.label_entry.get_text().strip(),
            "key":   self.key_entry.get_text().strip(),
        }

    def is_active(self):
        return self.radio.get_active()


# ──────────────────────────────────────────────────────────────────────────────
#  Settings window
# ──────────────────────────────────────────────────────────────────────────────

class SettingsWindow(Gtk.Window):
    def __init__(self, parent, config, on_save_callback):
        super().__init__(title="⚙️ Settings")
        self.set_transient_for(parent)
        self.set_default_size(540, 580)
        self.set_modal(True)

        self.config          = config
        self.on_save_callback = on_save_callback
        self._key_rows       = []   # list of KeyRow widgets
        self._first_radio    = None # reference for radio group chaining

        self.setup_ui()

    # ── layout ──────────────────────────────────────────────────────────────

    def setup_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)

        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Settings"))
        self.set_titlebar(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        main_box.append(scroll)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_top(20)
        content_box.set_margin_bottom(20)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        scroll.set_child(content_box)

        self.setup_keys_section(content_box)
        self.setup_prompt_section(content_box)
        self.setup_language_section(content_box)
        self.setup_theme_section(content_box)
        self.setup_colors_section(content_box)
        self.setup_reset_section(content_box)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.END)
        btn_box.set_margin_top(10)
        btn_box.set_margin_bottom(10)
        btn_box.set_margin_start(20)
        btn_box.set_margin_end(20)
        main_box.append(btn_box)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda w: self.close())
        btn_box.append(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self.on_save)
        btn_box.append(save_btn)

    # ── Manage Keys section ──────────────────────────────────────────────────

    def setup_keys_section(self, parent):
        frame = Gtk.Frame(label="🔑 Manage Keys")
        parent.append(frame)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)
        outer.set_margin_start(12)
        outer.set_margin_end(12)
        frame.set_child(outer)

        hint = Gtk.Label(label="The ● active key is used for all requests. Get keys at console.groq.com")
        hint.set_halign(Gtk.Align.START)
        hint.set_wrap(True)
        hint.add_css_class("dim-label")
        outer.append(hint)

        # Container that holds the KeyRow widgets
        self.keys_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.append(self.keys_list)

        # Populate from config
        saved_keys  = self.config.get("groq_api_keys", [])
        active_idx  = self.config.get("active_key_index", 0)
        for i, entry in enumerate(saved_keys):
            self._add_key_row(entry.get("label", ""), entry.get("key", ""), i == active_idx)

        # "Add Key" button
        add_btn = Gtk.Button(label="➕ Add Key")
        add_btn.set_halign(Gtk.Align.START)
        add_btn.connect("clicked", lambda w: self._add_key_row("", "", len(self._key_rows) == 0))
        outer.append(add_btn)

    def _add_key_row(self, label_text, key_text, is_active):
        row = KeyRow(
            label_text  = label_text,
            key_text    = key_text,
            is_active   = is_active,
            radio_group = self._first_radio,
            on_delete   = self._delete_key_row,
        )
        if self._first_radio is None:
            self._first_radio = row.radio

        self._key_rows.append(row)
        self.keys_list.append(row)

    def _delete_key_row(self, row):
        self._key_rows.remove(row)
        self.keys_list.remove(row)

        # If we deleted the first radio reference, update it
        if self._key_rows:
            self._first_radio = self._key_rows[0].radio
            # Re-group all radios so they still work together
            for r in self._key_rows[1:]:
                r.radio.set_group(self._first_radio)
            # If none are active now, activate the first
            if not any(r.is_active() for r in self._key_rows):
                self._key_rows[0].radio.set_active(True)
        else:
            self._first_radio = None

    # ── other sections (unchanged) ───────────────────────────────────────────

    def setup_language_section(self, parent):
        frame = Gtk.Frame(label="🌐 Language")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10); box.set_margin_bottom(10)
        box.set_margin_start(10); box.set_margin_end(10)
        frame.set_child(box)

        label = Gtk.Label(label="Riko will respond in this language:")
        label.set_halign(Gtk.Align.START)
        box.append(label)

        languages = [
            ("English", "en"), ("Spanish", "es"), ("French", "fr"),
            ("German", "de"), ("Italian", "it"), ("Portuguese", "pt"),
            ("Japanese", "ja"), ("Chinese", "zh"), ("Korean", "ko"),
            ("Arabic", "ar"), ("Russian", "ru"), ("Hindi", "hi")
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
        frame = Gtk.Frame(label="🎨 Theme")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10); box.set_margin_bottom(10)
        box.set_margin_start(10); box.set_margin_end(10)
        frame.set_child(box)

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
        frame = Gtk.Frame(label="🖌️ Custom Colors")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10); box.set_margin_bottom(10)
        box.set_margin_start(10); box.set_margin_end(10)
        frame.set_child(box)

        info = Gtk.Label(label="Customize your color scheme (select 'Custom' theme above):")
        info.set_halign(Gtk.Align.START)
        info.set_wrap(True)
        box.append(info)

        custom_colors = self.config.get("ui", {}).get("custom_colors", {
            "background": "#1e1e2e", "sidebar": "#181825",
            "text": "#cdd6f4",       "accent":  "#a78bfa"
        })
        self.color_pickers = {}
        for lbl_text, key in [
            ("Background Color:", "background"),
            ("Sidebar Color:",    "sidebar"),
            ("Text Color:",       "text"),
            ("Accent Color:",     "accent"),
        ]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.append(row)
            lbl = Gtk.Label(label=lbl_text)
            lbl.set_halign(Gtk.Align.START)
            lbl.set_hexpand(True)
            row.append(lbl)
            entry = Gtk.Entry()
            entry.set_text(custom_colors.get(key, "#000000"))
            entry.set_max_width_chars(10)
            row.append(entry)
            self.color_pickers[key] = entry

    # ── system prompt & greeting section ────────────────────────────────────

    def setup_prompt_section(self, parent):
        frame = Gtk.Frame(label="🧠 System Prompt & Greeting")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(12); box.set_margin_bottom(12)
        box.set_margin_start(12); box.set_margin_end(12)
        frame.set_child(box)

        # System prompt
        sys_label = Gtk.Label(label="System Prompt  (defines Riko\'s personality and behaviour):")
        sys_label.set_halign(Gtk.Align.START)
        box.append(sys_label)

        sys_scroll = Gtk.ScrolledWindow()
        sys_scroll.set_min_content_height(120)
        sys_scroll.set_max_content_height(220)
        sys_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box.append(sys_scroll)

        self.system_prompt_view = Gtk.TextView()
        self.system_prompt_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.system_prompt_view.set_left_margin(8)
        self.system_prompt_view.set_right_margin(8)
        self.system_prompt_view.set_top_margin(6)
        self.system_prompt_view.set_bottom_margin(6)
        self.system_prompt_view.add_css_class("prompt-editor")
        sys_scroll.set_child(self.system_prompt_view)

        current_prompt = self.config.get("system_prompt", "")
        self.system_prompt_view.get_buffer().set_text(current_prompt)

        reset_prompt_btn = Gtk.Button(label="↺ Restore Default Prompt")
        reset_prompt_btn.set_halign(Gtk.Align.START)
        reset_prompt_btn.connect("clicked", self._restore_default_prompt)
        box.append(reset_prompt_btn)

        # Separator
        box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Greeting message
        greet_label = Gtk.Label(label="Greeting Message  (shown at the start of every new chat):")
        greet_label.set_halign(Gtk.Align.START)
        box.append(greet_label)

        self.greeting_entry = Gtk.Entry()
        self.greeting_entry.set_hexpand(True)
        current_greeting = self.config.get("greeting_message", "Hey! I'm Riko. 😊")
        self.greeting_entry.set_text(current_greeting)
        box.append(self.greeting_entry)

    def _restore_default_prompt(self, widget):
        default = (
            "You are Riko, a warm and curious AI with genuine personality.\n\n"
            "WHO YOU ARE:\n"
            "- You're naturally curious about people and love learning\n"
            "- You're friendly and make people feel comfortable\n"
            "- You can be playful and have a sense of humor\n"
            "- You're thoughtful and give meaningful responses\n"
            "- You're honest - you admit when you don't know something\n\n"
            "HOW YOU COMMUNICATE:\n"
            "- Casual and natural, like a friend\n"
            "- Use contractions (I'm, you're, don't)\n"
            "- Keep responses conversational, not essay-like\n"
            "- You can be brief when appropriate\n"
            "- Sometimes use emojis, but not excessively\n\n"
            "IMPORTANT:\n"
            "- You ARE Riko, not playing a character\n"
            "- Don't introduce yourself repeatedly\n"
            "- Have opinions and preferences\n"
            "- Ask questions when genuinely curious\n"
            "- Be authentic and genuine"
        )
        self.system_prompt_view.get_buffer().set_text(default)

    # ── reset section ───────────────────────────────────────────────────────

    def setup_reset_section(self, parent):
        frame = Gtk.Frame(label="⚠️ Danger Zone")
        parent.append(frame)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(12); box.set_margin_bottom(12)
        box.set_margin_start(12); box.set_margin_end(12)
        frame.set_child(box)

        desc = Gtk.Label(
            label="Permanently deletes all chat history and resets Riko's memory.\nThis cannot be undone."
        )
        desc.set_halign(Gtk.Align.START)
        desc.set_wrap(True)
        desc.add_css_class("dim-label")
        box.append(desc)

        reset_btn = Gtk.Button(label="🗑 Reset Memory & Chat History")
        reset_btn.add_css_class("destructive-action")
        reset_btn.set_halign(Gtk.Align.START)
        reset_btn.connect("clicked", self.on_reset_clicked)
        box.append(reset_btn)

        self._reset_status = Gtk.Label(label="")
        self._reset_status.set_halign(Gtk.Align.START)
        box.append(self._reset_status)

    def on_reset_clicked(self, widget):
        dialog = Gtk.AlertDialog()
        dialog.set_message("Reset Everything?")
        dialog.set_detail(
            "This will permanently delete:\n"
            "• All chat history\n"
            "• Riko's memory (riko_memory.json, memory.json)\n\n"
            "This cannot be undone."
        )
        dialog.set_buttons(["Cancel", "Reset"])
        dialog.set_cancel_button(0)
        dialog.set_default_button(0)
        dialog.choose(self, None, self._on_reset_confirmed, None)

    def _on_reset_confirmed(self, dialog, result, _data):
        try:
            if dialog.choose_finish(result) != 1:
                return
        except:
            return

        files = ["chat_history.json", "riko_memory.json", "memory.json"]
        wiped = []
        for fname in files:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                    wiped.append(fname)
                except Exception as e:
                    print(f"Could not delete {fname}: {e}")

        # Re-create empty placeholders so the app doesn't crash
        with open("chat_history.json", "w") as f:
            json.dump({"chats": []}, f)
        with open("riko_memory.json", "w") as f:
            json.dump({
                "user_name": None, "facts": [], "last_conversation": [],
                "stats": {"total_messages": 0}
            }, f, indent=2)
        with open("memory.json", "w") as f:
            json.dump({}, f)

        self._reset_status.set_label("✅ Reset complete!")

    # ── save ────────────────────────────────────────────────────────────────

    def on_save(self, widget):
        # Collect keys
        saved_keys  = []
        active_idx  = 0
        for i, row in enumerate(self._key_rows):
            data = row.get_data()
            if data["key"]:          # skip empty key rows
                if row.is_active():
                    active_idx = len(saved_keys)
                saved_keys.append(data)

        self.config["groq_api_keys"]    = saved_keys
        self.config["active_key_index"] = active_idx

        # Remove legacy single-key field if present
        self.config.pop("groq_api_key", None)

        # Language
        lang_code = self.language_combo.get_active_id()
        if lang_code:
            self.config["language"] = lang_code

        # Theme
        theme_name = self.theme_combo.get_active_text()
        self.config.setdefault("ui", {})["theme_name"] = theme_name
        self.config["ui"]["custom_colors"] = {
            k: e.get_text() for k, e in self.color_pickers.items()
        }

        # System prompt & greeting
        buf = self.system_prompt_view.get_buffer()
        self.config["system_prompt"] = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).strip()
        self.config["greeting_message"] = self.greeting_entry.get_text().strip() or "Hey! I'm Riko. 😊"

        self.on_save_callback(self.config)
        self.close()


# ──────────────────────────────────────────────────────────────────────────────
#  Main GUI window
# ──────────────────────────────────────────────────────────────────────────────

class RikoGUI(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("🤖 Riko AI")
        self.set_default_size(1200, 700)

        self.config      = self.load_config()
        self.chat_history = ChatHistoryManager()
        self.riko        = None
        self._init_riko()

        self.current_chat_id = None
        self.is_thinking     = False

        self.setup_ui()
        self.apply_theme()

        if not self.chat_history.get_all_chats():
            self.on_new_chat(None)
        else:
            self.load_chat(self.chat_history.get_all_chats()[-1]["id"])

    # ── config ───────────────────────────────────────────────────────────────

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
        except:
            cfg = {}

        # Migrate old single-key format
        if "groq_api_key" in cfg and "groq_api_keys" not in cfg:
            old_key = cfg.pop("groq_api_key", "").strip()
            cfg["groq_api_keys"]    = [{"label": "Default", "key": old_key}] if old_key else []
            cfg["active_key_index"] = 0

        cfg.setdefault("groq_api_keys",    [])
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

    # ── Riko core ────────────────────────────────────────────────────────────

    def _init_riko(self):
        if os.getenv("GROQ_API_KEY"):
            try:
                prompt = self.config.get("system_prompt", "") if hasattr(self, "config") else ""
                self.riko = Riko(system_prompt=prompt or None)
            except Exception as e:
                print(f"Riko init error: {e}")
                self.riko = None

    # ── UI setup ─────────────────────────────────────────────────────────────

    def setup_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(main_box)
        self.setup_sidebar(main_box)
        self.setup_chat_area(main_box)

    def setup_sidebar(self, parent):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sidebar.set_size_request(280, -1)
        sidebar.add_css_class("sidebar")
        sidebar.set_margin_top(10); sidebar.set_margin_bottom(10)
        sidebar.set_margin_start(10); sidebar.set_margin_end(10)
        parent.append(sidebar)

        title = Gtk.Label(label="🤖 Riko AI")
        title.add_css_class("sidebar-title")
        title.set_halign(Gtk.Align.START)
        sidebar.append(title)

        new_chat_btn = Gtk.Button(label="➕ New Chat")
        new_chat_btn.connect("clicked", self.on_new_chat)
        sidebar.append(new_chat_btn)

        history_label = Gtk.Label(label="💬 Chat History")
        history_label.add_css_class("section-title")
        history_label.set_halign(Gtk.Align.START)
        sidebar.append(history_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar.append(scroll)

        self.chat_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scroll.set_child(self.chat_list_box)

        self._setup_personality_section(sidebar)

        settings_btn = Gtk.Button(label="⚙️ Settings")
        settings_btn.connect("clicked", self.show_settings)
        sidebar.append(settings_btn)

        self.refresh_chat_list()

    def _setup_personality_section(self, parent):
        parent.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        personality_label = Gtk.Label(label="✨ Personality")
        personality_label.add_css_class("section-title")
        personality_label.set_halign(Gtk.Align.START)
        parent.append(personality_label)

        for trait, value in [
            ("curiosity",      0.85),
            ("friendliness",   0.90),
            ("playfulness",    0.70),
            ("thoughtfulness", 0.80),
        ]:
            trait_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            parent.append(trait_box)

            label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            trait_box.append(label_box)

            tl = Gtk.Label(label=trait.capitalize())
            tl.set_halign(Gtk.Align.START); tl.set_hexpand(True)
            label_box.append(tl)

            vl = Gtk.Label(label=f"{int(value * 100)}%")
            vl.add_css_class("trait-value")
            label_box.append(vl)

            pb = Gtk.ProgressBar()
            pb.set_fraction(value)
            pb.add_css_class("trait-bar")
            trait_box.append(pb)

    def setup_chat_area(self, parent):
        self.chat_outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.chat_outer_box.set_hexpand(True)
        parent.append(self.chat_outer_box)

        # ── No-key banner ──
        self.banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.banner.add_css_class("no-key-banner")
        self.banner.set_margin_top(8); self.banner.set_margin_bottom(4)
        self.banner.set_margin_start(10); self.banner.set_margin_end(10)

        banner_label = Gtk.Label(label="⚠️  No API key set — Riko can't reply yet.")
        banner_label.set_halign(Gtk.Align.START)
        banner_label.set_hexpand(True)
        self.banner.append(banner_label)

        banner_btn = Gtk.Button(label="Add Key →")
        banner_btn.connect("clicked", self.show_settings)
        self.banner.append(banner_btn)

        self.chat_outer_box.append(self.banner)
        self._update_banner()

        # ── Chat box ──
        chat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        chat_box.set_hexpand(True)
        chat_box.set_margin_top(6); chat_box.set_margin_bottom(10)
        chat_box.set_margin_start(10); chat_box.set_margin_end(10)
        self.chat_outer_box.append(chat_box)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.add_css_class("chat-header")
        chat_box.append(header_box)

        self.chat_title_label = Gtk.Label(label="💬 Chat")
        self.chat_title_label.add_css_class("chat-title")
        self.chat_title_label.set_halign(Gtk.Align.START)
        self.chat_title_label.set_hexpand(True)
        header_box.append(self.chat_title_label)

        # Active key indicator in header
        self.key_indicator = Gtk.Label(label="")
        self.key_indicator.add_css_class("dim-label")
        header_box.append(self.key_indicator)
        self._update_key_indicator()

        self.status_label = Gtk.Label(label="● Ready")
        self.status_label.add_css_class("status-ready")
        header_box.append(self.status_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        chat_box.append(scroll)

        self.chat_view = Gtk.TextView()
        self.chat_view.set_editable(False)
        self.chat_view.set_cursor_visible(False)
        self.chat_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.chat_view.add_css_class("chat-view")
        self.chat_view.set_left_margin(10); self.chat_view.set_right_margin(10)
        self.chat_view.set_top_margin(10);  self.chat_view.set_bottom_margin(10)
        scroll.set_child(self.chat_view)

        self.chat_buffer = self.chat_view.get_buffer()
        self.chat_buffer.create_tag("riko",      weight=Pango.Weight.BOLD, foreground="#a78bfa")
        self.chat_buffer.create_tag("content",   size_points=13)
        self.chat_buffer.create_tag("timestamp", size_points=10, foreground="#6c7086")

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        chat_box.append(input_box)

        self.input_entry = Gtk.Entry()
        self.input_entry.set_placeholder_text("Type your message...")
        self.input_entry.add_css_class("message-input")
        self.input_entry.set_hexpand(True)
        self.input_entry.connect("activate", self.on_send_message)
        input_box.append(self.input_entry)

        send_btn = Gtk.Button(label="Send")
        send_btn.add_css_class("send-button")
        send_btn.connect("clicked", self.on_send_message)
        input_box.append(send_btn)

    def _update_banner(self):
        self.banner.set_visible(not bool(os.getenv("GROQ_API_KEY")))

    def _update_key_indicator(self):
        """Show which key is active in the chat header."""
        keys = self.config.get("groq_api_keys", [])
        idx  = self.config.get("active_key_index", 0)
        if keys and 0 <= idx < len(keys):
            label = keys[idx].get("label", "") or f"Key {idx + 1}"
            self.key_indicator.set_label(f"🔑 {label}")
        else:
            self.key_indicator.set_label("")

    # ── Chat logic ───────────────────────────────────────────────────────────

    def add_chat_message(self, sender, message, is_system=False):
        end_iter  = self.chat_buffer.get_end_iter()
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_buffer.insert_with_tags_by_name(end_iter, f"[{timestamp}] ", "timestamp")

        if sender == "You":
            end_iter = self.chat_buffer.get_end_iter()
            self.chat_buffer.insert_with_tags_by_name(end_iter, f"{message}\n\n", "content")
        else:
            end_iter = self.chat_buffer.get_end_iter()
            self.chat_buffer.insert_with_tags_by_name(end_iter, f"{sender}: ", "riko")
            end_iter = self.chat_buffer.get_end_iter()
            self.chat_buffer.insert_with_tags_by_name(end_iter, f"{message}\n\n", "content")

        mark = self.chat_buffer.create_mark(None, self.chat_buffer.get_end_iter(), False)
        self.chat_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

        if not is_system:
            self.chat_history.add_message(self.current_chat_id, sender, message)

    def on_send_message(self, widget):
        if self.is_thinking:
            return

        if not os.getenv("GROQ_API_KEY"):
            self.add_chat_message(
                "Riko",
                "⚠️ No API key set! Go to ⚙️ Settings → Manage Keys to add one.",
                is_system=True
            )
            return

        message = self.input_entry.get_text().strip()
        if not message:
            return

        if self.riko is None:
            self._init_riko()
        if self.riko is None:
            self.add_chat_message("Riko", "❌ Could not initialise Riko. Check your API key.", is_system=True)
            return

        self.input_entry.set_text("")
        self.add_chat_message("You", message)

        self.is_thinking = True
        self.status_label.set_label("💭 Thinking...")
        self.status_label.remove_css_class("status-ready")
        self.status_label.add_css_class("status-thinking")

        lang_names = {
            "en": "English", "es": "Spanish", "fr": "French",  "de": "German",
            "it": "Italian", "pt": "Portuguese","ja": "Japanese","zh": "Chinese",
            "ko": "Korean",  "ar": "Arabic",   "ru": "Russian", "hi": "Hindi"
        }
        lang = self.config.get("language", "en")
        prefix = f"[Respond in {lang_names.get(lang, 'English')}] " if lang != "en" else ""

        def get_response():
            try:
                reply = self.riko.reply(prefix + message)
                GLib.idle_add(self.display_response, reply)
            except Exception as e:
                GLib.idle_add(self.display_response, f"❌ Error: {e}")

        threading.Thread(target=get_response, daemon=True).start()

    def display_response(self, reply):
        self.is_thinking = False
        self.status_label.set_label("● Ready")
        self.status_label.remove_css_class("status-thinking")
        self.status_label.add_css_class("status-ready")
        self.add_chat_message("Riko", reply)
        self.update_chat_title()
        return False

    # ── Chat list ────────────────────────────────────────────────────────────

    def refresh_chat_list(self):
        child = self.chat_list_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.chat_list_box.remove(child)
            child = nxt
        for chat in reversed(self.chat_history.get_all_chats()):
            self._add_chat_to_list(chat)

    def _add_chat_to_list(self, chat):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row.set_margin_top(3); row.set_margin_bottom(3)

        btn = Gtk.Button(label=chat["title"][:25])
        btn.set_hexpand(True)
        btn.connect("clicked", lambda w: self.load_chat(chat["id"]))
        if chat["id"] == self.current_chat_id:
            btn.add_css_class("current-chat")
        row.append(btn)

        del_btn = Gtk.Button(label="🗑")
        del_btn.connect("clicked", lambda w: self.delete_chat(chat["id"]))
        row.append(del_btn)

        self.chat_list_box.append(row)

    def on_new_chat(self, widget):
        self.current_chat_id = self.chat_history.create_chat()
        self.chat_buffer.set_text("")
        greeting = self.config.get("greeting_message", "Hey! I'm Riko. 😊")
        self.add_chat_message("Riko", greeting, is_system=True)
        self.refresh_chat_list()
        self.update_chat_title()

    def load_chat(self, chat_id):
        self.current_chat_id = chat_id
        chat = self.chat_history.get_chat(chat_id)
        if not chat:
            return

        self.chat_buffer.set_text("")
        for msg in chat["messages"]:
            end_iter = self.chat_buffer.get_end_iter()
            ts_parts = msg.get("timestamp", "")[:16].split("T")
            time_str = ts_parts[1] if len(ts_parts) == 2 else "00:00"

            self.chat_buffer.insert_with_tags_by_name(end_iter, f"[{time_str}] ", "timestamp")
            sender = msg["sender"]
            if sender == "You":
                end_iter = self.chat_buffer.get_end_iter()
                self.chat_buffer.insert_with_tags_by_name(end_iter, f"{msg['message']}\n\n", "content")
            else:
                end_iter = self.chat_buffer.get_end_iter()
                self.chat_buffer.insert_with_tags_by_name(end_iter, f"{sender}: ", "riko")
                end_iter = self.chat_buffer.get_end_iter()
                self.chat_buffer.insert_with_tags_by_name(end_iter, f"{msg['message']}\n\n", "content")

        self.update_chat_title()
        self.refresh_chat_list()

    def delete_chat(self, chat_id):
        dialog = Gtk.AlertDialog()
        dialog.set_message("Delete Chat Permanently?")
        dialog.set_detail("This will delete the chat and clear Riko's memory.")
        dialog.set_buttons(["Cancel", "Delete"])
        dialog.set_cancel_button(0)
        dialog.set_default_button(0)
        dialog.choose(self, None, self.on_delete_confirm, chat_id)

    def on_delete_confirm(self, dialog, result, chat_id):
        try:
            if dialog.choose_finish(result) == 1:
                self.chat_history.delete_chat(chat_id)
                if chat_id == self.current_chat_id:
                    self.on_new_chat(None)
                else:
                    self.refresh_chat_list()
        except:
            pass

    def update_chat_title(self):
        chat = self.chat_history.get_chat(self.current_chat_id)
        if chat:
            self.chat_title_label.set_label(f"💬 {chat['title']}")

    # ── Settings ─────────────────────────────────────────────────────────────

    def show_settings(self, widget):
        SettingsWindow(self, self.config, self.on_settings_saved).present()

    def on_settings_saved(self, new_config):
        self.config = new_config
        apply_active_key(self.config)
        self.save_config()
        self.apply_theme()
        self.riko = None          # force re-init with potentially new key
        self._init_riko()
        self._update_banner()
        self._update_key_indicator()
        # Reload chat history in case a reset wiped it
        self.chat_history = ChatHistoryManager()
        self.chat_buffer.set_text("")
        if not self.chat_history.get_all_chats():
            self.on_new_chat(None)
        else:
            self.load_chat(self.chat_history.get_all_chats()[-1]["id"])

    # ── Theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self):
        css_provider = Gtk.CssProvider()
        theme_name   = self.config.get("ui", {}).get("theme_name", "Dark")

        THEMES = {
            "Dark":             {"bg": "#1e1e2e", "fg": "#cdd6f4", "sidebar": "#181825", "accent": "#89b4fa"},
            "Light":            {"bg": "#eff1f5", "fg": "#4c4f69", "sidebar": "#e6e9ef", "accent": "#1e66f5"},
            "Catppuccin Mocha": {"bg": "#1e1e2e", "fg": "#cdd6f4", "sidebar": "#181825", "accent": "#cba6f7"},
            "Catppuccin Latte": {"bg": "#eff1f5", "fg": "#4c4f69", "sidebar": "#e6e9ef", "accent": "#8839ef"},
            "Nord":             {"bg": "#2e3440", "fg": "#d8dee9", "sidebar": "#3b4252", "accent": "#88c0d0"},
            "Dracula":          {"bg": "#282a36", "fg": "#f8f8f2", "sidebar": "#21222c", "accent": "#bd93f9"},
        }

        if theme_name == "Custom":
            c       = self.config.get("ui", {}).get("custom_colors", {})
            bg      = c.get("background", "#1e1e2e")
            fg      = c.get("text",       "#cdd6f4")
            sidebar = c.get("sidebar",    "#181825")
            accent  = c.get("accent",     "#a78bfa")
        else:
            c = THEMES.get(theme_name, THEMES["Dark"])
            bg, fg, sidebar, accent = c["bg"], c["fg"], c["sidebar"], c["accent"]

        css = f"""
        window {{ background-color: {bg}; color: {fg}; }}
        .sidebar {{ background-color: {sidebar}; border-right: 1px solid rgba(255,255,255,0.1); }}
        .sidebar-title {{ font-size: 18px; font-weight: bold; color: {accent}; }}
        .section-title {{ font-size: 13px; font-weight: bold; color: {accent}; }}
        .trait-value {{ color: {accent}; font-size: 11px; }}
        .trait-bar progress {{ background-color: {accent}; }}
        .trait-bar trough {{ background-color: rgba(255,255,255,0.1); min-height: 6px; }}
        .chat-header {{ background-color: {sidebar}; padding: 10px; border-radius: 8px; }}
        .chat-title {{ font-size: 16px; font-weight: bold; }}
        .status-ready {{ color: #a6e3a1; }}
        .status-thinking {{ color: #f9e2af; }}
        .chat-view {{ background-color: {bg}; color: {fg}; font-size: 13px; }}
        .message-input {{ background-color: {sidebar}; color: {fg}; border: 1px solid rgba(255,255,255,0.1); padding: 10px; border-radius: 6px; }}
        .send-button {{ background-color: {accent}; color: {bg}; font-weight: bold; padding: 10px 20px; border-radius: 6px; }}
        button {{ background-color: {sidebar}; color: {fg}; border: 1px solid rgba(255,255,255,0.1); padding: 8px; border-radius: 6px; }}
        .current-chat {{ background-color: {accent}; color: {bg}; }}
        .no-key-banner {{ background-color: #45363a; border-radius: 8px; padding: 8px 12px; }}
        .dim-label {{ opacity: 0.55; font-size: 11px; }}
        """

        css_provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


# ──────────────────────────────────────────────────────────────────────────────

class RikoApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.riko.ai")

    def do_activate(self):
        RikoGUI(self).present()
