"""
main.py — Riko AI  (Kivy / Android / Pydroid 3)

Drop this file next to riko.py, config.json, chat_history.json.
Run with:  python main.py
"""

import os, sys, json, threading
from datetime import datetime

# ── Kivy config BEFORE importing kivy.* ──────────────────────────────────────
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")
import kivy
kivy.require("2.0.0")

from kivy.app            import App
from kivy.clock          import Clock
from kivy.core.window    import Window
from kivy.metrics        import dp
from kivy.lang           import Builder
from kivy.animation      import Animation

from kivy.uix.boxlayout      import BoxLayout
from kivy.uix.scrollview     import ScrollView
from kivy.uix.gridlayout     import GridLayout
from kivy.uix.floatlayout    import FloatLayout
from kivy.uix.label          import Label
from kivy.uix.button         import Button
from kivy.uix.textinput      import TextInput
from kivy.uix.popup          import Popup
from kivy.uix.togglebutton   import ToggleButton
from kivy.uix.slider         import Slider
from kivy.uix.switch         import Switch
from kivy.uix.spinner        import Spinner
from kivy.uix.widget         import Widget
from kivy.uix.image          import Image
from kivy.graphics           import Color, Rectangle, RoundedRectangle, Line

_ZOOM = 1.0

def fz(n):
    """Scaled font size."""
    return dp(n * _ZOOM)

def sz(n):
    """Scaled size (heights, widths, padding)."""
    return dp(n * _ZOOM)

def set_zoom(cfg):
    global _ZOOM
    try:
        _ZOOM = max(0.6, min(2.0, float(cfg.get('ui', {}).get('zoom', 1.0))))
    except:
        _ZOOM = 1.0


# ═══════════════════════════════════════════════════════════════════════════════
#  File paths
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE  = os.path.join(BASE_DIR, "config.json")
HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
MEMORY_FILE  = os.path.join(BASE_DIR, "riko_memory.json")
MEMORY_FILE2 = os.path.join(BASE_DIR, "memory.json")

# Critical on Android - Pydroid CWD is not the script folder
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)


# ═══════════════════════════════════════════════════════════════════════════════
#  Theme definitions
# ═══════════════════════════════════════════════════════════════════════════════

THEMES = {
    "Catppuccin Mocha": {
        "bg":      (0.118, 0.118, 0.180, 1),
        "sidebar": (0.094, 0.094, 0.149, 1),
        "surface": (0.161, 0.161, 0.231, 1),
        "accent":  (0.796, 0.651, 0.969, 1),
        "text":    (0.804, 0.839, 0.957, 1),
        "subtext": (0.651, 0.678, 0.812, 1),
        "input":   (0.161, 0.161, 0.231, 1),
        "user_bubble":  (0.204, 0.204, 0.298, 1),
        "riko_bubble":  (0.141, 0.141, 0.208, 1),
        "danger":  (0.820, 0.298, 0.298, 1),
    },
    "Dark": {
        "bg":      (0.118, 0.118, 0.180, 1),
        "sidebar": (0.094, 0.094, 0.149, 1),
        "surface": (0.145, 0.145, 0.200, 1),
        "accent":  (0.537, 0.706, 0.980, 1),
        "text":    (0.804, 0.839, 0.957, 1),
        "subtext": (0.600, 0.620, 0.700, 1),
        "input":   (0.145, 0.145, 0.200, 1),
        "user_bubble":  (0.180, 0.200, 0.280, 1),
        "riko_bubble":  (0.130, 0.130, 0.190, 1),
        "danger":  (0.820, 0.298, 0.298, 1),
    },
    "Light": {
        "bg":      (0.937, 0.945, 0.961, 1),
        "sidebar": (0.902, 0.914, 0.937, 1),
        "surface": (1.000, 1.000, 1.000, 1),
        "accent":  (0.118, 0.400, 0.961, 1),
        "text":    (0.298, 0.310, 0.412, 1),
        "subtext": (0.510, 0.525, 0.620, 1),
        "input":   (1.000, 1.000, 1.000, 1),
        "user_bubble":  (0.859, 0.882, 0.937, 1),
        "riko_bubble":  (1.000, 1.000, 1.000, 1),
        "danger":  (0.800, 0.200, 0.200, 1),
    },
    "Nord": {
        "bg":      (0.180, 0.204, 0.251, 1),
        "sidebar": (0.231, 0.259, 0.322, 1),
        "surface": (0.263, 0.298, 0.369, 1),
        "accent":  (0.533, 0.753, 0.816, 1),
        "text":    (0.847, 0.871, 0.914, 1),
        "subtext": (0.592, 0.655, 0.757, 1),
        "input":   (0.263, 0.298, 0.369, 1),
        "user_bubble":  (0.298, 0.337, 0.416, 1),
        "riko_bubble":  (0.231, 0.259, 0.322, 1),
        "danger":  (0.749, 0.380, 0.416, 1),
    },
    "Dracula": {
        "bg":      (0.157, 0.165, 0.212, 1),
        "sidebar": (0.129, 0.133, 0.173, 1),
        "surface": (0.247, 0.251, 0.322, 1),
        "accent":  (0.741, 0.576, 0.976, 1),
        "text":    (0.973, 0.973, 0.949, 1),
        "subtext": (0.631, 0.639, 0.761, 1),
        "input":   (0.247, 0.251, 0.322, 1),
        "user_bubble":  (0.267, 0.278, 0.353, 1),
        "riko_bubble":  (0.200, 0.204, 0.263, 1),
        "danger":  (0.918, 0.325, 0.325, 1),
    },
    "Catppuccin Latte": {
        "bg":      (0.937, 0.945, 0.961, 1),
        "sidebar": (0.902, 0.914, 0.937, 1),
        "surface": (1.000, 1.000, 1.000, 1),
        "accent":  (0.533, 0.224, 0.937, 1),
        "text":    (0.298, 0.310, 0.412, 1),
        "subtext": (0.510, 0.525, 0.620, 1),
        "input":   (1.000, 1.000, 1.000, 1),
        "user_bubble":  (0.859, 0.882, 0.937, 1),
        "riko_bubble":  (1.000, 1.000, 1.000, 1),
        "danger":  (0.800, 0.200, 0.200, 1),
    },
}

DEFAULT_THEME = "Catppuccin Mocha"


def hex_to_rgba(h):
    h = h.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return (r/255, g/255, b/255, 1)
    return (0, 0, 0, 1)


# ═══════════════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════════════

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
    except:
        cfg = {}

    # Migrate old single-key
    if "groq_api_key" in cfg and "groq_api_keys" not in cfg:
        old = cfg.pop("groq_api_key", "").strip()
        cfg["groq_api_keys"] = [{"label": "Default", "key": old}] if old else []
        cfg["active_key_index"] = 0

    cfg.setdefault("groq_api_keys",    [])
    cfg.setdefault("active_key_index", 0)
    cfg.setdefault("language",         "en")
    cfg.setdefault("system_prompt",    "")
    cfg.setdefault("greeting_message", "Hey! I'm Riko. ")
    cfg.setdefault("ui", {"theme_name": DEFAULT_THEME, "custom_colors": {}, "zoom": 1.0})
    cfg["ui"].setdefault("theme_name",    DEFAULT_THEME)
    cfg["ui"].setdefault("zoom", 1.0)
    cfg["ui"].setdefault("custom_colors", {})

    apply_active_key(cfg)
    set_zoom(cfg)
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Config save error: {e}")


def apply_active_key(cfg):
    keys = cfg.get("groq_api_keys", [])
    idx  = cfg.get("active_key_index", 0)
    if keys and 0 <= idx < len(keys):
        key = keys[idx].get("key", "").strip()
        if key:
            os.environ["GROQ_API_KEY"] = key
            return
    os.environ.pop("GROQ_API_KEY", None)


def get_active_key_label(cfg):
    keys = cfg.get("groq_api_keys", [])
    idx  = cfg.get("active_key_index", 0)
    if keys and 0 <= idx < len(keys):
        return keys[idx].get("label", "") or f"Key {idx+1}"
    return ""


def get_theme(cfg):
    name = cfg.get("ui", {}).get("theme_name", DEFAULT_THEME)
    if name == "Custom":
        cc = cfg.get("ui", {}).get("custom_colors", {})
        return {
            "bg":          hex_to_rgba(cc.get("background", "#1e1e2e")),
            "sidebar":     hex_to_rgba(cc.get("sidebar",    "#181825")),
            "surface":     hex_to_rgba(cc.get("surface",    "#313244")),
            "accent":      hex_to_rgba(cc.get("accent",     "#cba6f7")),
            "text":        hex_to_rgba(cc.get("text",       "#cdd6f4")),
            "subtext":     hex_to_rgba(cc.get("subtext",    "#a6adc8")),
            "input":       hex_to_rgba(cc.get("input",      "#313244")),
            "user_bubble": hex_to_rgba(cc.get("user_bubble","#313244")),
            "riko_bubble": hex_to_rgba(cc.get("riko_bubble","#24273a")),
            "danger":      (0.82, 0.30, 0.30, 1),
        }
    return THEMES.get(name, THEMES[DEFAULT_THEME])


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat history
# ═══════════════════════════════════════════════════════════════════════════════

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        return data if "chats" in data else {"chats": []}
    except:
        return {"chats": []}


def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"History save: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Themed widget helpers
# ═══════════════════════════════════════════════════════════════════════════════

def make_rect_bg(widget, color):
    """Draw a solid rectangle background on a widget."""
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda w, v: setattr(rect, 'pos', v),
                size=lambda w, v: setattr(rect, 'size', v))
    return rect


def make_rounded_bg(widget, color, radius=10):
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda w, v: setattr(rect, 'pos', v),
                size=lambda w, v: setattr(rect, 'size', v))
    return rect


def themed_button(text, theme, bg_key="surface", accent=False, danger=False, **kwargs):
    color = theme["danger"] if danger else (theme["accent"] if accent else theme[bg_key])
    txt_color = theme["bg"] if accent or danger else theme["text"]
    btn = Button(
        text=text,
        color=txt_color,
        background_normal="",
        background_color=color,
        font_size=fz(13),
        **kwargs
    )
    return btn


def themed_label(text, theme, key="text", font_size=14, bold=False, **kwargs):
    return Label(
        text=text,
        color=theme[key],
        font_size=dp(font_size),
        bold=bold,
        **kwargs
    )


def themed_input(hint, theme, multiline=False, **kwargs):
    ti = TextInput(
        hint_text=hint,
        multiline=multiline,
        background_color=theme["input"],
        foreground_color=theme["text"],
        hint_text_color=(*theme["subtext"][:3], 0.7),
        cursor_color=theme["accent"],
        font_size=fz(13),
        padding=[sz(10), sz(8)],
        **kwargs
    )
    return ti


# ═══════════════════════════════════════════════════════════════════════════════
#  Message bubble
# ═══════════════════════════════════════════════════════════════════════════════

class MessageBubble(BoxLayout):
    def __init__(self, sender, text, timestamp, theme, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None,
                         padding=[sz(4), sz(2)], spacing=sz(2), **kwargs)

        is_user = sender == "You"
        bubble_color = theme["user_bubble"] if is_user else theme["riko_bubble"]
        align = "right" if is_user else "left"

        # Sender + timestamp row
        meta_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=sz(18))
        if is_user:
            meta_box.add_widget(Widget())
        ts_lbl = Label(
            text=f"[{timestamp}]  {sender}",
            color=theme["subtext"],
            font_size=fz(11),
            size_hint_x=None,
            halign=align,
        )
        ts_lbl.bind(texture_size=lambda w, v: setattr(w, 'width', v[0]))
        meta_box.add_widget(ts_lbl)
        if not is_user:
            meta_box.add_widget(Widget())
        self.add_widget(meta_box)

        # Bubble
        bubble = BoxLayout(orientation="horizontal", size_hint_y=None, padding=[0, dp(2)])
        if is_user:
            bubble.add_widget(Widget(size_hint_x=0.15))

        msg_label = Label(
            text=text,
            color=theme["text"],
            font_size=fz(14),
            text_size=(None, None),
            halign=align,
            valign="top",
            markup=True,
        )

        inner = BoxLayout(size_hint_x=0.85, size_hint_y=None, padding=sz(10))
        make_rounded_bg(inner, bubble_color, radius=dp(10))

        def update_label_width(inner_w, inner_size):
            msg_label.text_size = (inner_size[0] - dp(20), None)

        inner.bind(size=update_label_width)

        def update_heights(lbl, tex_size):
            lbl.height = tex_size[1]
            inner.height = tex_size[1] + dp(20)
            bubble.height = inner.height + dp(4)
            self.height = bubble.height + meta_box.height + dp(8)

        msg_label.bind(texture_size=update_heights)
        inner.add_widget(msg_label)
        bubble.add_widget(inner)

        if not is_user:
            bubble.add_widget(Widget(size_hint_x=0.15))

        self.add_widget(bubble)
        # Trigger initial sizing
        Clock.schedule_once(lambda dt: update_heights(
            msg_label, msg_label.texture_size if msg_label.texture else (0, dp(20))), 0.05)


# ═══════════════════════════════════════════════════════════════════════════════
#  Sidebar
# ═══════════════════════════════════════════════════════════════════════════════

class Sidebar(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", spacing=sz(6),
                         padding=[sz(10), sz(10), sz(10), sz(10)], **kwargs)
        self.app = app
        self._chat_buttons = []
        self.build()

    def build(self):
        theme = self.app.theme
        make_rect_bg(self, theme["sidebar"])

        # Title
        title = themed_label("Riko AI", theme, font_size=18, bold=True,
                              size_hint_y=None, height=sz(40), halign="left")
        title.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        self.add_widget(title)

        # New chat button
        new_btn = themed_button("+ New Chat", theme, accent=True,
                                size_hint_y=None, height=sz(44))
        new_btn.bind(on_release=lambda _: self.app.on_new_chat())
        self.add_widget(new_btn)

        # Chat history label
        hist_lbl = themed_label("Chat History", theme, key="subtext",
                                 font_size=11, size_hint_y=None, height=sz(24),
                                 halign="left")
        hist_lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        self.add_widget(hist_lbl)

        # Chat list scroll
        chat_scroll = ScrollView(size_hint_y=1)
        self.chat_list = GridLayout(cols=1, spacing=sz(4),
                                    size_hint_y=None, padding=[0, dp(2)])
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        chat_scroll.add_widget(self.chat_list)
        self.add_widget(chat_scroll)

        # Settings button
        settings_btn = themed_button("Settings", theme,
                                      size_hint_y=None, height=sz(44))
        settings_btn.bind(on_release=lambda _: self.app.show_settings())
        self.add_widget(settings_btn)


    def refresh_chat_list(self):
        theme = self.app.theme
        self.chat_list.clear_widgets()
        chats = self.app.history.get("chats", [])
        for chat in reversed(chats):
            cid   = chat["id"]
            title = chat.get("title", "Chat")[:22]

            row = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=sz(40), spacing=sz(4))

            is_current = cid == self.app.current_chat_id
            btn_color  = theme["accent"] if is_current else theme["surface"]
            txt_color  = theme["bg"]     if is_current else theme["text"]

            chat_btn = Button(
                text=title,
                background_normal="", background_color=btn_color,
                color=txt_color, font_size=fz(12),
                size_hint_x=1, halign="left", text_size=(None, None),
            )
            chat_btn.bind(size=lambda w, _: setattr(w, 'text_size', (w.width - dp(10), None)))
            chat_btn.bind(on_release=lambda _, cid=cid: self.app.load_chat(cid))

            del_btn = Button(
                text="X", background_normal="", background_color=theme["surface"],
                color=theme["danger"], font_size=fz(14),
                size_hint_x=None, width=sz(36),
            )
            del_btn.bind(on_release=lambda _, cid=cid: self.app.confirm_delete_chat(cid))

            row.add_widget(chat_btn)
            row.add_widget(del_btn)
            self.chat_list.add_widget(row)


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat area
# ═══════════════════════════════════════════════════════════════════════════════

class ChatArea(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", spacing=0, **kwargs)
        self.app = app
        self.build()

    def build(self):
        theme = self.app.theme
        make_rect_bg(self, theme["bg"])

        # ── Header ──
        hdr = BoxLayout(orientation="horizontal", size_hint_y=None,
                         height=sz(54), padding=[sz(10), sz(8)], spacing=sz(8))
        make_rect_bg(hdr, theme["surface"])

        # Hamburger to toggle sidebar
        self.toggle_btn = Button(
            text="=", background_normal="", background_color=(0,0,0,0),
            color=theme["accent"], font_size=fz(22),
            size_hint_x=None, width=sz(40),
        )
        self.toggle_btn.bind(on_release=lambda _: self.app.toggle_sidebar())
        hdr.add_widget(self.toggle_btn)

        self.title_lbl = themed_label("Chat", theme, font_size=14, bold=True,
                                       halign="left", size_hint_x=1)
        self.title_lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        hdr.add_widget(self.title_lbl)

        self.key_lbl = themed_label("", theme, key="subtext", font_size=10,
                                     halign="right", size_hint_x=None)
        self.key_lbl.bind(texture_size=lambda w, v: setattr(w, 'width', v[0] + dp(4)))
        hdr.add_widget(self.key_lbl)

        self.status_lbl = themed_label("* Ready", theme, key="accent",
                                        font_size=11, size_hint_x=None, width=sz(80),
                                        halign="right")
        self.status_lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        hdr.add_widget(self.status_lbl)
        self.add_widget(hdr)

        # ── No-key banner ──
        self.banner = BoxLayout(orientation="horizontal", size_hint_y=None,
                                 height=sz(44), padding=[sz(10), sz(6)], spacing=sz(8))
        with self.banner.canvas.before:
            Color(0.27, 0.21, 0.23, 1)
            self._banner_rect = Rectangle(pos=self.banner.pos, size=self.banner.size)
        self.banner.bind(pos=lambda w, v: setattr(self._banner_rect, 'pos', v),
                          size=lambda w, v: setattr(self._banner_rect, 'size', v))
        banner_lbl = Label(text="No API key - Riko can't reply yet.",
                            color=(1, 0.8, 0.4, 1), font_size=fz(12), halign="left")
        banner_lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        add_key_btn = Button(text="Add Key", background_normal="",
                              background_color=theme["accent"],
                              color=theme["bg"], font_size=fz(12),
                              size_hint_x=None, width=sz(70))
        add_key_btn.bind(on_release=lambda _: self.app.show_settings())
        self.banner.add_widget(banner_lbl)
        self.banner.add_widget(add_key_btn)
        self.add_widget(self.banner)

        # ── Message scroll ──
        self.msg_scroll = ScrollView(size_hint_y=1, do_scroll_x=False)
        self.msg_list = GridLayout(cols=1, spacing=sz(6), size_hint_y=None,
                                    padding=[sz(8), sz(8)])
        self.msg_list.bind(minimum_height=self.msg_list.setter('height'))
        self.msg_scroll.add_widget(self.msg_list)
        self.add_widget(self.msg_scroll)

        # ── Input bar ──
        input_bar = BoxLayout(orientation="horizontal", size_hint_y=None,
                               height=sz(64), padding=[sz(8), sz(8)], spacing=sz(8))
        make_rect_bg(input_bar, theme["surface"])

        self.input_field = TextInput(
            hint_text="Type a message…",
            multiline=False,
            background_color=theme["input"],
            foreground_color=theme["text"],
            hint_text_color=(*theme["subtext"][:3], 0.7),
            cursor_color=theme["accent"],
            font_size=fz(13),
            padding=[sz(10), sz(10)],
        )
        self.input_field.bind(on_text_validate=lambda _: self.app.on_send())

        send_btn = Button(
            text="Send",
            background_normal="", background_color=theme["accent"],
            color=theme["bg"], font_size=fz(13), bold=True,
            size_hint_x=None, width=sz(70),
        )
        send_btn.bind(on_release=lambda _: self.app.on_send())
        input_bar.add_widget(self.input_field)
        input_bar.add_widget(send_btn)
        self.add_widget(input_bar)

    def update_banner(self):
        has_key = bool(os.getenv("GROQ_API_KEY"))
        self.banner.height = 0 if has_key else dp(44)
        self.banner.opacity = 0 if has_key else 1
        self.banner.disabled = has_key

    def set_status(self, text, color=None):
        theme = self.app.theme
        self.status_lbl.text  = text
        self.status_lbl.color = color or theme["accent"]

    def set_title(self, text):
        self.title_lbl.text = f" {text}"

    def set_key_label(self, text):
        self.key_lbl.text = f"[Key] {text}" if text else ""

    def add_message(self, sender, text, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M")
        bubble = MessageBubble(sender, text, timestamp, self.app.theme)
        self.msg_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: self._scroll_bottom(), 0.15)

    def _scroll_bottom(self):
        self.msg_scroll.scroll_y = 0

    def clear_messages(self):
        self.msg_list.clear_widgets()


# ═══════════════════════════════════════════════════════════════════════════════
#  Settings popup
# ═══════════════════════════════════════════════════════════════════════════════

class SettingsPopup(Popup):
    def __init__(self, app, **kwargs):
        self.riko_app = app
        theme = app.theme
        super().__init__(
            title="  Settings",
            title_color=theme["text"],
            separator_color=theme["accent"],
            background_color=theme["bg"],
            size_hint=(0.97, 0.95),
            **kwargs
        )
        self._key_rows = []   # list of dicts with widgets
        self.build()

    def build(self):
        app   = self.riko_app
        theme = app.theme
        cfg   = app.cfg

        root = BoxLayout(orientation="vertical", spacing=sz(8),
                          padding=[sz(6), sz(6)])

        scroll = ScrollView()
        content = GridLayout(cols=1, spacing=sz(10), size_hint_y=None,
                              padding=[sz(4), sz(4)])
        content.bind(minimum_height=content.setter('height'))
        scroll.add_widget(content)
        root.add_widget(scroll)

        # ── API Keys ──────────────────────────────────────────────────────────
        content.add_widget(self._section_header("[Key] API Keys", theme))
        hint = themed_label(
            "Select the active key (*). Get keys at console.groq.com",
            theme, key="subtext", font_size=11, size_hint_y=None, height=sz(30),
            halign="left")
        hint.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        content.add_widget(hint)

        self.keys_box = GridLayout(cols=1, spacing=sz(6), size_hint_y=None)
        self.keys_box.bind(minimum_height=self.keys_box.setter('height'))
        content.add_widget(self.keys_box)

        saved_keys = cfg.get("groq_api_keys", [])
        active_idx = cfg.get("active_key_index", 0)
        for i, entry in enumerate(saved_keys):
            self._add_key_row(entry.get("label",""), entry.get("key",""), i == active_idx)

        add_btn = themed_button("+ Add Key", theme, size_hint_y=None, height=sz(40))
        add_btn.bind(on_release=lambda _: self._add_key_row("", "", len(self._key_rows)==0))
        content.add_widget(add_btn)

        # ── System Prompt ─────────────────────────────────────────────────────
        content.add_widget(self._section_header("System Prompt", theme))
        plbl = themed_label("Defines Riko's personality:", theme, key="subtext",
                              font_size=11, size_hint_y=None, height=sz(20), halign="left")
        plbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        content.add_widget(plbl)

        self.prompt_input = TextInput(
            text=cfg.get("system_prompt", ""),
            multiline=True,
            background_color=theme["input"],
            foreground_color=theme["text"],
            hint_text_color=(*theme["subtext"][:3], 0.7),
            cursor_color=theme["accent"],
            font_size=fz(12),
            size_hint_y=None, height=sz(140),
            padding=[sz(8), sz(8)],
        )
        content.add_widget(self.prompt_input)

        restore_btn = themed_button("Restore Default Prompt", theme,
                                     size_hint_y=None, height=sz(38))
        restore_btn.bind(on_release=lambda _: self._restore_prompt())
        content.add_widget(restore_btn)

        # ── Greeting ──────────────────────────────────────────────────────────
        content.add_widget(self._section_header("Greeting Message", theme))
        self.greeting_input = themed_input(
            "Hey! I'm Riko. ", theme,
            size_hint_y=None, height=sz(44),
        )
        self.greeting_input.text = cfg.get("greeting_message", "Hey! I'm Riko. ")
        content.add_widget(self.greeting_input)

        # ── Language ──────────────────────────────────────────────────────────
        content.add_widget(self._section_header("Language", theme))
        langs = ["English","Spanish","French","German","Italian",
                 "Portuguese","Japanese","Chinese","Korean","Arabic","Russian","Hindi"]
        lang_codes = ["en","es","fr","de","it","pt","ja","zh","ko","ar","ru","hi"]
        cur_code = cfg.get("language", "en")
        cur_lang = langs[lang_codes.index(cur_code)] if cur_code in lang_codes else "English"
        self.lang_spinner = Spinner(
            text=cur_lang, values=langs,
            background_normal="", background_color=theme["surface"],
            color=theme["text"], font_size=fz(13),
            size_hint_y=None, height=sz(44),
        )
        self._lang_codes  = lang_codes
        self._lang_names  = langs
        content.add_widget(self.lang_spinner)

        # ── Theme ─────────────────────────────────────────────────────────────
        content.add_widget(self._section_header("Theme", theme))
        theme_names = list(THEMES.keys()) + ["Custom"]
        cur_theme = cfg.get("ui", {}).get("theme_name", DEFAULT_THEME)
        self.theme_spinner = Spinner(
            text=cur_theme if cur_theme in theme_names else DEFAULT_THEME,
            values=theme_names,
            background_normal="", background_color=theme["surface"],
            color=theme["text"], font_size=fz(13),
            size_hint_y=None, height=sz(44),
        )
        content.add_widget(self.theme_spinner)

        # ── Custom Colors ─────────────────────────────────────────────────────
        content.add_widget(self._section_header("Custom Colors (hex)", theme))
        cc = cfg.get("ui", {}).get("custom_colors", {})
        color_fields = [
            ("Background", "background", "#1e1e2e"),
            ("Sidebar",    "sidebar",    "#181825"),
            ("Accent",     "accent",     "#cba6f7"),
            ("Text",       "text",       "#cdd6f4"),
        ]
        self.color_inputs = {}
        for label, key, default in color_fields:
            row = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=sz(40), spacing=sz(8))
            lbl = themed_label(label + ":", theme, font_size=12,
                                size_hint_x=None, width=sz(100))
            ti = themed_input("", theme, size_hint_y=None, height=sz(38))
            ti.text = cc.get(key, default)
            self.color_inputs[key] = ti
            row.add_widget(lbl); row.add_widget(ti)
            content.add_widget(row)

        # ── Zoom ──────────────────────────────────────────────────────────────
        content.add_widget(self._section_header("Zoom / Text Size", theme))
        zoom_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                              height=sz(50), spacing=sz(8))
        cur_zoom = float(cfg.get("ui", {}).get("zoom", 1.0))
        self.zoom_label = Label(
            text=f"Scale: {cur_zoom:.1f}x",
            color=theme["text"], font_size=fz(13),
            size_hint_x=None, width=sz(90))
        self.zoom_slider = Slider(
            min=0.6, max=2.0, value=cur_zoom,
            step=0.1, size_hint_x=1)
        self.zoom_slider.bind(value=lambda s, v: setattr(
            self.zoom_label, "text", f"Scale: {v:.1f}x"))
        zoom_row.add_widget(self.zoom_label)
        zoom_row.add_widget(self.zoom_slider)
        content.add_widget(zoom_row)

        # ── Danger Zone ───────────────────────────────────────────────────────
        content.add_widget(self._section_header("! Danger Zone", theme))
        self.reset_status = themed_label("", theme, key="accent",
                                          font_size=12, size_hint_y=None, height=sz(22),
                                          halign="left")
        self.reset_status.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))

        reset_btn = themed_button("Reset All Memory & Chat History", theme,
                                   danger=True, size_hint_y=None, height=sz(44))
        reset_btn.bind(on_release=lambda _: self._confirm_reset())
        content.add_widget(reset_btn)
        content.add_widget(self.reset_status)

        # ── Save / Cancel ─────────────────────────────────────────────────────
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=sz(50), spacing=sz(10), padding=[0, dp(6)])
        cancel_btn = themed_button("Cancel", theme, size_hint_x=1)
        cancel_btn.bind(on_release=lambda _: self.dismiss())
        save_btn = themed_button("Save", theme, accent=True, size_hint_x=1)
        save_btn.bind(on_release=lambda _: self._save())
        btn_row.add_widget(cancel_btn); btn_row.add_widget(save_btn)
        root.add_widget(btn_row)

        self.content = root

    # ── helpers ───────────────────────────────────────────────────────────────

    def _section_header(self, text, theme):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=sz(34))
        lbl = themed_label(text, theme, key="accent", font_size=13, bold=True,
                            halign="left")
        lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        sep = Widget(size_hint_y=None, height=dp(1))
        make_rect_bg(sep, theme["accent"])
        box.add_widget(lbl); box.add_widget(sep)
        return box

    def _add_key_row(self, label_text, key_text, is_active):
        theme = self.riko_app.theme
        row_data = {}

        outer = BoxLayout(orientation="vertical", size_hint_y=None,
                           height=sz(90), spacing=sz(4))

        # Top: radio-like toggle + nickname
        top = BoxLayout(orientation="horizontal", size_hint_y=None,
                         height=sz(40), spacing=sz(6))

        active_btn = ToggleButton(
            text="*" if is_active else "o",
            group="api_keys",
            state="down" if is_active else "normal",
            background_normal="", background_down="",
            background_color=theme["surface"],
            color=theme["accent"] if is_active else theme["subtext"],
            font_size=fz(18),
            size_hint_x=None, width=sz(36),
        )
        # Keep only one active
        def on_active_toggle(btn, val, row_data=row_data):
            btn.text  = "*" if btn.state == "down" else "o"
            btn.color = theme["accent"] if btn.state == "down" else theme["subtext"]
        active_btn.bind(state=on_active_toggle)
        row_data["active_btn"] = active_btn

        nick = TextInput(
            text=label_text, hint_text="Nickname…",
            multiline=False,
            background_color=theme["input"], foreground_color=theme["text"],
            hint_text_color=(*theme["subtext"][:3], 0.7),
            font_size=fz(12), padding=[sz(8), sz(8)],
        )
        row_data["nick"] = nick

        del_btn = Button(
            text="X", background_normal="", background_color=theme["surface"],
            color=theme["danger"], font_size=fz(16),
            size_hint_x=None, width=sz(36),
        )
        del_btn.bind(on_release=lambda _, r=row_data, o=outer: self._delete_key_row(r, o))
        top.add_widget(active_btn); top.add_widget(nick); top.add_widget(del_btn)

        # Bottom: key field + show/hide
        bottom = BoxLayout(orientation="horizontal", size_hint_y=None,
                            height=sz(40), spacing=sz(6))
        spacer = Widget(size_hint_x=None, width=sz(36))
        key_ti = TextInput(
            text=key_text, hint_text="gsk_…",
            multiline=False, password=True,
            background_color=theme["input"], foreground_color=theme["text"],
            hint_text_color=(*theme["subtext"][:3], 0.7),
            font_size=fz(12), padding=[sz(8), sz(8)],
        )
        row_data["key"] = key_ti

        show_btn = ToggleButton(
            text="Show", background_normal="", background_down="",
            background_color=theme["surface"],
            color=theme["subtext"], font_size=fz(16),
            size_hint_x=None, width=sz(36),
        )
        show_btn.bind(state=lambda btn, state: setattr(key_ti, 'password', state != 'down'))
        bottom.add_widget(spacer); bottom.add_widget(key_ti); bottom.add_widget(show_btn)

        outer.add_widget(top); outer.add_widget(bottom)
        self.keys_box.add_widget(outer)
        row_data["outer"] = outer
        self._key_rows.append(row_data)

    def _delete_key_row(self, row_data, outer):
        if row_data in self._key_rows:
            self._key_rows.remove(row_data)
        self.keys_box.remove_widget(outer)
        # Ensure at least one active if available
        if self._key_rows and not any(
                r["active_btn"].state == "down" for r in self._key_rows):
            self._key_rows[0]["active_btn"].state = "down"

    def _restore_prompt(self):
        self.prompt_input.text = (
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

    def _confirm_reset(self):
        theme = self.riko_app.theme
        confirm = Popup(
            title="Reset Everything?",
            title_color=theme["danger"],
            separator_color=theme["danger"],
            background_color=theme["bg"],
            size_hint=(0.85, 0.40),
        )
        box = BoxLayout(orientation="vertical", spacing=sz(10), padding=sz(12))
        msg = themed_label(
            "This will permanently delete:\n- All chat history\n- Riko's memory\n\nCannot be undone.",
            theme, font_size=12, halign="left")
        msg.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        btns = BoxLayout(orientation="horizontal", size_hint_y=None,
                          height=sz(44), spacing=sz(8))
        cancel = themed_button("Cancel", theme, size_hint_x=1)
        cancel.bind(on_release=confirm.dismiss)
        yes = themed_button("Reset", theme, danger=True, size_hint_x=1)
        yes.bind(on_release=lambda _: self._do_reset(confirm))
        btns.add_widget(cancel); btns.add_widget(yes)
        box.add_widget(msg); box.add_widget(btns)
        confirm.content = box
        confirm.open()

    def _do_reset(self, confirm_popup):
        confirm_popup.dismiss()
        for f in [HISTORY_FILE, MEMORY_FILE, MEMORY_FILE2]:
            try: os.remove(f)
            except: pass
        try:
            with open(HISTORY_FILE, "w") as f: json.dump({"chats": []}, f)
            with open(MEMORY_FILE,  "w") as f:
                json.dump({"user_name": None, "facts": [],
                           "last_conversation": [], "stats": {"total_messages": 0}}, f)
            with open(MEMORY_FILE2, "w") as f: json.dump({}, f)
        except: pass
        self.reset_status.text = "Reset complete!"

    def _save(self):
        app = self.riko_app
        cfg = app.cfg

        # Keys
        new_keys  = []
        active_idx = 0
        for i, row in enumerate(self._key_rows):
            key_val = row["key"].text.strip()
            if not key_val: continue
            if row["active_btn"].state == "down":
                active_idx = len(new_keys)
            new_keys.append({"label": row["nick"].text.strip(), "key": key_val})
        cfg["groq_api_keys"]    = new_keys
        cfg["active_key_index"] = active_idx
        cfg.pop("groq_api_key", None)

        # Language
        lang_name = self.lang_spinner.text
        if lang_name in self._lang_names:
            cfg["language"] = self._lang_codes[self._lang_names.index(lang_name)]

        # Theme
        cfg.setdefault("ui", {})["theme_name"] = self.theme_spinner.text

        # Custom colors
        cfg["ui"]["custom_colors"] = {k: v.text.strip() for k, v in self.color_inputs.items()}

        # Zoom
        cfg.setdefault("ui", {})["zoom"] = round(self.zoom_slider.value, 2)

        # Prompt & greeting
        cfg["system_prompt"]    = self.prompt_input.text.strip()
        cfg["greeting_message"] = self.greeting_input.text.strip() or "Hey! I'm Riko. "

        save_config(cfg)
        apply_active_key(cfg)
        app.on_settings_saved()
        self.dismiss()


# ═══════════════════════════════════════════════════════════════════════════════
#  Root layout  (sidebar + chat, sidebar toggleable)
# ═══════════════════════════════════════════════════════════════════════════════

class RikoRoot(FloatLayout):
    SIDEBAR_WIDTH = sz(240)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.riko_app       = app
        self._sidebar_open  = True
        self._animating     = False
        self._build()

    def _build(self):
        app = self.riko_app

        # Main horizontal split
        self.main_box = BoxLayout(orientation="horizontal",
                                   pos_hint={"x":0,"y":0}, size_hint=(1,1))
        self.add_widget(self.main_box)

        self.sidebar   = Sidebar(app, size_hint_x=None, width=self.SIDEBAR_WIDTH)
        self.chat_area = ChatArea(app, size_hint_x=1)

        self.main_box.add_widget(self.sidebar)
        self.main_box.add_widget(self.chat_area)

    def toggle_sidebar(self):
        if self._animating: return
        self._animating = True
        if self._sidebar_open:
            anim = Animation(width=0, duration=0.25, t="out_quad")
            anim.bind(on_complete=lambda *_: setattr(self, '_animating', False))
            anim.start(self.sidebar)
            self._sidebar_open = False
        else:
            anim = Animation(width=self.SIDEBAR_WIDTH, duration=0.25, t="out_quad")
            anim.bind(on_complete=lambda *_: setattr(self, '_animating', False))
            anim.start(self.sidebar)
            self._sidebar_open = True


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════════════════════

class RikoApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title         = "Riko AI"
        self.cfg        = load_config()
        self.theme         = get_theme(self.cfg)
        self.history       = load_history()
        self.current_chat_id = -1
        self.is_thinking   = False
        self.riko          = None
        self._root_widget  = None

    # ── Kivy entry ────────────────────────────────────────────────────────────

    def build(self):
        Window.clearcolor = self.theme["bg"]
        # Keyboard overlays content instead of resizing the window
        Window.softinput_mode = 'below_target'
        self._root_widget = RikoRoot(self)
        return self._root_widget

    def on_start(self):
        self._init_riko()
        chats = self.history.get("chats", [])
        if not chats:
            self.on_new_chat()
        else:
            self.load_chat(chats[-1]["id"])
        self._update_ui_state()

    # ── Riko init ─────────────────────────────────────────────────────────────

    def _init_riko(self):
        if not os.getenv("GROQ_API_KEY"):
            self.riko = None
            return
        try:
            from riko import Riko
            prompt = self.cfg.get("system_prompt", "").strip() or None
            self.riko = Riko(system_prompt=prompt)
            self._riko_error = None
        except Exception as e:
            print(f"Riko init error: {e}")
            self._riko_error = str(e)
            self.riko = None

    # ── Chat ──────────────────────────────────────────────────────────────────

    def on_new_chat(self):
        chats  = self.history.setdefault("chats", [])
        new_id = len(chats)
        chats.append({
            "id": new_id,
            "title": f"Chat {new_id + 1}",
            "timestamp": datetime.now().isoformat(),
            "messages": []
        })
        save_history(self.history)
        self.current_chat_id = new_id
        self._root_widget.chat_area.clear_messages()
        greeting = self.cfg.get("greeting_message", "Hey! I'm Riko. ")
        self._root_widget.chat_area.add_message("Riko", greeting)
        self._root_widget.sidebar.refresh_chat_list()
        self._update_chat_title()

    def load_chat(self, chat_id):
        chat = self._get_chat(chat_id)
        if not chat:
            return
        self.current_chat_id = chat_id
        ca = self._root_widget.chat_area
        ca.clear_messages()
        for msg in chat.get("messages", []):
            ts_raw = msg.get("timestamp", "")
            ts = ts_raw[11:16] if len(ts_raw) >= 16 else "00:00"
            ca.add_message(msg["sender"], msg["message"], ts)
        self._update_chat_title()
        self._root_widget.sidebar.refresh_chat_list()

    def on_send(self):
        if self.is_thinking:
            return
        ca   = self._root_widget.chat_area
        text = ca.input_field.text.strip()
        if not text:
            return

        if not os.getenv("GROQ_API_KEY"):
            ca.add_message("Riko", "! No API key! Go to Settings → API Keys.")
            return

        if self.riko is None:
            self._init_riko()
        if self.riko is None:
            err = getattr(self, "_riko_error", "unknown error")
            ca.add_message("Riko", f"Could not start Riko: {err}")
            return

        ca.input_field.text = ""
        ca.add_message("You", text)
        self._add_to_history("You", text)

        lang_code = self.cfg.get("language", "en")
        lang_map  = {
            "es":"Spanish","fr":"French","de":"German","it":"Italian",
            "pt":"Portuguese","ja":"Japanese","zh":"Chinese","ko":"Korean",
            "ar":"Arabic","ru":"Russian","hi":"Hindi"
        }
        prefix = f"[Respond in {lang_map[lang_code]}] " if lang_code in lang_map else ""

        self.is_thinking = True
        ca.set_status("Thinking...", color=self.theme["accent"])

        def worker():
            try:
                reply = self.riko.reply(prefix + text)
                Clock.schedule_once(lambda dt: self._on_reply(reply), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._on_reply(f"Error: Error: {e}"), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _on_reply(self, reply):
        self.is_thinking = False
        ca = self._root_widget.chat_area
        ca.set_status("* Ready", color=self.theme["accent"])
        ca.add_message("Riko", reply)
        self._add_to_history("Riko", reply)
        self._update_chat_title()

    def _add_to_history(self, sender, message):
        chat = self._get_chat(self.current_chat_id)
        if not chat:
            return
        chat.setdefault("messages", []).append({
            "sender": sender, "message": message,
            "timestamp": datetime.now().isoformat()
        })
        # Auto-title from first user message
        msgs = chat["messages"]
        if sender == "You" and len(msgs) <= 2:
            title = message[:30] + ("…" if len(message) > 30 else "")
            chat["title"] = title
        save_history(self.history)

    # ── Delete chat ───────────────────────────────────────────────────────────

    def confirm_delete_chat(self, chat_id):
        theme = self.theme
        p = Popup(
            title="Delete Chat?",
            title_color=theme["danger"],
            separator_color=theme["danger"],
            background_color=theme["bg"],
            size_hint=(0.80, 0.35),
        )
        box = BoxLayout(orientation="vertical", spacing=sz(10), padding=sz(12))
        msg = themed_label("Delete this chat and clear memory?",
                            theme, font_size=13, halign="left")
        msg.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        btns = BoxLayout(size_hint_y=None, height=sz(44), spacing=sz(8))
        cancel = themed_button("Cancel", theme, size_hint_x=1)
        cancel.bind(on_release=p.dismiss)
        yes = themed_button("Delete", theme, danger=True, size_hint_x=1)
        yes.bind(on_release=lambda _: self._do_delete_chat(chat_id, p))
        btns.add_widget(cancel); btns.add_widget(yes)
        box.add_widget(msg); box.add_widget(btns)
        p.content = box
        p.open()

    def _do_delete_chat(self, chat_id, popup):
        popup.dismiss()
        chats = self.history.get("chats", [])
        self.history["chats"] = [c for c in chats if c["id"] != chat_id]
        # Re-index
        for i, c in enumerate(self.history["chats"]):
            c["id"] = i
        save_history(self.history)
        if chat_id == self.current_chat_id:
            self.on_new_chat()
        else:
            if self.current_chat_id > chat_id:
                self.current_chat_id -= 1
            self._root_widget.sidebar.refresh_chat_list()

    # ── Settings ──────────────────────────────────────────────────────────────

    def show_settings(self):
        SettingsPopup(self).open()

    def on_settings_saved(self):
        set_zoom(self.cfg)
        self.theme  = get_theme(self.cfg)
        Window.clearcolor = self.theme["bg"]
        self._init_riko()
        self.history = load_history()
        # Rebuild sidebar + chat area to pick up new theme
        rw = self._root_widget
        rw.main_box.clear_widgets()
        rw.sidebar   = Sidebar(self, size_hint_x=None, width=sz(240))
        rw.chat_area = ChatArea(self)
        rw.main_box.add_widget(rw.sidebar)
        rw.main_box.add_widget(rw.chat_area)
        self._update_ui_state()
        chats = self.history.get("chats", [])
        if not chats:
            self.on_new_chat()
        else:
            self.load_chat(chats[-1]["id"])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def toggle_sidebar(self):
        self._root_widget.toggle_sidebar()

    def _get_chat(self, chat_id):
        for c in self.history.get("chats", []):
            if c["id"] == chat_id:
                return c
        return None

    def _update_chat_title(self):
        chat = self._get_chat(self.current_chat_id)
        if chat:
            self._root_widget.chat_area.set_title(chat.get("title", "Chat"))

    def _update_ui_state(self):
        ca = self._root_widget.chat_area
        ca.update_banner()
        label = get_active_key_label(self.cfg)
        ca.set_key_label(label)
        self._root_widget.sidebar.refresh_chat_list()


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    RikoApp().run()
