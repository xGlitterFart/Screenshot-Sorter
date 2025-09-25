import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from PIL import Image

# ------------------------ Tooltip helper ------------------------
class Tooltip:
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tip = None
        widget.bind("<Motion>", self._on_motion)
        widget.bind("<Leave>", self._hide)

    def _on_motion(self, event):
        txt = self.text_func(event)
        if not txt:
            self._hide()
            return
        x = event.x_root + 12
        y = event.y_root + 12
        if self.tip is None:
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.attributes("-topmost", True)
            lbl = tk.Label(
                self.tip,
                text=txt,
                justify="left",
                background="#111827",
                foreground="#f9fafb",
                relief="solid",
                borderwidth=1,
                font=("Segoe UI", 9),
                padx=6, pady=4,
            )
            lbl.pack()
        else:
            for child in self.tip.winfo_children():
                if isinstance(child, tk.Label):
                    child.config(text=txt)
            self.tip.wm_geometry(f"+{x}+{y}")

    def _hide(self, *_):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None

# ------------------------ Intro Page ------------------------
class IntroductionPage:
    def __init__(self, root, on_continue):
        self.root = root
        self.on_continue = on_continue

        self.frame = tb.Frame(root, padding=20)
        self.frame.pack(fill="both", expand=True)

        intro_text = (
            "Screenshot Sorter (FFXIV)\n\n"
            "• Sort screenshots by Date / Zone / Character\n"
            "• Move & Archive (in source) or Copy to Destination\n"
            "• Optional watermark (image) with corner position and opacity (%)\n\n"
            "Tip: Make a backup before moving files. Have fun! ✨"
        )

        self.label = tb.Label(self.frame, text=intro_text, anchor="w", justify="left", font=("Segoe UI", 11))
        self.label.pack(pady=(0, 16), fill="x")

        self.continue_btn = tb.Button(self.frame, text="Continue", bootstyle=PRIMARY, command=self.proceed)
        self.continue_btn.pack()

    def proceed(self):
        self.frame.destroy()
        self.on_continue()

# ------------------------ Main App ------------------------
class ScreenshotSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot Sorter")

        # Counters
        self.total = 0
        self.done = 0
        self.ok_count = 0
        self.skip_count = 0
        self._error_lines = {}

        self.main_frame = tb.Frame(root, padding=15)
        self.main_frame.pack(fill="both", expand=True)

        # Warning
        warning = tb.Label(
            self.main_frame,
            text="⚠️ Please back up your photos before moving them!",
            foreground="#ef4444",
            font=("Segoe UI Semibold", 11),
        )
        warning.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        # Options
        self.option_var = tk.StringVar(value="1")
        self.opt1_rb = tb.Radiobutton(
            self.main_frame,
            text="Option 1: Move & archive in source folder",
            variable=self.option_var,
            value="1",
            command=self.toggle_destination,
            bootstyle="info",
        )
        self.opt2_rb = tb.Radiobutton(
            self.main_frame,
            text="Option 2: Copy to destination folder (source unchanged)",
            variable=self.option_var,
            value="2",
            command=self.toggle_destination,
            bootstyle="info",
        )
        self.opt1_rb.grid(row=1, column=0, columnspan=3, sticky="w")
        self.opt2_rb.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Paths
        tb.Label(self.main_frame, text="Source folder:").grid(row=3, column=0, sticky="w")
        self.src_entry = tb.Entry(self.main_frame, width=45)
        self.src_entry.grid(row=3, column=1, sticky="ew")
        self.src_browse_btn = tb.Button(self.main_frame, text="Browse", command=self.browse_source, bootstyle=SECONDARY)
        self.src_browse_btn.grid(row=3, column=2, sticky="ew", padx=(6, 0))

        tb.Label(self.main_frame, text="Destination folder:").grid(row=4, column=0, sticky="w")
        self.dest_entry = tb.Entry(self.main_frame, width=45, state="disabled")
        self.dest_entry.grid(row=4, column=1, sticky="ew")
        self.dest_browse_btn = tb.Button(self.main_frame, text="Browse", command=self.browse_destination, state="disabled", bootstyle=SECONDARY)
        self.dest_browse_btn.grid(row=4, column=2, sticky="ew", padx=(6, 0))

        # Start
        self.start_btn = tb.Button(self.main_frame, text="Start", command=self.start_sorting, bootstyle=SUCCESS)
        self.start_btn.grid(row=5, column=0, columnspan=3, pady=(10, 8), sticky="ew")

        # Progress
        self.progress = tb.Progressbar(self.main_frame, mode="determinate", value=0, bootstyle=STRIPED)
        self.progress.grid(row=6, column=0, columnspan=3, sticky="ew")
        self.status_lbl = tb.Label(self.main_frame, text="Ready.", font=("Segoe UI", 9))
        self.status_lbl.grid(row=7, column=0, columnspan=3, sticky="w", pady=(4, 8))

        # Log
        self.log_output = scrolledtext.ScrolledText(self.main_frame, height=15, state="disabled", font=("Consolas", 10))
        self.log_output.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(6, 0))
        Tooltip(self.log_output, self._hover_reason_for_event)

        # Theme selector
        tb.Label(self.main_frame, text="Theme:").grid(row=9, column=0, sticky="w", pady=(10, 0))
        self.theme_var = tk.StringVar(value=self.root.style.theme_use())
        themes = sorted(self.root.style.theme_names())
        self.theme_combo = tb.Combobox(self.main_frame, textvariable=self.theme_var, values=themes, state="readonly")
        self.theme_combo.grid(row=9, column=1, sticky="w", pady=(10, 0))
        self.theme_combo.bind("<<ComboboxSelected>>", self.change_theme)

        # --- Watermark (single checkbox + labeled group) ---
        self.enable_wm = tk.BooleanVar(value=False)
        self.wm_check = tb.Checkbutton(
            self.main_frame,
            text="Enable watermark",
            variable=self.enable_wm,
            bootstyle="round-toggle",
            command=self._on_toggle_wm,
        )
        self.wm_check.grid(row=10, column=0, sticky="w", pady=(12, 0))

        self.wm_group = tb.Labelframe(self.main_frame, text="Watermark settings", padding=10)
        self.wm_group.grid(row=11, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        # Row 0: Select image (left aligned only)
        self.wm_path = tk.StringVar(value="")
        self.wm_btn = tb.Button(self.wm_group, text="Select image…", command=self.browse_watermark, bootstyle=SECONDARY)
        self.wm_btn.grid(row=0, column=0, sticky="w", pady=(0, 4))

        # Row 1: Position (label + combobox)
        tb.Label(self.wm_group, text="Position:").grid(row=1, column=0, sticky="w", pady=(0, 4))
        self.wm_position = tk.StringVar(value="bottom-right")
        self.pos_combo = tb.Combobox(
            self.wm_group,
            textvariable=self.wm_position,
            values=["top-left", "top-right", "bottom-left", "bottom-right"],
            state="readonly",
            width=18,
        )
        self.pos_combo.grid(row=1, column=1, sticky="w", pady=(0, 4))

        # Row 2: Opacity % (entry)
        tb.Label(self.wm_group, text="Opacity (%):").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.wm_opacity_pct = tk.StringVar(value="70")
        self.opacity_entry = tb.Entry(self.wm_group, textvariable=self.wm_opacity_pct, width=10)
        self.opacity_entry.grid(row=2, column=1, sticky="w", pady=(0, 4))

        # Layout weights
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(8, weight=1)
        self.wm_group.grid_columnconfigure(2, weight=1)

        # Disable WM controls initially
        self._set_wm_controls_state(False)

    # ------------------- Helpers -------------------
    def _set_wm_controls_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for w in (self.wm_btn, self.pos_combo, self.opacity_entry):
            w.config(state=state)

    def _on_toggle_wm(self):
        enabled = self.enable_wm.get()
        self._set_wm_controls_state(enabled)
        if enabled:
            messagebox.showinfo(
                "Watermark Enabled",
                "When enabled:\n\n"
                "✔ Destination screenshots will include the watermark\n"
                "✔ Archive copies will also include the watermark"
            )

    def toggle_destination(self):
        if self.option_var.get() == "2":
            self.dest_entry.config(state="normal")
            self.dest_browse_btn.config(state="normal")
        else:
            self.dest_entry.config(state="disabled")
            self.dest_browse_btn.config(state="disabled")
            self.dest_entry.delete(0, tk.END)

    def browse_source(self):
        folder = filedialog.askdirectory(title="Select source folder")
        if folder:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, folder)

    def browse_destination(self):
        folder = filedialog.askdirectory(title="Select destination folder")
        if folder:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)

    def browse_watermark(self):
        path = filedialog.askopenfilename(
            title="Select watermark image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg")],
        )
        if path:
            self.wm_path.set(path)
            self.wm_btn.config(text=os.path.basename(path))  # show chosen file name

    def change_theme(self, event=None):
        new_theme = self.theme_var.get()
        try:
            self.root.style.theme_use(new_theme)
        except Exception as e:
            messagebox.showerror("Theme Error", f"Could not change theme:\n{e}")

    # ------------------- Logging -------------------
    def _append_text(self, text, tag=None):
        self.log_output.config(state="normal")
        start_index = self.log_output.index("end-1c")
        self.log_output.insert("end", text + "\n")
        end_index = self.log_output.index("end-1c")
        if tag:
            self.log_output.tag_add(tag, start_index, end_index)
        self.log_output.tag_config("success", foreground="#16a34a")
        self.log_output.tag_config("error", foreground="#ef4444")
        self.log_output.tag_config(
            "summary",
            foreground="#facc15",
            background="#374151",
            font=("Consolas", 10, "bold"),
            lmargin1=6, lmargin2=6, rmargin=6,
        )
        self.log_output.config(state="disabled")
        self.log_output.see("end")
        return start_index, end_index

    def log_ok(self, message):
        self._append_text(message, "success")

    def log_skip(self, message, reason):
        start, _ = self._append_text(message, "error")
        self._error_lines[start] = reason

    def log_summary(self):
        frame = (
            "==============================\n"
            f"✅ Success: {self.ok_count} files\n"
            f"⚠️ Skipped: {self.skip_count} files\n"
            "=============================="
        )
        self._append_text(frame, "summary")

    def _hover_reason_for_event(self, event):
        index = self.log_output.index(f"@{event.x},{event.y}")
        line = index.split(".")[0]
        start_index = f"{line}.0"
        return self._error_lines.get(start_index, "")

    # ------------------- Sorting -------------------
    def start_sorting(self):
        option = self.option_var.get()
        source_folder = self.src_entry.get()
        dest_folder = self.dest_entry.get() if option == "2" else None

        # clear log + reset
        self.log_output.config(state="normal")
        self.log_output.delete("1.0", "end")
        self.log_output.config(state="disabled")
        self.total = self._count_images(source_folder) if source_folder else 0
        self.done = 0
        self.ok_count = 0
        self.skip_count = 0
        self._error_lines.clear()

        if not source_folder or not os.path.isdir(source_folder):
            messagebox.showerror("Error", "Please select a valid source folder.")
            return
        if option == "2" and (not dest_folder or not os.path.isdir(dest_folder)):
            messagebox.showerror("Error", "Please select a valid destination folder.")
            return

        self.progress.config(value=0, maximum=max(self.total, 1))
        self.status_lbl.config(text=f"Starting… (0 / {self.total})")

        try:
            if option == "1":
                self.sort_and_archive_in_source(source_folder)
            else:
                self.copy_to_destination(dest_folder, source_folder)

            self.log_summary()
            messagebox.showinfo("Done", "Sorting completed.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    def _count_images(self, folder):
        if not folder or not os.path.isdir(folder):
            return 0
        return sum(1 for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg")))

    def _step_progress(self):
        self.done += 1
        self.progress.config(value=self.done)
        self.status_lbl.config(text=f"Processing… ({self.done} / {self.total})")
        self.root.update_idletasks()

    def extract_info(self, filename):
        pattern = r"^(\d{4}-\d{2}-\d{2})_\d{2}-\d{2}-\d{2}\.\d{3}-(.+)-([^-]+)\.(?:png|jpg|jpeg)$"
        match = re.match(pattern, filename, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            location = match.group(2).strip()
            character = match.group(3).strip()
            date_folder_name = "-".join(date_str.split("-")[::-1])
            return date_folder_name, location, character
        return None, None, None

    # ------ filename versioning ------
    def _next_available_path(self, path):
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 1
        while True:
            candidate = f"{base} ({i}){ext}"
            if not os.path.exists(candidate):
                return candidate
            i += 1

    # ------ Move & Archive ------
    def sort_and_archive_in_source(self, source_folder):
        archive_folder = os.path.join(source_folder, "Archive")
        os.makedirs(archive_folder, exist_ok=True)

        for file in os.listdir(source_folder):
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            full_src_path = os.path.join(source_folder, file)
            if os.path.isdir(full_src_path):
                continue

            date_folder, location, character = self.extract_info(file)
            if not date_folder or not location or not character:
                self.skip_count += 1
                self.log_skip(f"[SKIPPED] {file} – Unrecognized format", "Filename does not match FFXIV pattern.")
                self._step_progress()
                continue

            dest_dir = os.path.join(source_folder, date_folder, location, character)
            os.makedirs(dest_dir, exist_ok=True)

            dest_path = self._next_available_path(os.path.join(dest_dir, file))
            shutil.move(full_src_path, dest_path)  # move original

            # Watermark (if enabled), then archive the resulting file
            if self.enable_wm.get() and self.wm_path.get():
                self.apply_watermark(dest_path)

            archive_target = self._next_available_path(os.path.join(archive_folder, os.path.basename(dest_path)))
            shutil.copy2(dest_path, archive_target)

            self.ok_count += 1
            self.log_ok(f"[MOVED] {os.path.basename(dest_path)} → {date_folder}/{location}/{character}")
            self._step_progress()

    # ------ Copy to destination ------
    def copy_to_destination(self, dest_folder, source_folder):
        for file in os.listdir(source_folder):
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            full_src_path = os.path.join(source_folder, file)
            if os.path.isdir(full_src_path):
                continue

            date_folder, location, character = self.extract_info(file)
            if not date_folder or not location or not character:
                self.skip_count += 1
                self.log_skip(f"[SKIPPED] {file} – Unrecognized format", "Filename does not match FFXIV pattern.")
                self._step_progress()
                continue

            dest_dir = os.path.join(dest_folder, date_folder, location, character)
            os.makedirs(dest_dir, exist_ok=True)

            dest_file_path = self._next_available_path(os.path.join(dest_dir, file))
            shutil.copy2(full_src_path, dest_file_path)

            if self.enable_wm.get() and self.wm_path.get():
                self.apply_watermark(dest_file_path)

            self.ok_count += 1
            self.log_ok(f"[COPIED] {os.path.basename(dest_file_path)} → {date_folder}/{location}/{character}")
            self._step_progress()

    # ------ Watermark ------
    def _get_opacity_float(self):
        """Read opacity from the % entry and clamp to [0.05, 1.0]."""
        try:
            pct = float(self.wm_opacity_pct.get().strip())
        except Exception:
            pct = 70.0
        pct = max(5.0, min(100.0, pct))  # clamp 5–100%
        return pct / 100.0

    def apply_watermark(self, filepath):
        try:
            base = Image.open(filepath).convert("RGBA")
            wm = Image.open(self.wm_path.get()).convert("RGBA")

            # Trim transparent padding so it truly hugs the corner
            bbox = wm.getbbox()
            if bbox:
                wm = wm.crop(bbox)

            # Resize watermark to ~30% of base width (visible but not huge)
            scale = max(1, base.width // 3)
            ratio = wm.height / wm.width if wm.width else 1
            wm = wm.resize((scale, max(1, int(scale * ratio))), Image.LANCZOS)

            # Opacity
            opacity = self._get_opacity_float()
            alpha = wm.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            wm.putalpha(alpha)

            # Position
            margin = 10
            pos = self.wm_position.get()
            if pos == "top-left":
                xy = (margin, margin)
            elif pos == "top-right":
                xy = (base.width - wm.width - margin, margin)
            elif pos == "bottom-left":
                xy = (margin, base.height - wm.height - margin)
            else:  # bottom-right
                xy = (base.width - wm.width - margin, base.height - wm.height - margin)

            base.paste(wm, xy, wm)

            # Save preserving original format
            ext = os.path.splitext(filepath)[1].lower()
            if ext in (".jpg", ".jpeg"):
                base = base.convert("RGB")
                base.save(filepath, quality=95)
            else:
                base.save(filepath)

            self.log_ok(f"[WATERMARK] applied to {os.path.basename(filepath)}")

        except Exception as e:
            self.log_skip(f"[WATERMARK FAILED] {os.path.basename(filepath)}", str(e))

# ------------------------ entrypoint ------------------------
def main():
    # Try themes: "flatly", "cosmo", "journal", "superhero", "morph", "darkly"
    root = tb.Window(themename="darkly")
    root.title("Screenshot Sorter")
    root.geometry("1040x780")

    def start_main_app():
        ScreenshotSorterApp(root)

    IntroductionPage(root, on_continue=start_main_app)
    root.mainloop()

if __name__ == "__main__":
    main()
