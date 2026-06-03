"""
UI Mixin — 截屏功能
1. 截图到剪贴板：框选区域 → 自动复制，不保存文件
2. 截图预览：框选区域 → 弹出预览窗口，方便抄写
"""
import ctypes
import io
import tkinter as tk
from PIL import ImageTk

from .config import COLORS, FONT_FAMILY
from .ocr import ScreenshotSelector


def _image_to_clipboard(image):
    """将 PIL Image 复制到 Windows 剪贴板（不落盘）"""
    output = io.BytesIO()
    image.save(output, "BMP")
    dib_data = output.getvalue()[14:]

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

    if not user32.OpenClipboard(0):
        return False
    try:
        user32.EmptyClipboard()
        h_mem = kernel32.GlobalAlloc(0x0042, len(dib_data))
        if not h_mem:
            return False
        ptr = kernel32.GlobalLock(h_mem)
        ctypes.memmove(ptr, dib_data, len(dib_data))
        kernel32.GlobalUnlock(h_mem)
        result = user32.SetClipboardData(8, h_mem)
        return bool(result)
    finally:
        user32.CloseClipboard()


class ScreenshotMixin:
    """截屏功能 Mixin"""

    # ============ 截图到剪贴板 ============

    def _start_screenshot(self):
        """启动截屏（复制到剪贴板）"""
        self._screenshot_mode = "clipboard"
        self._launch_screenshot_selector()

    # ============ 截图预览 ============

    def _start_screenshot_preview(self):
        """启动截屏（预览窗口）"""
        self._screenshot_mode = "preview"
        self._launch_screenshot_selector()

    # ============ 通用截屏流程 ============

    def _launch_screenshot_selector(self):
        """隐藏主窗口并启动区域选取"""
        if self.input_window and self.input_window.winfo_exists():
            self._saved_geometry_screenshot = self.input_window.geometry()
            self.input_window.withdraw()
        self.root.after(200, self._do_screenshot)

    def _do_screenshot(self):
        """执行截屏选取"""
        self._screenshot_selector = ScreenshotSelector(
            self.root,
            on_complete=self._on_screenshot_done,
            on_cancel=self._on_screenshot_cancel
        )
        self._screenshot_selector.start()

    def _on_screenshot_done(self, image):
        """截图完成 → 根据模式处理"""
        # 恢复主窗口
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.deiconify()
            if hasattr(self, '_saved_geometry_screenshot') and self._saved_geometry_screenshot:
                self.input_window.geometry(self._saved_geometry_screenshot)
                self._saved_geometry_screenshot = None

        mode = getattr(self, '_screenshot_mode', 'clipboard')
        w, h = image.size

        if mode == "preview":
            self._log(f"🔍 截图预览 ({w}×{h})")
            self._show_screenshot_preview(image)
        else:
            try:
                success = _image_to_clipboard(image)
                if success:
                    self._log(f"📸 截图已复制到剪贴板 ({w}×{h})")
                    self._flash_status(f"📸 已复制到剪贴板 ({w}×{h})", COLORS["success"])
                    self._show_screenshot_toast(w, h)
                else:
                    self._log("❌ 复制到剪贴板失败")
                    self._flash_status("❌ 截图复制失败", COLORS["danger"])
            except Exception as e:
                self._log(f"❌ 截图失败: {e}")
                self._flash_status("❌ 截图失败", COLORS["danger"])

    def _on_screenshot_cancel(self):
        """截屏取消"""
        if self.input_window and self.input_window.winfo_exists():
            self.input_window.deiconify()
            if hasattr(self, '_saved_geometry_screenshot') and self._saved_geometry_screenshot:
                self.input_window.geometry(self._saved_geometry_screenshot)
                self._saved_geometry_screenshot = None

    # ============ 剪贴板成功提示 ============

    def _show_screenshot_toast(self, w, h):
        """截图复制成功后弹出短暂提示"""
        parent = self.input_window if (self.input_window and self.input_window.winfo_exists()) else self.root
        toast = tk.Toplevel(parent)
        toast.title("")
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=COLORS["border"])

        container = tk.Frame(toast, bg=COLORS["surface"],
                              highlightbackground=COLORS["success"],
                              highlightthickness=2, padx=20, pady=12)
        container.pack(padx=2, pady=2)

        tk.Label(container, text="📸 截图已复制到剪贴板",
                 font=(FONT_FAMILY, 11, "bold"),
                 fg=COLORS["success"], bg=COLORS["surface"]).pack(anchor="w")
        tk.Label(container, text=f"尺寸: {w} × {h}  ·  可直接粘贴",
                 font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["surface"]).pack(anchor="w", pady=(4, 0))

        toast.update_idletasks()
        tw = toast.winfo_reqwidth()
        th = toast.winfo_reqheight()
        sw = toast.winfo_screenwidth()
        sh = toast.winfo_screenheight()
        x = (sw - tw) // 2
        y = (sh - th) // 2
        toast.geometry(f"+{x}+{y}")

        toast.after(2000, lambda: toast.destroy())

    # ============ 截图预览窗口 ============

    def _show_screenshot_preview(self, image):
        """截图后显示预览窗口，方便抄写"""
        preview = tk.Toplevel(self.input_window if (self.input_window and self.input_window.winfo_exists()) else self.root)
        preview.title("截图预览")
        preview.configure(bg=COLORS["bg"])
        preview.attributes("-topmost", True)
        preview.resizable(True, True)

        sw = preview.winfo_screenwidth()
        sh = preview.winfo_screenheight()
        max_w = int(sw * 0.6)
        max_h = int(sh * 0.7)
        img_w, img_h = image.size

        scale = min(1.0, max_w / img_w, max_h / img_h)
        display_w = int(img_w * scale)
        display_h = int(img_h * scale)

        # header
        header = tk.Frame(preview, bg=COLORS["bg"], padx=16, pady=8)
        header.pack(fill=tk.X)
        tk.Label(header, text="📸 截图预览", font=(FONT_FAMILY, 12, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Label(header, text=f"{img_w} × {img_h}  ·  Esc 关闭  ·  滚轮缩放",
                 font=(FONT_FAMILY, 8), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        tk.Frame(preview, bg=COLORS["border"], height=1).pack(fill=tk.X)

        # 图片区域（可滚动）
        img_container = tk.Frame(preview, bg=COLORS["bg"])
        img_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        img_canvas = tk.Canvas(img_container, bg=COLORS["surface"],
                                highlightthickness=0, bd=0)
        v_scroll = tk.Scrollbar(img_container, orient=tk.VERTICAL, command=img_canvas.yview,
                                 bg=COLORS["scrollbar_thumb"], troughcolor=COLORS["scrollbar_bg"], width=5)
        h_scroll = tk.Scrollbar(img_container, orient=tk.HORIZONTAL, command=img_canvas.xview,
                                 bg=COLORS["scrollbar_thumb"], troughcolor=COLORS["scrollbar_bg"], width=5)
        img_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        img_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        display_img = image.resize((display_w, display_h))
        # 用局部变量保持引用，避免被 GC 回收
        state = {"photo": ImageTk.PhotoImage(display_img), "original": image, "scale": scale}
        img_canvas.create_image(0, 0, anchor="nw", image=state["photo"])

        img_canvas.configure(scrollregion=(0, 0, display_w, display_h))

        # header 显示序号
        if not hasattr(self, '_preview_count'):
            self._preview_count = 0
        self._preview_count += 1
        count = self._preview_count

        # 更新 header 显示序号
        for w in header.winfo_children():
            try:
                txt = w.cget("text")
                if "截图预览" in txt:
                    w.configure(text=f"📸 截图预览 #{count}")
                    break
            except Exception:
                pass

        # 底部
        bf = tk.Frame(preview, bg=COLORS["bg"], padx=16, pady=8)
        bf.pack(fill=tk.X)

        tk.Label(bf, text="鼠标滚轮缩放  ·  拖拽滚动条查看细节",
                 font=(FONT_FAMILY, 7), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        def _zoom_preview(event):
            factor = 1.1 if event.delta > 0 else 0.9
            new_scale = state["scale"] * factor
            new_scale = max(0.1, min(3.0, new_scale))
            state["scale"] = new_scale
            new_w = int(img_w * new_scale)
            new_h = int(img_h * new_scale)
            resized = state["original"].resize((new_w, new_h))
            state["photo"] = ImageTk.PhotoImage(resized)
            img_canvas.delete("all")
            img_canvas.create_image(0, 0, anchor="nw", image=state["photo"])
            img_canvas.configure(scrollregion=(0, 0, new_w, new_h))

        img_canvas.bind("<MouseWheel>", _zoom_preview)

        close_lbl = tk.Label(bf, text="关闭", font=(FONT_FAMILY, 9),
                              fg=COLORS["text_dim"], bg=COLORS["bg"],
                              cursor="hand2", padx=12, pady=4)
        close_lbl.pack(side=tk.RIGHT)
        close_lbl.bind("<ButtonPress-1>", lambda e: preview.destroy())
        close_lbl.bind("<Enter>", lambda e: close_lbl.configure(fg=COLORS["danger"]))
        close_lbl.bind("<Leave>", lambda e: close_lbl.configure(fg=COLORS["text_dim"]))

        win_w = min(display_w + 40, max_w)
        win_h = min(display_h + 100, max_h)
        x = (sw - win_w) // 2
        y = (sh - win_h) // 2
        preview.geometry(f"{win_w}x{win_h}+{x}+{y}")

        preview.bind("<Escape>", lambda e: preview.destroy())