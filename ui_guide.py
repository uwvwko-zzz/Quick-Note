"""
UI Mixin — 使用指南窗口
"""
import tkinter as tk

from config import COLORS, FONT_FAMILY, FONT_MONO
from storage import load_config, save_config


class GuideMixin:
    """使用指南弹窗"""

    def _show_guide(self):
        if hasattr(self, '_guide_win') and self._guide_win and self._guide_win.winfo_exists():
            self._guide_win.lift()
            self._guide_win.focus_force()
            return
        gw = tk.Toplevel(self.root)
        self._guide_win = gw
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

        def _on_guide_mousewheel(event):
            content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", _on_guide_mousewheel)
            for child in widget.winfo_children():
                _bind_mousewheel_recursive(child)

        def _delayed_bind():
            _bind_mousewheel_recursive(gw)
        gw.after(100, _delayed_bind)

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
            ("📷 OCR 截屏识别", [
                "点击 📷 按钮启动截屏识别",
                "拖拽鼠标框选屏幕上的文字区域",
                "识别完成后弹出结果窗口，支持多行",
                "可编辑、复制或保存为笔记 · Esc 关闭",
            ]),
            ("📋 今日计划 + 提醒", [
                "输入 !HH:MM 内容 → 创建定时提醒",
                "如: !14:00 开会讨论 → 14:00 弹窗提醒",
                "点击 📋 按钮查看今日计划",
                "到时自动弹窗 · 可完成/稍后提醒",
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
