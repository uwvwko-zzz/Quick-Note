"""
配置文件 — 常量、主题配色、标签定义、热键映射
"""

# ============ 配置 ============
HOTKEY = "ctrl+alt+e"
WINDOW_WIDTH = 560
WINDOW_HEIGHT = 700
CARD_MIN_WIDTH = 260
# ==============================

# ============ 标签定义 ============
TAGS = {
    "默认": {"color": "#8b8fa3", "icon": "📌"},
    "重要": {"color": "#f43f5e", "icon": "🔴"},
    "待办": {"color": "#f59e0b", "icon": "🟡"},
    "灵感": {"color": "#a78bfa", "icon": "🟣"},
    "代码": {"color": "#34d399", "icon": "🟢"},
    "学习": {"color": "#60a5fa", "icon": "🔵"},
}
TAG_LIST = list(TAGS.keys())

# ============ 主题配色 ============
THEMES = {
    "dark": {
        "bg": "#0E0E12", "surface": "#16161D", "surface_light": "#1E1E28",
        "surface_hover": "#26263A", "card_bg": "#181822", "card_hover": "#20202E",
        "card_selected": "#2A1E4A", "card_starred": "#261E30", "input_bg": "#1A1A26",
        "input_focus_bg": "#1E1E2C", "border": "#2A2A38", "border_focus": "#7c5cfc",
        "border_light": "#333348", "primary": "#7c5cfc", "primary_hover": "#9070ff",
        "primary_bg": "#2A1E50", "danger": "#f0465a", "danger_hover": "#e03050",
        "success": "#30d8a0", "warning": "#f0c030", "text": "#E4E4F0",
        "text_secondary": "#8888A8", "text_dim": "#4A4A64", "heading": "#C0B8D8",
        "heading_accent": "#A890FF", "header_bg": "#0E0E12", "footer_bg": "#0E0E12",
        "search_bg": "#1A1A26", "search_icon": "#6868A0", "pill_inactive_bg": "#1E1E2A",
        "pill_inactive_fg": "#5E5E78", "pill_hover_bg": "#28284A", "star_color": "#f0c030",
        "shadow": "#08080C", "scrollbar_bg": "#12121A", "scrollbar_thumb": "#30304A",
        "char_counter": "#3A3A54", "char_limit": "#f0465a", "glow_primary": "#7c5cfc",
        "glow_primary_dim": "#5a3cd0", "ambient_1": "#1a0a3a", "ambient_2": "#0a1a2a",
        "ambient_3": "#1a0a20", "glass_border": "#2A2A38", "glass_bg": "#1A1A24",
        "timeline_line": "#1E1E2E", "mode_indicator": "#7c5cfc",
    },
    "light": {
        "bg": "#F2F2F8", "surface": "#FFFFFF", "surface_light": "#EEEFF4",
        "surface_hover": "#E0E0F0", "card_bg": "#FFFFFF", "card_hover": "#F0F0FA",
        "card_selected": "#E0D8FF", "card_starred": "#FFF4E0", "input_bg": "#FFFFFF",
        "input_focus_bg": "#FCFAFF", "border": "#D0D0E0", "border_focus": "#7c5cfc",
        "border_light": "#C0C0D4", "primary": "#7c5cfc", "primary_hover": "#6d4df0",
        "primary_bg": "#E8E0FF", "danger": "#f0465a", "danger_hover": "#e03050",
        "success": "#20c090", "warning": "#e8a820", "text": "#1A1A2E",
        "text_secondary": "#605E78", "text_dim": "#A0A0B8", "heading": "#6828d8",
        "heading_accent": "#7840f0", "header_bg": "#F2F2F8", "footer_bg": "#F2F2F8",
        "search_bg": "#E8E8F2", "search_icon": "#6868A0", "pill_inactive_bg": "#E4E4F0",
        "pill_inactive_fg": "#9098A8", "pill_hover_bg": "#D4D4F0", "star_color": "#e8a820",
        "shadow": "#C0C0D0", "scrollbar_bg": "#E8E8F0", "scrollbar_thumb": "#C0C8D4",
        "char_counter": "#B0B0C8", "char_limit": "#f0465a", "glow_primary": "#7c5cfc",
        "glow_primary_dim": "#9880ff", "ambient_1": "#e8e0ff", "ambient_2": "#e0f0ff",
        "ambient_3": "#f0e0f0", "glass_border": "#D0D0E0", "glass_bg": "#E8E8F0",
        "timeline_line": "#D8D8E8", "mode_indicator": "#7c5cfc",
    },
}

COLORS = dict(THEMES["dark"])

FONT_FAMILY = "Microsoft YaHei"
FONT_MONO = "Consolas"

# ============ Win32 虚拟键码映射 ============
VK_MAP = {
    "ctrl": 0x11, "control": 0x11, "alt": 0x12, "shift": 0x10,
    "win": 0x5B, "windows": 0x5B, "super": 0x5B,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "escape": 0x1B, "esc": 0x1B, "tab": 0x09, "space": 0x20,
    "enter": 0x0D, "backspace": 0x08, "delete": 0x2E, "insert": 0x2D,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}
MOD_KEYS = {"ctrl", "control", "alt", "shift", "win", "windows", "super"}