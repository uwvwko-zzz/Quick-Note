"""Markdown 预览 Mixin"""
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from .config import COLORS, FONT_FAMILY, FONT_MONO
from .utils import parse_natural_tags
from .storage import add_note


class MarkdownMixin:
    """Markdown 文件预览功能"""

    def _open_markdown_file(self):
        if not self.input_window or not self.input_window.winfo_exists():
            return
        path = filedialog.askopenfilename(
            title="打开 Markdown 文件",
            parent=self.input_window,
            filetypes=[("Markdown", "*.md"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self._log(f"❌ 打开文件失败: {e}")
            messagebox.showerror("打开失败", f"无法读取文件:\n{e}", parent=self.input_window)
            return
        self._log(f"📄 打开: {os.path.basename(path)}")
        self._show_markdown_preview(content, os.path.basename(path), path)

    def _md_insert_inline(self, txt, line, extra_tags=()):
        """Parse inline markdown and insert with formatting tags"""
        pos = 0
        while pos < len(line):
            # Inline code `code`
            m = re.match(r'`([^`]+)`', line[pos:])
            if m:
                txt.insert(tk.END, m.group(1), ("inline_code",) + extra_tags)
                pos += m.end()
                continue
            # Bold **text**
            m = re.match(r'\*\*(.+?)\*\*', line[pos:])
            if m:
                txt.insert(tk.END, m.group(1), ("bold",) + extra_tags)
                pos += m.end()
                continue
            # Italic *text*
            m = re.match(r'\*(.+?)\*', line[pos:])
            if m:
                txt.insert(tk.END, m.group(1), ("italic",) + extra_tags)
                pos += m.end()
                continue
            # Strikethrough ~~text~~
            m = re.match(r'~~(.+?)~~', line[pos:])
            if m:
                txt.insert(tk.END, m.group(1), ("strike",) + extra_tags)
                pos += m.end()
                continue
            # Image ![alt](url)
            m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line[pos:])
            if m:
                txt.insert(tk.END, f"🖼 {m.group(1) or m.group(2)}", ("img_tag",) + extra_tags)
                pos += m.end()
                continue
            # Link [text](url)
            m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', line[pos:])
            if m:
                txt.insert(tk.END, m.group(1), ("link_tag",) + extra_tags)
                pos += m.end()
                continue
            # Ordinary character
            txt.insert(tk.END, line[pos], extra_tags if extra_tags else ())
            pos += 1

    def _render_markdown(self, txt, md_text):
        """Full markdown renderer — writes directly into Text widget"""
        lines = md_text.split("\n")
        i = 0
        in_code_block = False
        code_lines = []
        table_rows = []

        def flush_table():
            if not table_rows:
                return
            parsed = []
            max_widths = {}
            for row_line in table_rows:
                cells = [c.strip() for c in row_line.strip().split("|")[1:-1]]
                parsed.append(cells)
                for ci, c in enumerate(cells):
                    max_widths[ci] = max(max_widths.get(ci, 0), len(c))
            if parsed:
                header_cells = parsed[0]
                parts = []
                for ci, c in enumerate(header_cells):
                    w = max_widths.get(ci, 0)
                    parts.append(c.ljust(w))
                txt.insert(tk.END, "│ " + " │ ".join(parts) + " │\n", ("table_header",))
                sep_parts = ["─" * (max_widths.get(ci, 0) + 2) for ci in range(len(header_cells))]
                txt.insert(tk.END, "├" + "┼".join(sep_parts) + "┤\n", ("table_sep",))
            for ri, cells in enumerate(parsed[1:], 1):
                parts = []
                for ci, c in enumerate(cells):
                    w = max_widths.get(ci, 0)
                    parts.append(c.ljust(w))
                tag = ("table_row_alt",) if ri % 2 == 0 else ("table_cell",)
                txt.insert(tk.END, "│ " + " │ ".join(parts) + " │\n", tag)
            txt.insert(tk.END, "\n")
            table_rows.clear()

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Fenced code block
            if stripped.startswith("```"):
                if not in_code_block:
                    flush_table()
                    in_code_block = True
                    code_lines = []
                    lang = stripped[3:].strip()
                    if lang:
                        txt.insert(tk.END, f"  {lang}\n", ("code_lang",))
                    i += 1
                    continue
                else:
                    in_code_block = False
                    for ci, cl in enumerate(code_lines):
                        ln = f" {ci+1:>3} │ "
                        txt.insert(tk.END, ln, ("code_ln",))
                        txt.insert(tk.END, cl + "\n", ("code",))
                    txt.insert(tk.END, "\n")
                    code_lines = []
                    i += 1
                    continue
            if in_code_block:
                code_lines.append(line)
                i += 1
                continue

            # Table
            if "|" in stripped and stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if cells and all(re.match(r'^[-:]+$', c) for c in cells):
                    i += 1
                    continue
                table_rows.append(line)
                i += 1
                continue
            else:
                flush_table()

            # Horizontal rule
            if re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', stripped):
                txt.insert(tk.END, "\n")
                txt.insert(tk.END, "─" * 50 + "\n", ("hr",))
                txt.insert(tk.END, "\n")
                i += 1
                continue

            # Empty line
            if not stripped:
                txt.insert(tk.END, "\n")
                i += 1
                continue

            # Heading
            hm = re.match(r'^(#{1,6})\s+(.*)', line)
            if hm:
                level = len(hm.group(1))
                tag = f"h{level}"
                if level <= 2:
                    txt.insert(tk.END, "\n")
                txt.insert(tk.END, hm.group(2).strip() + "\n", (tag,))
                if level == 1:
                    txt.insert(tk.END, "━" * 40 + "\n", ("h1_line",))
                elif level == 2:
                    txt.insert(tk.END, "─" * 30 + "\n", ("h2_line",))
                i += 1
                continue

            # Blockquote
            if stripped.startswith(">"):
                flush_table()
                quote_text = re.sub(r'^>\s*', '', line)
                quote_lines = [quote_text.strip()]
                while i + 1 < len(lines) and lines[i + 1].strip().startswith(">"):
                    i += 1
                    quote_lines.append(re.sub(r'^>\s*', '', lines[i]).strip())
                txt.insert(tk.END, "  ┃ ", ("quote_bar",))
                combined = " ".join(quote_lines)
                self._md_insert_inline(txt, combined, ("quote",))
                txt.insert(tk.END, "\n\n")
                i += 1
                continue

            # Task list
            tm = re.match(r'^(\s*)[-*+]\s+\[([ xX])\]\s+(.*)', line)
            if tm:
                indent = len(tm.group(1))
                checked = tm.group(2).lower() == "x"
                text_content = tm.group(3)
                prefix = "  " * (indent // 2)
                box = "☑ " if checked else "☐ "
                txt.insert(tk.END, prefix + box, ("task_check",) if checked else ("task_uncheck",))
                self._md_insert_inline(txt, text_content.strip(), ("task_text",))
                txt.insert(tk.END, "\n")
                i += 1
                continue

            # Unordered list
            lm = re.match(r'^(\s*)[-*+]\s+(.*)', line)
            if lm:
                indent = len(lm.group(1))
                depth = indent // 2
                markers = ["●", "◦", "▪", "▫"]
                marker = markers[min(depth, len(markers) - 1)]
                prefix = "    " * depth + f" {marker} "
                txt.insert(tk.END, prefix, ("list_marker",))
                self._md_insert_inline(txt, lm.group(2).strip(), ("list",))
                txt.insert(tk.END, "\n")
                i += 1
                continue

            # Ordered list
            om = re.match(r'^(\s*)(\d+)\.\s+(.*)', line)
            if om:
                indent = len(om.group(1))
                depth = indent // 2
                num = om.group(2)
                prefix = "    " * depth + f" {num}. "
                txt.insert(tk.END, prefix, ("list_marker",))
                self._md_insert_inline(txt, om.group(3).strip(), ("list",))
                txt.insert(tk.END, "\n")
                i += 1
                continue

            # Paragraph
            self._md_insert_inline(txt, stripped, ())
            txt.insert(tk.END, "\n")
            i += 1

        flush_table()

    def _show_markdown_preview(self, content, filename, filepath):
        mw = tk.Toplevel(self.input_window)
        mw.title("")
        mw.configure(bg=COLORS["bg"])
        mw.attributes("-topmost", True)
        mw.resizable(True, True)
        mw.update_idletasks()
        win_w, win_h = 760, 620
        mw.geometry(f"{win_w}x{win_h}")
        mw.geometry(f"+{(mw.winfo_screenwidth()-win_w)//2}+{(mw.winfo_screenheight()-win_h)//2}")

        header = tk.Frame(mw, bg=COLORS["bg"], padx=20, pady=12)
        header.pack(fill=tk.X)
        tk.Label(header, text="📄 Markdown 预览", font=(FONT_FAMILY, 14, "bold"),
                 fg=COLORS["heading_accent"], bg=COLORS["bg"]).pack(side=tk.LEFT)
        tk.Label(header, text=filename, font=(FONT_FAMILY, 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.RIGHT)

        tk.Frame(mw, bg=COLORS["border"], height=1).pack(fill=tk.X, padx=20)

        body_f = tk.Frame(mw, bg=COLORS["bg"], padx=20, pady=10)
        body_f.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(body_f, font=(FONT_FAMILY, 11), wrap=tk.WORD,
                      bg=COLORS["surface"], fg=COLORS["text"],
                      insertbackground=COLORS["primary"],
                      selectbackground=COLORS["primary"],
                      selectforeground=COLORS["text"],
                      relief=tk.FLAT, borderwidth=0,
                      highlightthickness=2, highlightcolor=COLORS["border_focus"],
                      highlightbackground=COLORS["border"],
                      padx=20, pady=16, spacing1=2, spacing3=4, tabs="40p")
        scrollbar = tk.Scrollbar(body_f, orient=tk.VERTICAL, command=txt.yview,
                                  bg=COLORS["scrollbar_thumb"], troughcolor=COLORS["scrollbar_bg"], width=5)
        txt.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Block-level tags
        txt.tag_configure("h1", font=(FONT_FAMILY, 22, "bold"), foreground=COLORS["heading_accent"],
                          spacing1=16, spacing3=4)
        txt.tag_configure("h1_line", font=(FONT_FAMILY, 9), foreground=COLORS["primary"],
                          spacing1=0, spacing3=8)
        txt.tag_configure("h2", font=(FONT_FAMILY, 18, "bold"), foreground=COLORS["heading_accent"],
                          spacing1=14, spacing3=2)
        txt.tag_configure("h2_line", font=(FONT_FAMILY, 9), foreground=COLORS["border_light"],
                          spacing1=0, spacing3=8)
        txt.tag_configure("h3", font=(FONT_FAMILY, 15, "bold"), foreground=COLORS["primary"],
                          spacing1=10, spacing3=4)
        txt.tag_configure("h4", font=(FONT_FAMILY, 13, "bold"), foreground=COLORS["primary"],
                          spacing1=8, spacing3=3)
        txt.tag_configure("h5", font=(FONT_FAMILY, 12, "bold"), foreground=COLORS["text_secondary"],
                          spacing1=6, spacing3=2)
        txt.tag_configure("h6", font=(FONT_FAMILY, 11, "bold"), foreground=COLORS["text_dim"],
                          spacing1=6, spacing3=2)
        txt.tag_configure("code", font=(FONT_MONO, 10), foreground=COLORS["success"],
                          background=COLORS["input_bg"],
                          lmargin1=40, lmargin2=40, spacing1=1, spacing3=1)
        txt.tag_configure("code_ln", font=(FONT_MONO, 8), foreground=COLORS["text_dim"],
                          background=COLORS["input_bg"],
                          lmargin1=16, lmargin2=16, spacing1=1, spacing3=1)
        txt.tag_configure("code_lang", font=(FONT_MONO, 9, "italic"), foreground=COLORS["text_dim"],
                          background=COLORS["input_bg"],
                          lmargin1=16, lmargin2=16, spacing1=6, spacing3=0)
        txt.tag_configure("quote", font=(FONT_FAMILY, 11, "italic"), foreground=COLORS["text_secondary"],
                          lmargin1=30, lmargin2=30, spacing1=2, spacing3=2)
        txt.tag_configure("quote_bar", font=(FONT_FAMILY, 11), foreground=COLORS["primary"],
                          background=COLORS["primary_bg"])
        txt.tag_configure("list", font=(FONT_FAMILY, 11), spacing1=1, spacing3=1)
        txt.tag_configure("list_marker", font=(FONT_FAMILY, 11), foreground=COLORS["primary"])
        txt.tag_configure("task_check", font=(FONT_FAMILY, 12), foreground=COLORS["success"])
        txt.tag_configure("task_uncheck", font=(FONT_FAMILY, 12), foreground=COLORS["text_dim"])
        txt.tag_configure("task_text", font=(FONT_FAMILY, 11), foreground=COLORS["text"])
        txt.tag_configure("table_header", font=(FONT_MONO, 10, "bold"), foreground=COLORS["heading_accent"],
                          spacing1=6, spacing3=2)
        txt.tag_configure("table_sep", font=(FONT_MONO, 10), foreground=COLORS["border"])
        txt.tag_configure("table_cell", font=(FONT_MONO, 10), foreground=COLORS["text_secondary"])
        txt.tag_configure("table_row_alt", font=(FONT_MONO, 10), foreground=COLORS["text_secondary"],
                          background=COLORS["input_bg"])
        txt.tag_configure("hr", font=(FONT_FAMILY, 9), foreground=COLORS["border"],
                          justify="center", spacing1=8, spacing3=8)

        # Inline tags
        txt.tag_configure("bold", font=(FONT_FAMILY, 11, "bold"))
        txt.tag_configure("italic", font=(FONT_FAMILY, 11, "italic"))
        txt.tag_configure("inline_code", font=(FONT_MONO, 10),
                          foreground=COLORS["success"], background=COLORS["input_bg"])
        txt.tag_configure("strike", font=(FONT_FAMILY, 11), overstrike=True, foreground=COLORS["text_dim"])
        txt.tag_configure("link_tag", font=(FONT_FAMILY, 11, "underline"), foreground=COLORS["primary"])
        txt.tag_configure("img_tag", font=(FONT_FAMILY, 11), foreground=COLORS["text_secondary"])

        # Render
        self._render_markdown(txt, content)
        txt.configure(state=tk.DISABLED)

        bf = tk.Frame(mw, bg=COLORS["bg"], padx=20, pady=10)
        bf.pack(fill=tk.X)
        line_count = len(content.split("\n"))
        char_count = len(content)
        tk.Label(bf, text=f"{line_count} 行 · {char_count} 字 · Esc 关闭", font=(FONT_FAMILY, 7),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(side=tk.LEFT)

        def do_save_as_note():
            tag, clean = parse_natural_tags(content.strip())
            add_note(clean[:500], tag=tag)
            self._invalidate_cache()
            self._refresh_cards()
            self._log(f"💾 [{tag}] {filename}")
            save_note_lbl.configure(text="✓ 已保存", fg=COLORS["success"])
            mw.after(1500, lambda: save_note_lbl.configure(text="保存为笔记", fg="#ffffff"))
            self._flash_status("✓ 已保存为笔记", COLORS["success"])

        save_note_lbl = tk.Label(bf, text="保存为笔记", font=(FONT_FAMILY, 9, "bold"),
                                  fg="#ffffff", bg=COLORS["primary"], cursor="hand2", padx=16, pady=4)
        save_note_lbl.pack(side=tk.RIGHT, padx=(0, 8))
        save_note_lbl.bind("<ButtonPress-1>", lambda e: do_save_as_note())
        save_note_lbl.bind("<Enter>", lambda e: save_note_lbl.configure(bg=COLORS["primary_hover"]))
        save_note_lbl.bind("<Leave>", lambda e: save_note_lbl.configure(bg=COLORS["primary"]))

        def do_reload():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    new_content = f.read()
                txt.configure(state=tk.NORMAL)
                txt.delete("1.0", tk.END)
                self._render_markdown(txt, new_content)
                txt.configure(state=tk.DISABLED)
                reload_lbl.configure(text="✓ 已刷新", fg=COLORS["success"])
                mw.after(1500, lambda: reload_lbl.configure(text="刷新", fg=COLORS["text_secondary"]))
            except Exception:
                pass

        reload_lbl = tk.Label(bf, text="刷新", font=(FONT_FAMILY, 9),
                               fg=COLORS["text_secondary"], bg=COLORS["surface"],
                               cursor="hand2", padx=12, pady=4)
        reload_lbl.pack(side=tk.RIGHT, padx=(0, 6))
        reload_lbl.bind("<ButtonPress-1>", lambda e: do_reload())
        reload_lbl.bind("<Enter>", lambda e: reload_lbl.configure(bg=COLORS["surface_hover"]))
        reload_lbl.bind("<Leave>", lambda e: reload_lbl.configure(bg=COLORS["surface"]))

        mw.bind("<Escape>", lambda e: mw.destroy())