"""
UI Mixin — 笔记编辑窗口与右键菜单
"""
import tkinter as tk

from .config import COLORS, TAGS, TAG_LIST, FONT_FAMILY, FONT_MONO
from .utils import format_relative_time


class EditMixin:
    """笔记编辑、右键菜单、收藏、复制、标签修改"""

    def _show_edit_window(self, note_id):
        notes = self._load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if not note:
            return
        ew = tk.Toplevel(self.input_window)
        ew.title("")
        ew.geometry("480x320")
        ew.configure(bg=COLORS["bg"])
        ew.attributes("-topmost", True)
        ew.update_idletasks()
        ew.geometry(f"+{(ew.winfo_screenwidth()-480)//2}+{(ew.winfo_screenheight()-320)//2}")

        eh = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=10)
        eh.pack(fill=tk.X)
        tk.Label(eh, text=f"✏️ #{note_id}", font=(FONT_FAMILY, 11, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Label(eh, text=format_relative_time(note["time"]), font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        tag_row = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=4)
        tag_row.pack(fill=tk.X)
        edit_tag_var = tk.StringVar(value=note.get("tag", "默认"))
        edit_tag_widgets = {}

        def sel_tag(t):
            edit_tag_var.set(t)
            for tn, lbl in edit_tag_widgets.items():
                sel = tn == t
                lbl.configure(fg=TAGS[tn]["color"] if sel else COLORS["pill_inactive_fg"],
                               bg=COLORS["primary_bg"] if sel else COLORS["pill_inactive_bg"],
                               font=(FONT_FAMILY, 8, "bold" if sel else "normal"))

        for tn in TAG_LIST:
            sel = tn == edit_tag_var.get()
            lbl = tk.Label(tag_row, text=tn, font=(FONT_FAMILY, 8, "bold" if sel else "normal"),
                           fg=TAGS[tn]["color"] if sel else COLORS["pill_inactive_fg"],
                           bg=COLORS["primary_bg"] if sel else COLORS["pill_inactive_bg"],
                           padx=8, pady=2, cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=2)
            lbl.bind("<ButtonPress-1>", lambda e, t=tn: sel_tag(t))
            edit_tag_widgets[tn] = lbl

        body_f = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=8)
        body_f.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(body_f, font=(FONT_MONO, 11), wrap=tk.WORD, bg=COLORS["input_bg"], fg=COLORS["text"],
                      insertbackground=COLORS["primary"], selectbackground=COLORS["primary"],
                      selectforeground=COLORS["text"], relief=tk.FLAT, borderwidth=0,
                      highlightthickness=2, highlightcolor=COLORS["border_focus"],
                      highlightbackground=COLORS["border"], padx=12, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", note["content"])
        txt.focus_set()

        bf = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=8)
        bf.pack(fill=tk.X)

        def do_save(e=None):
            c = txt.get("1.0", tk.END).strip()
            if c:
                self._update_note(note_id, c, tag=edit_tag_var.get())
                self._invalidate_cache()
                self._refresh_cards()
                self._flash_status(f"✓ #{note_id}", COLORS["success"])
            ew.destroy()
            return "break"

        tk.Label(bf, text="↵ 保存 · Esc 取消", font=(FONT_MONO, 7), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        cancel_lbl = tk.Label(bf, text="取消", font=(FONT_FAMILY, 9), fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2", padx=12, pady=4)
        cancel_lbl.pack(side=tk.RIGHT)
        cancel_lbl.bind("<ButtonPress-1>", lambda e: ew.destroy())
        cancel_lbl.bind("<Enter>", lambda e: cancel_lbl.configure(fg=COLORS["danger"]))
        cancel_lbl.bind("<Leave>", lambda e: cancel_lbl.configure(fg=COLORS["text_dim"]))
        save_lbl = tk.Label(bf, text="保存", font=(FONT_FAMILY, 9, "bold"), fg=COLORS["primary"],
                             bg=COLORS["primary_bg"], cursor="hand2", padx=16, pady=4)
        save_lbl.pack(side=tk.RIGHT, padx=(0, 8))
        save_lbl.bind("<ButtonPress-1>", lambda e: do_save())
        save_lbl.bind("<Enter>", lambda e: save_lbl.configure(bg=COLORS["primary_hover"]))
        save_lbl.bind("<Leave>", lambda e: save_lbl.configure(bg=COLORS["primary_bg"]))
        txt.bind("<Control-Return>", do_save)
        txt.bind("<Escape>", lambda e: ew.destroy())
        ew.bind("<Escape>", lambda e: ew.destroy())

    def _show_context_menu(self, event, note_id):
        notes = self._load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if not note:
            return
        menu = tk.Menu(self.input_window, tearoff=0, bg=COLORS["surface"], fg=COLORS["text"],
                       activebackground=COLORS["primary"], activeforeground="#ffffff",
                       font=(FONT_FAMILY, 9), relief=tk.FLAT, bd=0)
        menu.add_command(label="💔 取消收藏" if note.get("starred") else "⭐ 收藏",
                         command=lambda: self._toggle_star(note_id))
        menu.add_command(label="✏️ 编辑", command=lambda: self._show_edit_window(note_id))
        menu.add_command(label="📋 复制", command=lambda: self._copy_content(note_id))
        menu.add_separator()
        tag_menu = tk.Menu(menu, tearoff=0, bg=COLORS["surface"], fg=COLORS["text"],
                           activebackground=COLORS["primary"], activeforeground="#ffffff", font=(FONT_FAMILY, 9))
        for tn in TAG_LIST:
            cur = " ✓" if note.get("tag", "默认") == tn else ""
            tag_menu.add_command(label=f"{TAGS[tn]['icon']} {tn}{cur}",
                                 command=lambda t=tn: self._change_tag(note_id, t))
        menu.add_cascade(label="🏷️ 标签", menu=tag_menu)
        menu.add_command(label="📌 置顶" if not note.get("pinned") else "📌 取消置顶",
                         command=lambda: self._toggle_pin(note_id))
        menu.add_separator()
        menu.add_command(label="🗑️ 删除", command=lambda: self._delete_note(note_id))
        menu.tk_popup(event.x_root, event.y_root)

    def _delete_note(self, note_id):
        self._delete_note_storage(note_id)
        self._invalidate_cache()
        self._log(f"🗑️ #{note_id}")
        self._refresh_cards()
        self._flash_status("✓ 已删除", COLORS["danger"])

    def _toggle_star(self, note_id):
        notes = self._load_notes()
        for n in notes:
            if n["id"] == note_id:
                n["starred"] = not n.get("starred", False)
                break
        self._save_notes(notes)
        self._invalidate_cache()
        self._refresh_cards()

    def _copy_content(self, note_id):
        notes = self._load_notes()
        note = next((n for n in notes if n["id"] == note_id), None)
        if note:
            self.input_window.clipboard_clear()
            self.input_window.clipboard_append(note["content"])
            self._flash_status("✓ 已复制", COLORS["success"])

    def _change_tag(self, note_id, tag_name):
        self._update_note(note_id, tag=tag_name)
        self._invalidate_cache()
        self._refresh_cards()
        self._flash_status(f"✓ → {tag_name}", COLORS["success"])