"""
工具函数 — Canvas 绘制、热键解析、自然语言标签、时间格式化
"""
import tkinter as tk
from .config import COLORS, TAG_LIST, VK_MAP, MOD_KEYS


def rounded_rect(canvas, x1, y1, x2, y2, radius=8, **kwargs):
    """在 Canvas 上绘制圆角矩形"""
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def parse_hotkey(hotkey_str):
    """将 'ctrl+alt+e' 解析为 ([mod_vk_codes], main_vk_code)"""
    parts = hotkey_str.lower().replace(" ", "").split("+")
    mods, main_key = [], 0
    for p in parts:
        if p in MOD_KEYS:
            vk = VK_MAP.get(p, 0)
            if vk:
                mods.append(vk)
        elif len(p) == 1:
            main_key = ord(p.upper())
        elif p in VK_MAP:
            main_key = VK_MAP[p]
    return mods, main_key


def parse_natural_tags(text):
    """从文本中解析 #标签 自然语言标签，返回 (tag_name, clean_text)"""
    found_tag = "默认"
    clean_text = text
    for tag_name in TAG_LIST:
        for pat in [f"#{tag_name}", f"#{tag_name.lower()}"]:
            if pat in text:
                found_tag = tag_name
                clean_text = text.replace(pat, "").strip()
                while "  " in clean_text:
                    clean_text = clean_text.replace("  ", " ")
                return found_tag, clean_text.strip()
    return found_tag, text.strip()


def format_relative_time(time_str):
    """将 '2024-01-01 12:00:00' 格式化为相对时间"""
    import datetime
    try:
        dt = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.datetime.now()
        diff = now - dt
        if diff.days == 0:
            if diff.seconds < 60:
                return "刚刚"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}分钟前"
            else:
                return f"今天 {dt.strftime('%H:%M')}"
        elif diff.days == 1:
            return f"昨天 {dt.strftime('%H:%M')}"
        elif diff.days < 7:
            return f"{diff.days}天前"
        elif diff.days < 365:
            return dt.strftime("%m月%d日")
        else:
            return dt.strftime("%Y年%m月%d日")
    except Exception:
        return time_str


def apply_theme(theme_name):
    """应用指定主题到全局 COLORS"""
    from .config import COLORS as _COLORS, THEMES
    if theme_name in THEMES:
        _COLORS.clear()
        _COLORS.update(THEMES[theme_name])


def check_for_update(current_version, callback):
    """在后台线程检查 GitHub 最新版本号，24小时内只请求一次 API"""
    import urllib.request
    import json
    import os
    import time

    def _worker():
        # 本地缓存文件路径
        cache_dir = os.path.join(os.path.expanduser("~"), ".quicknote")
        cache_file = os.path.join(cache_dir, "update_cache.json")
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception:
            pass

        # 读取缓存
        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                ts = cache.get("timestamp", 0)
                if time.time() - ts < 86400:  # 24小时内使用缓存
                    if cache.get("rate_limited"):
                        callback(None, "API 限流，请稍后再试")
                        return
                    latest = cache.get("latest", "")
                    if latest:
                        has_update = _compare_versions(latest, current_version)
                        callback(latest, has_update)
                        return
        except Exception:
            pass

        try:
            # 不用 GitHub API（有 60次/小时 限制）
            # 直接用 http.client 发 HEAD 请求到 releases/latest
            # GitHub 会返回 302 重定向，Location 头包含版本号
            import http.client
            import re
            conn = http.client.HTTPSConnection("github.com", timeout=10)
            conn.request("HEAD", "/uwvwko-zzz/Quick-Note/releases/latest",
                         headers={"User-Agent": "QuickNote"})
            resp = conn.getresponse()
            conn.close()

            if resp.status == 302:
                location = resp.getheader("Location", "")
                m = re.search(r'/tag/v?([\d.]+)', location)
                if m:
                    latest = m.group(1)
                else:
                    callback(None, "无法解析版本号")
                    return
            elif resp.status == 404:
                callback(None, "暂无发布版本")
                return
            else:
                callback(None, f"HTTP {resp.status}")
                return

            # 写入缓存
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump({"timestamp": time.time(), "latest": latest}, f)
            except Exception:
                pass
            has_update = _compare_versions(latest, current_version)
            callback(latest, has_update)
        except Exception as e:
            callback(None, str(e))

    import threading
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def _compare_versions(remote, local):
    """比较版本号，remote > local 返回 True"""
    try:
        r_parts = [int(x) for x in remote.split(".")]
        l_parts = [int(x) for x in local.split(".")]
        for i in range(max(len(r_parts), len(l_parts))):
            r = r_parts[i] if i < len(r_parts) else 0
            l = l_parts[i] if i < len(l_parts) else 0
            if r > l:
                return True
            elif r < l:
                return False
        return False
    except Exception:
        return False
