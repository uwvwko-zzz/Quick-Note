"""
QuickNoteApp — 主界面与交互逻辑（核心）
通过 Mixin 拆分各功能模块：
  - ui_cards:   笔记卡片列表渲染与交互
  - ui_edit:    笔记编辑窗口与右键菜单
  - ui_guide:   使用指南窗口
  - ui_markdown: Markdown 预览
  - ui_ocr:     OCR 截屏识别界面
  - ui_plan:    今日计划与提醒系统
  - ui_settings: 设置窗口
"""
import os
import time
import math
import datetime
import ctypes
import tkinter as tk
from tkinter import filedialog

from config import (COLORS, HOTKEY, WINDOW_WIDTH, WINDOW_HEIGHT,
                    TAGS, TAG_LIST, FONT_FAMILY, FONT_MONO)
from utils import (rounded_rect, parse_hotkey, parse_natural_tags, format_relative_time, apply_theme)
from storage import (load_config, save_config, get_current_theme, set_current_theme,
                     load_notes, save_notes, add_note, delete_note, update_note,
                     toggle_pin,
                     load_plans, save_plans, add_plan, update_plan, delete_plan,
                     get_today_plan, get_due_reminders)

# Mixin 导入
from ui_cards import CardsMixin
from ui_edit import EditMixin
from ui_guide import GuideMixin
from ui_markdown import MarkdownMixin
from ui_ocr import OcrMixin
from ui_plan import PlanMixin
from ui_settings import SettingsMixin

user32 = ctypes.windll.user32


class QuickNoteApp(CardsMixin, EditMixin, GuideMixin, MarkdownMixin,
                   OcrMixin, PlanMixin, SettingsMixin):
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
        self._card_hover_data = {}
        self._notes_cache = None
        self._mode = "note"
        self._breath_phase = 0
        self._breath_after_id = None
        self._ambient_after_id = None

    # ============ Storage 适配器（供 Mixin 调用）============

    def _load_notes(self):
        return load_notes()

    def _save_notes(self, notes):
        save_notes(notes)

    def _update_note(self, note_id, new_content=None, tag=None, starred=None, done=None, remind_time=None):
        update_note(note_id, new_content=new_content, tag=tag, starred=starred,
                     done=done, remind_time=remind_time)

    def _delete_note_storage(self, note_id):
        delete_note(note_id)

    def _toggle_pin(self, note_id):
        pinned = toggle_pin(note_id)
        self._invalidate_cache()
        self._refresh_cards()
        self._flash_status("📌 已置顶" if pinned else "📌 已取消置顶", COLORS["success"])

    # ============ 日志与控制台 ============

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

        import signal
        def _sigint_handler(sig, frame):
            self._log("⏹ 收到 Ctrl+C，正在退出...")
            self.stop()
        signal.signal(signal.SIGINT, _sigint_handler)

        self.root.mainloop()

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
        self._card_hover_data = {}
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

        # ======== MAIN CONTAINER ========
        self._main_frame = tk.Frame(win, bg=COLORS["bg"])
        self._main_frame.pack(fill=tk.BOTH, expand=True)

        # ======== HEADER ========
        self._build_header()

        # ======== FILTER BAR ========
        self._build_filter_bar()

        # ======== CARDS AREA ========
        self._build_cards_area()

        # ======== EMPTY STATE ========
        self._build_empty_state()

        # ======== COMMAND BAR ========
        self._build_command_bar()

        self._cmd_entry.focus_set()
        self.input_window.after(150, self._refresh_cards)

    # ============ Header ============

    def _build_header(self):
        header = tk.Frame(self._main_frame, bg=COLORS["bg"], height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        brand_frame = tk.Frame(header, bg=COLORS["bg"])
        brand_frame.pack(side=tk.LEFT, padx=(18, 0), pady=8)

        title_lbl = tk.Label(brand_frame, text="✍ Quick Note", font=(FONT_FAMILY, 13, "bold"),
                              fg=COLORS["heading_accent"], bg=COLORS["bg"])
        title_lbl.pack(side=tk.LEFT)

        tk.Label(brand_frame, text=" · ", font=(FONT_FAMILY, 10),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        subtitle_lbl = tk.Label(brand_frame, text="快速记录", font=(FONT_FAMILY, 8),
                                 fg=COLORS["text_dim"], bg=COLORS["bg"])
        subtitle_lbl.pack(side=tk.LEFT)

        btn_frame = tk.Frame(header, bg=COLORS["bg"])
        btn_frame.pack(side=tk.RIGHT, padx=(0, 10), pady=8)

        def _make_icon_btn(parent, text, font_spec, command, width=28, height=28):
            btn = tk.Label(parent, text=text, font=font_spec,
                           fg=COLORS["text_dim"], bg=COLORS["bg"],
                           width=2, cursor="hand2", anchor="center")
            btn.pack(side=tk.RIGHT, padx=1)
            btn.bind("<ButtonPress-1>", lambda e: command())
            btn.bind("<Enter>", lambda e: btn.configure(fg=COLORS["text"], bg=COLORS["surface_hover"]))
            btn.bind("<Leave>", lambda e: btn.configure(fg=COLORS["text_dim"], bg=COLORS["bg"]))
            return btn

        self._close_btn = _make_icon_btn(btn_frame, "✕", (FONT_FAMILY, 9, "bold"),
                                          lambda: self.input_window.destroy())
        sep = tk.Frame(btn_frame, bg=COLORS["border"], width=1, height=16)
        sep.pack(side=tk.RIGHT, padx=(6, 6), pady=4)

        icon = "🌙" if self.current_theme == "light" else "☀"
        self._theme_btn = _make_icon_btn(btn_frame, icon, (FONT_FAMILY, 10),
                                          self._toggle_theme)
        self._help_btn = _make_icon_btn(btn_frame, "?", (FONT_FAMILY, 10, "bold"),
                                         self._show_guide)
        self._settings_btn = _make_icon_btn(btn_frame, "⚙", ("Segoe UI Emoji", 10),
                                             self._show_settings_window)

        sep2 = tk.Frame(btn_frame, bg=COLORS["border"], width=1, height=16)
        sep2.pack(side=tk.RIGHT, padx=(6, 6), pady=4)

        self._md_btn = _make_icon_btn(btn_frame, "📄", (FONT_FAMILY, 10),
                                       self._open_markdown_file)
        self._export_btn = _make_icon_btn(btn_frame, "↗", (FONT_FAMILY, 11),
                                           self._export_notes)
        self._ocr_btn = _make_icon_btn(btn_frame, "📷", (FONT_FAMILY, 10),
                                        self._start_ocr)
        self._plan_btn = _make_icon_btn(btn_frame, "📋", (FONT_FAMILY, 10),
                                         self._show_today_plan)

        line_canvas = tk.Canvas(self._main_frame, height=2, bg=COLORS["bg"],
                                 highlightthickness=0, bd=0)
        line_canvas.pack(fill=tk.X, side=tk.TOP)

        def _draw_header_line(event=None):
            line_canvas.delete("hline")
            w = line_canvas.winfo_width()
            if w < 2:
                return
            steps = min(w // 2, 60)
            mid = w // 2
            for i in range(steps):
                alpha = 1.0 - (i / steps)
                color = self._alpha_color(COLORS["primary"], alpha)
                x_off = i * (mid // steps) if steps > 0 else 0
                line_canvas.create_line(mid - x_off, 0, mid - x_off + max(mid // steps, 1), 0,
                                         fill=color, tags="hline")
                line_canvas.create_line(mid + x_off, 0, mid + x_off + max(mid // steps, 1), 0,
                                         fill=color, tags="hline")

        line_canvas.bind("<Configure>", _draw_header_line)

    @staticmethod
    def _alpha_color(hex_color, alpha):
        """Blend color with bg based on alpha"""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            bg_hex = COLORS.get("bg", "#0C0C10")
            br = int(bg_hex[1:3], 16)
            bg_ = int(bg_hex[3:5], 16)
            bb = int(bg_hex[5:7], 16)
            nr = int(r * alpha + br * (1 - alpha))
            ng = int(g * alpha + bg_ * (1 - alpha))
            nb = int(b * alpha + bb * (1 - alpha))
            return f"#{nr:02x}{ng:02x}{nb:02x}"
        except Exception:
            return hex_color

    # ============ Filter Bar ============

    def _build_filter_bar(self):
        filter_container = tk.Frame(self._main_frame, bg=COLORS["bg"], height=38)
        filter_container.pack(fill=tk.X, side=tk.TOP)
        filter_container.pack_propagate(False)

        tk.Label(filter_container, text="🔍", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(18, 4), pady=6)

        pill_frame = tk.Frame(filter_container, bg=COLORS["bg"])
        pill_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

        self._filter_frame = pill_frame
        self._filter_btns = {}
        self._rebuild_filter_pills()

    def _rebuild_filter_pills(self):
        for w in self._filter_frame.winfo_children():
            w.destroy()
        self._filter_btns = {}
        for ft in ["全部"] + TAG_LIST:
            is_sel = ft == self._filter_tag
            if ft != "全部":
                tag_info = TAGS.get(ft, {})
                icon = tag_info.get("icon", "")
                display = f"{icon} {ft}" if icon else ft
            else:
                display = "全部"

            lbl = tk.Label(self._filter_frame, text=display,
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

    # ============ Cards Area ============

    def _build_cards_area(self):
        cards_outer = tk.Frame(self._main_frame, bg=COLORS["bg"])
        cards_outer.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=10)

        self._cards_canvas = tk.Canvas(cards_outer, bg=COLORS["bg"], highlightthickness=0, borderwidth=0)
        self._scrollbar = tk.Scrollbar(cards_outer, orient=tk.VERTICAL, command=self._cards_canvas.yview,
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
        self._empty_window = self._cards_canvas.create_window((WINDOW_WIDTH // 2, 100),
                                                                window=self._empty_frame, anchor="center")
        self._empty_icon_canvas = tk.Canvas(self._empty_frame, width=80, height=80,
                                             bg=COLORS["bg"], highlightthickness=0)
        self._empty_icon_canvas.pack(pady=(24, 10))
        self._draw_breathing_crystal()

        tk.Label(self._empty_frame, text="开始记录你的想法", font=(FONT_FAMILY, 14, "bold"),
                 fg=COLORS["text"], bg=COLORS["bg"]).pack()

        hints_frame = tk.Frame(self._empty_frame, bg=COLORS["bg"])
        hints_frame.pack(pady=(8, 0))

        hints = [
            ("✎", "输入文字直接记录"),
            ("#", "加 #标签 自动分类"),
            ("/", "输入 / 搜索笔记"),
        ]
        for icon, text in hints:
            row = tk.Frame(hints_frame, bg=COLORS["bg"])
            row.pack(pady=2)
            tk.Label(row, text=icon, font=(FONT_MONO, 9, "bold"),
                     fg=COLORS["primary"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text=text, font=(FONT_FAMILY, 9),
                     fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

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

    # ============ Command Bar ============

    def _build_command_bar(self):
        cmd_outer = tk.Frame(self._main_frame, bg=COLORS["bg"])
        cmd_outer.pack(fill=tk.X, side=tk.BOTTOM)

        sep_canvas = tk.Canvas(cmd_outer, height=1, bg=COLORS["bg"], highlightthickness=0, bd=0)
        sep_canvas.pack(fill=tk.X)
        sep_canvas.bind("<Configure>", lambda e: (
            sep_canvas.delete("sep"),
            sep_canvas.create_line(18, 0, sep_canvas.winfo_width() - 18, 0,
                                    fill=COLORS["border"], tags="sep")
        ))

        input_container = tk.Frame(cmd_outer, bg=COLORS["bg"], padx=14, pady=8)
        input_container.pack(fill=tk.X)

        input_bg = tk.Frame(input_container, bg=COLORS["input_bg"],
                             highlightbackground=COLORS["border"], highlightthickness=1,
                             padx=2, pady=2)
        input_bg.pack(fill=tk.X)

        self._mode_label = tk.Label(input_bg, text="✎", font=(FONT_FAMILY, 13),
                                     fg=COLORS["primary"], bg=COLORS["input_bg"], width=2)
        self._mode_label.pack(side=tk.LEFT, padx=(6, 2), pady=4)

        self._cmd_tag = "默认"
        self._cmd_tag_label = tk.Label(input_bg, text="📌 默认", font=(FONT_FAMILY, 8, "bold"),
                                        fg=TAGS["默认"]["color"], bg=COLORS["pill_inactive_bg"],
                                        padx=6, pady=2, cursor="hand2")
        self._cmd_tag_label.pack(side=tk.LEFT, padx=(0, 4), pady=4)
        self._cmd_tag_label.bind("<ButtonPress-1>", self._cycle_cmd_tag)
        self._cmd_tag_label.bind("<Enter>", lambda e: self._cmd_tag_label.configure(bg=COLORS["pill_hover_bg"]))
        self._cmd_tag_label.bind("<Leave>", lambda e: self._cmd_tag_label.configure(
            bg=COLORS["primary_bg"] if self._cmd_tag != "默认" else COLORS["pill_inactive_bg"]))

        sep = tk.Frame(input_bg, bg=COLORS["border"], width=1, height=18)
        sep.pack(side=tk.LEFT, padx=(2, 4), pady=4)

        self._cmd_entry = tk.Text(input_bg, font=(FONT_MONO, 12), height=1,
                                   bg=COLORS["input_bg"], fg=COLORS["text"], insertbackground=COLORS["primary"],
                                   selectbackground=COLORS["primary"], selectforeground=COLORS["text"],
                                   relief=tk.FLAT, borderwidth=0, highlightthickness=0,
                                   padx=4, pady=4, wrap=tk.WORD, spacing3=2)
        self._cmd_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=4)

        self._cmd_hint = tk.Label(input_bg, text="↵", font=(FONT_MONO, 14),
                                   fg=COLORS["text_dim"], bg=COLORS["input_bg"])
        self._cmd_hint.pack(side=tk.LEFT, padx=(4, 8), pady=4)

        def _on_entry_focus_in(event):
            input_bg.configure(highlightbackground=COLORS["border_focus"])
            self._on_cmd_focus_in(event)

        def _on_entry_focus_out(event):
            input_bg.configure(highlightbackground=COLORS["border"])

        self._input_bg_frame = input_bg

        self._placeholder_active = True
        self._cmd_entry.insert("1.0", "输入笔记... #标签 · / 搜索 · !HH:MM 提醒\n⇧↵ 换行")
        self._cmd_entry.configure(fg=COLORS["text_dim"])

        self._cmd_entry.bind("<FocusIn>", _on_entry_focus_in)
        self._cmd_entry.bind("<FocusOut>", _on_entry_focus_out)
        self._cmd_entry.bind("<Return>", self._on_cmd_key_return)
        self._cmd_entry.bind("<KeyRelease>", self._on_cmd_key)
        self._cmd_entry.bind("<Escape>", lambda e: self.input_window.destroy())
        self._cmd_entry.bind("<Configure>", self._on_cmd_resize)

        status_row = tk.Frame(cmd_outer, bg=COLORS["bg"], padx=18)
        status_row.pack(fill=tk.X, pady=(0, 6))

        self._status_label = tk.Label(status_row, text="", font=(FONT_FAMILY, 7),
                                       fg=COLORS["text_dim"], bg=COLORS["bg"])
        self._status_label.pack(side=tk.LEFT)

        self.count_label = tk.Label(status_row, text="", font=(FONT_FAMILY, 7),
                                     fg=COLORS["text_dim"], bg=COLORS["bg"])
        self.count_label.pack(side=tk.RIGHT)

        self._start_reminder_check()

    # ============ Command Bar Events ============

    def _on_cmd_key_return(self, event):
        if event.state & 0x1:
            return None
        return self._on_cmd_submit(event)

    def _on_cmd_resize(self, event=None):
        if not self._cmd_entry:
            return
        try:
            content = self._cmd_entry.get("1.0", "end-1c")
            lines = content.count("\n") + 1
            new_height = max(1, min(lines, 4))
            if self._cmd_entry.cget("height") != new_height:
                self._cmd_entry.configure(height=new_height)
        except tk.TclError:
            pass

    def _on_cmd_focus_in(self, event):
        if self._placeholder_active:
            self._cmd_entry.delete("1.0", tk.END)
            self._cmd_entry.configure(fg=COLORS["text"])
            self._placeholder_active = False

    def _on_cmd_key(self, event):
        text = self._cmd_entry.get("1.0", "end-1c").strip()
        first_line = text.split("\n")[0] if text else ""
        if first_line.startswith("/"):
            self._mode = "search"
            self._mode_label.configure(text="🔍")
            self._cmd_hint.configure(text="↵ 搜")
            self._search_var.set(first_line[1:].strip())
        elif first_line.startswith("!") and len(first_line) > 1 and first_line[1:3].isdigit() and ":" in first_line[3:6]:
            self._mode = "remind"
            self._mode_label.configure(text="⏰")
            self._cmd_hint.configure(text="↵ ⏰")
        else:
            if self._mode in ("search", "remind"):
                self._mode = "note"
                self._mode_label.configure(text="✎")
                self._cmd_hint.configure(text="↵")
                self._search_var.set("")
        self._on_cmd_resize()

    def _cycle_cmd_tag(self, event=None):
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
        self._cmd_tag = tag_name
        tag_info = TAGS[tag_name]
        self._cmd_tag_label.configure(
            text=f"{tag_info['icon']} {tag_name}",
            fg=tag_info["color"],
            bg=COLORS["primary_bg"],
        )

    def _on_cmd_submit(self, event):
        text = self._cmd_entry.get("1.0", "end-1c").strip()
        if self._placeholder_active or not text:
            return "break"
        first_line = text.split("\n")[0]
        if first_line.startswith("/"):
            self._search_var.set(first_line[1:].strip())
            self._refresh_cards()
            return "break"
        remind_time = None
        clean_text = text
        if first_line.startswith("!"):
            import re
            m = re.match(r'^!(\d{1,2}):(\d{2})\s+', first_line)
            if m:
                h, mi = int(m.group(1)), int(m.group(2))
                if 0 <= h <= 23 and 0 <= mi <= 59:
                    today = datetime.datetime.now().strftime("%Y-%m-%d")
                    remind_time = f"{today} {h:02d}:{mi:02d}"
                    clean_text = first_line[m.end():]
                    remaining = "\n".join(text.split("\n")[1:])
                    if remaining.strip():
                        clean_text += "\n" + remaining
                    clean_text = clean_text.strip()
        tag, clean = parse_natural_tags(clean_text)
        if tag == "默认" and self._cmd_tag != "默认":
            tag = self._cmd_tag
        if not clean:
            return "break"
        if remind_time:
            add_plan(clean, tag=tag, remind_time=remind_time)
            self._log(f"⏰ [{tag}] {clean[:30]} · 提醒 {remind_time[-5:]}")
            self._flash_status(f"⏰ 已记录 · {remind_time[-5:]} 提醒", COLORS["success"])
        else:
            note = add_note(clean, tag=tag)
            self._invalidate_cache()
            self._log(f"💾 [{tag}] {clean[:30]}")
            self._flash_status("✓ 已记录", COLORS["success"])
        self._cmd_entry.delete("1.0", tk.END)
        self._cmd_entry.configure(height=1)
        self._mode = "note"
        self._mode_label.configure(text="✎")
        self._cmd_hint.configure(text="↵")
        self._refresh_cards()
        return "break"

    # ============ Filter ============

    def _set_filter(self, tag_name):
        self._filter_tag = tag_name
        for ft, lbl in self._filter_btns.items():
            is_sel = ft == tag_name
            if ft != "全部":
                tag_info = TAGS.get(ft, {})
                icon = tag_info.get("icon", "")
                display = f"{icon} {ft}" if icon else ft
            else:
                display = "全部"
            lbl.configure(text=display,
                           bg=COLORS["primary_bg"] if is_sel else COLORS["pill_inactive_bg"],
                           fg=COLORS["primary"] if is_sel else COLORS["pill_inactive_fg"],
                           font=(FONT_FAMILY, 8, "bold" if is_sel else "normal"))
        self._refresh_cards()

    # ============ Cards Canvas Events ============

    def _on_cards_canvas_configure(self, event):
        try:
            cw = event.width
            self._cards_canvas.itemconfig(self._cards_window, width=cw)
            self._cards_canvas.coords(self._empty_window, cw // 2, 100)
        except tk.TclError:
            pass
        if self._resize_after_id:
            try:
                self.input_window.after_cancel(self._resize_after_id)
            except Exception:
                pass
        self._resize_after_id = self.input_window.after(200, self._do_resize)

    def _do_resize(self):
        self._resize_after_id = None
        try:
            self._refresh_cards()
        except tk.TclError:
            pass

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

    # ============ Export ============

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

    # ============ Status Flash ============

    def _flash_status(self, text, color):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        try:
            self._status_label.configure(text=text, fg=color)
        except tk.TclError:
            pass
        if self._save_flash_id:
            self.input_window.after_cancel(self._save_flash_id)
        self._save_flash_id = self.input_window.after(2000, self._reset_status)

    def _reset_status(self):
        if self.input_window and self.input_window.winfo_exists():
            try:
                self._status_label.configure(text="", fg=COLORS["text_dim"])
            except tk.TclError:
                pass