"""
UI Mixin — 今日计划与提醒系统
"""
import datetime
import tkinter as tk

from .config import COLORS, TAG_LIST, FONT_FAMILY, FONT_MONO
from .utils import parse_natural_tags
from .storage import (
    add_plan, update_plan, delete_plan, get_today_plan
)


class PlanMixin:
    """今日计划窗口、提醒弹窗、计划编辑"""

    def _show_today_plan(self, existing_pw=None):
        if existing_pw and existing_pw.winfo_exists():
            pw = existing_pw
            for w in pw.winfo_children():
                w.destroy()
            pw.unbind("<Escape>")
        elif hasattr(self, '_plan_win') and self._plan_win and self._plan_win.winfo_exists():
            self._plan_win.lift()
            self._plan_win.focus_force()
            return
        else:
            parent = self.input_window if (self.input_window and self.input_window.winfo_exists()) else self.root
            pw = tk.Toplevel(parent)
            self._plan_win = pw
            pw.title("")
            pw.configure(bg=COLORS["bg"])
            pw.attributes("-topmost", True)
            pw.resizable(True, True)
            pw.update_idletasks()
            win_w, win_h = 480, 480
            pw.geometry(f"{win_w}x{win_h}")
            pw.geometry(f"+{(pw.winfo_screenwidth()-win_w)//2}+{(pw.winfo_screenheight()-win_h)//2}")

        plan = get_today_plan()
        today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
        done_count = sum(1 for n in plan if n.get("done"))
        total_count = len(plan)

        header = tk.Frame(pw, bg=COLORS["bg"], padx=20, pady=12)
        header.pack(fill=tk.X)
        tk.Label(header, text=f"📋 今日计划", font=(FONT_FAMILY, 14, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Label(header, text=f"{today_str}", font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        progress_f = tk.Frame(pw, bg=COLORS["bg"], padx=20, pady=4)
        progress_f.pack(fill=tk.X)
        if total_count > 0:
            pct = done_count / total_count
            tk.Label(progress_f, text=f"完成 {done_count}/{total_count}", font=(FONT_FAMILY, 8),
                     fg=COLORS["text_secondary"], bg=COLORS["bg"]).pack(anchor="w")
            bar_bg = tk.Canvas(progress_f, height=6, bg=COLORS["border"], highlightthickness=0, bd=0)
            bar_bg.pack(fill=tk.X, pady=(4, 0))
            pw.after(50, lambda: bar_bg.create_rectangle(0, 0, int(bar_bg.winfo_width() * pct), 6,
                                                          fill=COLORS["success"], outline=""))
        else:
            tk.Label(progress_f, text="今天还没有计划，输入 !HH:MM 内容 创建提醒", font=(FONT_FAMILY, 8),
                     fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(anchor="w")

        tk.Frame(pw, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=20, pady=(8, 0))

        bf = tk.Frame(pw, bg=COLORS["bg"], padx=20, pady=6)
        bf.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Label(bf, text="如 !14:00 开会讨论 · !9:30 晨会 · Esc 关闭", font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        close_lbl = tk.Label(bf, text="关闭", font=(FONT_FAMILY, 9),
                              fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2", padx=12, pady=4)
        close_lbl.pack(side=tk.RIGHT)
        close_lbl.bind("<ButtonPress-1>", lambda e: pw.destroy())
        close_lbl.bind("<Enter>", lambda e: close_lbl.configure(fg=COLORS["danger"]))
        close_lbl.bind("<Leave>", lambda e: close_lbl.configure(fg=COLORS["text_dim"]))
        pw.bind("<Escape>", lambda e: pw.destroy())

        input_f = tk.Frame(pw, bg=COLORS["bg"], padx=20, pady=4)
        input_f.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(input_f, text="⏰", font=(FONT_FAMILY, 10),
                 fg=COLORS["primary"], bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 4))

        plan_var = tk.StringVar()
        plan_entry = tk.Entry(input_f, textvariable=plan_var, font=(FONT_MONO, 10),
                               bg=COLORS["input_bg"], fg=COLORS["text"],
                               insertbackground=COLORS["primary"],
                               selectbackground=COLORS["primary"],
                               relief=tk.FLAT, borderwidth=0,
                               highlightthickness=2, highlightcolor=COLORS["border_focus"],
                               highlightbackground=COLORS["border"])
        plan_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 6))
        plan_entry.insert(0, "!HH:MM 内容")
        plan_entry.configure(fg=COLORS["text_dim"])
        plan_placeholder = [True]

        def on_plan_focus_in(event):
            if plan_placeholder[0]:
                plan_entry.delete(0, tk.END)
                plan_entry.configure(fg=COLORS["text"])
                plan_placeholder[0] = False

        plan_entry.bind("<FocusIn>", on_plan_focus_in)

        def on_plan_submit(event):
            text = plan_var.get().strip()
            if plan_placeholder[0] or not text:
                return "break"
            remind_time = None
            clean_text = text
            if text.startswith("!"):
                import re
                m = re.match(r'^!(\d{1,2}):(\d{2})\s+', text)
                if m:
                    h, mi = int(m.group(1)), int(m.group(2))
                    if 0 <= h <= 23 and 0 <= mi <= 59:
                        today = datetime.datetime.now().strftime("%Y-%m-%d")
                        remind_time = f"{today} {h:02d}:{mi:02d}"
                        clean_text = text[m.end():].strip()
            tag, clean = parse_natural_tags(clean_text)
            if not clean:
                return "break"
            add_plan(clean, tag=tag, remind_time=remind_time)
            self._log(f"⏰ [{tag}] {clean[:30]}")
            self._show_today_plan(existing_pw=pw)
            return "break"

        plan_entry.bind("<Return>", on_plan_submit)

        hint_lbl = tk.Label(input_f, text="↵", font=(FONT_MONO, 12),
                             fg=COLORS["text_dim"], bg=COLORS["bg"])
        hint_lbl.pack(side=tk.LEFT)

        list_f = tk.Frame(pw, bg=COLORS["bg"], padx=20, pady=8)
        list_f.pack(fill=tk.BOTH, expand=True)

        list_canvas = tk.Canvas(list_f, bg=COLORS["bg"], highlightthickness=0, bd=0)
        list_sb = tk.Scrollbar(list_f, orient=tk.VERTICAL, command=list_canvas.yview,
                                bg=COLORS["scrollbar_thumb"], troughcolor=COLORS["scrollbar_bg"], width=5)
        list_canvas.configure(yscrollcommand=list_sb.set)
        list_sb.pack(side=tk.RIGHT, fill=tk.Y)
        list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(list_canvas, bg=COLORS["bg"])
        list_canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
        list_canvas.bind("<Configure>", lambda e: list_canvas.itemconfig(1, width=e.width))

        if not plan:
            tk.Label(inner, text="暂无计划 🎉", font=(FONT_FAMILY, 11),
                     fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(pady=30)
        else:
            for note in plan:
                is_done = note.get("done")
                rt = note.get("remind_time", "")
                time_str = rt[-5:] if rt else ""
                item_f = tk.Frame(inner, bg=COLORS["bg"])
                item_f.pack(fill=tk.X, pady=2)

                chk_text = "☑" if is_done else "☐"
                chk_fg = COLORS["success"] if is_done else COLORS["text_dim"]
                chk = tk.Label(item_f, text=chk_text, font=(FONT_FAMILY, 12),
                               fg=chk_fg, bg=COLORS["bg"], cursor="hand2")
                chk.pack(side=tk.LEFT, padx=(0, 8))

                def toggle_done(pid=note["id"], done=is_done):
                    update_plan(pid, done=not done)
                    self._show_today_plan(existing_pw=pw)

                chk.bind("<ButtonPress-1>", lambda e, f=toggle_done: f())

                if time_str:
                    tk.Label(item_f, text=f"⏰ {time_str}", font=(FONT_FAMILY, 8),
                             fg=COLORS["warning"] if not is_done else COLORS["text_dim"],
                             bg=COLORS["bg"]).pack(side=tk.LEFT, padx=(0, 8))

                content_fg = COLORS["text_dim"] if is_done else COLORS["text"]
                content_text = note["content"][:50] + ("..." if len(note["content"]) > 50 else "")
                content_lbl = tk.Label(item_f, text=content_text, font=(FONT_FAMILY, 9),
                         fg=content_fg, bg=COLORS["bg"], anchor="w", cursor="hand2")
                content_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

                def do_delete_plan(pid=note["id"]):
                    delete_plan(pid)
                    self._log(f"🗑️ 计划 #{pid} 已删除")
                    self._show_today_plan(existing_pw=pw)

                def do_edit_plan(pid=note["id"], old_content=note["content"], old_tag=note.get("tag", "待办")):
                    self._show_plan_edit_window(pid, old_content, old_tag, pw)

                more_lbl = tk.Label(item_f, text="⋯", font=(FONT_FAMILY, 11),
                                     fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2")
                more_lbl.pack(side=tk.RIGHT, padx=(4, 0))

                def show_plan_menu(e, pid=note["id"], oc=note["content"], ot=note.get("tag", "待办")):
                    menu = tk.Menu(pw, tearoff=0, bg=COLORS["surface"], fg=COLORS["text"],
                                   activebackground=COLORS["primary"], activeforeground="#ffffff",
                                   font=(FONT_FAMILY, 9), relief=tk.FLAT, bd=0)
                    menu.add_command(label="✏️ 编辑", command=lambda: do_edit_plan(pid, oc, ot))
                    menu.add_command(label="🗑️ 删除", command=lambda: do_delete_plan(pid))
                    menu.tk_popup(e.x_root, e.y_root)

                more_lbl.bind("<ButtonPress-1>", show_plan_menu)
                content_lbl.bind("<Double-ButtonPress-1>", lambda e, pid=note["id"], oc=note["content"], ot=note.get("tag","待办"): do_edit_plan(pid, oc, ot))
                item_f.bind("<ButtonPress-3>", show_plan_menu)

    def _show_plan_edit_window(self, plan_id, old_content, old_tag, parent_window):
        ew = tk.Toplevel(parent_window)
        ew.title("")
        ew.geometry("440x280")
        ew.configure(bg=COLORS["bg"])
        ew.attributes("-topmost", True)
        ew.resizable(False, False)
        ew.update_idletasks()
        ew.geometry(f"+{(ew.winfo_screenwidth()-440)//2}+{(ew.winfo_screenheight()-280)//2}")

        eh = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=10)
        eh.pack(fill=tk.X)
        tk.Label(eh, text="✏️ 编辑计划", font=(FONT_FAMILY, 12, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        body_f = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=8)
        body_f.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(body_f, font=(FONT_MONO, 11), wrap=tk.WORD, bg=COLORS["input_bg"], fg=COLORS["text"],
                      insertbackground=COLORS["primary"], selectbackground=COLORS["primary"],
                      selectforeground=COLORS["text"], relief=tk.FLAT, borderwidth=0,
                      highlightthickness=2, highlightcolor=COLORS["border_focus"],
                      highlightbackground=COLORS["border"], padx=12, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", old_content)
        txt.focus_set()

        bf = tk.Frame(ew, bg=COLORS["bg"], padx=20, pady=8)
        bf.pack(fill=tk.X)

        def do_save():
            c = txt.get("1.0", tk.END).strip()
            if c:
                update_plan(plan_id, content=c)
                self._log(f"✏️ 计划 #{plan_id} 已更新")
            ew.destroy()
            parent_window.destroy()
            self._show_today_plan()

        def do_delete():
            delete_plan(plan_id)
            self._log(f"🗑️ 计划 #{plan_id} 已删除")
            ew.destroy()
            parent_window.destroy()
            self._show_today_plan()

        tk.Label(bf, text="Esc 取消", font=(FONT_FAMILY, 7), fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        del_lbl = tk.Label(bf, text="🗑️ 删除", font=(FONT_FAMILY, 9),
                            fg=COLORS["danger"], bg=COLORS["bg"], cursor="hand2", padx=12, pady=4)
        del_lbl.pack(side=tk.RIGHT)
        del_lbl.bind("<ButtonPress-1>", lambda e: do_delete())
        del_lbl.bind("<Enter>", lambda e: del_lbl.configure(bg=COLORS["surface_hover"]))
        del_lbl.bind("<Leave>", lambda e: del_lbl.configure(bg=COLORS["bg"]))

        cancel_lbl = tk.Label(bf, text="取消", font=(FONT_FAMILY, 9),
                               fg=COLORS["text_dim"], bg=COLORS["bg"], cursor="hand2", padx=12, pady=4)
        cancel_lbl.pack(side=tk.RIGHT, padx=(0, 6))
        cancel_lbl.bind("<ButtonPress-1>", lambda e: ew.destroy())
        cancel_lbl.bind("<Enter>", lambda e: cancel_lbl.configure(fg=COLORS["danger"]))
        cancel_lbl.bind("<Leave>", lambda e: cancel_lbl.configure(fg=COLORS["text_dim"]))

        save_lbl = tk.Label(bf, text="保存", font=(FONT_FAMILY, 9, "bold"),
                             fg="#ffffff", bg=COLORS["primary"], cursor="hand2", padx=16, pady=4)
        save_lbl.pack(side=tk.RIGHT, padx=(0, 8))
        save_lbl.bind("<ButtonPress-1>", lambda e: do_save())
        save_lbl.bind("<Enter>", lambda e: save_lbl.configure(bg=COLORS["primary_hover"]))
        save_lbl.bind("<Leave>", lambda e: save_lbl.configure(bg=COLORS["primary"]))

        txt.bind("<Control-Return>", lambda e: do_save())
        txt.bind("<Escape>", lambda e: ew.destroy())
        ew.bind("<Escape>", lambda e: ew.destroy())

    # ============ 提醒系统 ============

    def _start_reminder_check(self):
        self._check_reminders()

    def _check_reminders(self):
        if not self.root:
            return
        from .storage import get_due_reminders
        due = get_due_reminders()
        for plan in due:
            self._show_reminder_popup(plan)
            update_plan(plan["id"], reminded=True)
        self.root.after(30000, self._check_reminders)

    def _show_reminder_popup(self, plan):
        rw = tk.Toplevel(self.root)
        rw.title("⏰ 提醒")
        rw.configure(bg=COLORS["bg"])
        rw.attributes("-topmost", True)
        rw.resizable(False, False)
        rw.overrideredirect(True)

        win_w, win_h = 360, 160
        rw.geometry(f"{win_w}x{win_h}")
        rw.update_idletasks()
        rw.geometry(f"+{(rw.winfo_screenwidth()-win_w)//2}+{(rw.winfo_screenheight()-win_h)//2}")

        container = tk.Frame(rw, bg=COLORS["surface"], padx=24, pady=16,
                              highlightbackground=COLORS["primary"], highlightthickness=2)
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        tk.Label(container, text="⏰ 提醒时间到！", font=(FONT_FAMILY, 13, "bold"),
                 fg=COLORS["warning"], bg=COLORS["surface"]).pack(anchor="w")
        tk.Label(container, text=plan["content"][:80], font=(FONT_FAMILY, 10),
                 fg=COLORS["text"], bg=COLORS["surface"], wraplength=300, justify="left").pack(anchor="w", pady=(8, 0))

        btn_f = tk.Frame(container, bg=COLORS["surface"])
        btn_f.pack(fill=tk.X, pady=(12, 0))

        def do_done():
            update_plan(plan["id"], done=True)
            rw.destroy()

        def do_snooze():
            new_time = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
            update_plan(plan["id"], remind_time=new_time, reminded=False)
            rw.destroy()

        done_lbl = tk.Label(btn_f, text="✓ 完成", font=(FONT_FAMILY, 9, "bold"),
                             fg="#ffffff", bg=COLORS["success"], cursor="hand2", padx=14, pady=3)
        done_lbl.pack(side=tk.RIGHT, padx=(6, 0))
        done_lbl.bind("<ButtonPress-1>", lambda e: do_done())

        snooze_lbl = tk.Label(btn_f, text="稍后提醒", font=(FONT_FAMILY, 9),
                               fg=COLORS["text_secondary"], bg=COLORS["surface_hover"], cursor="hand2", padx=10, pady=3)
        snooze_lbl.pack(side=tk.RIGHT)
        snooze_lbl.bind("<ButtonPress-1>", lambda e: do_snooze())

        close_lbl = tk.Label(btn_f, text="关闭", font=(FONT_FAMILY, 9),
                              fg=COLORS["text_dim"], bg=COLORS["surface"], cursor="hand2", padx=10, pady=3)
        close_lbl.pack(side=tk.LEFT)
        close_lbl.bind("<ButtonPress-1>", lambda e: rw.destroy())

        rw.bind("<Escape>", lambda e: rw.destroy())

        try:
            import winsound
            winsound.Beep(800, 300)
        except Exception:
            pass