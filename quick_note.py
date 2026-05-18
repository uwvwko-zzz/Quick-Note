"""
快速记录工具 - Quick Note Tool · Command Center Edition
按 Ctrl+Alt+E 全局热键呼出记录窗口，快速记录信息
数据保存到同级目录下的 notes.json 文件中
"""

import json
import os
import time
import math
import datetime
import ctypes
import ctypes.wintypes
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# 解决 Windows 高 DPI 模糊问题
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ============ 配置 ============
HOTKEY = "ctrl+alt+e"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "notes.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
WINDOW_WIDTH = 560
WINDOW_HEIGHT = 700
# ==============================

# ============ 标签定义 ============
TAGS = {
    "默认": {"color": "#8b8fa3", "icon": "📌"},
    "重要": {"color": "#f43f5e", "icon": "🔴"},
    "待办": {"color": "#f59e0b", "icon": "🟡"},
    "灵感": {"color": "#a78bfa", "icon": "🟣"},
    "代码": {"color": "#34d399", "icon": "🟢"},
    "学习": {"color": "#60a5fa", "icon": "🔵"},
}
TAG_LIST = list(TAGS.keys())

# ============ 主题配色 (Command Center 风格) ============
THEMES = {
    "dark": {
        "bg":               "#0E0E12",
        "surface":          "#16161D",
        "surface_light":    "#1E1E28",
        "surface_hover":    "#26263A",
        "card_bg":          "#181822",
        "card_hover":       "#20202E",
        "card_selected":    "#2A1E4A",
        "card_starred":     "#261E30",
        "input_bg":         "#1A1A26",
        "input_focus_bg":   "#1E1E2C",
        "border":           "#2A2A38",
        "border_focus":     "#7c5cfc",
        "border_light":     "#333348",
        "primary":          "#7c5cfc",
        "primary_hover":    "#9070ff",
        "primary_bg":       "#2A1E50",
        "danger":           "#f0465a",
        "danger_hover":     "#e03050",
        "success":          "#30d8a0",
        "warning":          "#f0c030",
        "text":             "#E4E4F0",
        "text_secondary":   "#8888A8",
        "text_dim":         "#4A4A64",
        "heading":          "#C0B8D8",
        "heading_accent":   "#A890FF",
        "header_bg":        "#0E0E12",
        "footer_bg":        "#0E0E12",
        "search_bg":        "#1A1A26",
        "search_icon":      "#6868A0",
        "pill_inactive_bg": "#1E1E2A",
        "pill_inactive_fg": "#5E5E78",
        "pill_hover_bg":    "#28284A",
        "star_color":       "#f0c030",
        "shadow":           "#08080C",
        "scrollbar_bg":     "#12121A",
        "scrollbar_thumb":  "#30304A",
        "char_counter":     "#3A3A54",
        "char_limit":       "#f0465a",
        "glow_primary":     "#7c5cfc",
        "glow_primary_dim": "#5a3cd0",
        "ambient_1":        "#1a0a3a",
        "ambient_2":        "#0a1a2a",
        "ambient_3":        "#1a0a20",
        "glass_border":     "#2A2A38",
        "glass_bg":         "#1A1A24",
        "timeline_line":    "#1E1E2E",
        "mode_indicator":   "#7c5cfc",
    },
    "light": {
        "bg":               "#F2F2F8",
        "surface":          "#FFFFFF",
        "surface_light":    "#EEEFF4",
        "surface_hover":    "#E0E0F0",
        "card_bg":          "#FFFFFF",
        "card_hover":       "#F0F0FA",
        "card_selected":    "#E0D8FF",
        "card_starred":     "#FFF4E0",
        "input_bg":         "#FFFFFF",
        "input_focus_bg":   "#FCFAFF",
        "border":           "#D0D0E0",
        "border_focus":     "#7c5cfc",
        "border_light":     "#C0C0D4",
        "primary":          "#7c5cfc",
        "primary_hover":    "#6d4df0",
        "primary_bg":       "#E8E0FF",
        "danger":           "#f0465a",
        "danger_hover":     "#e03050",
        "success":          "#20c090",
        "warning":          "#e8a820",
        "text":             "#1A1A2E",
        "text_secondary":   "#605E78",
        "text_dim":         "#A0A0B8",
        "heading":          "#6828d8",
        "heading_accent":   "#7840f0",
        "header_bg":        "#F2F2F8",
        "footer_bg":        "#F2F2F8",
        "search_bg":        "#E8E8F2",
        "search_icon":      "#6868A0",
        "pill_inactive_bg": "#E4E4F0",
        "pill_inactive_fg": "#9090A8",
        "pill_hover_bg":    "#D4D4F0",
        "star_color":       "#e8a820",
        "shadow":           "#C0C0D0",
        "scrollbar_bg":     "#E8E8F0",
        "scrollbar_thumb":  "#C0C0D4",
        "char_counter":     "#B0B0C8",
        "char_limit":       "#f0465a",
        "glow_primary":     "#7c5cfc",
        "glow_primary_dim": "#9880ff",
        "ambient_1":        "#e8e0ff",
        "ambient_2":        "#e0f0ff",
        "ambient_3":        "#f0e0f0",
        "glass_border":     "#D0D0E0",
        "glass_bg":         "#E8E8F0",
        "timeline_line":    "#D8D8E8",
        "mode_indicator":   "#7c5cfc",
    },
}

COLORS = dict(THEMES["dark"])

FONT_FAMILY = "Microsoft YaHei"
FONT_MONO = "Consolas"
# ==================================


def _rounded_rect(canvas, x1, y1, x2, y2, radius=8, **kwargs):
    """在 Canvas 上绘制圆角矩形"""
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def _parse_natural_tags(text):
    """从文本中解析 #标签 自然语言标签"""
    found_tag = "默认"
    clean_text = text
    for tag_name in TAG_LIST:
        patterns = [f"#{tag_name}", f"#{tag_name.lower()}"]
        for pat in patterns:
            if pat in text:
                found_tag = tag_name
                clean_text = text.replace(pat, "").strip()
                # Clean up extra spaces
                while "  " in clean_text:
                    clean_text = clean_text.replace("  ", " ")
                return found_tag, clean_text.strip()
    return found_tag, text.strip()


# ============ Win32 全局热键 API ============
user32 = ctypes.windll.user32

VK_MAP = {
    "ctrl": 0x11, "control": 0x11, "alt": 0x12, "shift": 0x10,
    "win": 0x5B, "windows": 0x5B, "super": 0x5B,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "escape": 0x1B, "esc": 0x1B, "tab": 0x09, "space": 0x20,
    "enter": 0x0D, "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}
MOD_KEYS = {"ctrl", "control", "alt", "shift", "win", "windows", "super"}


def _parse_hotkey(hotkey_str):
    parts = hotkey_str.lower().replace(" ", "").split("+")
    mods, main_key = [], 0
    for p in parts:
        if p in MOD_KEYS:
            vk = VK_MAP.get(p, 0)
            if vk:
                mods.append(vk)
        elif len(p) == 1:
            main_key = ord(p.upper())
        elif p in VK_MAP:
            main_key = VK_MAP[p]
    return mods, main_key


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_current_theme():
    return load_config().get("theme", "dark")


def set_current_theme(theme_name):
    cfg = load_config()
    cfg["theme"] = theme_name
    save_config(cfg)


def apply_theme(theme_name):
    global COLORS
    if theme_name in THEMES:
        COLORS.clear()
        COLORS.update(THEMES[theme_name])


def load_notes():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_notes(notes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def add_note(content, tag="默认"):
    notes = load_notes()
    note = {
        "id": (max((n["id"] for n in notes), default=0) + 1) if notes else 1,
        "content": content.strip(),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tag": tag,
        "starred": False,
    }
    notes.append(note)
    save_notes(notes)
    return note


def delete_note(note_id):
    notes = load_notes()
    notes = [n for n in notes if n["id"] != note_id]
    save_notes(notes)


def update_note(note_id, new_content=None, tag=None, starred=None):
    notes = load_notes()
    for n in notes:
        if n["id"] == note_id:
            if new_content is not None:
                n["content"] = new_content.strip()
                n["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if tag is not None:
                n["tag"] = tag
            if starred is not None:
                n["starred"] = starred
            break
    save_notes(notes)


def format_relative_time(time_str):
    try:
        dt = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        diff = now - dt
        if diff.days == 0:
            if diff.seconds < 60:
                return "刚刚"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}分钟前"
            else:
                return f"今天 {dt.strftime('%H:%M')}"
        elif diff.days == 1:
            return f"昨天 {dt.strftime('%H:%M')}"
        elif diff.days < 7:
            return f"{diff.days}天前"
        elif diff.days < 365:
            return dt.strftime("%m月%d日")
        else:
            return dt.strftime("%Y年%m月%d日")
    except Exception:
        return time_str


class QuickNoteApp:
    def __init__(self):
        self.root = None
        self.input_window = None
        self._hotkey_mods = []
        self._hotkey_vk = 0
        self._save_flash_id = None
        self._last_hotkey_time = 0
        self.current_theme = get_current_theme()
        apply_theme(self.current_theme)
        self._filter_tag = "全部"
        self._selected_card_id = None
        self._card_widgets = {}
        self._mode = "note"  # "note" or "search"
        self._breath_phase = 0
        self._breath_after_id = None
        self._glow_after_id = None
        self._glow_phase = 0

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\033[K[{ts}] {msg}", flush=True)

    def _console_tick(self):
        if not self.root:
            return
        notes = load_notes()
        total = len(notes)
        starred = sum(1 for n in notes if n.get("starred"))
        win_st = "🟢" if (self.input_window and self.input_window.winfo_exists()) else "⚪"
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\033[K[{ts}] {total}条 | ⭐{starred} | {win_st} | {self.current_theme}",
              end="", flush=True)
        self.root.after(30000, self._console_tick)

    def start(self):
        notes = load_notes()
        print()
        print("╔══════════════════════════════════════════════╗")
        print("║    ✍️  Quick Note · Command Center Edition   ║")
        print("╠══════════════════════════════════════════════╚")
        print(f"║ 热键: {HOTKEY}")
        print(f"║ 主题: {self.current_theme}")
        print(f"║ 笔记: {len(notes)} 条")
        print(f"║ 数据: {DATA_FILE}")
        print("╠══════════════════════════════════════════════╚")
        print("║ Ctrl+C 退出                                 ║")
        print("╚═══════════════════════════════════════════════╝")
        print()

        self._hotkey_mods, self._hotkey_vk = _parse_hotkey(HOTKEY)
        if self._hotkey_vk == 0:
            self._log("❌ 无法解析热键: " + HOTKEY)
            return
        self._log("✅ 热键就绪")

        self.root = tk.Tk()
        self.root.withdraw()
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        self._poll_hotkey()
        self._console_tick()

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        if self.root:
            self.root.quit()
        print("\n[QuickNote] 已退出")

    def _poll_hotkey(self):
        all_pressed = True
        for vk in self._hotkey_mods:
            if not user32.GetAsyncKeyState(vk) & 0x8000:
                all_pressed = False
                break
        if all_pressed and user32.GetAsyncKeyState(self._hotkey_vk) & 0x8000:
            now = time.time()
            if now - self._last_hotkey_time >= 0.3:
                self._last_hotkey_time = now
                try:
                    if self.input_window and self.input_window.winfo_exists():
                        self._bring_to_front()
                    else:
                        self._log("📌 热键触发")
                        self._show_input_window()
                except Exception as e:
                    self._log("❌ " + str(e))
        if self.root:
            self.root.after(50, self._poll_hotkey)

    def _bring_to_front(self):
        try:
            if self.input_window and self.input_window.winfo_exists():
                self.input_window.attributes("-topmost", False)
                self.input_window.attributes("-topmost", True)
                self.input_window.lift()
                self.input_window.focus_force()
        except Exception:
            pass

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        apply_theme(self.current_theme)
        set_current_theme(self.current_theme)
        self._log(f"🎨 → {self.current_theme}")
        if self.input_window and self.input_window.winfo_exists():
            self._saved_geometry = self.input_window.geometry()
            self._do_show_input_window()

    def _show_input_window(self):
        try:
            if self.input_window and self.input_window.winfo_exists():
                self.input_window.lift()
                self.input_window.focus_force()
                return
            self._do_show_input_window()
        except Exception as e:
            self._log(f"❌ {e}")
            import traceback
            traceback.print_exc()

    def _do_show_input_window(self):
        saved_geo = getattr(self, '_saved_geometry', None)
        if self.input_window and self.input_window.winfo_exists():
            if not saved_geo:
                saved_geo = self.input_window.geometry()
            self.input_window.destroy()

        self._card_widgets = {}
        self._selected_card_id = None
        self._mode = "note"
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *a: self._refresh_cards())

        # Cancel any running animations
        if self._breath_after_id:
            self.root.after_cancel(self._breath_after_id)
            self._breath_after_id = None
        if self._glow_after_id:
            self.root.after_cancel(self._glow_after_id)
            self._glow_after_id = None
        self._breath_phase = 0
        self._glow_phase = 0

        win = tk.Toplevel(self.root)
        win.title("")
        win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        win.configure(bg=COLORS["bg"])
        win.resizable(True, True)
        win.attributes("-topmost", True)
        win.focus_force()
        win.overrideredirect(False)
        self.input_window = win

        if saved_geo:
            win.geometry(saved_geo)
        else:
            win.update_idletasks()
            x = (win.winfo_screenwidth() - WINDOW_WIDTH) // 2
            y = (win.winfo_screenheight() - WINDOW_HEIGHT) // 2
            win.geometry(f"+{x}+{y}")
        self._saved_geometry = None

        # ======== AMBIENT BACKGROUND CANVAS ========
        self._bg_canvas = tk.Canvas(win, bg=COLORS["bg"], highlightthickness=0, bd=0)
        self._bg_canvas.pack(fill=tk.BOTH, expand=True)

        # ======== HEADER (drawn on bg_canvas) ========
        header_h = 44

        # Right control buttons
        btn_x = WINDOW_WIDTH - 14
        self._close_btn = tk.Canvas(self._bg_canvas, width=32, height=32,
                                     bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self._close_btn_win = self._bg_canvas.create_window(btn_x, 16, window=self._close_btn, anchor="e")
        self._close_btn.create_text(16, 16, text="✕", fill=COLORS["text_dim"],
                                     font=(FONT_FAMILY, 10, "bold"))
        self._close_btn.bind("<Enter>", lambda e: self._close_btn.configure(bg=COLORS["danger"]))
        self._close_btn.bind("<Leave>", lambda e: self._close_btn.configure(bg=COLORS["bg"]))
        self._close_btn.bind("<ButtonPress-1>", lambda e: win.destroy())

        btn_x -= 38
        self._theme_btn = tk.Canvas(self._bg_canvas, width=32, height=32,
                                     bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self._bg_canvas.create_window(btn_x, 16, window=self._theme_btn, anchor="e")
        theme_icon = "🌙" if self.current_theme == "light" else "☀"
        self._theme_btn.create_text(16, 16, text=theme_icon, fill=COLORS["text_dim"],
                                     font=(FONT_FAMILY, 10))
        self._theme_btn.bind("<Enter>", lambda e: self._theme_btn.configure(bg=COLORS["surface_hover"]))
        self._theme_btn.bind("<Leave>", lambda e: self._theme_btn.configure(bg=COLORS["bg"]))
        self._theme_btn.bind("<ButtonPress-1>", lambda e: self._toggle_theme())

        btn_x -= 38
        self._export_btn = tk.Canvas(self._bg_canvas, width=32, height=32,
                                      bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self._bg_canvas.create_window(btn_x, 16, window=self._export_btn, anchor="e")
        self._export_btn.create_text(16, 16, text="↗", fill=COLORS["text_dim"],
                                      font=(FONT_FAMILY, 11))
        self._export_btn.bind("<Enter>", lambda e: self._export_btn.configure(bg=COLORS["surface_hover"]))
        self._export_btn.bind("<Leave>", lambda e: self._export_btn.configure(bg=COLORS["bg"]))
        self._export_btn.bind("<ButtonPress-1>", lambda e: self._export_notes())

        # ======== MAIN CONTENT AREA ========
        content_y = header_h + 8

        # --- Filter pills row (compact) ---
        self._filter_frame = tk.Frame(win, bg=COLORS["bg"])
        self._bg_canvas.create_window(WINDOW_WIDTH // 2, content_y,
                                       window=self._filter_frame, anchor="n")

        self._filter_btns = {}
        filter_tags = ["全部"] + TAG_LIST
        for ft in filter_tags:
            is_sel = ft == self._filter_tag
            bg_c = COLORS["primary_bg"] if is_sel else COLORS["pill_inactive_bg"]
            fg_c = COLORS["primary"] if is_sel else COLORS["pill_inactive_fg"]
            font_weight = "bold" if is_sel else "normal"

            lbl = tk.Label(self._filter_frame, text=ft, font=(FONT_FAMILY, 8, font_weight),
                           fg=fg_c, bg=bg_c, padx=10, pady=3, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2)

            lbl.bind("<ButtonPress-1>", lambda e, t=ft: self._set_filter(t))
            lbl.bind("<Enter>", lambda e, l=lbl, t=ft: l.configure(bg=COLORS["pill_hover_bg"])
                     if self._filter_tag != t else None)
            lbl.bind("<Leave>", lambda e, l=lbl, t=ft: l.configure(
                bg=COLORS["primary_bg"] if self._filter_tag == t else COLORS["pill_inactive_bg"]))
            self._filter_btns[ft] = lbl

        content_y += 36

        # --- Cards scroll area (fills middle) ---
        cards_frame = tk.Frame(win, bg=COLORS["bg"])
        self._bg_canvas.create_window(0, content_y, window=cards_frame, anchor="nw",
                                       tags="cards_area")

        self._cards_canvas = tk.Canvas(cards_frame, bg=COLORS["bg"],
                                        highlightthickness=0, borderwidth=0)
        self._scrollbar = tk.Scrollbar(cards_frame, orient=tk.VERTICAL,
                                        command=self._cards_canvas.yview,
                                        troughcolor=COLORS["scrollbar_bg"],
                                        bg=COLORS["scrollbar_thumb"],
                                        activebackground=COLORS["primary"],
                                        highlightthickness=0, borderwidth=0, width=5)
        self._cards_canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._cards_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._cards_inner = tk.Frame(self._cards_canvas, bg=COLORS["bg"])
        self._cards_window = self._cards_canvas.create_window((0, 0), window=self._cards_inner, anchor="nw")

        self._resize_after_id = None
        self._scroll_after_id = None
        self._cards_inner.bind("<Configure>", self._on_frame_configure)
        self._cards_canvas.bind("<Configure>", self._on_cards_canvas_configure)
        self._cards_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._cards_canvas.bind("<Button-4>", lambda e: self._cards_canvas.yview_scroll(-1, "units"))
        self._cards_canvas.bind("<Button-5>", lambda e: self._cards_canvas.yview_scroll(1, "units"))

        # Empty state
        self._empty_frame = tk.Frame(self._cards_canvas, bg=COLORS["bg"])
        self._empty_window = self._cards_canvas.create_window(
            (WINDOW_WIDTH // 2, 120), window=self._empty_frame, anchor="center")

        # Breathing crystal icon — animated
        self._empty_icon_canvas = tk.Canvas(self._empty_frame, width=80, height=80,
                                             bg=COLORS["bg"], highlightthickness=0)
        self._empty_icon_canvas.pack(pady=(20, 8))
        self._draw_breathing_crystal()

        tk.Label(self._empty_frame, text="开始记录你的想法", font=(FONT_FAMILY, 13, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg"]).pack()
        tk.Label(self._empty_frame, text="输入文字直接记录 · #标签 自动分类 · / 搜索",
                 font=(FONT_FAMILY, 8), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(pady=(6, 0))

        # ======== BOTTOM COMMAND BAR ========
        cmd_bar_h = 72
        cmd_frame = tk.Frame(win, bg=COLORS["bg"])
        self._cmd_win = self._bg_canvas.create_window(
            0, win.winfo_reqheight() - cmd_bar_h,
            window=cmd_frame, anchor="nw", tags="cmd_bar")

        # Glow canvas behind input
        self._glow_canvas = tk.Canvas(cmd_frame, height=cmd_bar_h, bg=COLORS["bg"],
                                       highlightthickness=0, bd=0)
        self._glow_canvas.pack(fill=tk.X)

        # Inner input row
        input_row = tk.Frame(self._glow_canvas, bg=COLORS["bg"])
        self._glow_canvas.create_window(WINDOW_WIDTH // 2, 36, window=input_row, anchor="center",
                                         tags="input_row")

        # Mode indicator
        self._mode_label = tk.Label(input_row, text="✎", font=(FONT_FAMILY, 12),
                                     fg=COLORS["primary"], bg=COLORS["bg"], width=2)
        self._mode_label.pack(side=tk.LEFT, padx=(0, 4))

        # Command entry — single line, sleek
        self._cmd_var = tk.StringVar()
        self._cmd_entry = tk.Entry(
            input_row, textvariable=self._cmd_var,
            font=(FONT_MONO, 12), bg=COLORS["input_bg"], fg=COLORS["text"],
            insertbackground=COLORS["primary"], selectbackground=COLORS["primary"],
            selectforeground=COLORS["text"],
            relief=tk.FLAT, borderwidth=0, highlightthickness=0,
            width=35,
        )
        self._cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)

        # Right side: submit hint
        self._cmd_hint = tk.Label(input_row, text="↵", font=(FONT_MONO, 14),
                                   fg=COLORS["text_dim"], bg=COLORS["bg"])
        self._cmd_hint.pack(side=tk.LEFT, padx=(8, 4))

        # Status bar at very bottom
        self._status_label = tk.Label(cmd_frame, text="", font=(FONT_FAMILY, 7),
                                       fg=COLORS["text_dim"], bg=COLORS["bg"])
        self._status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 4))

        # Placeholder
        self._placeholder_active = True
        self._cmd_entry.insert(0, "输入笔记... #标签 自动识别 · / 搜索")
        self._cmd_entry.configure(fg=COLORS["text_dim"])

        # Entry bindings
        self._cmd_entry.bind("<FocusIn>", self._on_cmd_focus_in)
        self._cmd_entry.bind("<Return>", self._on_cmd_submit)
        self._cmd_entry.bind("<KeyRelease>", self._on_cmd_key)
        self._cmd_entry.bind("<Escape>", lambda e: win.destroy())

        # Count label
        self.count_label = tk.Label(cmd_frame, text="", font=(FONT_FAMILY, 7),
                                     fg=COLORS["text_dim"], bg=COLORS["bg"])
        self.count_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20)

        # Layout update on resize
        self._bg_canvas.bind("<Configure>", self._on_bg_configure)

        # Focus entry
        self._cmd_entry.focus_set()
        self._refresh_cards()

    # ============ Background & Ambient ============

    def _on_bg_configure(self, event):
        w = event.width
        h = event.height
        if w < 2 or h < 2:
            return

        self._bg_canvas.delete("ambient")

        # Ambient gradient circles — very subtle
        for cx, cy, r, color_key in [
            (w * 0.2, h * 0.3, 200, "ambient_1"),
            (w * 0.8, h * 0.2, 180, "ambient_2"),
            (w * 0.5, h * 0.7, 220, "ambient_3"),
        ]:
            color = COLORS.get(color_key, "#1a1a2a")
            self._bg_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                         fill=color, outline="", tags="ambient")

        # Reposition elements
        self._bg_canvas.coords("cards_area", 0, 52)

        cmd_h = 72
        self._bg_canvas.coords("cmd_bar", 0, h - cmd_h)

        # Resize cards container
        cards_w = w - 6
        cards_h = h - 52 - cmd_h - 36
        try:
            self._bg_canvas.itemconfig("cards_area", width=cards_w, height=max(cards_h, 50))
        except tk.TclError:
            pass

    # ============ Breathing Crystal Animation ============

    def _draw_breathing_crystal(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        cv = self._empty_icon_canvas
        cv.delete("crystal")

        self._breath_phase += 0.08
        scale = 1.0 + 0.12 * math.sin(self._breath_phase)
        alpha_sim = 0.6 + 0.4 * math.sin(self._breath_phase)

        cx, cy = 40, 40
        size = 24 * scale

        # Outer glow
        glow_size = size + 14
        glow_color = COLORS["glow_primary_dim"]
        cv.create_oval(cx - glow_size, cy - glow_size, cx + glow_size, cy + glow_size,
                        fill="", outline=glow_color, width=2, tags="crystal")

        # Inner crystal (diamond shape)
        pts = [cx, cy - size, cx + size * 0.7, cy, cx, cy + size, cx - size * 0.7, cy]
        fill_color = COLORS["primary"]
        cv.create_polygon(pts, fill=fill_color, outline="", smooth=False, tags="crystal")

        # Highlight
        h_size = size * 0.4
        cv.create_polygon(cx, cy - size + 4, cx + h_size * 0.5, cy - 2,
                           cx, cy + 2, cx - h_size * 0.5, cy - 2,
                           fill=COLORS.get("glow_primary", "#9070ff"), outline="",
                           smooth=False, tags="crystal")

        self._breath_after_id = self.input_window.after(60, self._draw_breathing_crystal)

    # ============ Input Glow Animation ============

    def _start_glow(self):
        self._glow_phase += 0.1
        if not self.input_window or not self.input_window.winfo_exists():
            return

        try:
            gc = self._glow_canvas
            gc.delete("glow_line")

            w = gc.winfo_width()
            if w < 2:
                w = WINDOW_WIDTH

            intensity = 0.5 + 0.5 * math.sin(self._glow_phase)
            # Draw a pulsing glow line at top of command bar
            gc.create_line(40, 0, w - 40, 0, fill=COLORS["glow_primary"],
                            width=2, tags="glow_line")
            # Subtle glow oval
            glow_w = 160 + 40 * intensity
            gc.create_oval(w // 2 - glow_w, -8, w // 2 + glow_w, 8,
                            fill=COLORS["glow_primary"], outline="", tags="glow_line")
        except tk.TclError:
            pass

        self._glow_after_id = self.input_window.after(50, self._start_glow)

    def _stop_glow(self):
        if self._glow_after_id:
            try:
                self.root.after_cancel(self._glow_after_id)
            except Exception:
                pass
            self._glow_after_id = None
        try:
            self._glow_canvas.delete("glow_line")
        except Exception:
            pass
        self._glow_phase = 0

    # ============ Command Bar Events ============

    def _on_cmd_focus_in(self, event):
        if self._placeholder_active:
            self._cmd_entry.delete(0, tk.END)
            self._cmd_entry.configure(fg=COLORS["text"])
            self._placeholder_active = False

    def _on_cmd_focus_out(self, event):
        if not self._cmd_var.get().strip() and not self._placeholder_active:
            self._cmd_entry.insert(0, "输入笔记... #标签 自动识别 · / 搜索")
            self._cmd_entry.configure(fg=COLORS["text_dim"])
            self._placeholder_active = True
            self._mode = "note"
            self._mode_label.configure(text="✎")
        self._stop_glow()

    def _on_cmd_key(self, event):
        text = self._cmd_var.get()
        # Mode detection
        if text.startswith("/"):
            self._mode = "search"
            self._mode_label.configure(text="🔍")
            self._cmd_hint.configure(text="↵ 搜")
            search_kw = text[1:].strip()
            if hasattr(self, 'search_var'):
                self.search_var.set(search_kw)
            elif hasattr(self, '_search_var'):
                self._search_var.set(search_kw)
        else:
            if self._mode == "search":
                self._mode = "note"
                self._mode_label.configure(text="✎")
                self._cmd_hint.configure(text="↵")
                if hasattr(self, '_search_var'):
                    self._search_var.set("")

    def _on_cmd_submit(self, event):
        text = self._cmd_var.get().strip()

        if self._placeholder_active:
            return "break"

        if not text:
            return "break"

        # Search mode
        if text.startswith("/"):
            keyword = text[1:].strip()
            if hasattr(self, '_search_var'):
                self._search_var.set(keyword)
                self._refresh_cards()
            return "break"

        # Note mode — parse natural tags
        tag, clean_content = _parse_natural_tags(text)
        if not clean_content:
            return "break"

        note = add_note(clean_content, tag=tag)
        self._log(f"💾 [{tag}] {clean_content[:30]}")

        # Clear and reset
        self._cmd_var.set("")
        self._refresh_cards()
        self._flash_status("✓ 已记录", COLORS["success"])

        return "break"

    # ============ Filter ============

    def _set_filter(self, tag_name):
        self._filter_tag = tag_name
        self._refresh_filter_btns()
        self._refresh_cards()

    def _refresh_filter_btns(self):
        for ft, lbl in self._filter_btns.items():
            is_sel = ft == self._filter_tag
            lbl.configure(
                bg=COLORS["primary_bg"] if is_sel else COLORS["pill_inactive_bg"],
                fg=COLORS["primary"] if is_sel else COLORS["pill_inactive_fg"],
                font=(FONT_FAMILY, 8, "bold" if is_sel else "normal"),
            )

    # ============ Cards Canvas ============

    def _on_cards_canvas_configure(self, event):
        if self._resize_after_id:
            try:
                self.input_window.after_cancel(self._resize_after_id)
            except Exception:
                pass
        self._resize_after_id = self.input_window.after(30, lambda: self._do_resize(event))

    def _do_resize(self, event):
        try:
            cw = event.width
            self._cards_canvas.itemconfig(self._cards_window, width=cw)
            self._cards_canvas.coords(self._empty_window, cw // 2, 120)
            self._refresh_cards()
        except tk.TclError:
            pass
        self._resize_after_id = None

    def _on_frame_configure(self, event):
        if self._scroll_after_id:
            try:
                self.input_window.after_cancel(self._scroll_after_id)
            except Exception:
                pass
        self._scroll_after_id = self.input_window.after(50, self._do_scroll)

    def _do_scroll(self):
        try:
            self._cards_canvas.configure(scrollregion=self._cards_canvas.bbox("all"))
        except tk.TclError:
            pass
        self._scroll_after_id = None

    def _on_mousewheel(self, event):
        self._cards_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ============ Notes Operations ============

    def _delete_note(self, note_id):
        delete_note(note_id)
        self._log(f"🗑️ #{note_id}")
        self._refresh_cards()
        self._flash_status("✓ 已删除", COLORS["danger"])

    def _toggle_star(self, note_id):
        notes = load_notes()
        for n in notes:
            if n["id"] == note_id:
                n["starred"] = not n.get("starred", False)
                break
        save_notes(notes)
        self._refresh_cards()

    def _copy_content(self, note_id):
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if note:
            self.input_window.clipboard_clear()
            self.input_window.clipboard_append(note["content"])
            self._flash_status("✓ 已复制", COLORS["success"])

    def _export_notes(self):
        notes = load_notes()
        if not notes:
            return
        export_dir = filedialog.askdirectory(title="导出到", parent=self.input_window)
        if not export_dir:
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = os.path.join(export_dir, f"quick_note_{ts}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Quick Note 导出\n{'='*40}\n\n")
            for n in notes:
                star = " ★" if n.get("starred") else ""
                f.write(f"[{n.get('tag','默认')}] {n['time']}{star}\n{n['content']}\n{'-'*30}\n\n")
        self._flash_status(f"✓ 已导出 {len(notes)} 条", COLORS["success"])

    def _show_edit_window(self, note_id):
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if not note:
            return

        ew = tk.Toplevel(self.input_window)
        ew.title("")
        ew.geometry("480x320")
        ew.configure(bg=COLORS["bg"])
        ew.attributes("-topmost", True)
        ew.overrideredirect(False)
        ew.update_idletasks()
        ew.geometry(f"+{(ew.winfo_screenwidth()-480)//2}+{(ew.winfo_screenheight()-320)//2}")

        # Header
        eh = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=10)
        eh.pack(fill=tk.X)
        tk.Label(eh, text=f"✏️ #{note['id']}", font=(FONT_FAMILY, 11, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Label(eh, text=format_relative_time(note["time"]), font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        # Tag pills
        tag_row = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=4)
        tag_row.pack(fill=tk.X)
        edit_tag_var = tk.StringVar(value=note.get("tag", "默认"))
        edit_tag_widgets = {}

        def sel_tag(t):
            edit_tag_var.set(t)
            for tn, lbl in edit_tag_widgets.items():
                sel = tn == t
                lbl.configure(
                    fg=TAGS[tn]["color"] if sel else COLORS["pill_inactive_fg"],
                    bg=COLORS["primary_bg"] if sel else COLORS["pill_inactive_bg"],
                    font=(FONT_FAMILY, 8, "bold" if sel else "normal"),
                )

        for tn in TAG_LIST:
            sel = tn == edit_tag_var.get()
            lbl = tk.Label(tag_row, text=tn, font=(FONT_FAMILY, 8, "bold" if sel else "normal"),
                           fg=TAGS[tn]["color"] if sel else COLORS["pill_inactive_fg"],
                           bg=COLORS["primary_bg"] if sel else COLORS["pill_inactive_bg"],
                           padx=8, pady=2, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<ButtonPress-1>", lambda e, t=tn: sel_tag(t))
            edit_tag_widgets[tn] = lbl

        # Text
        body_f = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=8)
        body_f.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(body_f, font=(FONT_MONO, 11), wrap=tk.WORD,
                      bg=COLORS["input_bg"], fg=COLORS["text"],
                      insertbackground=COLORS["primary"],
                      selectbackground=COLORS["primary"],
                      selectforeground=COLORS["text"],
                      relief=tk.FLAT, borderwidth=0, highlightthickness=2,
                      highlightcolor=COLORS["border_focus"],
                      highlightbackground=COLORS["border"],
                      padx=12, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", note["content"])
        txt.focus_set()

        # Footer
        bf = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=8)
        bf.pack(fill=tk.X)

        def do_save(e=None):
            c = txt.get("1.0", tk.END).strip()
            if c:
                update_note(note_id, c, tag=edit_tag_var.get())
                self._refresh_cards()
                self._flash_status(f"✓ #{note_id}", COLORS["success"])
            ew.destroy()
            return "break"

        tk.Label(bf, text="↵ 保存 · Esc 取消", font=(FONT_MONO, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        # Save / Cancel
        cancel_lbl = tk.Label(bf, text="取消", font=(FONT_FAMILY, 9),
                               fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2",
                               padx=12, pady=4)
        cancel_lbl.pack(side=tk.RIGHT)
        cancel_lbl.bind("<ButtonPress-1>", lambda e: ew.destroy())
        cancel_lbl.bind("<Enter>", lambda e: cancel_lbl.configure(fg=COLORS["danger"]))
        cancel_lbl.bind("<Leave>", lambda e: cancel_lbl.configure(fg=COLORS["text_dim"]))

        save_lbl = tk.Label(bf, text="保存", font=(FONT_FAMILY, 9, "bold"),
                             fg=COLORS["primary"], bg=COLORS["primary_bg"], cursor="hand2",
                             padx=16, pady=4)
        save_lbl.pack(side=tk.RIGHT, padx=(0, 8))
        save_lbl.bind("<ButtonPress-1>", lambda e: do_save())
        save_lbl.bind("<Enter>", lambda e: save_lbl.configure(bg=COLORS["primary_hover"]))
        save_lbl.bind("<Leave>", lambda e: save_lbl.configure(bg=COLORS["primary_bg"]))

        txt.bind("<Control-Return>", do_save)
        txt.bind("<Escape>", lambda e: ew.destroy())
        ew.bind("<Escape>", lambda e: ew.destroy())

    def _show_context_menu(self, event, note_id):
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if not note:
            return
        menu = tk.Menu(self.input_window, tearoff=0,
                       bg=COLORS["surface"], fg=COLORS["text"],
                       activebackground=COLORS["primary"], activeforeground="#ffffff",
                       font=(FONT_FAMILY, 9), relief=tk.FLAT, bd=0)
        star_text = "💔 取消收藏" if note.get("starred") else "⭐ 收藏"
        menu.add_command(label=star_text, command=lambda: self._toggle_star(note_id))
        menu.add_command(label="✏️ 编辑", command=lambda: self._show_edit_window(note_id))
        menu.add_command(label="📋 复制", command=lambda: self._copy_content(note_id))
        menu.add_separator()
        tag_menu = tk.Menu(menu, tearoff=0,
                           bg=COLORS["surface"], fg=COLORS["text"],
                           activebackground=COLORS["primary"], activeforeground="#ffffff",
                           font=(FONT_FAMILY, 9))
        for tn in TAG_LIST:
            cur = " ✓" if note.get("tag", "默认") == tn else ""
            tag_menu.add_command(label=f"{TAGS[tn]['icon']} {tn}{cur}",
                                 command=lambda t=tn: self._change_tag(note_id, t))
        menu.add_cascade(label="🏷️ 标签", menu=tag_menu)
        menu.add_separator()
        menu.add_command(label="🗑️ 删除", command=lambda: self._delete_note(note_id))
        menu.tk_popup(event.x_root, event.y_root)

    def _change_tag(self, note_id, tag_name):
        update_note(note_id, tag=tag_name)
        self._refresh_cards()
        self._flash_status(f"✓ → {tag_name}", COLORS["success"])

    # ============ Cards List (Timeline) ============

    def _refresh_cards(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return

        for w in self._cards_inner.winfo_children():
            w.destroy()
        self._card_widgets = {}

        self._cards_inner.columnconfigure(0, weight=1)

        notes = load_notes()
        keyword = ""
        if hasattr(self, '_search_var'):
            keyword = self._search_var.get().strip().lower()

        filtered = []
        for n in notes:
            if self._filter_tag != "全部" and n.get("tag", "默认") != self._filter_tag:
                continue
            if keyword:
                nt = n.get("tag", "默认")
                searchable = f"{n['content']} {n['time']} {nt}".lower()
                if keyword not in searchable:
                    continue
            filtered.append(n)

        filtered.sort(key=lambda n: (not n.get("starred", False), n.get("time", "")), reverse=True)

        total = len(notes)
        shown = len(filtered)

        if shown == 0:
            self._cards_canvas.itemconfig(self._empty_window, state="normal")
        else:
            self._cards_canvas.itemconfig(self._empty_window, state="hidden")

        for idx, note in enumerate(filtered):
            self._create_card(note, idx)

        if keyword or self._filter_tag != "全部":
            self.count_label.config(text=f"🔍 {shown}/{total}")
        else:
            starred = sum(1 for n in notes if n.get("starred"))
            extra = f" · ⭐{starred}" if starred else ""
            self.count_label.config(text=f"共 {total} 条{extra}")

    def _create_card(self, note, index=0):
        note_id = note["id"]
        is_selected = self._selected_card_id == note_id
        is_starred = note.get("starred", False)
        tag_name = note.get("tag", "默认")
        tag_info = TAGS.get(tag_name, TAGS["默认"])
        tag_color = tag_info["color"]

        if is_selected:
            card_bg = COLORS["card_selected"]
        elif is_starred:
            card_bg = COLORS["card_starred"]
        else:
            card_bg = COLORS["surface"]

        # Timeline row
        row = tk.Frame(self._cards_inner, bg=COLORS["bg"])
        row.grid(row=index, column=0, sticky="ew", padx=16, pady=(0, 2))

        # Left: timeline dot + line
        tl_col = tk.Frame(row, bg=COLORS["bg"], width=24)
        tl_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        tl_col.pack_propagate(False)

        dot_cv = tk.Canvas(tl_col, width=24, height=24, bg=COLORS["bg"],
                           highlightthickness=0, bd=0)
        dot_cv.pack(pady=(4, 0))
        # Outer ring
        dot_cv.create_oval(6, 6, 18, 18, fill="", outline=tag_color, width=2)
        # Inner dot
        dot_cv.create_oval(9, 9, 15, 15, fill=tag_color, outline="")

        # Card body
        card = tk.Frame(row, bg=card_bg, padx=12, pady=8, cursor="hand2",
                        highlightbackground=COLORS.get("glass_border", COLORS["border"]),
                        highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if is_selected:
            card.configure(highlightbackground=COLORS["primary"])

        # Row 1: tag + star + time + more
        r1 = tk.Frame(card, bg=card_bg)
        r1.pack(fill=tk.X)

        tk.Label(r1, text=tag_name, font=(FONT_FAMILY, 7, "bold"),
                 fg=tag_color, bg=card_bg).pack(side=tk.LEFT)

        rel_time = format_relative_time(note["time"])
        tk.Label(r1, text=rel_time, font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=card_bg).pack(side=tk.LEFT, padx=(8, 0))

        if is_starred:
            tk.Label(r1, text="⭐", font=(FONT_FAMILY, 8),
                     fg=COLORS["star_color"], bg=card_bg).pack(side=tk.LEFT, padx=(6, 0))

        more = tk.Label(r1, text="⋯", font=(FONT_FAMILY, 11),
                        fg=COLORS["text_dim"], bg=card_bg, cursor="hand2")
        more.pack(side=tk.RIGHT)
        more.bind("<ButtonPress-1>", lambda e, nid=note_id: self._show_context_menu(e, nid))

        # Content
        preview = note["content"].replace("\n", " ")[:100]
        tk.Label(card, text=preview, font=(FONT_FAMILY, 9),
                 fg=COLORS["text"], bg=card_bg,
                 anchor="nw", wraplength=380, justify="left").pack(fill=tk.X, pady=(4, 0), anchor="w")

        # Bindings
        all_w = [card, row, r1, dot_cv]
        for w in all_w:
            w.bind("<ButtonPress-1>", lambda e, nid=note_id: self._on_card_click(nid))
            w.bind("<Double-ButtonPress-1>", lambda e, nid=note_id: self._show_edit_window(nid))
            w.bind("<ButtonPress-3>", lambda e, nid=note_id: self._show_context_menu(e, nid))

        hover_d = {"card": card, "row": row, "r1": r1, "is_sel": is_selected,
                   "is_star": is_starred, "all_w": all_w, "more": more}
        for w in all_w:
            w.bind("<Enter>", lambda e, d=hover_d: self._card_enter(d))
            w.bind("<Leave>", lambda e, d=hover_d: self._card_leave(d))

        self._card_widgets[note_id] = card

    def _card_enter(self, d):
        card = d["card"]
        is_sel = d["is_sel"]
        bg = COLORS["card_selected"] if is_sel else COLORS["card_hover"]
        try:
            card.configure(bg=bg, highlightbackground=COLORS["primary"])
            for w in d["all_w"]:
                try:
                    if w.winfo_class() in ("Label", "Frame", "Canvas"):
                        old = w.cget("bg")
                        if old in (COLORS["surface"], COLORS["card_hover"],
                                   COLORS["card_selected"], COLORS["card_starred"]):
                            w.configure(bg=bg)
                except tk.TclError:
                    pass
            d["more"].configure(bg=bg)
        except tk.TclError:
            pass

    def _card_leave(self, d):
        card = d["card"]
        is_sel = d["is_sel"]
        is_star = d["is_star"]
        bg = COLORS["card_selected"] if is_sel else (COLORS["card_starred"] if is_star else COLORS["surface"])
        try:
            if not is_sel:
                card.configure(highlightbackground=COLORS.get("glass_border", COLORS["border"]))
            card.configure(bg=bg)
            for w in d["all_w"]:
                try:
                    if w.winfo_class() in ("Label", "Frame", "Canvas"):
                        old = w.cget("bg")
                        if old in (COLORS["surface"], COLORS["card_hover"],
                                   COLORS["card_selected"], COLORS["card_starred"]):
                            w.configure(bg=bg)
                except tk.TclError:
                    pass
        except tk.TclError:
            pass

    def _on_card_click(self, note_id):
        self._selected_card_id = note_id
        # Refresh selection visuals
        for nid, card_widget in self._card_widgets.items():
            try:
                is_sel = nid == note_id
                bg = COLORS["card_selected"] if is_sel else COLORS["surface"]
                border = COLORS["primary"] if is_sel else COLORS.get("glass_border", COLORS["border"])
                card_widget.configure(bg=bg, highlightbackground=border)
                for child in card_widget.winfo_children():
                    if child.winfo_class() == "Frame":
                        for sub in child.winfo_children():
                            if sub.winfo_class() in ("Label", "Canvas"):
                                try:
                                    old = sub.cget("bg")
                                    if old in (COLORS["surface"], COLORS["card_hover"],
                                               COLORS["card_selected"], COLORS["card_starred"]):
                                        sub.configure(bg=bg)
                                except tk.TclError:
                                    pass
                        try:
                            old = child.cget("bg")
                            if old in (COLORS["surface"], COLORS["card_hover"],
                                       COLORS["card_selected"], COLORS["card_starred"]):
                                child.configure(bg=bg)
                        except tk.TclError:
                            pass
            except tk.TclError:
                pass

    def _flash_status(self, text, color):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        if hasattr(self, '_status_label'):
            try:
                self._status_label.configure(text=text, fg=color)
            except tk.TclError:
                pass
        if self._save_flash_id:
            self.input_window.after_cancel(self._save_flash_id)
        self._save_flash_id = self.input_window.after(2000, self._reset_status)

    def _reset_status(self):
        if self.input_window and self.input_window.winfo_exists():
            if hasattr(self, '_status_label'):
                try:
                    self._status_label.configure(text="", fg=COLORS["text_dim"])
                except tk.TclError:
                    pass


def main():
    app = QuickNoteApp()
    app.start()


if __name__ == "__main__":
    main()