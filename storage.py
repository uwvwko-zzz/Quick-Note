"""
数据持久层 — 笔记 CRUD、配置读写
"""
import json
import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "notes.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
PLAN_FILE = os.path.join(DATA_DIR, "plan.json")


# ============ 配置 ============

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_current_theme():
    return load_config().get("theme", "dark")


def get_window_size():
    cfg = load_config()
    return cfg.get("window_width", 650), cfg.get("window_height", 740)


def set_window_size(width, height):
    cfg = load_config()
    cfg["window_width"] = width
    cfg["window_height"] = height
    save_config(cfg)


def set_current_theme(theme_name):
    cfg = load_config()
    cfg["theme"] = theme_name
    save_config(cfg)


def get_float_ball_pos():
    """获取浮动球位置，返回 (x, y) 或 None"""
    cfg = load_config()
    pos = cfg.get("float_ball_pos")
    if pos and isinstance(pos, (list, tuple)) and len(pos) == 2:
        return tuple(pos)
    return None


def set_float_ball_pos(x, y):
    """保存浮动球位置"""
    cfg = load_config()
    cfg["float_ball_pos"] = [x, y]
    save_config(cfg)


def get_float_ball_enabled():
    """获取浮动球是否启用"""
    return load_config().get("float_ball_enabled", True)


def set_float_ball_enabled(enabled):
    """设置浮动球是否启用"""
    cfg = load_config()
    cfg["float_ball_enabled"] = enabled
    save_config(cfg)


# ============ 笔记 CRUD ============

def load_notes():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_notes(notes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


def add_note(content, tag="默认"):
    notes = load_notes()
    max_order = max((n.get("order", 0) for n in notes), default=0)
    note = {
        "id": (max((n["id"] for n in notes), default=0) + 1) if notes else 1,
        "content": content.strip(),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tag": tag,
        "starred": False,
        "order": max_order + 1,
    }
    notes.append(note)
    save_notes(notes)
    return note


def delete_note(note_id):
    notes = load_notes()
    notes = [n for n in notes if n["id"] != note_id]
    save_notes(notes)


def toggle_pin(note_id):
    """切换笔记置顶状态"""
    notes = load_notes()
    for n in notes:
        if n["id"] == note_id:
            n["pinned"] = not n.get("pinned", False)
            save_notes(notes)
            return n["pinned"]
    return False


def update_note(note_id, new_content=None, tag=None, starred=None, done=None, remind_time=None):
    notes = load_notes()
    for n in notes:
        if n["id"] == note_id:
            if new_content is not None:
                n["content"] = new_content.strip()
                n["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if tag is not None:
                n["tag"] = tag
            if starred is not None:
                n["starred"] = starred
            if done is not None:
                n["done"] = done
            if remind_time is not None:
                n["remind_time"] = remind_time
            break
    save_notes(notes)


# ============ 今日计划 (plan.json) ============

def load_plans():
    """加载所有计划数据"""
    if not os.path.exists(PLAN_FILE):
        return []
    try:
        with open(PLAN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_plans(plans):
    """保存所有计划数据"""
    with open(PLAN_FILE, "w", encoding="utf-8") as f:
        json.dump(plans, f, ensure_ascii=False, indent=2)


def add_plan(content, tag="待办", remind_time=None):
    """添加一条计划"""
    plans = load_plans()
    plan = {
        "id": (max((p["id"] for p in plans), default=0) + 1) if plans else 1,
        "content": content.strip(),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tag": tag,
        "done": False,
        "remind_time": remind_time,
        "reminded": False,
    }
    plans.append(plan)
    save_plans(plans)
    return plan


def update_plan(plan_id, content=None, tag=None, done=None, remind_time=None, reminded=None):
    """更新计划"""
    plans = load_plans()
    for p in plans:
        if p["id"] == plan_id:
            if content is not None:
                p["content"] = content.strip()
            if tag is not None:
                p["tag"] = tag
            if done is not None:
                p["done"] = done
            if remind_time is not None:
                p["remind_time"] = remind_time
            if reminded is not None:
                p["reminded"] = reminded
            break
    save_plans(plans)


def delete_plan(plan_id):
    """删除计划"""
    plans = load_plans()
    plans = [p for p in plans if p["id"] != plan_id]
    save_plans(plans)


def get_today_plan():
    """获取今天的计划"""
    plans = load_plans()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    plan = []
    for p in plans:
        # 今日的计划（按 time 字段判断）
        if p.get("time", "").startswith(today):
            plan.append(p)
            continue
        # 有 remind_time 且是今天的（跨天未完成的也纳入）
        rt = p.get("remind_time", "")
        if rt and rt.startswith(today) and not p.get("done"):
            plan.append(p)
    # 按 remind_time 排序：有时间的在前
    plan.sort(key=lambda p: p.get("remind_time") or "99:99")
    return plan


def get_due_reminders():
    """获取已到提醒时间但未提醒的计划"""
    plans = load_plans()
    now = datetime.datetime.now()
    due = []
    for p in plans:
        rt = p.get("remind_time", "")
        if not rt or p.get("done") or p.get("reminded"):
            continue
        try:
            remind_dt = datetime.datetime.strptime(rt, "%Y-%m-%d %H:%M")
            if remind_dt <= now:
                due.append(p)
        except ValueError:
            pass
    return due
