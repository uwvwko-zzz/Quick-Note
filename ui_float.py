"""
UI Mixin — 桌面浮动球
圆形悬浮按钮，左键点击打开主窗口，拖拽移动，右键菜单，自动吸边
"""
import math
import tkinter as tk

from config import (COLORS, FLOAT_BALL_SIZE, FLOAT_BALL_ICON,
                    FLOAT_BALL_SNAP_MARGIN, FLOAT_BALL_OPACITY,
                    FONT_FAMILY)
from storage import (get_float_ball_pos, set_float_ball_pos,
                     get_float_ball_enabled, set_float_ball_enabled)


class FloatBallMixin:
    """桌面浮动球 Mixin"""

    def _create_float_ball(self):
        """创建桌面浮动球"""
        if not get_float_ball_enabled():
            return
        if hasattr(self, '_float_win') and self._float_win and self._float_win.winfo_exists():
            return

        size = FLOAT_BALL_SIZE
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-transparentcolor", "#010101")
        win.configure(bg="#010101")
        win.resizable(False, False)
        self._float_win = win

        # 浮动球位置
        saved_pos = get_float_ball_pos()
        if saved_pos:
            x, y = saved_pos
            # 确保位置在屏幕内
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = max(0, min(x, sw - size))
            y = max(0, min(y, sh - size))
        else:
            # 默认位置：屏幕右侧中间
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = sw - size - 20
            y = (sh - size) // 2
        win.geometry(f"{size}x{size}+{x}+{y}")

        # Canvas 绘制浮动球
        canvas = tk.Canvas(win, width=size, height=size,
                           bg="#010101", highlightthickness=0, bd=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self._float_canvas = canvas

        # 呼吸动画相位
        self._float_breath_phase = 0
        self._float_breath_after_id = None

        # 拖拽状态
        self._float_drag_start_x = 0
        self._float_drag_start_y = 0
        self._float_drag_moved = False
        self._float_win_x = x
        self._float_win_y = y

        # 绘制浮动球
        self._draw_float_ball()

        # 绑定事件
        canvas.bind("<ButtonPress-1>", self._float_on_press)
        canvas.bind("<B1-Motion>", self._float_on_drag)
        canvas.bind("<ButtonRelease-1>", self._float_on_release)
        canvas.bind("<ButtonPress-3>", self._float_on_right_click)
        canvas.bind("<Enter>", self._float_on_enter)
        canvas.bind("<Leave>", self._float_on_leave)

        # 开始呼吸动画
        self._float_start_breath()

        # 窗口关闭时保存位置
        win.protocol("WM_DELETE_WINDOW", self._float_on_close)

        self._log("🔵 浮动球已创建")

    def _draw_float_ball(self, hover=False):
        """绘制浮动球"""
        if not hasattr(self, '_float_canvas') or not self._float_canvas:
            return
        try:
            if not self._float_win or not self._float_win.winfo_exists():
                return
        except tk.TclError:
            return

        canvas = self._float_canvas
        canvas.delete("ball")
        size = FLOAT_BALL_SIZE
        cx, cy = size // 2, size // 2

        # 呼吸缩放
        scale = 1.0 + 0.05 * math.sin(self._float_breath_phase)
        r = (size // 2 - 4) * scale

        # 外圈光晕
        glow_r = r + 3
        glow_color = COLORS.get("glow_primary_dim", "#5a3cd0")
        if hover:
            glow_color = COLORS.get("primary", "#7c5cfc")
            glow_r = r + 5
        canvas.create_oval(cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
                           fill="", outline=glow_color, width=2, tags="ball")

        # 主圆球
        ball_color = COLORS.get("primary", "#7c5cfc")
        if hover:
            ball_color = COLORS.get("primary_hover", "#9070ff")
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                           fill=ball_color, outline="", tags="ball")

        # 高光弧（上方小半圆，模拟光泽）
        hl_r = r * 0.55
        hl_offset = r * 0.2
        hl_color = self._float_blend_color(ball_color, "#ffffff", 0.3)
        canvas.create_oval(cx - hl_r, cy - r + hl_offset,
                           cx + hl_r, cy - r + hl_offset + hl_r,
                           fill=hl_color, outline="", tags="ball")

        # 图标文字
        icon = FLOAT_BALL_ICON
        font_size = max(10, int(r * 0.7))
        canvas.create_text(cx, cy + 1, text=icon,
                           font=("Segoe UI Emoji", font_size),
                           fill="#ffffff", tags="ball")

    @staticmethod
    def _float_blend_color(hex1, hex2, ratio):
        """混合两个颜色"""
        try:
            r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
            r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex1

    # ============ 呼吸动画 ============

    def _float_start_breath(self):
        """启动呼吸动画"""
        self._float_do_breath()

    def _float_do_breath(self):
        """呼吸动画帧"""
        if not hasattr(self, '_float_win'):
            return
        try:
            if not self._float_win or not self._float_win.winfo_exists():
                return
        except tk.TclError:
            return

        self._float_breath_phase += 0.06
        # 仅更新光晕大小，不重绘全部（节省性能）
        # 每隔几帧完整重绘
        self._draw_float_ball()
        self._float_breath_after_id = self._float_win.after(80, self._float_do_breath)

    def _float_stop_breath(self):
        """停止呼吸动画"""
        if self._float_breath_after_id:
            try:
                self._float_win.after_cancel(self._float_breath_after_id)
            except Exception:
                pass
            self._float_breath_after_id = None

    # ============ 拖拽与点击 ============

    def _float_on_press(self, event):
        """鼠标按下"""
        self._float_drag_start_x = event.x
        self._float_drag_start_y = event.y
        self._float_drag_moved = False
        # 记录窗口当前位置
        try:
            geo = self._float_win.geometry()
            # geo format: WxH+X+Y
            pos = geo.split("+")
            self._float_win_x = int(pos[1])
            self._float_win_y = int(pos[2])
        except Exception:
            pass

    def _float_on_drag(self, event):
        """鼠标拖拽"""
        dx = event.x - self._float_drag_start_x
        dy = event.y - self._float_drag_start_y
        if abs(dx) > 3 or abs(dy) > 3:
            self._float_drag_moved = True
        if self._float_drag_moved:
            new_x = self._float_win_x + dx
            new_y = self._float_win_y + dy
            # 限制在屏幕内
            sw = self._float_win.winfo_screenwidth()
            sh = self._float_win.winfo_screenheight()
            size = FLOAT_BALL_SIZE
            new_x = max(-size // 2, min(new_x, sw - size // 2))
            new_y = max(0, min(new_y, sh - size))
            self._float_win.geometry(f"+{new_x}+{new_y}")
            self._float_win_x = new_x
            self._float_win_y = new_y

    def _float_on_release(self, event):
        """鼠标释放"""
        if not self._float_drag_moved:
            # 点击 → 打开主窗口
            self._log("📌 浮动球点击")
            self._show_input_window()
        # 保存当前位置（无论点击还是拖拽）
        self._float_save_pos()

    def _float_save_pos(self):
        """保存浮动球当前位置"""
        if not hasattr(self, '_float_win') or not self._float_win:
            return
        try:
            if self._float_win.winfo_exists():
                geo = self._float_win.geometry()
                pos = geo.split("+")
                set_float_ball_pos(int(pos[1]), int(pos[2]))
        except tk.TclError:
            pass

    def _float_snap_to_edge(self):
        """吸附到屏幕边缘"""
        if not hasattr(self, '_float_win') or not self._float_win:
            return
        try:
            if not self._float_win.winfo_exists():
                return
        except tk.TclError:
            return

        size = FLOAT_BALL_SIZE
        sw = self._float_win.winfo_screenwidth()
        margin = FLOAT_BALL_SNAP_MARGIN

        try:
            geo = self._float_win.geometry()
            pos = geo.split("+")
            cur_x = int(pos[1])
            cur_y = int(pos[2])
        except Exception:
            return

        # 判断靠近左边还是右边
        mid = sw // 2
        if cur_x + size // 2 <= mid:
            snap_x = margin
        else:
            snap_x = sw - size - margin

        # 动画移动到吸边位置
        self._float_animate_snap(cur_x, cur_y, snap_x, cur_y, steps=6)

        # 保存位置
        set_float_ball_pos(snap_x, cur_y)

    def _float_animate_snap(self, from_x, from_y, to_x, to_y, steps=6):
        """动画吸附效果"""
        if steps <= 0:
            self._float_win.geometry(f"+{to_x}+{to_y}")
            self._float_win_x = to_x
            self._float_win_y = to_y
            return

        ratio = 1 - (steps / 8)
        # ease-out
        ratio = 1 - (1 - ratio) ** 2
        cur_x = int(from_x + (to_x - from_x) * ratio)
        cur_y = int(from_y + (to_y - from_y) * ratio)
        self._float_win.geometry(f"+{cur_x}+{cur_y}")
        self._float_win.after(15, lambda: self._float_animate_snap(
            from_x, from_y, to_x, to_y, steps - 1))

    # ============ 右键菜单 ============

    def _float_on_right_click(self, event):
        """右键菜单 — 自定义样式"""
        if not hasattr(self, '_float_win') or not self._float_win:
            return
        try:
            if not self._float_win.winfo_exists():
                return
        except tk.TclError:
            return

        # 如果已有弹出菜单则先关闭
        if hasattr(self, '_float_popup') and self._float_popup:
            try:
                if self._float_popup.winfo_exists():
                    self._float_popup.destroy()
            except tk.TclError:
                pass

        theme_label = "☀ 切换亮色" if self.current_theme == "dark" else "🌙 切换暗色"

        items = [
            ("✍", "打开 Quick Note", self._show_input_window),
            None,  # separator
            ("📋", "今日计划", self._show_plan_from_float),
            ("📷", "OCR 识别", self._start_ocr_from_float),
            (theme_label[:1], theme_label[2:], self._toggle_theme_with_float),
            None,  # separator
            ("👁", "隐藏浮动球", self._hide_float_ball),
            ("❌", "退出程序", self.stop),
        ]

        popup = tk.Toplevel(self._float_win)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=COLORS.get("border", "#28283A"))
        self._float_popup = popup

        outer = tk.Frame(popup, bg=COLORS.get("surface", "#151519"),
                         highlightbackground=COLORS.get("border", "#28283A"),
                         highlightthickness=1)
        outer.pack(padx=1, pady=1)

        for item in items:
            if item is None:
                # 分隔线
                sep = tk.Frame(outer, bg=COLORS.get("border", "#28283A"), height=1)
                sep.pack(fill=tk.X, padx=12, pady=4)
                continue

            icon, label, cmd = item
            row = tk.Frame(outer, bg=COLORS.get("surface", "#151519"), cursor="hand2")
            row.pack(fill=tk.X, padx=4, pady=1)

            icon_lbl = tk.Label(row, text=icon, font=("Segoe UI Emoji", 11),
                                fg=COLORS.get("text_secondary", "#9090B0"),
                                bg=COLORS.get("surface", "#151519"), width=2, anchor="center")
            icon_lbl.pack(side=tk.LEFT, padx=(8, 2), pady=6)

            text_lbl = tk.Label(row, text=label, font=(FONT_FAMILY, 9),
                                fg=COLORS.get("text", "#E8E8F4"),
                                bg=COLORS.get("surface", "#151519"), anchor="w")
            text_lbl.pack(side=tk.LEFT, padx=(2, 16), pady=6, fill=tk.X, expand=True)

            # 快捷键提示（部分项）
            shortcut = ""
            if "打开" in label:
                shortcut = "Ctrl+Alt+E"
            elif "退出" in label:
                shortcut = "Ctrl+C"
            if shortcut:
                sc_lbl = tk.Label(row, text=shortcut, font=(FONT_FAMILY, 7),
                                  fg=COLORS.get("text_dim", "#505068"),
                                  bg=COLORS.get("surface", "#151519"))
                sc_lbl.pack(side=tk.RIGHT, padx=(0, 10), pady=6)

            def on_enter(e, r=row, il=icon_lbl, tl=text_lbl):
                r.configure(bg=COLORS.get("primary", "#7c5cfc"))
                il.configure(bg=COLORS.get("primary", "#7c5cfc"), fg="#ffffff")
                tl.configure(bg=COLORS.get("primary", "#7c5cfc"), fg="#ffffff")
                # 快捷键标签也需要更新
                for w in r.winfo_children():
                    if w != il and w != tl:
                        try:
                            w.configure(bg=COLORS.get("primary", "#7c5cfc"),
                                        fg="#ffffff")
                        except Exception:
                            pass

            def on_leave(e, r=row, il=icon_lbl, tl=text_lbl):
                r.configure(bg=COLORS.get("surface", "#151519"))
                il.configure(bg=COLORS.get("surface", "#151519"),
                             fg=COLORS.get("text_secondary", "#9090B0"))
                tl.configure(bg=COLORS.get("surface", "#151519"),
                             fg=COLORS.get("text", "#E8E8F4"))
                for w in r.winfo_children():
                    if w != il and w != tl:
                        try:
                            w.configure(bg=COLORS.get("surface", "#151519"),
                                        fg=COLORS.get("text_dim", "#505068"))
                        except Exception:
                            pass

            def on_click(e, c=cmd, p=popup):
                try:
                    p.destroy()
                except Exception:
                    pass
                c()

            for w in (row, icon_lbl, text_lbl):
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<ButtonPress-1>", on_click)

        # 定位弹出菜单
        popup.update_idletasks()
        pw = popup.winfo_reqwidth()
        ph = popup.winfo_reqheight()
        px = event.x_root + 4
        py = event.y_root + 4
        # 防止超出屏幕
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        if px + pw > sw:
            px = sw - pw - 8
        if py + ph > sh:
            py = sh - ph - 8
        popup.geometry(f"+{px}+{py}")

        # 点击外部关闭
        def close_popup(e=None):
            try:
                popup.destroy()
            except Exception:
                pass

        popup.bind("<FocusOut>", close_popup)
        popup.after(100, lambda: popup.focus_force())
        # 延迟绑定全局点击关闭
        self.root.after(200, lambda: self._bind_popup_close(popup))

    def _bind_popup_close(self, popup):
        """绑定全局点击关闭弹出菜单"""
        def on_press(e):
            try:
                if popup and popup.winfo_exists():
                    # 检查点击是否在 popup 内
                    x = popup.winfo_rootx()
                    y = popup.winfo_rooty()
                    w = popup.winfo_width()
                    h = popup.winfo_height()
                    if not (x <= e.x_root <= x + w and y <= e.y_root <= y + h):
                        popup.destroy()
            except tk.TclError:
                pass
        # 绑定到所有顶级窗口
        try:
            for widget in (self.root, self._float_win):
                if widget and widget.winfo_exists():
                    widget.bind("<ButtonPress-1>", on_press, add="+")
        except Exception:
            pass

    def _show_plan_from_float(self):
        """从浮动球直接打开今日计划"""
        self._show_today_plan()

    def _start_ocr_from_float(self):
        """从浮动球直接启动 OCR"""
        self._start_ocr()

    def _toggle_theme_with_float(self):
        """切换主题并刷新浮动球"""
        self._toggle_theme()
        # 重绘浮动球以适配新主题
        self._draw_float_ball()

    def _hide_float_ball(self):
        """隐藏浮动球"""
        if hasattr(self, '_float_win') and self._float_win:
            try:
                if self._float_win.winfo_exists():
                    # 保存当前位置
                    geo = self._float_win.geometry()
                    pos = geo.split("+")
                    set_float_ball_pos(int(pos[1]), int(pos[2]))
                    self._float_stop_breath()
                    self._float_win.destroy()
            except tk.TclError:
                pass
        self._float_win = None
        self._float_canvas = None
        self._log("🔵 浮动球已隐藏（可在设置中重新开启）")

    # ============ 悬停效果 ============

    def _float_on_enter(self, event):
        """鼠标进入"""
        if hasattr(self, '_float_win') and self._float_win:
            try:
                if self._float_win.winfo_exists():
                    self._draw_float_ball(hover=True)
            except tk.TclError:
                pass

    def _float_on_leave(self, event):
        """鼠标离开"""
        if hasattr(self, '_float_win') and self._float_win:
            try:
                if self._float_win.winfo_exists():
                    self._draw_float_ball(hover=False)
            except tk.TclError:
                pass

    # ============ 关闭处理 ============

    def _float_on_close(self):
        """浮动球关闭"""
        self._float_stop_breath()
        if hasattr(self, '_float_win') and self._float_win:
            try:
                if self._float_win.winfo_exists():
                    geo = self._float_win.geometry()
                    pos = geo.split("+")
                    set_float_ball_pos(int(pos[1]), int(pos[2]))
            except tk.TclError:
                pass

    def _recreate_float_ball(self):
        """重建浮动球（主题切换时调用）"""
        if hasattr(self, '_float_win') and self._float_win:
            try:
                if self._float_win.winfo_exists():
                    self._float_stop_breath()
                    self._float_win.destroy()
            except tk.TclError:
                pass
        self._float_win = None
        self._float_canvas = None
        self._create_float_ball()

    def _toggle_float_ball_visibility(self):
        """切换浮动球显示/隐藏"""
        if hasattr(self, '_float_win') and self._float_win:
            try:
                if self._float_win.winfo_exists():
                    self._hide_float_ball()
                    set_float_ball_enabled(False)
                    return
            except tk.TclError:
                pass
        # 创建浮动球
        set_float_ball_enabled(True)
        self._create_float_ball()