"""
UI Mixin — OCR 截屏识别界面
"""
import tkinter as tk
from tkinter import messagebox

from config import COLORS, FONT_FAMILY, FONT_MONO
from utils import parse_natural_tags
from storage import add_note
from ocr import run_ocr, ScreenshotSelector


class OcrMixin:
    """OCR 截屏选取、加载动画、结果展示"""

    def _start_ocr(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        self._saved_geometry_ocr = self.input_window.geometry()
        self.input_window.withdraw()
        self.root.after(200, self._do_screenshot_select)

    def _do_screenshot_select(self):
        self._selector = ScreenshotSelector(
            self.root,
            on_complete=self._on_screenshot_captured,
            on_cancel=self._on_screenshot_cancel
        )
        self._selector.start()

    def _on_screenshot_captured(self, image):
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.deiconify()
            if hasattr(self, '_saved_geometry_ocr') and self._saved_geometry_ocr:
                self.input_window.geometry(self._saved_geometry_ocr)
                self._saved_geometry_ocr = None
        self._show_ocr_loading()
        run_ocr(image, callback=self._on_ocr_success, error_callback=self._on_ocr_error)

    def _on_screenshot_cancel(self):
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.deiconify()
            if hasattr(self, '_saved_geometry_ocr') and self._saved_geometry_ocr:
                self.input_window.geometry(self._saved_geometry_ocr)
                self._saved_geometry_ocr = None

    def _show_ocr_loading(self):
        self._ocr_loading_win = tk.Toplevel(self.input_window)
        lw = self._ocr_loading_win
        lw.title("")
        lw.configure(bg=COLORS["bg"])
        lw.attributes("-topmost", True)
        lw.resizable(False, False)
        lw.overrideredirect(True)

        win_w, win_h = 280, 140
        lw.geometry(f"{win_w}x{win_h}")
        lw.update_idletasks()
        lw.geometry(f"+{(lw.winfo_screenwidth()-win_w)//2}+{(lw.winfo_screenheight()-win_h)//2}")

        container = tk.Frame(lw, bg=COLORS["surface"], padx=24, pady=20,
                              highlightbackground=COLORS["border"], highlightthickness=1)
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        tk.Label(container, text="📷", font=(FONT_FAMILY, 20),
                 bg=COLORS["surface"], fg=COLORS["text"]).pack(pady=(0, 8))

        self._ocr_loading_label = tk.Label(container, text="正在识别中...",
                                            font=(FONT_FAMILY, 10),
                                            fg=COLORS["text_secondary"], bg=COLORS["surface"])
        self._ocr_loading_label.pack()

        self._ocr_progress_canvas = tk.Canvas(container, width=200, height=6,
                                                bg=COLORS["bg"], highlightthickness=0, bd=0)
        self._ocr_progress_canvas.pack(pady=(10, 0))

        self._ocr_progress_phase = 0
        self._ocr_progress_bar_id = None
        self._animate_ocr_progress()

    def _animate_ocr_progress(self):
        lw = getattr(self, '_ocr_loading_win', None)
        if not lw or not lw.winfo_exists():
            return
        cv = self._ocr_progress_canvas
        cv.delete("bar")
        self._ocr_progress_phase += 4
        if self._ocr_progress_phase > 200:
            self._ocr_progress_phase = 0
        bar_w = 60
        x = self._ocr_progress_phase
        if x + bar_w > 200:
            x = 200 - bar_w - (x + bar_w - 200)
        cv.create_rectangle(x, 0, x + bar_w, 6,
                             fill=COLORS["primary"], outline="", tags="bar")
        dots = "." * ((self._ocr_progress_phase // 20) % 4)
        try:
            self._ocr_loading_label.configure(text=f"正在识别中{dots}")
        except tk.TclError:
            return
        self._ocr_progress_bar_id = lw.after(80, self._animate_ocr_progress)

    def _close_ocr_loading(self):
        lw = getattr(self, '_ocr_loading_win', None)
        if lw and lw.winfo_exists():
            if self._ocr_progress_bar_id:
                try:
                    lw.after_cancel(self._ocr_progress_bar_id)
                except Exception:
                    pass
                self._ocr_progress_bar_id = None
            lw.destroy()
        self._ocr_loading_win = None

    def _on_ocr_success(self, text):
        if self.root:
            self.root.after(0, lambda: self._fill_ocr_result(text))

    def _on_ocr_error(self, error_msg):
        if self.root:
            self.root.after(0, lambda: self._show_ocr_error(error_msg))

    def _fill_ocr_result(self, text):
        self._close_ocr_loading()
        if not self.input_window or not self.input_window.winfo_exists():
            return
        text = text.strip()
        if not text:
            self._flash_status("📷 未识别到文字", COLORS["warning"])
            return
        self._log(f"📷 OCR 完成: {text[:50]}")
        self._flash_status("📷 OCR 识别完成", COLORS["success"])
        self._show_ocr_result_window(text)

    def _show_ocr_result_window(self, text):
        if hasattr(self, '_ocr_result_win') and self._ocr_result_win and self._ocr_result_win.winfo_exists():
            self._ocr_result_win.destroy()
        ow = tk.Toplevel(self.input_window)
        self._ocr_result_win = ow
        ow.title("")
        ow.configure(bg=COLORS["bg"])
        ow.attributes("-topmost", True)
        ow.resizable(True, True)
        ow.update_idletasks()

        win_w, win_h = 520, 420
        ow.geometry(f"{win_w}x{win_h}")
        ow.geometry(f"+{(ow.winfo_screenwidth()-win_w)//2}+{(ow.winfo_screenheight()-win_h)//2}")

        header = tk.Frame(ow, bg=COLORS["bg"], padx=20, pady=12)
        header.pack(fill=tk.X)
        tk.Label(header, text="📷 OCR 识别结果", font=(FONT_FAMILY, 14, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        line_count = len(text.split("\n"))
        char_count = len(text)
        tk.Label(header, text=f"{line_count} 行 · {char_count} 字", font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        tk.Frame(ow, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=20)

        body_f = tk.Frame(ow, bg=COLORS["bg"], padx=20, pady=10)
        body_f.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(body_f, font=(FONT_MONO, 11), wrap=tk.WORD,
                      bg=COLORS["input_bg"], fg=COLORS["text"],
                      insertbackground=COLORS["primary"],
                      selectbackground=COLORS["primary"],
                      selectforeground=COLORS["text"],
                      relief=tk.FLAT, borderwidth=0,
                      highlightthickness=2, highlightcolor=COLORS["border_focus"],
                      highlightbackground=COLORS["border"],
                      padx=12, pady=10)
        scrollbar = tk.Scrollbar(body_f, orient=tk.VERTICAL, command=txt.yview,
                                  bg=COLORS["scrollbar_thumb"], troughcolor=COLORS["scrollbar_bg"], width=5)
        txt.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.insert("1.0", text)
        txt.focus_set()

        bf = tk.Frame(ow, bg=COLORS["bg"], padx=20, pady=10)
        bf.pack(fill=tk.X)

        tk.Label(bf, text="Esc 关闭 · 编辑后可保存为笔记", font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        close_lbl = tk.Label(bf, text="关闭", font=(FONT_FAMILY, 9),
                              fg=COLORS["text_dim"], bg=COLORS["bg"],
                              cursor="hand2", padx=12, pady=4)
        close_lbl.pack(side=tk.RIGHT)
        close_lbl.bind("<ButtonPress-1>", lambda e: ow.destroy())
        close_lbl.bind("<Enter>", lambda e: close_lbl.configure(fg=COLORS["danger"]))
        close_lbl.bind("<Leave>", lambda e: close_lbl.configure(fg=COLORS["text_dim"]))

        def do_copy():
            ow.clipboard_clear()
            ow.clipboard_append(txt.get("1.0", tk.END).strip())
            copy_lbl.configure(text="✓ 已复制", fg=COLORS["success"])
            ow.after(1500, lambda: copy_lbl.configure(text="复制", fg=COLORS["text_secondary"]))

        copy_lbl = tk.Label(bf, text="复制", font=(FONT_FAMILY, 9),
                             fg=COLORS["text_secondary"], bg=COLORS["surface"],
                             cursor="hand2", padx=12, pady=4)
        copy_lbl.pack(side=tk.RIGHT, padx=(0, 6))
        copy_lbl.bind("<ButtonPress-1>", lambda e: do_copy())
        copy_lbl.bind("<Enter>", lambda e: copy_lbl.configure(bg=COLORS["surface_hover"]))
        copy_lbl.bind("<Leave>", lambda e: copy_lbl.configure(bg=COLORS["surface"]))

        def do_save_note():
            content = txt.get("1.0", tk.END).strip()
            if not content:
                return
            tag, clean = parse_natural_tags(content)
            add_note(clean, tag=tag)
            self._invalidate_cache()
            self._refresh_cards()
            self._log(f"💾 [{tag}] {clean[:30]}")
            save_lbl.configure(text="✓ 已保存", fg=COLORS["success"])
            ow.after(1500, lambda: save_lbl.configure(text="保存为笔记", fg="#ffffff"))
            self._flash_status("✓ OCR 结果已保存为笔记", COLORS["success"])

        save_lbl = tk.Label(bf, text="保存为笔记", font=(FONT_FAMILY, 9, "bold"),
                             fg="#ffffff", bg=COLORS["primary"],
                             cursor="hand2", padx=16, pady=4)
        save_lbl.pack(side=tk.RIGHT, padx=(0, 8))
        save_lbl.bind("<ButtonPress-1>", lambda e: do_save_note())
        save_lbl.bind("<Enter>", lambda e: save_lbl.configure(bg=COLORS["primary_hover"]))
        save_lbl.bind("<Leave>", lambda e: save_lbl.configure(bg=COLORS["primary"]))

        ow.bind("<Escape>", lambda e: ow.destroy())
        txt.bind("<Escape>", lambda e: ow.destroy())

    def _show_ocr_error(self, error_msg):
        self._close_ocr_loading()
        if not self.input_window or not self.input_window.winfo_exists():
            return
        self._log(f"❌ OCR 错误: {error_msg}")
        if "未安装" in error_msg:
            messagebox.showerror(
                "OCR 依赖缺失",
                "截屏 OCR 功能需要以下依赖：\n\n"
                "pip install paddleocr paddlepaddle Pillow\n\n"
                f"详细错误：{error_msg}",
                parent=self.input_window
            )
        else:
            self._flash_status(f"❌ OCR 失败: {error_msg[:30]}", COLORS["danger"])