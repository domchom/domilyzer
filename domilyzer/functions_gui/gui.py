import os
import sys
import gc
import json
import threading
import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter.filedialog import askdirectory

from domilyzer.functions_gui.retro_theme import (
    RetroHeaderMixin,
    SegmentedProgress,
    _apply_retro_theme,
    _RETRO,
)


class _StdoutToLog:
    """File-like proxy that funnels worker-thread ``print`` output, line by line,
    into the GUI log (which marshals each line back to the Tk thread)."""

    def __init__(self, gui):
        self.gui = gui
        self._buf = ""

    def write(self, text):
        if not text:
            return
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self.gui.log_message(line)

    def flush(self):
        if self._buf:
            self.gui.log_message(self._buf)
            self._buf = ""

# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------

_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".domilyzer_config.json")

# Default channel LUT names, in channel order.
DEFAULT_CHANNELS = ("Red", "Cyan", "Blue", "Magenta")


def _load_config():
    try:
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_config(data):
    try:
        existing = _load_config()
        existing.update(data)
        with open(_CONFIG_PATH, "w") as f:
            json.dump(existing, f)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# LUT helpers (shared by every GUI instead of being duplicated per class)
# ---------------------------------------------------------------------------

def load_fiji_lut(filepath):
    with open(filepath, "rb") as f:
        raw = np.frombuffer(f.read(), dtype=np.uint8)

    # If 768 or 800 bytes, assume single LUT and trim header if needed
    if raw.size in [768, 800]:
        lut_data = raw[-768:]  # Trim to last 768 bytes
        r = lut_data[0:256]
        g = lut_data[256:512]
        b = lut_data[512:768]
        return np.stack((r, g, b))

    # If size is larger than 800, assume it's a concatenated or category LUT
    # (like Glasbey or unionjack). We'll try to extract the first RGB triplet only.
    if raw.size >= 768 and raw.size % 3 == 0:
        num_colors = raw.size // 3
        r = raw[0:num_colors]
        g = raw[num_colors:2 * num_colors]
        b = raw[2 * num_colors:3 * num_colors]
        max_len = min(256, len(r), len(g), len(b))
        return np.stack((r[:max_len], g[:max_len], b[:max_len]))


def build_lut_dict():
    """Build the dictionary of built-in LUTs plus any Fiji .lut files in assets."""
    grays = np.tile(np.arange(256, dtype="uint8"), (3, 1))

    red = np.zeros((3, 256), dtype="uint8")
    red[0] = np.arange(256, dtype="uint8")

    green = np.zeros((3, 256), dtype="uint8")
    green[1] = np.arange(256, dtype="uint8")

    blue = np.zeros((3, 256), dtype="uint8")
    blue[2] = np.arange(256, dtype="uint8")

    magenta = np.zeros((3, 256), dtype="uint8")
    magenta[0] = np.arange(256, dtype="uint8")
    magenta[2] = np.arange(256, dtype="uint8")

    cyan = np.zeros((3, 256), dtype="uint8")
    cyan[1] = np.arange(256, dtype="uint8")
    cyan[2] = np.arange(256, dtype="uint8")

    yellow = np.zeros((3, 256), dtype="uint8")
    yellow[0] = np.arange(256, dtype="uint8")
    yellow[1] = np.arange(256, dtype="uint8")

    fiji_luts = {
        "Grays": grays,
        "Red": red,
        "Green": green,
        "Blue": blue,
        "Magenta": magenta,
        "Cyan": cyan,
        "Yellow": yellow,
    }

    # Load any extra Fiji LUTs shipped in assets/LUTs into the dictionary.
    luts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "LUTs"))
    if os.path.isdir(luts_dir):
        for lut_file in sorted(os.listdir(luts_dir)):
            if lut_file.endswith(".lut"):
                lut_name = lut_file.split(".")[0]
                lut = load_fiji_lut(os.path.join(luts_dir, lut_file))
                if lut is not None:
                    fiji_luts[lut_name] = lut

    return fiji_luts


# ---------------------------------------------------------------------------
# Shared base GUI
# ---------------------------------------------------------------------------

class _ConversionGUI(RetroHeaderMixin, tk.Tk):
    """Shared layout, styling, LUT pickers, and settings persistence for the
    three conversion GUIs. Subclasses set the class-level flags below to control
    which option widgets appear, and override ``start_analysis`` to snapshot the
    fields they care about."""

    wordmark = "Domilyzer"
    title_text = "Conversion"
    header_text = "Conversion"
    microscope_type = None
    config_key = "base"
    start_text = "Start conversion"

    # Which optional option widgets this GUI shows.
    show_single_plane = False
    show_metadata = False
    show_folder_of_folders = False

    def __init__(self):
        super().__init__()
        self.title(self.title_text)
        self._theme = _load_config().get("theme", "light")
        if self._theme not in ("light", "dark"):
            self._theme = "light"
        _apply_retro_theme(self, self._theme)

        # Set by the mode-switch buttons; read by runner.main to decide which
        # window to open next (None = quit the program).
        self.next_mode = None
        self._is_running = False

        # ---- shared variables ----
        self.lut_dict = build_lut_dict()
        self.lut_names = list(self.lut_dict.keys())

        self.folder_path = tk.StringVar()
        self.avg_project = tk.BooleanVar(value=False)
        self.max_project = tk.BooleanVar(value=True)
        self.single_plane = tk.BooleanVar(value=False)
        self.auto_metadata_extraction = tk.BooleanVar(value=True)
        self.folder_of_folders = tk.BooleanVar(value=True)

        self.channel_vars = [tk.StringVar(value=name) for name in DEFAULT_CHANNELS]
        # Keep the original public names pointing at the same StringVars so the
        # rest of the codebase can keep reading channel1_var .. channel4_var.
        (self.channel1_var, self.channel2_var,
         self.channel3_var, self.channel4_var) = self.channel_vars
        self._swatches = {}  # keep PhotoImage refs alive

        self._restore_settings()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.minsize(560, 600)
        self._center()

    # ---- styling ----

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # ---- layout ----

    def _build_ui(self):
        root = ttk.Frame(self, padding=(14, 8, 14, 14))
        root.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)

        header = self._build_header(root, subtitle=self.header_text)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self._build_folder_frame(root, row=1)

        # Two columns: options on the left, channel LUTs on the right.
        self._build_options_frame(root, row=2, column=0)
        self._build_channels_frame(root, row=2, column=1)

        self._build_button_bar(root, row=3)
        self._build_bottom(root, start_row=4)

    def _build_folder_frame(self, parent, row):
        frame = ttk.LabelFrame(parent, text="Input folder", padding=10)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        ttk.Entry(frame, textvariable=self.folder_path, width=48).grid(
            row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Select folder…", command=self.get_folder_path).grid(
            row=0, column=1, sticky="e")

    def _build_options_frame(self, parent, row, column):
        frame = ttk.LabelFrame(parent, text="Projection & options", padding=10)
        frame.grid(row=row, column=column, sticky="nsew", padx=(0, 10))

        r = 0
        ttk.Checkbutton(
            frame, text="MAX project z-stacks", variable=self.max_project,
            command=lambda: self.update_checkboxes("max") if self.max_project.get() else None,
        ).grid(row=r, column=0, sticky="w", pady=1)
        r += 1
        ttk.Checkbutton(
            frame, text="AVG project z-stacks", variable=self.avg_project,
            command=lambda: self.update_checkboxes("avg") if self.avg_project.get() else None,
        ).grid(row=r, column=0, sticky="w", pady=1)
        r += 1

        if self.show_single_plane:
            ttk.Checkbutton(
                frame, text="Data is single plane", variable=self.single_plane,
                command=lambda: self.update_checkboxes("single") if self.single_plane.get() else None,
            ).grid(row=r, column=0, sticky="w", pady=1)
            r += 1

        if self.show_folder_of_folders:
            ttk.Checkbutton(
                frame, text="Folder of folders", variable=self.folder_of_folders,
                command=lambda: self.update_checkboxes("folder_of_folders") if self.folder_of_folders.get() else None,
            ).grid(row=r, column=0, sticky="w", pady=1)
            r += 1

        if self.show_metadata:
            ttk.Checkbutton(
                frame, text="Extract and save metadata",
                variable=self.auto_metadata_extraction,
            ).grid(row=r, column=0, sticky="w", pady=1)
            r += 1

        ttk.Label(
            frame, text="Select none of the above to save the full hyperstack.",
            style="Hint.TLabel", wraplength=200, justify="left",
        ).grid(row=r, column=0, sticky="w", pady=(6, 0))

    def _build_channels_frame(self, parent, row, column):
        frame = ttk.LabelFrame(parent, text="Channel LUTs", padding=10)
        frame.grid(row=row, column=column, sticky="nsew")
        for i, var in enumerate(self.channel_vars):
            ttk.Label(frame, text=f"Ch{i + 1}").grid(row=i, column=0, sticky="w", padx=(0, 6), pady=2)
            combo = ttk.Combobox(frame, textvariable=var, values=self.lut_names,
                                 width=14, state="readonly")
            combo.grid(row=i, column=1, sticky="w", pady=2)
            swatch = tk.Label(frame, borderwidth=1, relief="solid")
            swatch.grid(row=i, column=2, sticky="w", padx=(8, 0))
            self._swatches[i] = swatch
            self._refresh_swatch(i)
            combo.bind("<<ComboboxSelected>>", lambda _e, idx=i: self._refresh_swatch(idx))

    # Microscope modes, in display order, for the mode-switch buttons.
    _MODES = ("Bruker", "Flamingo", "Olympus")

    def _build_button_bar(self, parent, row):
        bar = ttk.Frame(parent)
        bar.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        self.start_button = ttk.Button(bar, text=self.start_text, style="Retro.Accent.TButton",
                                       command=self.start_analysis)
        self.start_button.pack(side=tk.LEFT)
        ttk.Button(bar, text="Close Window", command=self._on_close).pack(side=tk.LEFT, padx=8)
        self.theme_button = ttk.Button(
            bar, text=("Light Mode" if self._theme == "dark" else "Dark Mode"),
            command=self._toggle_theme, width=10)
        self.theme_button.pack(side=tk.LEFT)

        # Right side: jump to another microscope. The current mode's button is
        # disabled; the rest are disabled while a conversion runs.
        self._mode_buttons = []
        for mode in reversed(self._MODES):
            b = ttk.Button(bar, text=mode, width=9,
                           command=lambda m=mode: self._switch_mode(m))
            b.pack(side=tk.RIGHT, padx=(6, 0))
            if mode == self.microscope_type:
                b.configure(state="disabled")
            self._mode_buttons.append((b, mode))

    def _build_bottom(self, parent, start_row):
        """Status line, marching progress bar, and a scrolling log -- the
        conversion now runs in-window and streams here."""
        parent.rowconfigure(start_row + 2, weight=1)

        self.status_label = ttk.Label(parent, text="Status: Ready",
                                      font=("TkDefaultFont", 10, "bold"), anchor="w")
        self.status_label.grid(row=start_row, column=0, columnspan=2, sticky="ew", pady=(12, 2))

        self.progress_bar = SegmentedProgress(parent)
        self.progress_bar.grid(row=start_row + 1, column=0, columnspan=2, sticky="ew")

        self.log_text = scrolledtext.ScrolledText(parent, height=9, state="disabled", wrap=tk.WORD)
        self.log_text.grid(row=start_row + 2, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        self._style_log()

    # ---- light / dark theme toggle ----

    def _toggle_theme(self):
        self._theme = "dark" if self._theme == "light" else "light"
        _save_config({"theme": self._theme})
        _apply_retro_theme(self, self._theme)       # restyles every ttk widget + root bg
        self._refresh_palette_widgets()             # update the explicitly-colored bits
        try:
            self.theme_button.configure(
                text=("Light Mode" if self._theme == "dark" else "Dark Mode"))
        except tk.TclError:
            pass

    def _refresh_palette_widgets(self):
        """Re-apply palette colors to widgets that carry explicit (non-ttk)
        colors: window background, header canvas, log field, progress, swatches."""
        try:
            self.configure(bg=_RETRO["bg"])
        except tk.TclError:
            return
        canvas = getattr(self, "_header_canvas", None)
        if canvas is not None:
            try:
                canvas.configure(bg=_RETRO["bg"])
                self._draw_header(canvas)
            except tk.TclError:
                pass
        self._style_log()
        if getattr(self, "progress_bar", None) is not None:
            try:
                self.progress_bar.configure(bg=_RETRO["trough"])
            except tk.TclError:
                pass
        for idx in list(self._swatches):
            self._refresh_swatch(idx)

    def _style_log(self):
        """Give the log its classic parchment/dark terminal look."""
        log = getattr(self, "log_text", None)
        if log is None:
            return
        try:
            log.configure(background=_RETRO["log_bg"], foreground=_RETRO["log_fg"],
                          relief="sunken", borderwidth=2, highlightthickness=0,
                          insertbackground=_RETRO["log_fg"])
            log.tag_configure("error", foreground=_RETRO["error"])
        except tk.TclError:
            pass

    # ---- LUT swatch preview ----

    def _refresh_swatch(self, idx):
        lut = self.lut_dict.get(self.channel_vars[idx].get())
        swatch = self._swatches[idx]
        if lut is None:
            return
        width, height = 52, 16
        img = tk.PhotoImage(width=width, height=height)
        cols = []
        for x in range(width):
            j = int(x / (width - 1) * (lut.shape[1] - 1))
            cols.append(f"#{int(lut[0][j]):02x}{int(lut[1][j]):02x}{int(lut[2][j]):02x}")
        row_str = "{" + " ".join(cols) + "}"
        img.put(" ".join(row_str for _ in range(height)))
        swatch.configure(image=img)
        swatch.image = img  # prevent garbage collection

    # ---- actions ----

    def update_checkboxes(self, selected):
        """Keep the projection checkboxes mutually exclusive."""
        projection = {"max": self.max_project, "avg": self.avg_project,
                      "single": self.single_plane}
        if selected in projection:
            for name, var in projection.items():
                if name != selected:
                    var.set(False)

    def get_folder_path(self):
        chosen = askdirectory()
        if chosen:
            self.folder_path.set(chosen)

    # ---- window navigation ----

    def _switch_mode(self, mode):
        """Hand off to another microscope's window (handled by runner.main)."""
        if self._is_running or mode == self.microscope_type:
            return
        self._save_settings()
        self.next_mode = mode
        self._cleanup_tk_vars()
        self.destroy()

    def _on_close(self):
        """Close the program (no further window). A running conversion is on a
        daemon thread and will not block exit."""
        self._save_settings()
        self.next_mode = None
        self._cleanup_tk_vars()
        self.destroy()

    def _cleanup_tk_vars(self):
        """Drop and collect this window's Tk control variables now -- while the
        interpreter is alive and we're on the main thread -- just before the
        window is destroyed.

        Otherwise the old window's ``StringVar``/``BooleanVar`` objects survive
        into the *next* window and get garbage-collected later on a worker thread
        (during the next conversion's numpy allocations), where
        ``Variable.__del__`` raises "main thread is not in main loop"."""
        for name in ("folder_path", "avg_project", "max_project", "single_plane",
                     "auto_metadata_extraction", "folder_of_folders",
                     "channel1_var", "channel2_var", "channel3_var", "channel4_var"):
            if hasattr(self, name):
                delattr(self, name)
        self.channel_vars = []
        gc.collect()

    # ---- run the conversion in-window ----

    def _collect_params(self):
        """Snapshot the current widget values into kwargs for run_conversion."""
        return {
            "parent_folder_path": self.folder_path.get(),
            "microscope_type": self.microscope_type,
            "max_project": self.max_project.get(),
            "avg_project": self.avg_project.get(),
            "single_plane": self.single_plane.get(),
            "auto_metadata_extract": self.auto_metadata_extraction.get(),
            "folder_of_folders": self.folder_of_folders.get(),
            "ch1_lut": self.lut_dict[self.channel_vars[0].get()],
            "ch2_lut": self.lut_dict[self.channel_vars[1].get()],
            "ch3_lut": self.lut_dict[self.channel_vars[2].get()],
            "ch4_lut": self.lut_dict[self.channel_vars[3].get()],
        }

    def start_analysis(self):
        if self._is_running:
            return
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            self.clear_log()
            self.log_message("ERROR: Select a valid input folder first")
            return
        self._save_settings()
        params = self._collect_params()

        self._set_running(True)
        self.clear_log()
        self.set_status(f"Converting ({self.microscope_type})…")
        self.log_message(f"Starting {self.microscope_type} conversion…")
        threading.Thread(target=self._worker, args=(params,), daemon=True).start()

    def _worker(self, params):
        from domilyzer.runner import run_conversion
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = _StdoutToLog(self)
        error = None
        try:
            run_conversion(**params)
        except Exception as e:  # surface failures in the log instead of the console
            error = e
        finally:
            try:
                sys.stdout.flush()
            except Exception:
                pass
            sys.stdout, sys.stderr = old_out, old_err
        self.after(0, lambda: self._on_done(error))

    def _on_done(self, error):
        self._set_running(False)
        self.progress_bar.stop()
        if error is not None:
            self.log_message(f"ERROR: {error}")
            self.set_status("Conversion failed")
            self.progress_bar.configure(value=0)
        else:
            self.set_status("Conversion complete")
            self.progress_bar.configure(maximum=100, value=100)

    def _set_running(self, running):
        """Toggle button availability + the marching progress sweep."""
        self._is_running = running
        state = "disabled" if running else "normal"
        try:
            self.start_button.configure(state=state)
        except tk.TclError:
            pass
        for btn, mode in getattr(self, "_mode_buttons", []):
            if mode == self.microscope_type:
                continue  # current mode's button stays disabled
            try:
                btn.configure(state=state)
            except tk.TclError:
                pass
        if running:
            self.progress_bar.configure(value=0)
            self.progress_bar.start()

    # ---- log / status (thread-safe via after) ----

    def log_message(self, msg):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return

        def _append():
            try:
                if not self.winfo_exists():
                    return
            except tk.TclError:
                return
            self.log_text.configure(state="normal")
            tag = ("error",) if "ERROR" in msg.upper() else ()
            self.log_text.insert(tk.END, msg + "\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
        self.after(0, _append)

    def clear_log(self):
        try:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", tk.END)
            self.log_text.configure(state="disabled")
        except tk.TclError:
            pass

    def set_status(self, text):
        try:
            if self.winfo_exists():
                self.after(0, lambda: self.status_label.configure(text=f"Status: {text}"))
        except tk.TclError:
            pass

    # ---- settings persistence ----

    def _save_settings(self):
        _save_config({
            "last_folder": self.folder_path.get(),
            f"channels_{self.config_key}": [v.get() for v in self.channel_vars],
        })

    def _restore_settings(self):
        cfg = _load_config()
        last_folder = cfg.get("last_folder", "")
        if last_folder and os.path.isdir(last_folder):
            self.folder_path.set(last_folder)
        channels = cfg.get(f"channels_{self.config_key}")
        if isinstance(channels, list):
            for var, name in zip(self.channel_vars, channels):
                if name in self.lut_dict:
                    var.set(name)

# ---------------------------------------------------------------------------
# Concrete GUIs
# ---------------------------------------------------------------------------

class BaseGUI(_ConversionGUI):
    title_text = "Bruker Conversion"
    header_text = "Bruker conversion"
    config_key = "bruker"
    microscope_type = "Bruker"
    show_single_plane = True
    show_metadata = True


class FlamingoGUI(_ConversionGUI):
    title_text = "Flamingo Conversion"
    header_text = "Flamingo conversion"
    config_key = "flamingo"
    microscope_type = "Flamingo"
    show_folder_of_folders = True


class OlympusGUI(_ConversionGUI):
    title_text = "Olympus Conversion"
    header_text = "Olympus conversion"
    config_key = "olympus"
    microscope_type = "Olympus"
