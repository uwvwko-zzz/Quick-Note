"""
UI Mixin — 笔记卡片列表渲染与交互
"""
import tkinter as tk

from config import COLORS, TAGS, FONT_FAMILY, FONT_MONO, WINDOW_WIDTH
from utils import format_relative_time


class CardsMixin:
    """笔记卡片的创建、悬停、选择、刷新"""

    @staticmethod
    def _blend_color(hex_color, alpha=0.15):
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            bg_hex = COLORS.get("surface", "#151519")
            br = int(bg_hex[1:3], 16)
            bg_ = int(bg_hex[3:5], 16)
            bb = int(bg_hex[5:7], 16)
            nr = int(r * alpha + br * (1 - alpha))
            ng = int(g * alpha + bg_ * (1 - alpha))
            nb = int(b * alpha + bb * (1 - alpha))
            return f"#{nr:02x}{ng:02x}{nb:02x}"
        except Exception:
            return COLORS.get("primary_bg", "#2A1E50")

    def _get_card_bg_colors(self):
        return (COLORS["surface"], COLORS["card_hover"], COLORS["card_selected"],
                COLORS["card_starred"], COLORS["surface_light"], COLORS["card_bg"])

    def _invalidate_cache(self):
        self._notes_cache = None

    def _get_notes(self):
        if self._notes_cache is None:
            self._notes_cache = self._load_notes()
        return self._notes_cache

    def _refresh_cards(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        try:
            self.input_window.update_idletasks()
            cw = self._cards_canvas.winfo_width()
            if cw <= 1:
                cw = WINDOW_WIDTH - 30
            self._cards_canvas.itemconfig(self._cards_window, width=cw)
            self._cards_inner.configure(width=cw)
            if not hasattr(self, '_width_debugged'):
                self._width_debugged = True
                self._log(f"DEBUG canvas_w={cw} inner_w={self._cards_inner.winfo_width()}")
        except tk.TclError:
            pass
        for w in self._cards_inner.winfo_children():
            w.destroy()
        self._card_widgets = {}
        self._card_hover_data = {}
        self._cards_inner.columnconfigure(0, weight=1)

        notes = self._get_notes()
        keyword = self._search_var.get().strip().lower() if hasattr(self, '_search_var') else ""
        filtered = []
        for n in notes:
            if self._filter_tag != "全部" and n.get("tag", "默认") != self._filter_tag:
                continue
            if keyword:
                searchable = f"{n['content']} {n['time']} {n.get('tag','默认')}".lower()
                if keyword not in searchable:
                    continue
            filtered.append(n)
        # 排序: 置顶 → 收藏 → 手动 order (降序)
        filtered.sort(key=lambda n: (
            n.get("pinned", False),    # True > False → 置顶在前
            n.get("starred", False),   # True > False → 收藏在前
            n.get("order", 0) or 0,    # 大 → 前
        ), reverse=True)

        total, shown = len(notes), len(filtered)
        self._cards_canvas.itemconfig(self._empty_window, state="normal" if shown == 0 else "hidden")
        for idx, note in enumerate(filtered):
            self._create_card(note, idx)

        if keyword or self._filter_tag != "全部":
            self.count_label.config(text=f"🔍 {shown}/{total}")
        else:
            starred = sum(1 for n in notes if n.get("starred"))
            self.count_label.config(text=f"共 {total} 条" + (f" · ⭐{starred}" if starred else ""))

    def _create_card(self, note, index=0):
        note_id = note["id"]
        is_selected = self._selected_card_id == note_id
        is_starred = note.get("starred", False)
        tag_name = note.get("tag", "默认")
        tag_info = TAGS.get(tag_name, TAGS["默认"])
        tag_color = tag_info["color"]
        tag_icon = tag_info["icon"]

        if is_selected:
            card_bg = COLORS["card_selected"]
        elif is_starred:
            card_bg = COLORS["card_starred"]
        else:
            card_bg = COLORS["surface"]

        card = tk.Frame(self._cards_inner, bg=card_bg, cursor="hand2",
                         highlightbackground=COLORS["glass_border"], highlightthickness=1,
                         padx=0, pady=0)
        card.grid(row=index, column=0, sticky="ew", padx=4, pady=(0, 1))
        if is_selected:
            card.configure(highlightbackground=COLORS["primary"])

        accent_canvas = tk.Frame(card, width=3, bg=tag_color, highlightthickness=0, height=28)
        accent_canvas.pack(side=tk.LEFT, fill=tk.Y)
        accent_canvas.pack_propagate(False)
        accent_canvas.pack_propagate(False)

        content_area = tk.Frame(card, bg=card_bg, padx=8, pady=2)
        content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = card

        tag_lbl = tk.Label(content_area, text=tag_icon, font=(FONT_FAMILY, 9),
                           fg=tag_color, bg=card_bg, width=2)
        tag_lbl.pack(side=tk.LEFT, padx=(0, 4))

        more = tk.Label(content_area, text="⋯", font=(FONT_FAMILY, 9), fg=COLORS["text_dim"],
                         bg=card_bg, cursor="hand2")
        more.pack(side=tk.RIGHT, padx=(2, 0))
        more.bind("<ButtonPress-1>", lambda e, nid=note_id: self._show_context_menu(e, nid))

        time_lbl = tk.Label(content_area, text=f"{format_relative_time(note['time'])} #{note_id}",
                            font=(FONT_FAMILY, 7), fg=COLORS["text_dim"], bg=card_bg)
        time_lbl.pack(side=tk.RIGHT, padx=(0, 2))

        is_pinned = note.get("pinned", False)
        pin_lbl = None
        if is_pinned:
            pin_lbl = tk.Label(content_area, text="📌", font=(FONT_FAMILY, 8),
                                fg=COLORS["primary"], bg=card_bg)
            pin_lbl.pack(side=tk.RIGHT, padx=(2, 0))

        star_lbl = None
        if is_starred:
            star_lbl = tk.Label(content_area, text="⭐", font=(FONT_FAMILY, 8),
                                 fg=COLORS["star_color"], bg=card_bg)
            star_lbl.pack(side=tk.RIGHT, padx=(2, 0))

        content_text = note["content"].replace("\n", " ↵ ")
        display_text = content_text[:60] + ("…" if len(content_text) > 60 else "")
        content_lbl = tk.Label(content_area, text=display_text, font=(FONT_FAMILY, 9),
                                fg=COLORS["text"], bg=card_bg, anchor="w")
        content_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        badge = content_area
        badge_bg = card_bg
        r1 = content_area
        r3 = content_area

        all_w = [card, inner, content_area, content_lbl, accent_canvas, time_lbl, tag_lbl]
        if pin_lbl:
            all_w.append(pin_lbl)
        if star_lbl:
            all_w.append(star_lbl)

        def _on_card_mousewheel(event):
            self._cards_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        for w in all_w:
            w.bind("<ButtonPress-1>", lambda e, nid=note_id: self._on_card_click(nid))
            w.bind("<Double-ButtonPress-1>", lambda e, nid=note_id: self._show_edit_window(nid))
            w.bind("<ButtonPress-3>", lambda e, nid=note_id: self._show_context_menu(e, nid))
            w.bind("<MouseWheel>", _on_card_mousewheel)
            w.bind("<Button-4>", lambda e: self._cards_canvas.yview_scroll(-1, "units"))
            w.bind("<Button-5>", lambda e: self._cards_canvas.yview_scroll(1, "units"))

        hover_d = {
            "card": card, "inner": inner, "content_area": content_area,
            "accent": accent_canvas, "all_w": all_w, "more": more,
            "badge": badge, "star_lbl": star_lbl,
            "is_sel": is_selected, "is_star": is_starred,
            "tag_color": tag_color, "badge_bg": badge_bg,
            "r1": r1, "r3": r3,
        }
        for w in all_w:
            w.bind("<Enter>", lambda e, d=hover_d: self._card_enter(d))
            w.bind("<Leave>", lambda e, d=hover_d: self._card_leave(d))

        self._card_widgets[note_id] = card
        self._card_hover_data[note_id] = hover_d
        card.update_idletasks()
        if index == 0:
            self._log(f"DEBUG card #{note_id} h={card.winfo_height()} inner_h={content_area.winfo_height()}")

    def _card_enter(self, d):
        bg = COLORS["card_selected"] if d["is_sel"] else COLORS["card_hover"]
        badge_hover = self._blend_color(d["tag_color"], 0.25)
        card_bgs = self._get_card_bg_colors()
        try:
            d["card"].configure(bg=bg, highlightbackground=COLORS["primary"])
            d["inner"].configure(bg=bg)
            d["content_area"].configure(bg=bg)
            d["r1"].configure(bg=bg)
            d["r3"].configure(bg=bg)
            d["accent"].configure(bg=d["tag_color"])
            d["more"].configure(bg=bg)
            for w in d["all_w"]:
                try:
                    cls = w.winfo_class()
                    if cls in ("Label", "Frame"):
                        old = w.cget("bg")
                        if old in card_bgs or old == bg:
                            w.configure(bg=bg)
                        elif old == d["badge_bg"]:
                            w.configure(bg=badge_hover)
                except tk.TclError:
                    pass
            if d["badge"]:
                d["badge"].configure(bg=badge_hover)
        except tk.TclError:
            pass

    def _card_leave(self, d):
        bg = COLORS["card_selected"] if d["is_sel"] else (COLORS["card_starred"] if d["is_star"] else COLORS["surface"])
        card_bgs = self._get_card_bg_colors()
        try:
            if not d["is_sel"]:
                d["card"].configure(highlightbackground=COLORS["glass_border"])
            d["card"].configure(bg=bg)
            d["inner"].configure(bg=bg)
            d["content_area"].configure(bg=bg)
            d["r1"].configure(bg=bg)
            d["r3"].configure(bg=bg)
            d["more"].configure(bg=bg)
            for w in d["all_w"]:
                try:
                    cls = w.winfo_class()
                    if cls in ("Label", "Frame"):
                        old = w.cget("bg")
                        if old in card_bgs or old == bg:
                            w.configure(bg=bg)
                        elif old == self._blend_color(d["tag_color"], 0.25):
                            w.configure(bg=d["badge_bg"])
                except tk.TclError:
                    pass
            if d["badge"]:
                d["badge"].configure(bg=d["badge_bg"])
        except tk.TclError:
            pass

    def _on_card_click(self, note_id):
        self._selected_card_id = note_id
        card_bgs = self._get_card_bg_colors()
        for nid, cw in self._card_widgets.items():
            try:
                is_sel = nid == note_id
                bg = COLORS["card_selected"] if is_sel else COLORS["surface"]
                cw.configure(bg=bg, highlightbackground=COLORS["primary"] if is_sel else COLORS["glass_border"])

                d = self._card_hover_data.get(nid)
                if d:
                    d["inner"].configure(bg=bg)
                    d["content_area"].configure(bg=bg)
                    d["r1"].configure(bg=bg)
                    d["r3"].configure(bg=bg)
                    d["more"].configure(bg=bg)
                    for w in d["all_w"]:
                        try:
                            if w.winfo_class() in ("Label", "Frame"):
                                old = w.cget("bg")
                                if old in card_bgs:
                                    w.configure(bg=bg)
                        except tk.TclError:
                            pass
            except tk.TclError:
                pass