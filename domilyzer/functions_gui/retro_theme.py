"""Retro beveled theme + rainbow Turing-pattern header banner.

Shared look-and-feel for the Domilyzer conversion GUIs, mirroring the Wave
Analysis tool: classic Win2k/Motif beveled panels, white sunken fields, a
steel-blue selection, a warm-gray (light) or dark-gray (dark) palette, and a
circular reaction-diffusion logo beside a serif wordmark.

Drop the :class:`RetroHeaderMixin` in front of ``tk.Tk`` and call
``_apply_retro_theme(self, palette)`` once per interpreter.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk


# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------

# Classic beveled palette (Win2k / Motif look). Both variants share every key so
# the GUI can flip between a warm light gray and a dark gray at runtime.
_RETRO_LIGHT = {
    "bg": "#d4d0c8",       # warm panel gray
    "field": "#ffffff",    # entry / list / text field background
    "text": "#1a1a1a",
    "disabled": "#9a968f",
    "light": "#ffffff",    # top-left bevel highlight
    "dark": "#808080",     # bottom-right bevel shadow
    "trough": "#bfbbb3",
    "select": "#4a6b8a",   # muted steel-blue selection
    "active": "#e3e0d9",   # hovered button face
    "pressed": "#bdb9b1",  # pressed button face
    "log_bg": "#f3eede",   # parchment log field
    "log_fg": "#2a2a2a",
    "error": "#b00000",
    "accent_text": "#3f6088",
    "header_title": "#2a2a2a",
    "header_shadow": "#b9b5ad",
    "header_sub": "#6a6a6a",
    "header_pin": "#a8a49c",
}

_RETRO_DARK = {
    "bg": "#3a3936",       # dark warm gray panel
    "field": "#262521",    # sunken dark field
    "text": "#e6e3da",
    "disabled": "#7d7a72",
    "light": "#56544e",    # top-left bevel highlight (lighter than bg)
    "dark": "#1c1b19",     # bottom-right bevel shadow (darker than bg)
    "trough": "#2a2926",
    "select": "#5a82ab",
    "active": "#4a4843",
    "pressed": "#2c2b28",
    "log_bg": "#22211d",   # near-black warm terminal
    "log_fg": "#d8d4c6",
    "error": "#ff7a7a",
    "accent_text": "#9bbbe0",
    "header_title": "#ececdf",
    "header_shadow": "#262522",
    "header_sub": "#9a978d",
    "header_pin": "#5a5852",
}

# Active palette, mutated in place so every runtime _RETRO[...] lookup follows
# the current choice. Start light; _set_palette / saved config can switch it.
_RETRO = dict(_RETRO_LIGHT)


# ---------------------------------------------------------------------------
# Segmented marching progress bar
# ---------------------------------------------------------------------------

class SegmentedProgress(tk.Canvas):
    """Classic segmented progress bar: discrete blue blocks marching across a
    sunken gray trough. Supports ``configure(maximum=..., value=...)`` plus an
    indeterminate marching sweep via ``start()`` / ``stop()``."""

    _COMET = ("#6f97c6", "#8fb3dc", "#a9c6e6", "#c4d8ef")

    def __init__(self, parent, **kw):
        super().__init__(parent, height=16, highlightthickness=0,
                         bg=_RETRO["trough"], bd=2, relief="sunken", **kw)
        self._max = 100.0
        self._val = 0.0
        self._marching = False
        self._phase = 0
        self._anim_id = None
        self._interval = 90
        self.bind("<Configure>", lambda _e: self._redraw())

    def configure(self, cnf=None, **kw):
        if "maximum" in kw:
            self._max = max(float(kw.pop("maximum") or 1), 1.0)
        if "value" in kw:
            self._val = float(kw.pop("value") or 0)
        if cnf is not None or kw:
            super().configure(cnf, **kw)
        self._redraw()

    config = configure

    def start(self):
        if self._marching:
            return
        self._marching = True
        self._step()

    def stop(self):
        self._marching = False
        if self._anim_id is not None:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None
        self._redraw()

    def _step(self):
        if not self._marching:
            return
        try:
            if not self.winfo_exists():
                return
            self._phase += 1
            self._redraw()
            self._anim_id = self.after(self._interval, self._step)
        except tk.TclError:
            self._marching = False

    def _redraw(self):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 2:
            return
        pad = 2
        seg, gap = 11, 3
        period = seg + gap
        frac = min(self._val / self._max, 1.0) if self._max else 0.0
        filled = (w - 2 * pad) * frac

        if self._marching:
            n = max(int((w - 2 * pad) // period), 1)
            head = self._phase % (n + len(self._COMET))
            for k, shade in enumerate(self._COMET):
                idx = head - k
                if 0 <= idx < n:
                    sx = pad + idx * period
                    self.create_rectangle(sx, pad, min(sx + seg, w - pad), h - pad,
                                          fill=shade, outline=shade)

        x = pad
        while x - pad < filled:
            x1 = min(x + seg, pad + filled)
            self.create_rectangle(x, pad, x1, h - pad,
                                  fill=_RETRO["select"], outline=_RETRO["select"])
            x += period


def _set_palette(name):
    _RETRO.clear()
    _RETRO.update(_RETRO_DARK if name == "dark" else _RETRO_LIGHT)


def _apply_retro_theme(root, palette="light"):
    """Give *root* -- and every child/Toplevel sharing its interpreter -- the
    classic beveled look: grooved panels, raised buttons, white sunken fields,
    steel-blue selection. Call once per Tk interpreter; failures are swallowed so
    a missing theme never blocks the GUI."""
    _set_palette(palette)
    p = _RETRO
    try:
        style = ttk.Style(root)
        style.theme_use("clam")  # most themeable theme; bundled everywhere
    except tk.TclError:
        return

    # Retro fonts: classic Mac Geneva for the UI.
    families = set(tkfont.families(root))
    ui_family = next((f for f in ("Geneva", "Chicago", "ChicagoFLF") if f in families), None)
    if ui_family:
        for named in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                      "TkIconFont", "TkTooltipFont", "TkSmallCaptionFont"):
            try:
                tkfont.nametofont(named).configure(family=ui_family)
            except tk.TclError:
                pass
    root._retro_ui_family = ui_family

    base_font = tkfont.nametofont("TkDefaultFont")
    bold_font = (base_font.actual("family"), base_font.actual("size"), "bold")

    root.configure(bg=p["bg"])

    # Classic (non-ttk) tk widgets read defaults from the option database.
    root.option_add("*Toplevel.background", p["bg"])
    for widget in ("Listbox", "Text", "*TCombobox*Listbox"):
        root.option_add(f"*{widget}.background", p["field"])
        root.option_add(f"*{widget}.foreground", p["text"])
        root.option_add(f"*{widget}.selectBackground", p["select"])
        root.option_add(f"*{widget}.selectForeground", "white")

    style.configure(
        ".", background=p["bg"], foreground=p["text"], fieldbackground=p["field"],
        bordercolor=p["dark"], lightcolor=p["light"], darkcolor=p["dark"],
        troughcolor=p["trough"], focuscolor=p["bg"], font=base_font,
    )
    style.configure("TFrame", background=p["bg"])
    style.configure("TLabel", background=p["bg"], foreground=p["text"])
    style.configure("Hint.TLabel", background=p["bg"], foreground=p["disabled"])
    style.configure("TLabelframe", background=p["bg"], relief="groove",
                    bordercolor=p["dark"], lightcolor=p["light"], darkcolor=p["dark"])
    style.configure("TLabelframe.Label", background=p["bg"], foreground=p["text"],
                    font=bold_font)
    style.configure("TSeparator", background=p["dark"])

    # Raised, beveled buttons; sink in on press.
    style.configure("TButton", background=p["bg"], foreground=p["text"],
                    relief="raised", padding=(10, 4), anchor="center",
                    bordercolor=p["dark"], lightcolor=p["light"], darkcolor=p["dark"])
    style.map("TButton",
              background=[("pressed", p["pressed"]), ("active", p["active"]),
                          ("disabled", p["bg"])],
              foreground=[("disabled", p["disabled"])],
              relief=[("pressed", "sunken")])
    # Primary action button: bold, with a pale-blue raised face. Its text stays
    # dark in both themes for contrast on the light-blue face.
    style.configure("Retro.Accent.TButton", font=bold_font, foreground="#15233a",
                    relief="raised", borderwidth=2, padding=(10, 4),
                    background="#8fb3dc", bordercolor="#2f4f73",
                    lightcolor="#bcd3ed", darkcolor="#5b7da6")
    style.map("Retro.Accent.TButton",
              background=[("pressed", "#6f97c6"), ("active", "#a3c2e6"),
                          ("disabled", p["bg"])],
              foreground=[("disabled", p["disabled"])],
              relief=[("pressed", "sunken")])

    # White, sunken text fields.
    for field in ("TEntry", "TSpinbox", "TCombobox"):
        style.configure(field, fieldbackground=p["field"], foreground=p["text"],
                        background=p["bg"], relief="sunken", arrowcolor=p["text"],
                        bordercolor=p["dark"], lightcolor=p["dark"],
                        darkcolor=p["dark"], insertcolor=p["text"])
    style.map("TCombobox",
              fieldbackground=[("readonly", p["field"]), ("disabled", p["bg"])],
              selectbackground=[("readonly", p["select"])],
              selectforeground=[("readonly", "white")],
              foreground=[("disabled", p["disabled"])])

    style.configure("TCheckbutton", background=p["bg"], foreground=p["text"],
                    indicatorcolor=p["field"], indicatorrelief="sunken",
                    focuscolor=p["bg"])
    style.map("TCheckbutton", background=[("active", p["bg"])],
              indicatorcolor=[("selected", p["field"]), ("pressed", p["active"])])

    for sb in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(sb, background=p["bg"], troughcolor=p["trough"],
                        bordercolor=p["dark"], arrowcolor=p["text"],
                        lightcolor=p["light"], darkcolor=p["dark"])


# ---------------------------------------------------------------------------
# Header banner mixin (rainbow Turing-pattern logo + serif wordmark)
# ---------------------------------------------------------------------------

class RetroHeaderMixin:
    """Adds the circular reaction-diffusion logo + serif wordmark banner used at
    the top of every window. Host class supplies a ``wordmark`` attribute."""

    wordmark = "Domilyzer"

    # Classic six-color Apple logo stripes, top-to-bottom (used as a fallback).
    _APPLE_STRIPES = ("#5cb85c", "#f7d000", "#f5821f", "#e03a3e", "#8e44ad", "#3aa0dd")
    # Mid gray used for the logo's below-threshold gaps and its outer stroke.
    _LOGO_GAP = (110, 110, 110)

    @staticmethod
    def _bg_rgb():
        h = _RETRO["bg"].lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def _turing_logo_base(self):
        """Generate (once) a rainbow Turing / excitable-media pattern as a PIL
        image. Returns the cached image, or ``False`` if the imaging libs are
        unavailable so the caller can fall back to the stripe mark."""
        if getattr(self, "_turing_base", None) is not None:
            return self._turing_base
        try:
            import numpy as np
            from scipy.ndimage import gaussian_filter
            from PIL import Image
        except Exception:
            self._turing_base = False
            return False

        # Reaction-diffusion at a single dominant wavelength: short-range
        # activation vs. long-range inhibition converges to clean, uniformly
        # spaced wavy stripes -- the classic pufferfish-skin labyrinth.
        n = 150
        rng = np.random.default_rng(8)
        grid = rng.standard_normal((n, n))
        activate, inhibit, amp = 4.0, 8.0, 0.15
        for _ in range(150):
            act = gaussian_filter(grid, activate, mode="wrap")
            inh = gaussian_filter(grid, inhibit, mode="wrap")
            grid = np.clip(grid + amp * np.sign(act - inh), -1.0, 1.0)
        sharp = gaussian_filter(grid, 0.6, mode="wrap")
        sharp = (sharp - sharp.min()) / (np.ptp(sharp) + 1e-9)
        stripes = sharp >= 0.5

        # Soft random color blobs land across the maze, indexing the muted
        # six-color Apple rainbow.
        color_field = gaussian_filter(
            np.random.default_rng(42).standard_normal((n, n)), 25.0, mode="wrap")
        color_field = (color_field - color_field.min()) / (np.ptp(color_field) + 1e-9)

        palette = np.array(
            [[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in self._APPLE_STRIPES],
            dtype=float,
        )
        stops = np.linspace(0.0, 1.0, len(palette))
        lut_x = np.linspace(0.0, 1.0, 256)
        lut = np.stack([np.interp(lut_x, stops, palette[:, k]) for k in range(3)], axis=1)
        levels = 6
        banded = np.clip(np.floor(color_field * levels) / (levels - 1), 0.0, 1.0)
        idx = (banded * 255).astype(int)
        rgb = lut[idx].astype("uint8").copy()
        rgb[~stripes] = self._LOGO_GAP  # below threshold -> mid gray for contrast
        self._turing_base = Image.fromarray(rgb, "RGB").convert("RGBA")
        return self._turing_base

    def _draw_logo(self, canvas, x, y, size):
        """Draw the circular Turing-pattern logo (or stripe fallback). Returns
        the x coordinate of the logo's right edge."""
        base = self._turing_logo_base()
        if base:
            try:
                from PIL import Image, ImageDraw, ImageTk
                ss = max(size * 2, 2)  # supersample for clean circular edges
                stroke = max(int(ss * 0.08), 1)
                inner = max(ss - 2 * stroke, 2)

                disc = Image.new("RGBA", (ss, ss), self._LOGO_GAP + (255,))
                pat = base.resize((inner, inner), Image.LANCZOS).convert("RGBA")
                pat_mask = Image.new("L", (inner, inner), 0)
                ImageDraw.Draw(pat_mask).ellipse((0, 0, inner - 1, inner - 1), fill=255)
                disc.paste(pat, (stroke, stroke), pat_mask)

                outer_mask = Image.new("L", (ss, ss), 0)
                ImageDraw.Draw(outer_mask).ellipse((0, 0, ss - 1, ss - 1), fill=255)
                bg = Image.new("RGBA", (ss, ss), self._bg_rgb() + (255,))
                composed = (Image.composite(disc, bg, outer_mask)
                            .resize((size, size), Image.LANCZOS).convert("RGB"))
                canvas._wa_logo_photo = ImageTk.PhotoImage(composed)
                canvas.create_image(x, y, anchor="nw", image=canvas._wa_logo_photo)
                return x + size
            except Exception:
                pass

        # Fallback: classic six-color Apple stripes.
        lw = int(size * 0.95)
        n = len(self._APPLE_STRIPES)
        stripe_h = size / n
        skew = 6
        for i, col in enumerate(self._APPLE_STRIPES):
            y0 = y + i * stripe_h
            y1 = y0 + stripe_h + 0.6
            canvas.create_polygon(x + skew, y0, x + lw + skew, y0,
                                  x + lw, y1, x, y1, fill=col, outline=col)
        return x + lw + skew

    def _header_font_family(self):
        """Pick the most Apple-Garamond-ish serif that's actually installed."""
        if getattr(self, "_hdr_family", None):
            return self._hdr_family
        available = set(tkfont.families())
        for cand in ("Apple Garamond", "Garamond", "Palatino", "Palatino Linotype",
                     "Hoefler Text", "Georgia", "Times New Roman"):
            if cand in available:
                self._hdr_family = cand
                break
        else:
            self._hdr_family = tkfont.nametofont("TkDefaultFont").actual("family")
        return self._hdr_family

    def _build_header(self, parent, subtitle=None):
        """Banner with the rainbow logo, a serif wordmark, classic Mac pinstripes,
        and a beveled divider underneath."""
        self._header_subtitle = subtitle
        canvas = tk.Canvas(parent, height=68, highlightthickness=0,
                           bg=_RETRO["bg"], bd=0)
        canvas.grid_propagate(True)
        canvas.bind("<Configure>", lambda _e, c=canvas: self._draw_header(c))
        self.after(60, lambda c=canvas: self._draw_header(c))
        self._header_canvas = canvas
        return canvas

    def _draw_header(self, canvas):
        try:
            if not canvas.winfo_exists():
                return
        except tk.TclError:
            return
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10:
            return
        canvas.delete("all")

        lx, ly = 4, 8
        size = max(h - 20, 24)
        logo_right = self._draw_logo(canvas, lx, ly, size)

        fam = self._header_font_family()
        title_x = logo_right + 16
        cy = h // 2
        title_font = tkfont.Font(family=fam, size=25, weight="bold")
        canvas.create_text(title_x + 1, cy - 8, text=self.wordmark, anchor="w",
                           font=title_font, fill=_RETRO["header_shadow"])
        canvas.create_text(title_x, cy - 9, text=self.wordmark, anchor="w",
                           font=title_font, fill=_RETRO["header_title"])

        sub = getattr(self, "_header_subtitle", None)
        if sub:
            spaced = "  ".join(sub.upper())
            canvas.create_text(title_x + 2, cy + 15, text=spaced, anchor="w",
                               font=(fam, 9), fill=_RETRO["header_sub"])

        # Classic Mac title-bar pinstripes filling the empty space on the right.
        ps_x0 = title_x + title_font.measure(self.wordmark) + 26
        ps_x1 = w - 8
        if ps_x1 - ps_x0 > 50:
            for i in range(6):
                yy = cy - 15 + i * 6
                canvas.create_line(ps_x0, yy, ps_x1, yy, fill=_RETRO["header_pin"])

        canvas.create_line(0, h - 2, w, h - 2, fill=_RETRO["dark"])
        canvas.create_line(0, h - 1, w, h - 1, fill=_RETRO["light"])
