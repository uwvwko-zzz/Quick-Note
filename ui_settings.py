"""
UI Mixin — 设置窗口
"""
import tkinter as tk
from tkinter import messagebox

from config import COLORS, FONT_FAMILY, FONT_MONO, WINDOW_WIDTH, WINDOW_HEIGHT
from storage import (load_config, save_config, get_window_size, set_window_size,
                     get_float_ball_enabled, set_float_ball_enabled)


class SettingsMixin:
    """应用设置窗口"""

    def _show_settings_window(self):
        if hasattr(self, '_settings_win') and self._settings_win and self._settings_win.winfo_exists():
            self._settings_win.lift()
            self._settings_win.focus_force()
            return
        sw = tk.Toplevel(self.input_window)
        self._settings_win = sw
        sw.title("")
        sw.configure(bg=COLORS["bg"])
        sw.attributes("-topmost", True)
        sw.resizable(False, False)
        sw.update_idletasks()
        win_w, win_h = 480, 480
        sw.geometry(f"{win_w}x{win_h}")
        sw.geometry(f"+{(sw.winfo_screenwidth()-win_w)//2}+{(sw.winfo_screenheight()-win_h)//2}")

        cfg = load_config()

        header = tk.Frame(sw, bg=COLORS["bg"], padx=20, pady=12)
        header.pack(fill=tk.X)
        tk.Label(header, text="⚙ 设置", font=(FONT_FAMILY, 14, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Label(header, text="v1.0", font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        tk.Frame(sw, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=20)

        # Scrollable body
        scroll_container = tk.Frame(sw, bg=COLORS["bg"])
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=20)

        body = tk.Frame(scroll_container, bg=COLORS["bg"], pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        def make_section(title):
            tk.Label(body, text=title, font=(FONT_FAMILY, 10, "bold"),
                     fg=COLORS["primary"], bg=COLORS["bg"], anchor="w").pack(fill=tk.X, pady=(12, 4))

        make_section("🚀 启动")

        guide_var = tk.BooleanVar(value=cfg.get("show_guide", True))
        topmost_var = tk.BooleanVar(value=cfg.get("topmost", True))
        sound_var = tk.BooleanVar(value=cfg.get("reminder_sound", True))

        def auto_save(*args):
            c = load_config()
            c["show_guide"] = guide_var.get()
            c["topmost"] = topmost_var.get()
            c["reminder_sound"] = sound_var.get()
            save_config(c)

        guide_var.trace_add("write", auto_save)
        topmost_var.trace_add("write", auto_save)
        sound_var.trace_add("write", auto_save)

        # 使用指南
        row_guide = tk.Frame(body, bg=COLORS["bg"])
        row_guide.pack(fill=tk.X, pady=3)
        tk.Label(row_guide, text="使用指南", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Checkbutton(row_guide, variable=guide_var, text="启动时显示",
                        font=(FONT_FAMILY, 8), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                        selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                        activeforeground=COLORS["text"], cursor="hand2").pack(side=tk.RIGHT)

        # 窗口置顶
        row_topmost = tk.Frame(body, bg=COLORS["bg"])
        row_topmost.pack(fill=tk.X, pady=3)
        tk.Label(row_topmost, text="主窗口", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Checkbutton(row_topmost, variable=topmost_var, text="窗口置顶",
                        font=(FONT_FAMILY, 8), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                        selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                        activeforeground=COLORS["text"], cursor="hand2").pack(side=tk.RIGHT)

        # 浮动球
        float_var = tk.BooleanVar(value=get_float_ball_enabled())

        def on_float_toggle(*args):
            enabled = float_var.get()
            set_float_ball_enabled(enabled)
            if enabled:
                # 延迟创建，避免在设置窗口中直接操作
                self.root.after(200, self._create_float_ball)
            else:
                self._hide_float_ball()

        float_var.trace_add("write", on_float_toggle)

        row_float = tk.Frame(body, bg=COLORS["bg"])
        row_float.pack(fill=tk.X, pady=3)
        tk.Label(row_float, text="浮动球", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Checkbutton(row_float, variable=float_var, text="桌面显示",
                        font=(FONT_FAMILY, 8), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                        selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                        activeforeground=COLORS["text"], cursor="hand2").pack(side=tk.RIGHT)

        make_section("⏰ 提醒")

        # 提醒声音
        row_sound = tk.Frame(body, bg=COLORS["bg"])
        row_sound.pack(fill=tk.X, pady=3)
        tk.Label(row_sound, text="提醒声音", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Checkbutton(row_sound, variable=sound_var, text="提示音",
                        font=(FONT_FAMILY, 8), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                        selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                        activeforeground=COLORS["text"], cursor="hand2").pack(side=tk.RIGHT)

        make_section("📐 窗口大小")

        saved_w, saved_h = get_window_size()

        size_info = tk.Frame(body, bg=COLORS["bg"])
        size_info.pack(fill=tk.X, pady=(4, 6))

        size_row = tk.Frame(body, bg=COLORS["bg"])
        size_row.pack(fill=tk.X, pady=2)

        tk.Label(size_row, text="宽度", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 4))
        width_var = tk.StringVar(value=str(saved_w))
        width_entry = tk.Entry(size_row, textvariable=width_var, font=(FONT_MONO, 10),
                                width=6, bg=COLORS["input_bg"], fg=COLORS["text"],
                                insertbackground=COLORS["primary"],
                                relief=tk.FLAT, borderwidth=0,
                                highlightthickness=1, highlightcolor=COLORS["border_focus"],
                                highlightbackground=COLORS["border"])
        width_entry.pack(side=tk.LEFT, padx=(0, 12), ipady=3)

        tk.Label(size_row, text="高度", font=(FONT_FAMILY, 9),
                 fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 4))
        height_var = tk.StringVar(value=str(saved_h))
        height_entry = tk.Entry(size_row, textvariable=height_var, font=(FONT_MONO, 10),
                                 width=6, bg=COLORS["input_bg"], fg=COLORS["text"],
                                 insertbackground=COLORS["primary"],
                                 relief=tk.FLAT, borderwidth=0,
                                 highlightthickness=1, highlightcolor=COLORS["border_focus"],
                                 highlightbackground=COLORS["border"])
        height_entry.pack(side=tk.LEFT, ipady=3)

        tk.Label(size_row, text="px", font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(4, 0))

        # 内联确定按钮
        inline_apply = tk.Label(size_row, text="确定", font=(FONT_FAMILY, 8, "bold"),
                                 fg="#ffffff", bg=COLORS["primary"], cursor="hand2", padx=10, pady=2)
        inline_apply.pack(side=tk.LEFT, padx=(12, 0))
        inline_apply.bind("<ButtonPress-1>", lambda e: do_apply_size())
        inline_apply.bind("<Enter>", lambda e: inline_apply.configure(bg=COLORS["primary_hover"]))
        inline_apply.bind("<Leave>", lambda e: inline_apply.configure(bg=COLORS["primary"]))

        # 最小/最大提示
        tk.Label(body, text="范围: 400–1200 × 400–1000", font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(anchor="w", pady=(2, 0))

        status_lbl = tk.Label(body, text="", font=(FONT_FAMILY, 8),
                               fg=COLORS["text_dim"], bg=COLORS["bg"])
        status_lbl.pack(anchor="w", pady=(4, 0))

        bf = tk.Frame(sw, bg=COLORS["bg"], padx=20, pady=10)
        bf.pack(fill=tk.X)

        tk.Label(bf, text="点击确定立即生效 · Esc 关闭", font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        def do_apply_size():
            try:
                w = int(width_var.get())
                h = int(height_var.get())
            except ValueError:
                status_lbl.configure(text="❌ 请输入有效数字", fg=COLORS["danger"])
                return
            w = max(400, min(1200, w))
            h = max(400, min(1000, h))
            set_window_size(w, h)
            # 直接修改当前窗口大小
            if self.input_window and self.input_window.winfo_exists():
                self.input_window.geometry(f"{w}x{h}")
                self.input_window.update_idletasks()
                x = (self.input_window.winfo_screenwidth() - w) // 2
                y = (self.input_window.winfo_screenheight() - h) // 2
                self.input_window.geometry(f"+{x}+{y}")
            status_lbl.configure(text=f"✓ 已应用: {w} × {h}", fg=COLORS["success"])
            size_info_lbl.configure(text=f"当前: {w} × {h}")

        size_info_lbl = tk.Label(size_info, text=f"当前: {saved_w} × {saved_h}", font=(FONT_MONO, 9),
                 fg=COLORS["text_dim"], bg=COLORS["bg"])
        size_info_lbl.pack(side=tk.LEFT)

        apply_lbl = tk.Label(bf, text="确定", font=(FONT_FAMILY, 9, "bold"),
                              fg="#ffffff", bg=COLORS["primary"], cursor="hand2", padx=16, pady=4)
        apply_lbl.pack(side=tk.RIGHT, padx=(0, 8))
        apply_lbl.bind("<ButtonPress-1>", lambda e: do_apply_size())
        apply_lbl.bind("<Enter>", lambda e: apply_lbl.configure(bg=COLORS["primary_hover"]))
        apply_lbl.bind("<Leave>", lambda e: apply_lbl.configure(bg=COLORS["primary"]))

        close_lbl = tk.Label(bf, text="关闭", font=(FONT_FAMILY, 9),
                              fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2", padx=12, pady=4)
        close_lbl.pack(side=tk.RIGHT)
        close_lbl.bind("<ButtonPress-1>", lambda e: sw.destroy())
        close_lbl.bind("<Enter>", lambda e: close_lbl.configure(fg=COLORS["danger"]))
        close_lbl.bind("<Leave>", lambda e: close_lbl.configure(fg=COLORS["text_dim"]))
        sw.bind("<Escape>", lambda e: sw.destroy())
