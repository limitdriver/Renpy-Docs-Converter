import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import re
import json
import os
import urllib.request
import webbrowser

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "character_map.json")
CURRENT_VERSION = "v1.1.0"
RELEASES_URL = "https://github.com/limitdriver/Renpy-Docs-Converter/releases"
RELEASES_API = "https://api.github.com/repos/limitdriver/Renpy-Docs-Converter/releases/latest"


def check_for_update():
    try:
        req = urllib.request.Request(RELEASES_API, headers={"User-Agent": "RenpyConverter"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        latest = data.get("tag_name", "")
        if latest and latest != CURRENT_VERSION:
            return latest
    except Exception:
        pass
    return None

DEFAULT_CHAR_MAP = {
    "Quiet Woman": "qwoman",
    "Narrator": "narrator",
    "???": "mystery",
}


def load_char_map():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return dict(DEFAULT_CHAR_MAP)


def save_char_map(char_map):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(char_map, f, indent=2)


def convert(text, char_map):
    text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    lines = text.splitlines()
    output = []
    current_speaker = None  # None means narration

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        # Narration: line starts with ">"
        if line.startswith(">"):
            content = line[1:].strip()
            if content:
                output.append(f'"{content}"')
            current_speaker = None
            continue

        # Check for "Speaker: dialogue" pattern
        speaker_match = re.match(r'^([^:]+):\s*(.*)', line)
        if speaker_match:
            speaker_name = speaker_match.group(1).strip()
            dialogue = speaker_match.group(2).strip()
            var = char_map.get(speaker_name, speaker_name.lower().replace(" ", "_"))
            current_speaker = var
            if dialogue:
                output.append(f'{var} "{dialogue}"')
            continue

        # Continuation line — use current speaker if set, else narration
        if current_speaker:
            output.append(f'{current_speaker} "{line}"')
        else:
            output.append(f'"{line}"')

    return "\n".join(output)


class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ren'Py Script Converter")
        self.geometry("900x700")
        self.configure(bg="#1e1e2e")
        self.char_map = load_char_map()
        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Consolas", 10))
        style.configure("TButton", background="#313244", foreground="#cdd6f4", font=("Consolas", 10), borderwidth=0)
        style.map("TButton", background=[("active", "#45475a")])
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4", padding=[10, 4])
        style.map("TNotebook.Tab", background=[("selected", "#45475a")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # --- Converter Tab ---
        conv_frame = ttk.Frame(notebook)
        notebook.add(conv_frame, text="Converter")

        paned = tk.PanedWindow(conv_frame, orient=tk.HORIZONTAL, bg="#1e1e2e", sashwidth=6, sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True)

        # Input panel
        in_frame = ttk.Frame(paned)
        ttk.Label(in_frame, text="Input  (paste Google Doc text here)").pack(anchor="w", padx=4, pady=(4, 2))
        self.input_text = scrolledtext.ScrolledText(
            in_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief=tk.FLAT, borderwidth=0
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        paned.add(in_frame, minsize=200)

        # Output panel
        out_frame = ttk.Frame(paned)
        out_top = ttk.Frame(out_frame)
        out_top.pack(fill=tk.X, padx=4, pady=(4, 2))
        ttk.Label(out_top, text="Output  (Ren'Py script)").pack(side=tk.LEFT)
        ttk.Button(out_top, text="Copy", command=self._copy_output).pack(side=tk.RIGHT)
        out_scroll = tk.Scrollbar(out_frame)
        out_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 4))
        self.output_text = tk.Text(
            out_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief=tk.FLAT, borderwidth=0, state=tk.DISABLED,
            yscrollcommand=out_scroll.set
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        out_scroll.config(command=self.output_text.yview)
        # Syntax highlight tags
        self.output_text.tag_configure("var", foreground="#cba6f7")       # variable name — purple
        self.output_text.tag_configure("string", foreground="#f9e2af")    # dialogue string — yellow
        self.output_text.tag_configure("narration", foreground="#a6e3a1") # narration string — green
        self.output_text.tag_configure("quote", foreground="#6c7086")     # quote marks — muted
        paned.add(out_frame, minsize=200)

        # Convert button
        btn_frame = ttk.Frame(conv_frame)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 6))
        ttk.Button(btn_frame, text="Convert →", command=self._do_convert).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Clear", command=self._clear).pack(side=tk.RIGHT, padx=(0, 6))

        # --- Character Map Tab ---
        map_frame = ttk.Frame(notebook)
        notebook.add(map_frame, text="Character Map")

        ttk.Label(map_frame, text='Map "Display Name" → renpy_variable  (one per row, colon-separated)').pack(
            anchor="w", padx=8, pady=(8, 2)
        )
        self.map_text = scrolledtext.ScrolledText(
            map_frame, wrap=tk.NONE, font=("Consolas", 10),
            bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief=tk.FLAT, borderwidth=0, height=20
        )
        self.map_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))
        self._populate_map_text()

        map_btn = ttk.Frame(map_frame)
        map_btn.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Button(map_btn, text="Save Character Map", command=self._save_map).pack(side=tk.RIGHT)

        # --- Help Tab ---
        help_frame = ttk.Frame(notebook)
        notebook.add(help_frame, text="Help")
        help_text = (
            "Syntax Rules\n"
            "============\n\n"
            "> This is narration.        →  \"This is narration.\"\n\n"
            "Quiet Woman: Hello there.  →  qwoman \"Hello there.\"\n\n"
            "Continuation line          →  uses last speaker (or narration if none)\n\n"
            "Blank line                 →  keeps current speaker (blank lines are ignored)\n\n"
            "> narration line           →  resets speaker back to narration\n\n"
            "Character Map tab lets you define Name → variable mappings.\n"
            "Unknown names fall back to lowercased underscored variable names.\n"
        )
        help_label = tk.Text(
            help_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg="#181825", fg="#cdd6f4", relief=tk.FLAT, borderwidth=0,
            state=tk.NORMAL, padx=12, pady=12
        )
        help_label.insert("1.0", help_text)
        help_label.configure(state=tk.DISABLED)
        help_label.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        help_btn = ttk.Frame(help_frame)
        help_btn.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Label(help_btn, text=f"Version {CURRENT_VERSION}").pack(side=tk.LEFT)
        ttk.Button(help_btn, text="Check for Updates", command=self._check_updates).pack(side=tk.RIGHT)

    def _populate_map_text(self):
        self.map_text.delete("1.0", tk.END)
        for name, var in self.char_map.items():
            self.map_text.insert(tk.END, f"{name}: {var}\n")

    def _save_map(self):
        raw = self.map_text.get("1.0", tk.END).strip()
        new_map = {}
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                messagebox.showerror("Parse Error", f"Invalid line (missing ':'): {line!r}")
                return
            key, _, val = line.partition(":")
            new_map[key.strip()] = val.strip()
        self.char_map = new_map
        save_char_map(self.char_map)
        messagebox.showinfo("Saved", "Character map saved.")

    def _do_convert(self):
        raw = self.input_text.get("1.0", tk.END)
        result = convert(raw, self.char_map)
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, result)
        self._highlight_output()
        self.output_text.configure(state=tk.DISABLED)

    def _highlight_output(self):
        content = self.output_text.get("1.0", tk.END)
        for line_num, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            # narration: line is just "..."
            narr_match = re.match(r'^(".*")$', line)
            if narr_match:
                start = f"{line_num}.0"
                self.output_text.tag_add("quote", f"{line_num}.0", f"{line_num}.1")
                self.output_text.tag_add("narration", f"{line_num}.1", f"{line_num}.{len(line) - 1}")
                self.output_text.tag_add("quote", f"{line_num}.{len(line) - 1}", f"{line_num}.{len(line)}")
                continue
            # dialogue: var "..."
            dial_match = re.match(r'^(\S+) (".*")$', line)
            if dial_match:
                var_end = len(dial_match.group(1))
                str_start = var_end + 1
                self.output_text.tag_add("var", f"{line_num}.0", f"{line_num}.{var_end}")
                self.output_text.tag_add("quote", f"{line_num}.{str_start}", f"{line_num}.{str_start + 1}")
                self.output_text.tag_add("string", f"{line_num}.{str_start + 1}", f"{line_num}.{len(line) - 1}")
                self.output_text.tag_add("quote", f"{line_num}.{len(line) - 1}", f"{line_num}.{len(line)}")

    def _copy_output(self):
        text = self.output_text.get("1.0", tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(text)

    def _check_updates(self):
        latest = check_for_update()
        if latest:
            if messagebox.askyesno("Update Available", f"Version {latest} is available.\nOpen the releases page?"):
                webbrowser.open(RELEASES_URL)
        else:
            messagebox.showinfo("Up to Date", f"You're on the latest version ({CURRENT_VERSION}).")

    def _clear(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state=tk.DISABLED)


if __name__ == "__main__":
    app = ConverterApp()
    app.mainloop()
