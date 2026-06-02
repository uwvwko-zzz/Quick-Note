"""
OCR 模块 — 截屏选取 + PaddleOCR 文字识别
"""
import threading
import tkinter as tk
from config import COLORS, FONT_FAMILY

# PaddleOCR 懒加载单例
_ocr_engine = None


def _get_ocr_engine():
    """懒加载 PaddleOCR 引擎"""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        except ImportError:
            raise RuntimeError(
                "未安装 PaddleOCR，请先运行：\n"
                "pip install paddleocr paddlepaddle"
            )
    return _ocr_engine


def preload_ocr(log_callback=None):
    """在后台线程预加载 PaddleOCR 引擎，避免首次使用时等待"""
    def _preload():
        try:
            if log_callback:
                log_callback("📷 OCR 引擎预加载中...")
            _get_ocr_engine()
            if log_callback:
                log_callback("✅ OCR 引擎预加载完成")
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ OCR 预加载跳过: {e}")
    t = threading.Thread(target=_preload, daemon=True)
    t.start()


def run_ocr(image, callback, error_callback):
    """在后台线程运行 OCR 识别

    Args:
        image: Pillow Image 对象
        callback: 识别成功回调，参数为识别出的文字字符串
        error_callback: 识别失败回调，参数为错误信息字符串
    """
    def _worker():
        try:
            engine = _get_ocr_engine()
            import numpy as np
            img_array = np.array(image)
            results = engine.ocr(img_array, cls=True)
            lines = []
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                        lines.append(text)
            text = "\n".join(lines)
            callback(text)
        except Exception as e:
            error_callback(str(e))

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


class ScreenshotSelector:
    """全屏截图覆盖层，支持鼠标拖拽选取矩形区域"""

    def __init__(self, root, on_complete, on_cancel=None):
        """
        Args:
            root: Tkinter 主窗口
            on_complete: 选取完成回调，参数为 Pillow Image 裁剪对象
            on_cancel: 取消回调（可选）
        """
        self.root = root
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self._start_x = 0
        self._start_y = 0
        self._rect_id = None
        self._overlay = None
        self._screenshot = None
        self._photo = None

    def start(self):
        """启动截屏选取"""
        try:
            from PIL import ImageGrab
        except ImportError:
            tk.messagebox.showerror(
                "依赖缺失",
                "截屏功能需要 Pillow 库，请运行：\npip install Pillow",
                parent=self.root
            )
            return

        # 截取整个屏幕
        self._screenshot = ImageGrab.grab()

        # 创建全屏覆盖窗口
        self._overlay = tk.Toplevel(self.root)
        self._overlay.attributes("-fullscreen", True)
        self._overlay.attributes("-topmost", True)
        self._overlay.configure(bg="black")
        self._overlay.attributes("-alpha", 0.3)
        self._overlay.cursor = "cross"

        screen_w = self._overlay.winfo_screenwidth()
        screen_h = self._overlay.winfo_screenheight()

        # 用 Canvas 显示截图 + 选区
        self._canvas = tk.Canvas(
            self._overlay, width=screen_w, height=screen_h,
            bg="black", highlightthickness=0, cursor="cross"
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # 提示文字
        self._canvas.create_text(
            screen_w // 2, 30,
            text="拖拽鼠标选取识别区域 · Esc 取消",
            font=(FONT_FAMILY, 14),
            fill="#ffffff", tags="hint"
        )

        # 绑定鼠标事件
        self._canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self._canvas.bind("<B1-Motion>", self._on_mouse_move)
        self._canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self._overlay.bind("<Escape>", self._on_cancel)

    def _on_mouse_down(self, event):
        self._start_x = event.x
        self._start_y = event.y
        if self._rect_id:
            self._canvas.delete(self._rect_id)

    def _on_mouse_move(self, event):
        if self._rect_id:
            self._canvas.delete(self._rect_id)
        # 绘制选区矩形（蓝色边框 + 半透明填充效果）
        x1, y1 = self._start_x, self._start_y
        x2, y2 = event.x, event.y
        self._rect_id = self._canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#7c5cfc", width=2,
            fill="#3a2a8a", stipple="gray25"
        )

    def _on_mouse_up(self, event):
        x1 = min(self._start_x, event.x)
        y1 = min(self._start_y, event.y)
        x2 = max(self._start_x, event.x)
        y2 = max(self._start_y, event.y)

        # 选区太小则忽略
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            self._on_cancel(None)
            return

        self._overlay.destroy()

        # 裁剪选中区域
        cropped = self._screenshot.crop((x1, y1, x2, y2))
        self.on_complete(cropped)

    def _on_cancel(self, event):
        if self._overlay and self._overlay.winfo_exists():
            self._overlay.destroy()
        if self.on_cancel:
            self.on_cancel()