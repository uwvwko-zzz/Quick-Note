"""
快速记录工具 - Quick Note Tool
按 Ctrl+Alt+E 全局热键呼出记录窗口，快速记录信息
数据保存到同级目录下的 notes.json 文件中
"""

import json
import os
import time
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
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 780
CARD_MIN_WIDTH = 260
# ==============================

# ============ 标签定义 ============
TAGS = {
    "默认": {"color": "#8b8fa3", "bg_dark": "#2a2a32", "bg_light": "#f1f5f9", "icon": "📌"},
    "重要": {"color": "#f43f5e", "bg_dark": "#30202a", "bg_light": "#fff1f2", "icon": "🔴"},
    "待办": {"color": "#f59e0b", "bg_dark": "#302a20", "bg_light": "#fffbeb", "icon": "🟡"},
    "灵感": {"color": "#a78bfa", "bg_dark": "#28203a", "bg_light": "#f5f3ff", "icon": "🟣"},
    "代码": {"color": "#34d399", "bg_dark": "#203028", "bg_light": "#ecfdf5", "icon": "🟢"},
    "学习": {"color": "#60a5fa", "bg_dark": "#202838", "bg_light": "#eff6ff", "icon": "🔵"},
}
TAG_LIST = list(TAGS.keys())

# ============ 主题配色 ============
THEMES = {
    "dark": {
        "bg":               "#18181C",
        "surface":          "#1E1E24",
        "surface_light":    "#24242B",
        "surface_hover":    "#2E2E38",
        "card_bg":          "#222229",
        "card_hover":       "#2A2A33",
        "card_selected":    "#2E2545",
        "card_starred":     "#2A2630",
        "input_bg":         "#222229",
        "input_focus_bg":   "#262630",
        "border":           "#2A2A32",
        "border_focus":     "#7c5cfc",
        "border_light":     "#333340",
        "primary":          "#7c5cfc",
        "primary_hover":    "#9070ff",
        "primary_bg":       "#2E2545",
        "danger":           "#f0465a",
        "danger_hover":     "#e03050",
        "success":          "#30d8a0",
        "warning":          "#f0c030",
        "text":             "#E0E0E0",
        "text_secondary":   "#9094A8",
        "text_dim":         "#6E7285",
        "heading":          "#C0B8D8",
        "heading_accent":   "#A890FF",
        "header_bg":        "#1C1C22",
        "header_accent":    "#7c5cfc",
        "footer_bg":        "#1C1C22",
        "search_bg":        "#24242B",
        "pill_inactive_bg": "#28282F",
        "pill_inactive_fg": "#6E7285",
        "empty_icon":       "#333340",
        "empty_text":       "#6E7285",
        "star_color":       "#f0c030",
        "shadow":           "#101014",
        "scrollbar_bg":     "#1E1E24",
        "scrollbar_thumb":  "#38384A",
        "char_counter":     "#55556A",
        "char_limit":       "#f0465a",
        "glow_primary":     "#7c5cfc30",
        "combo_bg":         "#24242B",
        "combo_fg":         "#E0E0E0",
        "combo_arrow":      "#6E7285",
    },
    "light": {
        "bg":               "#F5F5F7",
        "surface":          "#FFFFFF",
        "surface_light":    "#F0F0F3",
        "surface_hover":    "#E8E8EC",
        "card_bg":          "#FFFFFF",
        "card_hover":       "#F4F4F8",
        "card_selected":    "#EDE8FF",
        "card_starred":     "#FFF8E8",
        "input_bg":         "#FFFFFF",
        "input_focus_bg":   "#FCFAFF",
        "border":           "#D8D8E0",
        "border_focus":     "#7c5cfc",
        "border_light":     "#C8C8D4",
        "primary":          "#7c5cfc",
        "primary_hover":    "#6d4df0",
        "primary_bg":       "#F0ECFF",
        "danger":           "#f0465a",
        "danger_hover":     "#e03050",
        "success":          "#20c090",
        "warning":          "#e8a820",
        "text":             "#1A1A2E",
        "text_secondary":   "#605E78",
        "text_dim":         "#9898A8",
        "heading":          "#6828d8",
        "heading_accent":   "#7840f0",
        "header_bg":        "#FAFAFC",
        "header_accent":    "#7c5cfc",
        "footer_bg":        "#F2F2F5",
        "search_bg":        "#EEEEF2",
        "pill_inactive_bg": "#EDEDF2",
        "pill_inactive_fg": "#9898A8",
        "empty_icon":       "#D0D0D8",
        "empty_text":       "#9898A8",
        "star_color":       "#e8a820",
        "shadow":           "#C8C8D0",
        "scrollbar_bg":     "#F0F0F3",
        "scrollbar_thumb":  "#C8C8D0",
        "char_counter":     "#A0A0B0",
        "char_limit":       "#f0465a",
        "glow_primary":     "#7c5cfc20",
        "combo_bg":         "#FFFFFF",
        "combo_fg":         "#1A1A2E",
        "combo_arrow":      "#9898A8",
    },
}

COLORS = dict(THEMES["dark"])

FONT_FAMILY = "Microsoft YaHei"
FONT_MONO = "Consolas"
# ==================================


def _style_ttk_combobox(win, theme_name):
    """为 ttk.Combobox 应用与暗色主题匹配的样式"""
    style = ttk.Style(win)
    style.theme_use("clam")

    bg = COLORS["combo_bg"]
    fg = COLORS["combo_fg"]
    arrow = COLORS["combo_arrow"]
    border = COLORS["border"]
    select_bg = COLORS["primary"]
    field_bg = COLORS["input_bg"]

    style.configure("Dark.TCombobox",
                    fieldbackground=field_bg,
                    background=bg,
                    foreground=fg,
                    arrowcolor=arrow,
                    bordercolor=border,
                    lightcolor=border,
                    darkcolor=border,
                    insertcolor=COLORS["primary"],
                    selectbackground=select_bg,
                    selectforeground=fg,
                    padding=(8, 4),
                    relief=tk.FLAT,
                    focuscolor=COLORS["border_focus"],
                    )
    style.map("Dark.TCombobox",
              fieldbackground=[("readonly", field_bg)],
              foreground=[("readonly", fg)],
              selectbackground=[("readonly", select_bg)],
              bordercolor=[("focus", COLORS["border_focus"])],
              lightcolor=[("focus", COLORS["border_focus"])],
              darkcolor=[("focus", COLORS["border_focus"])],
              )
    return "Dark.TCombobox"


# ============ Win32 全局热键 API ============
user32 = ctypes.windll.user32

# GetAsyncKeyState 虚拟键码映射
VK_MAP = {
    "ctrl": 0x11, "control": 0x11,
    "alt": 0x12,
    "shift": 0x10,
    "win": 0x5B, "windows": 0x5B, "super": 0x5B,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "escape": 0x1B, "esc": 0x1B,
    "tab": 0x09, "space": 0x20, "enter": 0x0D,
    "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23,
    "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}
MOD_KEYS = {"ctrl", "control", "alt", "shift", "win", "windows", "super"}

def _parse_hotkey(hotkey_str):
    """将 'ctrl+alt+e' 解析为 ([mod_vk_codes], main_vk_code)"""
    parts = hotkey_str.lower().replace(" ", "").split("+")
    mods = []
    main_key = 0
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
# ==================================



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


def get_tag_pill_colors(tag_name):
    tag_info = TAGS.get(tag_name, TAGS["默认"])
    if get_current_theme() == "dark":
        pill_bg = tag_info["bg_dark"]
    else:
        pill_bg = tag_info["bg_light"]
    pill_fg = tag_info["color"]
    return pill_bg, pill_fg, tag_info["icon"]


class QuickNoteApp:
    def __init__(self):
        self.root = None
        self.input_window = None
        self._hotkey_mods = []
        self._hotkey_vk = 0
        self._card_cols = 2
        self._save_flash_id = None
        self._creating_window = False
        self._window_lock = threading.Lock()
        self._last_hotkey_time = 0
        self.current_theme = get_current_theme()
        apply_theme(self.current_theme)
        self._selected_tag = "默认"
        self._filter_tag = "全部"
        self._selected_card_id = None
        self._card_widgets = {}
        # 线程安全的热键事件队列
        self._hotkey_event = threading.Event()

    # ============ 控制台日志 ============

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\033[K[{ts}] {msg}", flush=True)

    def _console_tick(self):
        if not self.root:
            return
        notes = load_notes()
        total = len(notes)
        starred = sum(1 for n in notes if n.get("starred"))
        win_st = "🟢打开" if (self.input_window and self.input_window.winfo_exists()) else "⚪隐藏"
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\033[K[{ts}] 笔记:{total} | 收藏:{starred} | 窗口:{win_st} | 主题:{self.current_theme}",
              end="", flush=True)
        self.root.after(30000, self._console_tick)

    # ============ 启动/停止 ============

    def start(self):
        notes = load_notes()
        print()
        print("╔══════════════════════════════════════════════╗")
        print("║         ✍️  Quick Note 快速记录工具         ║")
        print("╠═══════════════════════════════════════════════╚")
        print(f"║ 热键: {HOTKEY}")
        print(f"║ 主题: {self.current_theme}")
        print(f"║ 笔记: {len(notes)} 条")
        print(f"║ 数据: {DATA_FILE}")
        print("╠═══════════════════════════════════════════════╚")
        print("║ 按Ctrl+C 退出                             ║")
        print("╚═══════════════════════════════════════════════╝")
        print()

        # 解析热键
        self._hotkey_mods, self._hotkey_vk = _parse_hotkey(HOTKEY)
        if self._hotkey_vk == 0:
            self._log("❌ 无法解析热键: " + HOTKEY)
            return
        self._log("✅ 热键已就绪 (GetAsyncKeyState: mods=" + str(self._hotkey_mods) + ", vk=0x" + format(self._hotkey_vk, "X") + ")")

        self.root = tk.Tk()
        self.root.withdraw()
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        # 启动轮询
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

    # ============ 热键处理 (GetAsyncKeyState) ============

    def _poll_hotkey(self):
        """主线程轮询: 使用 GetAsyncKeyState 检测热键"""
        # 检查所有修键是否按下
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
                        self._log("📌 热键触发，打开窗口...")
                        self._show_input_window()
                except Exception as e:
                    self._log("❌ 热键处理出错: " + str(e))

        if self.root:
            self.root.after(50, self._poll_hotkey)

    def _bring_to_front(self):
        """将已有窗口置顶"""
        try:
            if self.input_window and self.input_window.winfo_exists():
                self.input_window.attributes("-topmost", False)
                self.input_window.attributes("-topmost", True)
                self.input_window.lift()
                self.input_window.focus_force()
                self._log("📌 窗口已置顶")
        except Exception as e:
            self._log("❌ 置顶出错: " + str(e))
    # ============ 主题切换 ============

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        apply_theme(self.current_theme)
        set_current_theme(self.current_theme)
        self._log(f"🎨 切换主题: {self.current_theme}")
        if self.input_window and self.input_window.winfo_exists():
            self._saved_geometry = self.input_window.geometry()
            self._show_input_window()

    # ============ 窗口创建 ============

    def _show_input_window(self):
        try:
            if self.input_window and self.input_window.winfo_exists():
                self.input_window.lift()
                self.input_window.focus_force()
                self._log("📌 窗口已存在，置顶")
                return
            self._log("📌 开始创建窗口...")
            self._do_show_input_window()
            self._log("📌 窗口创建完成")
        except Exception as e:
            self._log(f"❌ 创建窗口出错: {e}")
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

        win = tk.Toplevel(self.root)
        win.title("Quick Note")
        win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        win.configure(bg=COLORS["bg"])
        win.resizable(True, True)
        win.attributes("-topmost", True)
        win.focus_force()
        self.input_window = win

        # No visible border — clean edge
        win.configure(highlightbackground=COLORS["bg"], highlightthickness=0)

        if saved_geo:
            win.geometry(saved_geo)
        else:
            win.update_idletasks()
            x = (win.winfo_screenwidth() - WINDOW_WIDTH) // 2
            y = (win.winfo_screenheight() - WINDOW_HEIGHT) // 2
            win.geometry(f"+{x}+{y}")
        self._saved_geometry = None

        # ======== 1. Header — clean, minimal ========
        header = tk.Frame(win, bg=COLORS["header_bg"], padx=0, pady=0)
        header.pack(fill=tk.X)

        header_canvas = tk.Canvas(header, height=52, bg=COLORS["header_bg"],
                                  highlightthickness=0, borderwidth=0)
        header_canvas.pack(fill=tk.X)

        def _draw_header_bg(event=None):
            w = header_canvas.winfo_width()
            if w < 2:
                return
            header_canvas.delete("bg")
            # Clean flat background (no gradient)
            header_canvas.create_rectangle(0, 0, w, 52, fill=COLORS["header_bg"], outline="", tags="bg")
            # Icon — positioned with comfortable spacing
            header_canvas.create_text(24, 26, text="✎", font=(FONT_FAMILY, 15),
                                      fill=COLORS["primary"], anchor="w", tags="bg")
            # Title — cleaner, vertically centered
            header_canvas.create_text(50, 26, text="Quick Note", font=(FONT_FAMILY, 13, "bold"),
                                      fill=COLORS["heading_accent"], anchor="w", tags="bg")

        header_canvas.bind("<Configure>", _draw_header_bg)

        # Status indicator
        self.status_dot = tk.Label(header, text="●", font=(FONT_FAMILY, 5),
                                   fg=COLORS["success"], bg=COLORS["header_bg"])
        self.status_dot.place(x=162, y=23)
        self.status_label = tk.Label(header, text="就绪", font=(FONT_FAMILY, 8),
                                     fg=COLORS["text_dim"], bg=COLORS["header_bg"])
        self.status_label.place(x=174, y=21)

        # Right buttons
        right_btns = tk.Frame(header, bg=COLORS["header_bg"])
        right_btns.place(relx=1.0, y=10, anchor="ne", x=-10)

        self._make_icon_btn(right_btns, "\U0001f4e4", self._export_notes)
        theme_icon = "\U0001f319" if self.current_theme == "light" else "\u2600\ufe0f"
        self._make_icon_btn(right_btns, theme_icon, self._toggle_theme)
        self._make_icon_btn(right_btns, "\u2715", lambda: win.destroy(), is_close=True)

        # ======== Content body ========
        body = tk.Frame(win, bg=COLORS["bg"])
        body.pack(fill=tk.BOTH, expand=True)

        # ---- 2. Input section (no border, elevation via background) ----
        input_section = tk.Frame(body, bg=COLORS["bg"], padx=24, pady=16)
        input_section.pack(fill=tk.X)

        # Input card — dark surface, no visible border when unfocused
        self._input_border = tk.Frame(input_section, bg=COLORS["input_bg"], padx=0, pady=0)
        self._input_border.pack(fill=tk.X)

        self.text_input = tk.Text(
            self._input_border, font=(FONT_MONO, 11), wrap=tk.WORD, height=4,
            bg=COLORS["input_bg"], fg=COLORS["text"],
            insertbackground=COLORS["primary"],
            selectbackground=COLORS["primary"],
            selectforeground=COLORS["text"],
            relief=tk.FLAT, borderwidth=14, highlightthickness=2,
            highlightcolor=COLORS["input_bg"],
            highlightbackground=COLORS["input_bg"],
            padx=8, pady=8,
        )
        self.text_input.pack(fill=tk.X)

        self.text_input.bind("<FocusIn>", self._on_input_focus_in)
        self.text_input.bind("<FocusOut>", self._on_input_focus_out)

        # Placeholder
        self._placeholder_active = True
        self._placeholder_text = "输入笔记、灵感、待办事项..."
        self.text_input.insert("1.0", self._placeholder_text)
        self.text_input.configure(fg=COLORS["text_dim"])

        def _on_input_click(event):
            if self._placeholder_active:
                self.text_input.delete("1.0", tk.END)
                self.text_input.configure(fg=COLORS["text"])
                self._placeholder_active = False

        def _on_input_leave(event):
            if not self.text_input.get("1.0", tk.END).strip() and not self._placeholder_active:
                self.text_input.insert("1.0", self._placeholder_text)
                self.text_input.configure(fg=COLORS["text_dim"])
                self._placeholder_active = True

        self.text_input.bind("<ButtonPress-1>", _on_input_click)
        self.text_input.bind("<FocusIn>", lambda e: (_on_input_click(e), self._on_input_focus_in(e)))
        self.text_input.bind("<FocusOut>", lambda e: (_on_input_leave(e), self._on_input_focus_out(e)))

        # Char counter
        self._char_counter = tk.Label(self._input_border, text="0", font=(FONT_MONO, 8),
                                      fg=COLORS["char_counter"], bg=COLORS["input_bg"],
                                      anchor="e")
        self._char_counter.place(relx=1.0, rely=1.0, x=-18, y=-10, anchor="se")
        self.text_input.bind("<KeyRelease>", self._update_char_counter)

        # ---- 3. Tags + Save row ----
        action_row = tk.Frame(input_section, bg=COLORS["bg"])
        action_row.pack(fill=tk.X, pady=(10, 0))

        tk.Label(action_row, text="🏷️", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 4))

        # Dark-themed Combobox via ttk Style
        self._tag_var = tk.StringVar(value="默认")
        combo_style = _style_ttk_combobox(win, self.current_theme)
        tag_combo = ttk.Combobox(action_row, textvariable=self._tag_var,
                                 values=TAG_LIST, state="readonly", width=7,
                                 font=(FONT_FAMILY, 9), style=combo_style)
        tag_combo.pack(side=tk.LEFT, padx=(0, 14))

        # Save button — pill-shaped with hover glow
        save_btn = tk.Frame(action_row, bg=COLORS["primary"], padx=18, pady=5, cursor="hand2")
        save_btn.pack(side=tk.LEFT)

        save_lbl = tk.Label(save_btn, text="💾  保存笔记", font=(FONT_FAMILY, 9, "bold"),
                            fg="#ffffff", bg=COLORS["primary"], cursor="hand2")
        save_lbl.pack()

        save_btn.bind("<ButtonPress-1>", lambda e: self._save_note(None))
        save_lbl.bind("<ButtonPress-1>", lambda e: self._save_note(None))
        save_btn.bind("<Enter>", lambda e: (save_btn.configure(bg=COLORS["primary_hover"]),
                                             save_lbl.configure(bg=COLORS["primary_hover"])))
        save_btn.bind("<Leave>", lambda e: (save_btn.configure(bg=COLORS["primary"]),
                                             save_lbl.configure(bg=COLORS["primary"])))

        # Keyboard hint — clearer contrast
        tk.Label(action_row, text="Ctrl+Enter 保存  ·  Esc 关闭", font=(FONT_MONO, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        # ---- NO separator line — use spacing instead ----

        # ---- 6. Search + Filter ----
        list_section = tk.Frame(body, bg=COLORS["bg"], padx=24, pady=4)
        list_section.pack(fill=tk.BOTH, expand=True)

        filter_row = tk.Frame(list_section, bg=COLORS["bg"])
        filter_row.pack(fill=tk.X, pady=(0, 10))

        # Search box — elevated surface
        search_outer = tk.Frame(filter_row, bg=COLORS["search_bg"], padx=0, pady=0)
        search_outer.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        search_inner = tk.Frame(search_outer, bg=COLORS["search_bg"])
        search_inner.pack(fill=tk.X)

        tk.Label(search_inner, text=" 🔍", font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["search_bg"]).pack(side=tk.LEFT, padx=(6, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._refresh_cards())

        self.search_entry = tk.Entry(
            search_inner, textvariable=self.search_var,
            font=(FONT_FAMILY, 9), bg=COLORS["search_bg"], fg=COLORS["text"],
            insertbackground=COLORS["primary"], selectbackground=COLORS["primary"],
            selectforeground=COLORS["text"],
            relief=tk.FLAT, borderwidth=6, highlightthickness=0,
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Filter pills — pill-shaped with better spacing
        self._filter_btns = {}
        filter_tags = ["全部"] + TAG_LIST
        for ft in filter_tags:
            is_sel = ft == self._filter_tag
            bg = COLORS["primary_bg"] if is_sel else COLORS["pill_inactive_bg"]
            fg = COLORS["primary"] if is_sel else COLORS["pill_inactive_fg"]

            fb = tk.Frame(filter_row, bg=bg, padx=12, pady=5, cursor="hand2")
            fb.pack(side=tk.LEFT, padx=(0, 4))

            fl = tk.Label(fb, text=ft, font=(FONT_FAMILY, 8),
                          fg=fg, bg=bg, cursor="hand2")
            fl.pack()

            fb.bind("<ButtonPress-1>", lambda e, t=ft: self._set_filter(t))
            fl.bind("<ButtonPress-1>", lambda e, t=ft: self._set_filter(t))
            self._filter_btns[ft] = (fb, fl)

        # ---- Cards scroll area ----
        cards_container = tk.Frame(list_section, bg=COLORS["bg"])
        cards_container.pack(fill=tk.BOTH, expand=True)

        self._cards_canvas = tk.Canvas(cards_container, bg=COLORS["bg"],
                                       highlightthickness=0, borderwidth=0)
        self._scrollbar = tk.Scrollbar(cards_container, orient=tk.VERTICAL,
                                       command=self._cards_canvas.yview,
                                       troughcolor=COLORS["scrollbar_bg"],
                                       bg=COLORS["scrollbar_thumb"],
                                       activebackground=COLORS["primary"],
                                       highlightthickness=0, borderwidth=0,
                                       width=6)
        self._cards_canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._cards_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._cards_frame = tk.Frame(self._cards_canvas, bg=COLORS["bg"])
        self._cards_window = self._cards_canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")

        self._resize_after_id = None
        self._scroll_after_id = None
        self._cards_frame.bind("<Configure>", self._on_frame_configure)
        self._cards_canvas.bind("<Configure>", self._on_canvas_configure)

        self._cards_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._cards_canvas.bind("<Button-4>", lambda e: self._cards_canvas.yview_scroll(-1, "units"))
        self._cards_canvas.bind("<Button-5>", lambda e: self._cards_canvas.yview_scroll(1, "units"))

        # ---- Empty state — cleaner, no redundant button ----
        self._empty_frame = tk.Frame(self._cards_canvas, bg=COLORS["bg"])
        self._empty_window = self._cards_canvas.create_window(
            (WINDOW_WIDTH // 2, 200), window=self._empty_frame, anchor="center")

        # Simple line icon using text
        empty_icon = tk.Label(self._empty_frame, text="✎", font=(FONT_FAMILY, 36),
                              fg=COLORS["primary"], bg=COLORS["bg"])
        empty_icon.pack(pady=(20, 8))

        tk.Label(self._empty_frame, text="还没有笔记", font=(FONT_FAMILY, 13, "bold"),
                 fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack()

        tk.Label(self._empty_frame, text="在上方输入框中开始记录你的想法",
                 font=(FONT_FAMILY, 9), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(pady=(4, 0))
        tk.Label(self._empty_frame, text="记录灵感、待办、代码片段或学习内容",
                 font=(FONT_FAMILY, 8), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(pady=(2, 0))

        # ======== 8. Footer — no separator line, just spacing ========
        footer = tk.Frame(win, bg=COLORS["footer_bg"], padx=24, pady=8)
        footer.pack(fill=tk.X)

        self.count_label = tk.Label(footer, text="", font=(FONT_FAMILY, 8),
                                    fg=COLORS["text_dim"], bg=COLORS["footer_bg"])
        self.count_label.pack(side=tk.LEFT)

        tk.Label(footer, text=f"⌨ {HOTKEY}", font=(FONT_MONO, 7),
                 fg=COLORS["text_dim"], bg=COLORS["footer_bg"]).pack(side=tk.RIGHT)

        # Bindings
        self.text_input.bind("<Control-Return>", self._save_note)
        self.text_input.bind("<Escape>", lambda e: win.destroy())
        self.text_input.focus_set()

        self._refresh_cards()

    def _on_input_focus_in(self, event):
        """输入框聚焦 — 紫色微光边框"""
        self.text_input.configure(
            highlightcolor=COLORS["border_focus"],
            highlightbackground=COLORS["border_focus"],
            highlightthickness=2,
        )

    def _on_input_focus_out(self, event):
        """输入框失焦 — 恢复无框"""
        self.text_input.configure(
            highlightcolor=COLORS["input_bg"],
            highlightbackground=COLORS["input_bg"],
            highlightthickness=2,
        )

    def _update_char_counter(self, event=None):
        """更新字符计数（Twitter 风格）"""
        content = self.text_input.get("1.0", tk.END)
        count = len(content.strip())
        color = COLORS["char_limit"] if count > 500 else COLORS["char_counter"]
        self._char_counter.configure(text=str(count), fg=color)

    def _make_icon_btn(self, parent, text, command, is_close=False):
        c = tk.Canvas(parent, width=34, height=30, bg=COLORS["header_bg"],
                      highlightthickness=0, cursor="hand2")
        c.pack(side=tk.LEFT, padx=2)
        c.create_text(17, 15, text=text, fill=COLORS["text_dim"],
                      font=(FONT_FAMILY, 11 if not is_close else 10, "bold" if is_close else "normal"))

        if is_close:
            c.bind("<Enter>", lambda e: (c.configure(bg=COLORS["danger"]),
                                          c.itemconfig(c.find_all()[0], fill="#ffffff")))
            c.bind("<Leave>", lambda e: (c.configure(bg=COLORS["header_bg"]),
                                          c.itemconfig(c.find_all()[0], fill=COLORS["text_dim"])))
        else:
            c.bind("<Enter>", lambda e: c.configure(bg=COLORS["surface_hover"]))
            c.bind("<Leave>", lambda e: c.configure(bg=COLORS["header_bg"]))
        c.bind("<ButtonPress-1>", lambda e: command())

    def _on_canvas_configure(self, event):
        if self._resize_after_id:
            self.input_window.after_cancel(self._resize_after_id)
        self._resize_after_id = self.input_window.after(30, lambda: self._do_canvas_resize(event))

    def _do_canvas_resize(self, event):
        try:
            canvas_w = event.width
            self._card_cols = max(1, canvas_w // CARD_MIN_WIDTH)
            self._cards_canvas.itemconfig(self._cards_window, width=canvas_w)
            self._cards_canvas.coords(self._empty_window, canvas_w // 2, 180)
            self._refresh_cards()
        except tk.TclError:
            pass
        self._resize_after_id = None

    def _on_frame_configure(self, event):
        if self._scroll_after_id:
            self.input_window.after_cancel(self._scroll_after_id)
        self._scroll_after_id = self.input_window.after(50, self._do_scroll_update)

    def _do_scroll_update(self):
        try:
            self._cards_canvas.configure(scrollregion=self._cards_canvas.bbox("all"))
        except tk.TclError:
            pass
        self._scroll_after_id = None

    def _on_mousewheel(self, event):
        self._cards_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _set_filter(self, tag_name):
        self._filter_tag = tag_name
        self._refresh_filter_btns()
        self._refresh_cards()

    def _refresh_filter_btns(self):
        for ft, (fb, fl) in self._filter_btns.items():
            is_sel = ft == self._filter_tag
            bg = COLORS["primary_bg"] if is_sel else COLORS["pill_inactive_bg"]
            fg = COLORS["primary"] if is_sel else COLORS["pill_inactive_fg"]
            fb.configure(bg=bg)
            fl.configure(bg=bg, fg=fg)

    # ============ 笔记操作 ============

    def _save_note(self, event):
        content = self.text_input.get("1.0", tk.END).strip()
        if hasattr(self, '_placeholder_active') and self._placeholder_active:
            return "break"
        if not content:
            return "break"
        tag = self._tag_var.get() if hasattr(self, '_tag_var') else "默认"
        note = add_note(content, tag=tag)
        self._log(f"💾 已保存 [{note.get('tag','默认')}]: {note['content'][:40]}")
        self.text_input.delete("1.0", tk.END)
        self._update_char_counter()
        self._refresh_cards()
        self._flash_status("✓ 已保存!", COLORS["success"])
        self.text_input.focus_set()
        return "break"

    def _delete_note(self, note_id):
        delete_note(note_id)
        self._log(f"🗑️ 已删除记录 #{note_id}")
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
            self._flash_status("✓ 已复制到剪贴板", COLORS["success"])

    def _export_notes(self):
        notes = load_notes()
        if not notes:
            messagebox.showinfo("提示", "没有可导出的记录", parent=self.input_window)
            return
        export_dir = filedialog.askdirectory(title="选择导出目录", parent=self.input_window)
        if not export_dir:
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = os.path.join(export_dir, f"quick_note_{ts}.txt")
        json_path = os.path.join(export_dir, f"quick_note_{ts}.json")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Quick Note 导出 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"共 {len(notes)} 条记录\n" + "=" * 50 + "\n\n")
            for n in notes:
                star = " ★" if n.get("starred") else ""
                f.write(f"[#{n['id']}] [{n.get('tag','默认')}]{star}\n{n['time']}\n{n['content']}\n{'-'*40}\n\n")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        self._flash_status(f"✓ 已导出 {len(notes)} 条", COLORS["success"])
        messagebox.showinfo("导出成功", f"已导出到:\n{txt_path}", parent=self.input_window)

    def _show_edit_window(self, note_id):
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if not note:
            return

        ew = tk.Toplevel(self.input_window)
        ew.title(f"编辑 #{note['id']}")
        ew.geometry("520x400")
        ew.configure(bg=COLORS["bg"])
        ew.attributes("-topmost", True)
        ew.update_idletasks()
        ew.geometry(f"+{(ew.winfo_screenwidth()-520)//2}+{(ew.winfo_screenheight()-400)//2}")

        # 标题 — clean, no colored separator
        eh = tk.Frame(ew, bg=COLORS["header_bg"], padx=18, pady=10)
        eh.pack(fill=tk.X)
        tk.Label(eh, text=f"✏️  编辑记录 #{note['id']}", font=(FONT_FAMILY, 12, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["header_bg"]).pack(side=tk.LEFT)
        tk.Label(eh, text=f"🕐 {format_relative_time(note['time'])}", font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["header_bg"]).pack(side=tk.RIGHT)
        # No colored line — just spacing

        # 标签选择
        tag_row = tk.Frame(ew, bg=COLORS["bg"], padx=18, pady=10)
        tag_row.pack(fill=tk.X)
        tk.Label(tag_row, text="🏷️", font=(FONT_FAMILY, 10),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 6))

        edit_tag_var = tk.StringVar(value=note.get("tag", "默认"))
        edit_tag_widgets = {}

        def sel_edit_tag(t):
            edit_tag_var.set(t)
            for tn, (pf, pl) in edit_tag_widgets.items():
                pbg, pfg, _ = get_tag_pill_colors(tn)
                sel = tn == t
                pf.configure(bg=pbg if sel else COLORS["pill_inactive_bg"])
                pl.configure(bg=pbg if sel else COLORS["pill_inactive_bg"],
                             fg=pfg if sel else COLORS["pill_inactive_fg"])

        for tn in TAG_LIST:
            pbg, pfg, icon = get_tag_pill_colors(tn)
            sel = tn == edit_tag_var.get()
            pf = tk.Frame(tag_row, bg=pbg if sel else COLORS["pill_inactive_bg"], padx=8, pady=2, cursor="hand2")
            pf.pack(side=tk.LEFT, padx=3)
            pl = tk.Label(pf, text=f"{icon} {tn}", font=(FONT_FAMILY, 8),
                          fg=pfg if sel else COLORS["pill_inactive_fg"],
                          bg=pbg if sel else COLORS["pill_inactive_bg"], cursor="hand2")
            pl.pack()
            pf.bind("<ButtonPress-1>", lambda e, t=tn: sel_edit_tag(t))
            pl.bind("<ButtonPress-1>", lambda e, t=tn: sel_edit_tag(t))
            edit_tag_widgets[tn] = (pf, pl)

        # 编辑框 — no always-visible colored border
        body_f = tk.Frame(ew, bg=COLORS["bg"], padx=18, pady=4)
        body_f.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(body_f, font=(FONT_MONO, 11), wrap=tk.WORD,
                      bg=COLORS["input_bg"], fg=COLORS["text"],
                      insertbackground=COLORS["primary"],
                      selectbackground=COLORS["primary"],
                      selectforeground=COLORS["text"],
                      relief=tk.FLAT, borderwidth=10, highlightthickness=2,
                      highlightcolor=COLORS["border_focus"],
                      highlightbackground=COLORS["input_bg"],
                      padx=6, pady=8)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", note["content"])
        txt.focus_set()

        # 底部按钮
        btn_row = tk.Frame(ew, bg=COLORS["bg"], padx=18, pady=10)
        btn_row.pack(fill=tk.X)

        def do_save(e=None):
            c = txt.get("1.0", tk.END).strip()
            if c:
                update_note(note_id, c, tag=edit_tag_var.get())
                self._log(f"✏️ 已更新记录 #{note_id}")
                self._refresh_cards()
                self._flash_status(f"✓ 已更新 #{note_id}", COLORS["success"])
            ew.destroy()
            return "break"

        sb = tk.Frame(btn_row, bg=COLORS["primary"], padx=14, pady=4, cursor="hand2")
        sb.pack(side=tk.LEFT)
        sb_lbl = tk.Label(sb, text="💾  保存", font=(FONT_FAMILY, 9, "bold"),
                          fg="#ffffff", bg=COLORS["primary"], cursor="hand2")
        sb_lbl.pack()
        sb.bind("<ButtonPress-1>", lambda e: do_save())
        sb_lbl.bind("<ButtonPress-1>", lambda e: do_save())
        sb.bind("<Enter>", lambda e: (sb.configure(bg=COLORS["primary_hover"]),
                                       sb_lbl.configure(bg=COLORS["primary_hover"])))
        sb.bind("<Leave>", lambda e: (sb.configure(bg=COLORS["primary"]),
                                       sb_lbl.configure(bg=COLORS["primary"])))

        cb = tk.Frame(btn_row, bg=COLORS["surface_light"], padx=14, pady=4, cursor="hand2")
        cb.pack(side=tk.LEFT, padx=(8, 0))
        cb_lbl = tk.Label(cb, text="取消", font=(FONT_FAMILY, 9),
                          fg=COLORS["text_secondary"], bg=COLORS["surface_light"], cursor="hand2")
        cb_lbl.pack()
        cb.bind("<ButtonPress-1>", lambda e: ew.destroy())
        cb_lbl.bind("<ButtonPress-1>", lambda e: ew.destroy())
        cb.bind("<Enter>", lambda e: (cb.configure(bg=COLORS["danger"]),
                                       cb_lbl.configure(bg=COLORS["danger"], fg="#ffffff")))
        cb.bind("<Leave>", lambda e: (cb.configure(bg=COLORS["surface_light"]),
                                       cb_lbl.configure(bg=COLORS["surface_light"], fg=COLORS["text_secondary"])))

        tk.Label(btn_row, text="Ctrl+Enter 保存  ·  Esc 取消", font=(FONT_MONO, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        txt.bind("<Control-Return>", do_save)
        txt.bind("<Escape>", lambda e: ew.destroy())
        ew.bind("<Escape>", lambda e: ew.destroy())

    # ============ 右键菜单 ============

    def _show_context_menu(self, event, note_id):
        notes = load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if not note:
            return

        menu = tk.Menu(self.input_window, tearoff=0,
                       bg=COLORS["surface"], fg=COLORS["text"],
                       activebackground=COLORS["primary"], activeforeground="#ffffff",
                       font=(FONT_FAMILY, 9), relief=tk.FLAT, bd=0)

        star_text = "⭐ 取消收藏" if note.get("starred") else "⭐ 收藏"
        menu.add_command(label=star_text, command=lambda: self._toggle_star(note_id))
        menu.add_command(label="✏️ 编辑", command=lambda: self._show_edit_window(note_id))
        menu.add_command(label="📋 复制内容", command=lambda: self._copy_content(note_id))
        menu.add_separator()

        tag_menu = tk.Menu(menu, tearoff=0,
                           bg=COLORS["surface"], fg=COLORS["text"],
                           activebackground=COLORS["primary"], activeforeground="#ffffff",
                           font=(FONT_FAMILY, 9))
        for tn in TAG_LIST:
            ti = TAGS[tn]
            cur = " ✓" if note.get("tag", "默认") == tn else ""
            tag_menu.add_command(label=f"{ti['icon']} {tn}{cur}",
                                 command=lambda t=tn: self._change_tag(note_id, t))
        menu.add_cascade(label="🏷️ 标签", menu=tag_menu)

        menu.add_separator()
        menu.add_command(label="🗑️ 删除", command=lambda: self._delete_note(note_id))

        menu.tk_popup(event.x_root, event.y_root)

    def _change_tag(self, note_id, tag_name):
        update_note(note_id, tag=tag_name)
        self._refresh_cards()
        self._flash_status(f"✓ 已标记为 {tag_name}", COLORS["success"])

    # ============ 5. 卡片列表（现代卡片设计） ============

    def _refresh_cards(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return

        for w in self._cards_frame.winfo_children():
            w.destroy()
        self._card_widgets = {}

        # Configure grid columns
        cols = getattr(self, '_card_cols', 2)
        for c in range(cols):
            self._cards_frame.columnconfigure(c, weight=1, uniform="col")
        # Clear old column configs beyond current cols
        for c in range(cols, cols + 5):
            self._cards_frame.columnconfigure(c, weight=0)

        notes = load_notes()
        keyword = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""

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
            self._cards_canvas.itemconfig(self._cards_window, state="normal")
            self._cards_canvas.itemconfig(self._empty_window, state="normal")
        else:
            self._cards_canvas.itemconfig(self._empty_window, state="hidden")

        for idx, note in enumerate(filtered):
            self._create_card(note, idx)

        if keyword or self._filter_tag != "全部":
            self.count_label.config(text=f"🔍 匹配 {shown}/{total} 条")
        else:
            starred = sum(1 for n in notes if n.get("starred"))
            extra = f"  ·  ⭐{starred}" if starred else ""
            self.count_label.config(text=f"共 {total} 条记录{extra}")

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
            card_bg = COLORS["card_bg"]

        cols = getattr(self, '_card_cols', 2)
        row = index // cols
        col = index % cols

        # Card wrapper — no shadow border, use elevation via bg difference
        outer = tk.Frame(self._cards_frame, bg=COLORS["bg"], padx=0, pady=0, cursor="hand2")
        outer.grid(row=row, column=col, sticky="nsew", padx=(0, 8), pady=(0, 8))

        # Top color bar (subtle, thin)
        top_bar = tk.Frame(outer, bg=tag_color, height=2)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)

        # Main card body — no visible border by default, use background elevation
        card = tk.Frame(outer, bg=card_bg, padx=14, pady=10, cursor="hand2",
                        highlightbackground=card_bg, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=(0, 0), pady=(0, 0))
        if is_selected:
            card.configure(highlightbackground=COLORS["primary"])

        # Row 1: tag + star + more
        row1 = tk.Frame(card, bg=card_bg)
        row1.pack(fill=tk.X)

        dot_canvas = tk.Canvas(row1, width=8, height=8, bg=card_bg,
                               highlightthickness=0, borderwidth=0)
        dot_canvas.pack(side=tk.LEFT, padx=(0, 4))
        dot_canvas.create_oval(0, 0, 8, 8, fill=tag_color, outline="")

        tk.Label(row1, text=tag_name, font=(FONT_FAMILY, 8, "bold"),
                 fg=tag_color, bg=card_bg).pack(side=tk.LEFT)

        if is_starred:
            tk.Label(row1, text="⭐", font=(FONT_FAMILY, 9),
                     fg=COLORS["star_color"], bg=card_bg).pack(side=tk.LEFT, padx=(6, 0))

        more_btn = tk.Label(row1, text="⋯", font=(FONT_FAMILY, 12),
                            fg=COLORS["text_dim"], bg=card_bg, cursor="hand2")
        more_btn.pack(side=tk.RIGHT)
        more_btn.bind("<ButtonPress-1>", lambda e, nid=note_id: self._show_context_menu(e, nid))

        # Row 2: Content
        content_preview = note["content"].replace("\n", " ")[:80]
        content_lbl = tk.Label(card, text=content_preview, font=(FONT_FAMILY, 9),
                               fg=COLORS["text"], bg=card_bg,
                               anchor="nw", wraplength=220, justify="left")
        content_lbl.pack(fill=tk.X, pady=(6, 0), anchor="w")

        # Row 3: Time + meta
        rel_time = format_relative_time(note["time"])
        char_count = len(note["content"])
        footer_text = f"{rel_time}  ·  {char_count}字"
        if note.get("updated_at"):
            footer_text += "  ·  已编辑"
        footer_lbl = tk.Label(card, text=footer_text, font=(FONT_FAMILY, 7),
                              fg=COLORS["text_dim"], bg=card_bg, anchor="w")
        footer_lbl.pack(fill=tk.X, pady=(4, 0), anchor="w")

        # Event bindings
        all_widgets = [card, outer, row1, dot_canvas, content_lbl, footer_lbl, top_bar]

        for w in all_widgets:
            w.bind("<ButtonPress-1>", lambda e, nid=note_id: self._on_card_click(nid))
            w.bind("<Double-ButtonPress-1>", lambda e, nid=note_id: self._show_edit_window(nid))
            w.bind("<ButtonPress-3>", lambda e, nid=note_id: self._show_context_menu(e, nid))

        hover_data = {
            "more_btn": more_btn,
            "card": card,
            "top_bar": top_bar,
            "tag_color": tag_color,
            "is_selected": is_selected,
            "is_starred": is_starred,
            "card_widgets": all_widgets,
            "dot_canvas": dot_canvas,
        }

        for w in all_widgets:
            w.bind("<Enter>", lambda e, d=hover_data: self._on_card_hover_enter(d))
            w.bind("<Leave>", lambda e, d=hover_data: self._on_card_hover_leave(d))

        self._card_widgets[note_id] = card


    def _on_card_hover_enter(self, data):
        card = data["card"]
        more_btn = data["more_btn"]
        is_selected = data["is_selected"]
        is_starred = data["is_starred"]
        widgets = data["card_widgets"]

        try:
            if is_selected:
                hover_bg = COLORS["card_selected"]
            elif is_starred:
                hover_bg = COLORS["card_starred"]
            else:
                hover_bg = COLORS["card_hover"]

            card.configure(bg=hover_bg, highlightbackground=COLORS["primary"])
            valid_bgs = (COLORS["card_bg"], COLORS["card_hover"],
                         COLORS["card_selected"], COLORS["card_starred"])
            for w in widgets:
                try:
                    if w.winfo_class() in ("Label", "Frame", "Canvas"):
                        old_bg = w.cget("bg")
                        if old_bg in valid_bgs:
                            w.configure(bg=hover_bg)
                except tk.TclError:
                    pass
            more_btn.configure(bg=hover_bg)
        except tk.TclError:
            pass

    def _on_card_hover_leave(self, data):
        card = data["card"]
        more_btn = data["more_btn"]
        is_selected = data["is_selected"]
        is_starred = data["is_starred"]
        widgets = data["card_widgets"]

        try:
            if is_selected:
                bg = COLORS["card_selected"]
            elif is_starred:
                bg = COLORS["card_starred"]
            else:
                bg = COLORS["card_bg"]

            if not is_selected:
                card.configure(highlightbackground=bg)

            card.configure(bg=bg)
            valid_bgs = (COLORS["card_bg"], COLORS["card_hover"],
                         COLORS["card_selected"], COLORS["card_starred"])
            for w in widgets:
                try:
                    if w.winfo_class() in ("Label", "Frame", "Canvas"):
                        old_bg = w.cget("bg")
                        if old_bg in valid_bgs:
                            w.configure(bg=bg)
                except tk.TclError:
                    pass
        except tk.TclError:
            pass

    def _on_card_click(self, note_id):
        self._selected_card_id = note_id
        for nid, card_widget in self._card_widgets.items():
            try:
                is_sel = nid == note_id
                # 找到对应的 note 判断是否收藏
                notes = load_notes()
                n = next((x for x in notes if x["id"] == nid), None)
                is_starred = n.get("starred", False) if n else False

                if is_sel:
                    bg = COLORS["card_selected"]
                elif is_starred:
                    bg = COLORS["card_starred"]
                else:
                    bg = COLORS["card_bg"]

                border = COLORS["primary"] if is_sel else bg
                card_widget.configure(bg=bg, highlightbackground=border)

                for child in card_widget.winfo_children():
                    if child.winfo_class() == "Frame":
                        for sub in child.winfo_children():
                            if sub.winfo_class() in ("Label", "Frame", "Canvas"):
                                old_bg = sub.cget("bg")
                                if old_bg in (COLORS["card_bg"], COLORS["card_hover"],
                                              COLORS["card_selected"], COLORS["card_starred"]):
                                    sub.configure(bg=bg)
                        old_bg = child.cget("bg")
                        if old_bg in (COLORS["card_bg"], COLORS["card_hover"],
                                      COLORS["card_selected"], COLORS["card_starred"]):
                            child.configure(bg=bg)
                    elif child.winfo_class() in ("Label", "Canvas"):
                        old_bg = child.cget("bg")
                        if old_bg in (COLORS["card_bg"], COLORS["card_hover"],
                                      COLORS["card_selected"], COLORS["card_starred"]):
                            child.configure(bg=bg)
            except tk.TclError:
                pass

    def _flash_status(self, text, color):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        self.status_label.config(text=text, fg=color)
        self.status_dot.config(fg=color)
        if self._save_flash_id:
            self.input_window.after_cancel(self._save_flash_id)
        self._save_flash_id = self.input_window.after(2000, self._reset_status)

    def _reset_status(self):
        if self.input_window and self.input_window.winfo_exists():
            self.status_label.config(text="就绪", fg=COLORS["text_dim"])
            self.status_dot.config(fg=COLORS["success"])


def main():
    app = QuickNoteApp()
    app.start()


if __name__ == "__main__":
    main()