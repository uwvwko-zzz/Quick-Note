"""
QuickNoteApp — 主界面与交互逻辑
"""
import os
import time
import math
import datetime
import ctypes
import tkinter as tk
from tkinter import messagebox, filedialog

from config import (COLORS, HOTKEY, WINDOW_WIDTH, WINDOW_HEIGHT,
                    TAGS, TAG_LIST, FONT_FAMILY, FONT_MONO)
from utils import rounded_rect, parse_hotkey, parse_natural_tags, format_relative_time, apply_theme
from storage import (load_config, save_config, get_current_theme, set_current_theme,
                     load_notes, save_notes, add_note, delete_note, update_note)

user32 = ctypes.windll.user32


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
        self._mode = "note"
        self._breath_phase = 0
        self._breath_after_id = None

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

    # ============ 启动/停止 ============

    def start(self):
        notes = load_notes()
        print()
        print("╔══════════════════════════════════════════════╗")
        print("║    ✍️  Quick Note · Command Center Edition   ║")
        print("╠══════════════════════════════════════════════╚")
        print(f"║ 热键: {HOTKEY}")
        print(f"║ 主题: {self.current_theme}")
        print(f"║ 笔记: {len(notes)} 条")
        print("╠══════════════════════════════════════════════╚")
        print("║ Ctrl+C 退出                                 ║")
        print("╚═══════════════════════════════════════════════╝")
        print()

        self._hotkey_mods, self._hotkey_vk = parse_hotkey(HOTKEY)
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

        cfg = load_config()
        if cfg.get("show_guide", True):
            self.root.after(300, self._show_guide)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        if self.root:
            self.root.quit()
        print("\n[QuickNote] 已退出")

    # ============ 热键轮询 ============

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

    # ============ 使用指南 ============

    def _show_guide(self):
        gw = tk.Toplevel(self.root)
        gw.title("使用指南")
        gw.geometry("520x620")
        gw.configure(bg=COLORS["bg"])
        gw.resizable(False, True)
        gw.attributes("-topmost", True)
        gw.update_idletasks()
        gw.geometry(f"+{(gw.winfo_screenwidth()-520)//2}+{(gw.winfo_screenheight()-620)//2}")

        header = tk.Frame(gw, bg=COLORS["bg"], padx=28, pady=16)
        header.pack(fill=tk.X)
        tk.Label(header, text="✍️ Quick Note", font=(FONT_FAMILY, 16, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(anchor="w")
        tk.Label(header, text="Command Center Edition · 快速上手指南", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(anchor="w", pady=(2, 0))

        scroll_container = tk.Frame(gw, bg=COLORS["bg"])
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=20)

        content_canvas = tk.Canvas(scroll_container, bg=COLORS["bg"], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(scroll_container, orient=tk.VERTICAL, command=content_canvas.yview,
                                  bg=COLORS["scrollbar_thumb"], troughcolor=COLORS["scrollbar_bg"], width=5)
        content_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        content_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content = tk.Frame(content_canvas, bg=COLORS["bg"], padx=8)
        content_canvas.create_window((0, 0), window=content, anchor="nw", tags="content_win")
        content.bind("<Configure>", lambda e: content_canvas.configure(scrollregion=content_canvas.bbox("all")))
        content_canvas.bind("<Configure>", lambda e: content_canvas.itemconfig("content_win", width=e.width))
        content_canvas.bind("<MouseWheel>", lambda e: content_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        guide_sections = [
            ("⌨️ 基本操作", [
                "输入文字 + Enter → 创建笔记", "输入 /关键词 → 搜索笔记",
                "双击卡片 → 编辑笔记", "右键卡片 → 收藏/编辑/删除",
                "Ctrl+Alt+E → 全局呼出窗口", "Esc → 关闭窗口",
            ]),
            ("🏷️ 自然语言标签", [
                "在文字中加 #标签名 自动分类", "如: 买牛奶 #待办",
                "支持: #默认 #重要 #待办 #灵感 #代码 #学习", "标签会自动从内容中移除",
            ]),
            ("🔍 搜索模式", [
                "输入 / 开头进入搜索模式 (图标变🔍)",
                "如: /bug  /学习  /2024", "删除 / 自动回到笔记模式",
            ]),
            ("💡 更多功能", [
                "☀/🌙 切换亮色/暗色主题", "↗ 导出笔记为 TXT 文件", "⭐ 收藏的笔记自动置顶",
            ]),
        ]
        for title, items in guide_sections:
            tk.Label(content, text=title, font=(FONT_FAMILY, 10, "bold"),
                     fg=COLORS["primary"], bg=COLORS["bg"], anchor="w").pack(fill=tk.X, pady=(12, 4))
            for item in items:
                row = tk.Frame(content, bg=COLORS["bg"])
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text="·", font=(FONT_MONO, 9), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(8, 6))
                tk.Label(row, text=item, font=(FONT_FAMILY, 9), fg=COLORS["text_secondary"], bg=COLORS["bg"], anchor="w").pack(side=tk.LEFT)

        bottom = tk.Frame(gw, bg=COLORS["bg"], padx=28, pady=16)
        bottom.pack(fill=tk.X)

        dont_show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(bottom, text="不再显示此指南", variable=dont_show_var,
                        font=(FONT_FAMILY, 9), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                        selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                        activeforeground=COLORS["text"], cursor="hand2").pack(side=tk.LEFT)

        def close_guide():
            if dont_show_var.get():
                cfg = load_config()
                cfg["show_guide"] = False
                save_config(cfg)
            gw.destroy()
            self._show_input_window()

        start_btn = tk.Label(bottom, text="开始使用 →", font=(FONT_FAMILY, 10, "bold"),
                             fg="#ffffff", bg=COLORS["primary"], padx=20, pady=6, cursor="hand2")
        start_btn.pack(side=tk.RIGHT)
        start_btn.bind("<ButtonPress-1>", lambda e: close_guide())
        start_btn.bind("<Enter>", lambda e: start_btn.configure(bg=COLORS["primary_hover"]))
        start_btn.bind("<Leave>", lambda e: start_btn.configure(bg=COLORS["primary"]))
        gw.bind("<Escape>", lambda e: close_guide())
        gw.focus_set()

    # ============ 主题切换 ============

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        apply_theme(self.current_theme)
        set_current_theme(self.current_theme)
        self._log(f"🎨 → {self.current_theme}")
        if self.input_window and self.input_window.winfo_exists():
            self._saved_geometry = self.input_window.geometry()
            self._do_show_input_window()

    # ============ 主窗口 ============

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

        if self._breath_after_id:
            self.root.after_cancel(self._breath_after_id)
            self._breath_after_id = None
        self._breath_phase = 0

        win = tk.Toplevel(self.root)
        win.title("")
        win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        win.configure(bg=COLORS["bg"])
        win.resizable(True, True)
        win.attributes("-topmost", True)
        win.focus_force()
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

        # ======== HEADER BUTTONS ========
        self._build_header_buttons()

        # ======== MAIN CONTENT ========
        content_y = 52

        # Filter pills
        self._filter_frame = tk.Frame(win, bg=COLORS["bg"])
        self._bg_canvas.create_window(WINDOW_WIDTH // 2, content_y, window=self._filter_frame, anchor="n")
        self._build_filter_pills()
        content_y += 36

        # Cards scroll area
        cards_frame = tk.Frame(win, bg=COLORS["bg"])
        self._bg_canvas.create_window(0, content_y, window=cards_frame, anchor="nw", tags="cards_area")
        self._build_cards_area(cards_frame)

        # Empty state
        self._build_empty_state()

        # ======== BOTTOM COMMAND BAR ========
        self._build_command_bar(win)

        self._bg_canvas.bind("<Configure>", self._on_bg_configure)
        self._cmd_entry.focus_set()
        self._refresh_cards()

    def _build_header_buttons(self):
        btn_x = WINDOW_WIDTH - 14
        # Close
        self._close_btn = tk.Canvas(self._bg_canvas, width=32, height=32,
                                     bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self._bg_canvas.create_window(btn_x, 16, window=self._close_btn, anchor="e")
        self._close_btn.create_text(16, 16, text="✕", fill=COLORS["text_dim"], font=(FONT_FAMILY, 10, "bold"))
        self._close_btn.bind("<Enter>", lambda e: self._close_btn.configure(bg=COLORS["danger"]))
        self._close_btn.bind("<Leave>", lambda e: self._close_btn.configure(bg=COLORS["bg"]))
        self._close_btn.bind("<ButtonPress-1>", lambda e: self.input_window.destroy())

        btn_x -= 38
        # Theme
        self._theme_btn = tk.Canvas(self._bg_canvas, width=32, height=32,
                                     bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self._bg_canvas.create_window(btn_x, 16, window=self._theme_btn, anchor="e")
        icon = "🌙" if self.current_theme == "light" else "☀"
        self._theme_btn.create_text(16, 16, text=icon, fill=COLORS["text_dim"], font=(FONT_FAMILY, 10))
        self._theme_btn.bind("<Enter>", lambda e: self._theme_btn.configure(bg=COLORS["surface_hover"]))
        self._theme_btn.bind("<Leave>", lambda e: self._theme_btn.configure(bg=COLORS["bg"]))
        self._theme_btn.bind("<ButtonPress-1>", lambda e: self._toggle_theme())

        btn_x -= 38
        # Export
        self._export_btn = tk.Canvas(self._bg_canvas, width=32, height=32,
                                      bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self._bg_canvas.create_window(btn_x, 16, window=self._export_btn, anchor="e")
        self._export_btn.create_text(16, 16, text="↗", fill=COLORS["text_dim"], font=(FONT_FAMILY, 11))
        self._export_btn.bind("<Enter>", lambda e: self._export_btn.configure(bg=COLORS["surface_hover"]))
        self._export_btn.bind("<Leave>", lambda e: self._export_btn.configure(bg=COLORS["bg"]))
        self._export_btn.bind("<ButtonPress-1>", lambda e: self._export_notes())

        btn_x -= 38
        # Help
        self._help_btn = tk.Canvas(self._bg_canvas, width=32, height=32,
                                    bg=COLORS["bg"], highlightthickness=0, cursor="hand2")
        self._bg_canvas.create_window(btn_x, 16, window=self._help_btn, anchor="e")
        self._help_btn.create_text(16, 16, text="?", fill=COLORS["text_dim"], font=(FONT_FAMILY, 11, "bold"))
        self._help_btn.bind("<Enter>", lambda e: self._help_btn.configure(bg=COLORS["surface_hover"]))
        self._help_btn.bind("<Leave>", lambda e: self._help_btn.configure(bg=COLORS["bg"]))
        self._help_btn.bind("<ButtonPress-1>", lambda e: self._show_guide())

    def _build_filter_pills(self):
        self._filter_btns = {}
        for ft in ["全部"] + TAG_LIST:
            is_sel = ft == self._filter_tag
            lbl = tk.Label(self._filter_frame, text=ft,
                           font=(FONT_FAMILY, 8, "bold" if is_sel else "normal"),
                           fg=COLORS["primary"] if is_sel else COLORS["pill_inactive_fg"],
                           bg=COLORS["primary_bg"] if is_sel else COLORS["pill_inactive_bg"],
                           padx=10, pady=3, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<ButtonPress-1>", lambda e, t=ft: self._set_filter(t))
            lbl.bind("<Enter>", lambda e, l=lbl, t=ft: l.configure(bg=COLORS["pill_hover_bg"])
                     if self._filter_tag != t else None)
            lbl.bind("<Leave>", lambda e, l=lbl, t=ft: l.configure(
                bg=COLORS["primary_bg"] if self._filter_tag == t else COLORS["pill_inactive_bg"]))
            self._filter_btns[ft] = lbl

    def _build_cards_area(self, parent):
        self._cards_canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0, borderwidth=0)
        self._scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=self._cards_canvas.yview,
                                        troughcolor=COLORS["scrollbar_bg"], bg=COLORS["scrollbar_thumb"],
                                        activebackground=COLORS["primary"], highlightthickness=0, borderwidth=0, width=5)
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

    def _build_empty_state(self):
        self._empty_frame = tk.Frame(self._cards_canvas, bg=COLORS["bg"])
        self._empty_window = self._cards_canvas.create_window((WINDOW_WIDTH // 2, 120),
                                                                window=self._empty_frame, anchor="center")
        self._empty_icon_canvas = tk.Canvas(self._empty_frame, width=80, height=80,
                                             bg=COLORS["bg"], highlightthickness=0)
        self._empty_icon_canvas.pack(pady=(20, 8))
        self._draw_breathing_crystal()
        tk.Label(self._empty_frame, text="开始记录你的想法", font=(FONT_FAMILY, 13, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg"]).pack()
        tk.Label(self._empty_frame, text="输入文字直接记录 · #标签 自动分类 · / 搜索",
                 font=(FONT_FAMILY, 8), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(pady=(6, 0))

    def _build_command_bar(self, win):
        cmd_bar_h = 72
        cmd_frame = tk.Frame(win, bg=COLORS["bg"])
        self._cmd_win = self._bg_canvas.create_window(0, win.winfo_reqheight() - cmd_bar_h,
                                                        window=cmd_frame, anchor="nw", tags="cmd_bar")
        glow_canvas = tk.Canvas(cmd_frame, height=cmd_bar_h, bg=COLORS["bg"], highlightthickness=0, bd=0)
        glow_canvas.pack(fill=tk.X)

        input_row = tk.Frame(glow_canvas, bg=COLORS["bg"])
        glow_canvas.create_window(WINDOW_WIDTH // 2, 36, window=input_row, anchor="center", tags="input_row")

        self._mode_label = tk.Label(input_row, text="✎", font=(FONT_FAMILY, 12),
                                     fg=COLORS["primary"], bg=COLORS["bg"], width=2)
        self._mode_label.pack(side=tk.LEFT, padx=(0, 4))

        # Tag selector in command bar
        self._cmd_tag = "默认"
        self._cmd_tag_label = tk.Label(input_row, text="📌 默认", font=(FONT_FAMILY, 8, "bold"),
                                        fg=TAGS["默认"]["color"], bg=COLORS["pill_inactive_bg"],
                                        padx=6, pady=2, cursor="hand2")
        self._cmd_tag_label.pack(side=tk.LEFT, padx=(0, 6))
        self._cmd_tag_label.bind("<ButtonPress-1>", self._cycle_cmd_tag)
        self._cmd_tag_label.bind("<Enter>", lambda e: self._cmd_tag_label.configure(bg=COLORS["pill_hover_bg"]))
        self._cmd_tag_label.bind("<Leave>", lambda e: self._cmd_tag_label.configure(
            bg=COLORS["primary_bg"] if self._cmd_tag != "默认" else COLORS["pill_inactive_bg"]))

        self._cmd_var = tk.StringVar()
        self._cmd_entry = tk.Entry(input_row, textvariable=self._cmd_var, font=(FONT_MONO, 12),
                                    bg=COLORS["input_bg"], fg=COLORS["text"], insertbackground=COLORS["primary"],
                                    selectbackground=COLORS["primary"], selectforeground=COLORS["text"],
                                    relief=tk.FLAT, borderwidth=0, highlightthickness=0, width=35)
        self._cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)

        self._cmd_hint = tk.Label(input_row, text="↵", font=(FONT_MONO, 14),
                                   fg=COLORS["text_dim"], bg=COLORS["bg"])
        self._cmd_hint.pack(side=tk.LEFT, padx=(8, 4))

        self._status_label = tk.Label(cmd_frame, text="", font=(FONT_FAMILY, 7),
                                       fg=COLORS["text_dim"], bg=COLORS["bg"])
        self._status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 4))

        self._placeholder_active = True
        self._cmd_entry.insert(0, "输入笔记... #标签 自动识别 · / 搜索")
        self._cmd_entry.configure(fg=COLORS["text_dim"])

        self._cmd_entry.bind("<FocusIn>", self._on_cmd_focus_in)
        self._cmd_entry.bind("<Return>", self._on_cmd_submit)
        self._cmd_entry.bind("<KeyRelease>", self._on_cmd_key)
        self._cmd_entry.bind("<Escape>", lambda e: win.destroy())

        self.count_label = tk.Label(cmd_frame, text="", font=(FONT_FAMILY, 7),
                                     fg=COLORS["text_dim"], bg=COLORS["bg"])
        self.count_label.pack(side=tk.BOTTOM, fill=tk.X, padx=20)

    # ============ Background & Ambient ============

    def _on_bg_configure(self, event):
        w, h = event.width, event.height
        if w < 2 or h < 2:
            return
        self._bg_canvas.delete("ambient")
        for cx, cy, r, key in [(w*0.2, h*0.3, 200, "ambient_1"), (w*0.8, h*0.2, 180, "ambient_2"), (w*0.5, h*0.7, 220, "ambient_3")]:
            self._bg_canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=COLORS.get(key, "#1a1a2a"), outline="", tags="ambient")
        self._bg_canvas.coords("cards_area", 0, 52)
        self._bg_canvas.coords("cmd_bar", 0, h - 72)
        try:
            self._bg_canvas.itemconfig("cards_area", width=w-6, height=max(h-52-72-36, 50))
        except tk.TclError:
            pass

    # ============ Breathing Crystal ============

    def _draw_breathing_crystal(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        cv = self._empty_icon_canvas
        cv.delete("crystal")
        self._breath_phase += 0.08
        scale = 1.0 + 0.12 * math.sin(self._breath_phase)
        cx, cy = 40, 40
        size = 24 * scale
        glow_size = size + 14
        cv.create_oval(cx-glow_size, cy-glow_size, cx+glow_size, cy+glow_size,
                        fill="", outline=COLORS["glow_primary_dim"], width=2, tags="crystal")
        pts = [cx, cy-size, cx+size*0.7, cy, cx, cy+size, cx-size*0.7, cy]
        cv.create_polygon(pts, fill=COLORS["primary"], outline="", smooth=False, tags="crystal")
        h_size = size * 0.4
        cv.create_polygon(cx, cy-size+4, cx+h_size*0.5, cy-2, cx, cy+2, cx-h_size*0.5, cy-2,
                           fill=COLORS["glow_primary"], outline="", smooth=False, tags="crystal")
        self._breath_after_id = self.input_window.after(60, self._draw_breathing_crystal)

    # ============ Command Bar Events ============

    def _on_cmd_focus_in(self, event):
        if self._placeholder_active:
            self._cmd_entry.delete(0, tk.END)
            self._cmd_entry.configure(fg=COLORS["text"])
            self._placeholder_active = False

    def _on_cmd_key(self, event):
        text = self._cmd_var.get()
        if text.startswith("/"):
            self._mode = "search"
            self._mode_label.configure(text="🔍")
            self._cmd_hint.configure(text="↵ 搜")
            self._search_var.set(text[1:].strip())
        else:
            if self._mode == "search":
                self._mode = "note"
                self._mode_label.configure(text="✎")
                self._cmd_hint.configure(text="↵")
                self._search_var.set("")

    def _cycle_cmd_tag(self, event=None):
        """点击标签选择器，弹出下拉菜单直接选择"""
        menu = tk.Menu(self.input_window, tearoff=0, bg=COLORS["surface"], fg=COLORS["text"],
                       activebackground=COLORS["primary"], activeforeground="#ffffff",
                       font=(FONT_FAMILY, 9), relief=tk.FLAT, bd=0)
        for tn in TAG_LIST:
            tag_info = TAGS[tn]
            cur = " ✓" if self._cmd_tag == tn else ""
            menu.add_command(label=f"{tag_info['icon']} {tn}{cur}",
                             command=lambda t=tn: self._set_cmd_tag(t))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def _set_cmd_tag(self, tag_name):
        """设置命令栏标签"""
        self._cmd_tag = tag_name
        tag_info = TAGS[tag_name]
        self._cmd_tag_label.configure(
            text=f"{tag_info['icon']} {tag_name}",
            fg=tag_info["color"],
            bg=COLORS["primary_bg"],
        )

    def _on_cmd_submit(self, event):
        text = self._cmd_var.get().strip()
        if self._placeholder_active or not text:
            return "break"
        if text.startswith("/"):
            self._search_var.set(text[1:].strip())
            self._refresh_cards()
            return "break"
        # Parse natural tags from text; if no #tag found, use selected tag
        tag, clean = parse_natural_tags(text)
        if tag == "默认" and self._cmd_tag != "默认":
            tag = self._cmd_tag
        if not clean:
            return "break"
        add_note(clean, tag=tag)
        self._log(f"💾 [{tag}] {clean[:30]}")
        self._cmd_var.set("")
        self._refresh_cards()
        self._flash_status("✓ 已记录", COLORS["success"])
        return "break"

    # ============ Filter ============

    def _set_filter(self, tag_name):
        self._filter_tag = tag_name
        for ft, lbl in self._filter_btns.items():
            is_sel = ft == tag_name
            lbl.configure(bg=COLORS["primary_bg"] if is_sel else COLORS["pill_inactive_bg"],
                           fg=COLORS["primary"] if is_sel else COLORS["pill_inactive_fg"],
                           font=(FONT_FAMILY, 8, "bold" if is_sel else "normal"))
        self._refresh_cards()

    # ============ Cards Canvas ============

    def _on_cards_canvas_configure(self, event):
        if self._resize_after_id:
            try: self.input_window.after_cancel(self._resize_after_id)
            except Exception: pass
        self._resize_after_id = self.input_window.after(30, lambda: self._do_resize(event))

    def _do_resize(self, event):
        try:
            cw = event.width
            self._cards_canvas.itemconfig(self._cards_window, width=cw)
            self._cards_canvas.coords(self._empty_window, cw // 2, 120)
            self._refresh_cards()
        except tk.TclError: pass
        self._resize_after_id = None

    def _on_frame_configure(self, event):
        if self._scroll_after_id:
            try: self.input_window.after_cancel(self._scroll_after_id)
            except Exception: pass
        self._scroll_after_id = self.input_window.after(50, self._do_scroll)

    def _do_scroll(self):
        try: self._cards_canvas.configure(scrollregion=self._cards_canvas.bbox("all"))
        except tk.TclError: pass
        self._scroll_after_id = None

    def _on_mousewheel(self, event):
        self._cards_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ============ Notes Operations ============

    def _export_notes(self):
        notes = load_notes()
        if not notes:
            return
        export_dir = filedialog.askdirectory(title="导出到", parent=self.input_window)
        if not export_dir:
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(export_dir, f"quick_note_{ts}.txt")
        with open(path, "w", encoding="utf-8") as f:
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
        ew.update_idletasks()
        ew.geometry(f"+{(ew.winfo_screenwidth()-480)//2}+{(ew.winfo_screenheight()-320)//2}")

        eh = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=10)
        eh.pack(fill=tk.X)
        tk.Label(eh, text=f"✏️ #{note['id']}", font=(FONT_FAMILY, 11, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Label(eh, text=format_relative_time(note["time"]), font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        tag_row = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=4)
        tag_row.pack(fill=tk.X)
        edit_tag_var = tk.StringVar(value=note.get("tag", "默认"))
        edit_tag_widgets = {}

        def sel_tag(t):
            edit_tag_var.set(t)
            for tn, lbl in edit_tag_widgets.items():
                sel = tn == t
                lbl.configure(fg=TAGS[tn]["color"] if sel else COLORS["pill_inactive_fg"],
                               bg=COLORS["primary_bg"] if sel else COLORS["pill_inactive_bg"],
                               font=(FONT_FAMILY, 8, "bold" if sel else "normal"))

        for tn in TAG_LIST:
            sel = tn == edit_tag_var.get()
            lbl = tk.Label(tag_row, text=tn, font=(FONT_FAMILY, 8, "bold" if sel else "normal"),
                           fg=TAGS[tn]["color"] if sel else COLORS["pill_inactive_fg"],
                           bg=COLORS["primary_bg"] if sel else COLORS["pill_inactive_bg"],
                           padx=8, pady=2, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<ButtonPress-1>", lambda e, t=tn: sel_tag(t))
            edit_tag_widgets[tn] = lbl

        body_f = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=8)
        body_f.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(body_f, font=(FONT_MONO, 11), wrap=tk.WORD, bg=COLORS["input_bg"], fg=COLORS["text"],
                      insertbackground=COLORS["primary"], selectbackground=COLORS["primary"],
                      selectforeground=COLORS["text"], relief=tk.FLAT, borderwidth=0,
                      highlightthickness=2, highlightcolor=COLORS["border_focus"],
                      highlightbackground=COLORS["border"], padx=12, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", note["content"])
        txt.focus_set()

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

        tk.Label(bf, text="↵ 保存 · Esc 取消", font=(FONT_MONO, 7), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        cancel_lbl = tk.Label(bf, text="取消", font=(FONT_FAMILY, 9), fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2", padx=12, pady=4)
        cancel_lbl.pack(side=tk.RIGHT)
        cancel_lbl.bind("<ButtonPress-1>", lambda e: ew.destroy())
        cancel_lbl.bind("<Enter>", lambda e: cancel_lbl.configure(fg=COLORS["danger"]))
        cancel_lbl.bind("<Leave>", lambda e: cancel_lbl.configure(fg=COLORS["text_dim"]))
        save_lbl = tk.Label(bf, text="保存", font=(FONT_FAMILY, 9, "bold"), fg=COLORS["primary"],
                             bg=COLORS["primary_bg"], cursor="hand2", padx=16, pady=4)
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
        menu = tk.Menu(self.input_window, tearoff=0, bg=COLORS["surface"], fg=COLORS["text"],
                       activebackground=COLORS["primary"], activeforeground="#ffffff",
                       font=(FONT_FAMILY, 9), relief=tk.FLAT, bd=0)
        menu.add_command(label="💔 取消收藏" if note.get("starred") else "⭐ 收藏",
                         command=lambda: self._toggle_star(note_id))
        menu.add_command(label="✏️ 编辑", command=lambda: self._show_edit_window(note_id))
        menu.add_command(label="📋 复制", command=lambda: self._copy_content(note_id))
        menu.add_separator()
        tag_menu = tk.Menu(menu, tearoff=0, bg=COLORS["surface"], fg=COLORS["text"],
                           activebackground=COLORS["primary"], activeforeground="#ffffff", font=(FONT_FAMILY, 9))
        for tn in TAG_LIST:
            cur = " ✓" if note.get("tag", "默认") == tn else ""
            tag_menu.add_command(label=f"{TAGS[tn]['icon']} {tn}{cur}",
                                 command=lambda t=tn: self._change_tag(note_id, t))
        menu.add_cascade(label="🏷️ 标签", menu=tag_menu)
        menu.add_separator()
        menu.add_command(label="🗑️ 删除", command=lambda: self._delete_note(note_id))
        menu.tk_popup(event.x_root, event.y_root)

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

    def _change_tag(self, note_id, tag_name):
        update_note(note_id, tag=tag_name)
        self._refresh_cards()
        self._flash_status(f"✓ → {tag_name}", COLORS["success"])

    # ============ Cards List ============

    def _refresh_cards(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        for w in self._cards_inner.winfo_children():
            w.destroy()
        self._card_widgets = {}
        self._cards_inner.columnconfigure(0, weight=1)

        notes = load_notes()
        keyword = self._search_var.get().strip().lower() if hasattr(self, '_search_var') else ""
        filtered = []
        for n in notes:
            if self._filter_tag != "全部" and n.get("tag", "默认") != self._filter_tag:
                continue
            if keyword:
                searchable = f"{n['content']} {n['time']} {n.get('tag','默认')}".lower()
                if keyword not in searchable:
                    continue
            filtered.append(n)
        filtered.sort(key=lambda n: (not n.get("starred", False), n.get("time", "")), reverse=True)

        total, shown = len(notes), len(filtered)
        self._cards_canvas.itemconfig(self._empty_window, state="normal" if shown == 0 else "hidden")
        for idx, note in enumerate(filtered):
            self._create_card(note, idx)

        if keyword or self._filter_tag != "全部":
            self.count_label.config(text=f"🔍 {shown}/{total}")
        else:
            starred = sum(1 for n in notes if n.get("starred"))
            self.count_label.config(text=f"共 {total} 条" + (f" · ⭐{starred}" if starred else ""))

    def _create_card(self, note, index=0):
        note_id = note["id"]
        is_selected = self._selected_card_id == note_id
        is_starred = note.get("starred", False)
        tag_name = note.get("tag", "默认")
        tag_color = TAGS.get(tag_name, TAGS["默认"])["color"]
        card_bg = COLORS["card_selected"] if is_selected else (COLORS["card_starred"] if is_starred else COLORS["surface"])

        row = tk.Frame(self._cards_inner, bg=COLORS["bg"])
        row.grid(row=index, column=0, sticky="ew", padx=16, pady=(0, 2))

        tl_col = tk.Frame(row, bg=COLORS["bg"], width=24)
        tl_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        tl_col.pack_propagate(False)
        dot_cv = tk.Canvas(tl_col, width=24, height=24, bg=COLORS["bg"], highlightthickness=0, bd=0)
        dot_cv.pack(pady=(4, 0))
        dot_cv.create_oval(6, 6, 18, 18, fill="", outline=tag_color, width=2)
        dot_cv.create_oval(9, 9, 15, 15, fill=tag_color, outline="")

        card = tk.Frame(row, bg=card_bg, padx=12, pady=8, cursor="hand2",
                        highlightbackground=COLORS["glass_border"], highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if is_selected:
            card.configure(highlightbackground=COLORS["primary"])

        r1 = tk.Frame(card, bg=card_bg)
        r1.pack(fill=tk.X)
        tk.Label(r1, text=tag_name, font=(FONT_FAMILY, 7, "bold"), fg=tag_color, bg=card_bg).pack(side=tk.LEFT)
        tk.Label(r1, text=format_relative_time(note["time"]), font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=card_bg).pack(side=tk.LEFT, padx=(8, 0))
        if is_starred:
            tk.Label(r1, text="⭐", font=(FONT_FAMILY, 8), fg=COLORS["star_color"], bg=card_bg).pack(side=tk.LEFT, padx=(6, 0))
        more = tk.Label(r1, text="⋯", font=(FONT_FAMILY, 11), fg=COLORS["text_dim"], bg=card_bg, cursor="hand2")
        more.pack(side=tk.RIGHT)
        more.bind("<ButtonPress-1>", lambda e, nid=note_id: self._show_context_menu(e, nid))

        tk.Label(card, text=note["content"].replace("\n", " ")[:100], font=(FONT_FAMILY, 9),
                 fg=COLORS["text"], bg=card_bg, anchor="nw", wraplength=380, justify="left").pack(fill=tk.X, pady=(4, 0))

        all_w = [card, row, r1, dot_cv]
        for w in all_w:
            w.bind("<ButtonPress-1>", lambda e, nid=note_id: self._on_card_click(nid))
            w.bind("<Double-ButtonPress-1>", lambda e, nid=note_id: self._show_edit_window(nid))
            w.bind("<ButtonPress-3>", lambda e, nid=note_id: self._show_context_menu(e, nid))

        hover_d = {"card": card, "all_w": all_w, "more": more, "is_sel": is_selected, "is_star": is_starred}
        for w in all_w:
            w.bind("<Enter>", lambda e, d=hover_d: self._card_enter(d))
            w.bind("<Leave>", lambda e, d=hover_d: self._card_leave(d))
        self._card_widgets[note_id] = card

    def _card_enter(self, d):
        bg = COLORS["card_selected"] if d["is_sel"] else COLORS["card_hover"]
        try:
            d["card"].configure(bg=bg, highlightbackground=COLORS["primary"])
            for w in d["all_w"]:
                try:
                    if w.winfo_class() in ("Label", "Frame", "Canvas"):
                        old = w.cget("bg")
                        if old in (COLORS["surface"], COLORS["card_hover"], COLORS["card_selected"], COLORS["card_starred"]):
                            w.configure(bg=bg)
                except tk.TclError: pass
            d["more"].configure(bg=bg)
        except tk.TclError: pass

    def _card_leave(self, d):
        bg = COLORS["card_selected"] if d["is_sel"] else (COLORS["card_starred"] if d["is_star"] else COLORS["surface"])
        try:
            if not d["is_sel"]:
                d["card"].configure(highlightbackground=COLORS["glass_border"])
            d["card"].configure(bg=bg)
            for w in d["all_w"]:
                try:
                    if w.winfo_class() in ("Label", "Frame", "Canvas"):
                        old = w.cget("bg")
                        if old in (COLORS["surface"], COLORS["card_hover"], COLORS["card_selected"], COLORS["card_starred"]):
                            w.configure(bg=bg)
                except tk.TclError: pass
        except tk.TclError: pass

    def _on_card_click(self, note_id):
        self._selected_card_id = note_id
        for nid, cw in self._card_widgets.items():
            try:
                is_sel = nid == note_id
                bg = COLORS["card_selected"] if is_sel else COLORS["surface"]
                cw.configure(bg=bg, highlightbackground=COLORS["primary"] if is_sel else COLORS["glass_border"])
                for child in cw.winfo_children():
                    if child.winfo_class() == "Frame":
                        for sub in child.winfo_children():
                            if sub.winfo_class() in ("Label", "Canvas"):
                                try:
                                    if sub.cget("bg") in (COLORS["surface"], COLORS["card_hover"], COLORS["card_selected"], COLORS["card_starred"]):
                                        sub.configure(bg=bg)
                                except tk.TclError: pass
                        try:
                            if child.cget("bg") in (COLORS["surface"], COLORS["card_hover"], COLORS["card_selected"], COLORS["card_starred"]):
                                child.configure(bg=bg)
                        except tk.TclError: pass
            except tk.TclError: pass

    def _flash_status(self, text, color):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        try: self._status_label.configure(text=text, fg=color)
        except tk.TclError: pass
        if self._save_flash_id:
            self.input_window.after_cancel(self._save_flash_id)
        self._save_flash_id = self.input_window.after(2000, self._reset_status)

    def _reset_status(self):
        if self.input_window and self.input_window.winfo_exists():
            try: self._status_label.configure(text="", fg=COLORS["text_dim"])
            except tk.TclError: pass