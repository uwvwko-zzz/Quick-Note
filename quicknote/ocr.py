"""
OCR 模块 — 截屏选取 + PaddleOCR 文字识别
"""
import threading
import tkinter as tk
from .config import COLORS, FONT_FAMILY

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

    @staticmethod
    def _get_virtual_screen():
        """获取所有显示器的虚拟屏幕范围（左上角可能为负数）"""
        import ctypes
        # 获取虚拟屏幕（包含所有显示器）的范围
        SM_XVIRTUALSCREEN = 76
        SM_YVIRTUALSCREEN = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79
        user32 = ctypes.windll.user32
        x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        w = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        h = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        return x, y, w, h

    def start(self):
        """启动截屏选取（支持多显示器）"""
        try:
            from PIL import ImageGrab
        except ImportError:
            tk.messagebox.showerror(
                "依赖缺失",
                "截屏功能需要 Pillow 库，请运行：\npip install Pillow",
                parent=self.root
            )
            return

        # 获取所有显示器的虚拟屏幕范围
        vx, vy, vw, vh = self._get_virtual_screen()
        self._vx, self._vy = vx, vy

        # 截取所有显示器（优先用 all_screens）
        try:
            self._screenshot = ImageGrab.grab(all_screens=True)
        except TypeError:
            # 旧版 Pillow 不支持 all_screens，用 bbox
            self._screenshot = ImageGrab.grab(bbox=(vx, vy, vx + vw, vy + vh))

        # 创建覆盖窗口（不使用 overrideredirect，以便跨显示器）
        self._overlay = tk.Toplevel(self.root)
        self._overlay.attributes("-topmost", True)
        self._overlay.configure(bg="black")
        # 去掉标题栏但保留跨显示器能力
        self._overlay.overrideredirect(False)
        self._overlay.attributes("-alpha", 0.3)
        # 使用 geometry 定位并覆盖所有显示器
        self._overlay.geometry(f"{vw}x{vh}+{vx}+{vy}")
        # 隐藏标题栏（在 overrideredirect(False) 下）
        try:
            self._overlay.attributes("-toolwindow", True)
        except Exception:
            pass

        self._overlay.cursor = "cross"

        # 用 Canvas 显示选区
        self._canvas = tk.Canvas(
            self._overlay, width=vw, height=vh,
            bg="black", highlightthickness=0, cursor="cross"
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # 提示文字（居中）
        self._canvas.create_text(
            vw // 2, 30,
            text="拖拽鼠标选取区域 · Esc 取消",
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
        # 绘制选区矩形（紫色边框 + 半透明填充效果）
        x1, y1 = self._start_x, self._start_y
        x2, y2 = event.x, event.y
        self._rect_id = self._canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#9070ff", width=3,
            fill="#7c5cfc", stipple="gray12"
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

        # 计算画布在屏幕上的实际位置，修正标题栏等导致的偏移
        # canvas 的 event.x/y 是相对于 canvas 内部的坐标
        # 但截图是从虚拟屏幕左上角开始的，需要偏移修正
        try:
            canvas_root_x = self._canvas.winfo_rootx()
            canvas_root_y = self._canvas.winfo_rooty()
        except Exception:
            canvas_root_x = self._vx
            canvas_root_y = self._vy

        # 画布屏幕坐标 → 截图像素坐标的偏移
        offset_x = canvas_root_x - self._vx
        offset_y = canvas_root_y - self._vy

        self._overlay.destroy()

        # 裁剪选中区域（修正偏移）
        crop_x1 = x1 + offset_x
        crop_y1 = y1 + offset_y
        crop_x2 = x2 + offset_x
        crop_y2 = y2 + offset_y
        cropped = self._screenshot.crop((crop_x1, crop_y1, crop_x2, crop_y2))
        self.on_complete(cropped)

    def _on_cancel(self, event):
        if self._overlay and self._overlay.winfo_exists():
            self._overlay.destroy()
        if self.on_cancel:
            self.on_cancel()