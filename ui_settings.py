"""
UI Mixin — 设置窗口
"""
import tkinter as tk

from config import COLORS, FONT_FAMILY
from storage import load_config, save_config


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
        win_w, win_h = 480, 300
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

        body = tk.Frame(sw, bg=COLORS["bg"], padx=20, pady=10)
        body.pack(fill=tk.BOTH, expand=True)

        def make_section(title):
            tk.Label(body, text=title, font=(FONT_FAMILY, 10, "bold"),
                     fg=COLORS["primary"], bg=COLORS["bg"], anchor="w").pack(fill=tk.X, pady=(12, 4))

        def make_row(label_text, widget_factory):
            row = tk.Frame(body, bg=COLORS["bg"])
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label_text, font=(FONT_FAMILY, 9),
                     fg=COLORS["text_secondary"], bg=COLORS["bg"], anchor="w").pack(side=tk.LEFT)
            w = widget_factory(row)
            return w

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

        def guide_factory(parent):
            chk = tk.Checkbutton(parent, variable=guide_var, text="启动时显示",
                                  font=(FONT_FAMILY, 8), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                                  selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                                  activeforeground=COLORS["text"], cursor="hand2")
            chk.pack(side=tk.RIGHT)
            return chk
        make_row("使用指南", guide_factory)

        def topmost_factory(parent):
            chk = tk.Checkbutton(parent, variable=topmost_var, text="窗口置顶",
                                  font=(FONT_FAMILY, 8), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                                  selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                                  activeforeground=COLORS["text"], cursor="hand2")
            chk.pack(side=tk.RIGHT)
            return chk
        make_row("主窗口", topmost_factory)

        make_section("⏰ 提醒")

        def sound_factory(parent):
            chk = tk.Checkbutton(parent, variable=sound_var, text="提示音",
                                  font=(FONT_FAMILY, 8), fg=COLORS["text_secondary"], bg=COLORS["bg"],
                                  selectcolor=COLORS["surface"], activebackground=COLORS["bg"],
                                  activeforeground=COLORS["text"], cursor="hand2")
            chk.pack(side=tk.RIGHT)
            return chk
        make_row("提醒声音", sound_factory)

        bf = tk.Frame(sw, bg=COLORS["bg"], padx=20, pady=10)
        bf.pack(fill=tk.X)
        tk.Label(bf, text="设置自动保存 · Esc 关闭", font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        close_lbl = tk.Label(bf, text="关闭", font=(FONT_FAMILY, 9),
                              fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2", padx=12, pady=4)
        close_lbl.pack(side=tk.RIGHT)
        close_lbl.bind("<ButtonPress-1>", lambda e: sw.destroy())
        close_lbl.bind("<Enter>", lambda e: close_lbl.configure(fg=COLORS["danger"]))
        close_lbl.bind("<Leave>", lambda e: close_lbl.configure(fg=COLORS["text_dim"]))
        sw.bind("<Escape>", lambda e: sw.destroy())