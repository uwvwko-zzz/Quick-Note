"""
快速记录工具 - Quick Note · Command Center Edition
入口文件
"""

# 解决 Windows 高 DPI 模糊问题
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

from quicknote.app import QuickNoteApp


def main():
    app = QuickNoteApp()
    app.start()


if __name__ == "__main__":
    main()