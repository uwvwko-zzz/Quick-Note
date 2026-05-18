"""
数据持久层 — 笔记 CRUD、配置读写
"""
import json
import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "notes.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


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


def set_current_theme(theme_name):
    cfg = load_config()
    cfg["theme"] = theme_name
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
    note = {
        "id": (max((n["id"] for n in notes), default=0) + 1) if notes else 1,
        "content": content.strip(),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tag": tag,
        "starred": False,
    }
    notes.append(note)
    save_notes(notes)
    return note


def delete_note(note_id):
    notes = load_notes()
    notes = [n for n in notes if n["id"] != note_id]
    save_notes(notes)


def update_note(note_id, new_content=None, tag=None, starred=None):
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
            break
    save_notes(notes)