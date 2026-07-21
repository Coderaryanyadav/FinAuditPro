"""
FinAuditPro - Login Screen (Tkinter recreation)

Run with:   python login.py

Dependencies:
- tkinter (standard library, already included with Python)
- Pillow (optional but recommended, for crisp image scaling)
    pip install pillow

If Pillow isn't installed, the script still runs fine — it just falls back
to Tkinter's built-in (lower quality) image scaling.

Make sure "audit_ai_illustration.png" stays in the SAME FOLDER as this file.
"""

import os
import tkinter as tk
from tkinter import font as tkfont

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "audit_ai_illustration.png")

# ---------- Palette ----------
BLUE = "#2554E8"
BLUE_HOVER = "#1B44C8"
DARK_BLUE = "#0F2A5E"
TEAL = "#12C6C0"
PANEL_LILAC = "#EAF0FC"
CARD_WHITE = "#FFFFFF"
TEXT_DARK = "#101828"
TEXT_GRAY = "#8A93A6"
BORDER_GRAY = "#DDE3EE"
BORDER_FOCUS = BLUE
PLACEHOLDER_GRAY = "#A9B1C3"

WIN_W, WIN_H = 1440, 820
LEFT_W = 720


class RoundedEntry(tk.Frame):
    """A clean bordered entry field that turns blue when focused."""

    def __init__(self, master, placeholder, show=None, **kwargs):
        super().__init__(master, bg=BORDER_GRAY, **kwargs)
        self._border_color_idle = BORDER_GRAY
        self.configure(bg=self._border_color_idle)

        inner = tk.Frame(self, bg=CARD_WHITE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.entry = tk.Entry(
            inner, font=("Segoe UI", 12), bd=0, relief="flat",
            fg=TEXT_DARK, insertbackground=TEXT_DARK,
            highlightthickness=0, bg=CARD_WHITE,
        )
        self.entry.pack(fill="both", expand=True, padx=14, pady=12)

        self.placeholder = placeholder
        self.show_char = show
        self._showing_placeholder = True
        self._set_placeholder()

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _set_placeholder(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=PLACEHOLDER_GRAY, show="")
        self._showing_placeholder = True

    def _on_focus_in(self, _event):
        self.configure(bg=BORDER_FOCUS)
        if self._showing_placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT_DARK, show=self.show_char or "")
            self._showing_placeholder = False

    def _on_focus_out(self, _event):
        self.configure(bg=self._border_color_idle)
        if not self.entry.get():
            self._set_placeholder()

    def get_value(self):
        return "" if self._showing_placeholder else self.entry.get()


class HoverButton(tk.Label):
    def __init__(self, master, text, command=None, bg=BLUE, hover_bg=BLUE_HOVER,
                 fg="white", **kwargs):
        super().__init__(master, text=text, bg=bg, fg=fg, cursor="hand2", **kwargs)
        self.command = command
        self.bg_normal = bg
        self.bg_hover = hover_bg
        self.bind("<Enter>", lambda e: self.config(bg=self.bg_hover))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_normal))
        self.bind("<Button-1>", lambda e: self.command() if self.command else None)


class FinAuditProLogin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FinAuditPro")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.configure(bg=CARD_WHITE)
        self.minsize(1150, 680)

        self._load_fonts()
        self._build_title_bar()
        self._build_left_panel()
        self._build_right_panel()

    def _load_fonts(self):
        self.title_font = tkfont.Font(family="Segoe UI", size=28, weight="bold")
        self.label_font = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.small_font = tkfont.Font(family="Segoe UI", size=10)
        self.logo_font = tkfont.Font(family="Segoe UI", size=19, weight="bold")

    # ---------------- Window title bar (fake, matches screenshot chrome) ----------------
    def _build_title_bar(self):
        bar = tk.Frame(self, bg=CARD_WHITE, height=38)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        logo_box = tk.Frame(bar, bg=BLUE, width=20, height=20)
        logo_box.pack(side="left", padx=(14, 6), pady=9)
        logo_box.pack_propagate(False)
        tk.Label(logo_box, text="F", bg=BLUE, fg="white",
                 font=("Segoe UI", 10, "bold")).pack(expand=True)

        tk.Label(bar, text="FinAuditPro", bg=CARD_WHITE, fg=TEXT_DARK,
                 font=("Segoe UI", 10)).pack(side="left", pady=9)

        tk.Frame(self, bg=BORDER_GRAY, height=1).pack(side="top", fill="x")

    # ---------------- Left illustration panel ----------------
    def _build_left_panel(self):
        left = tk.Frame(self, bg=CARD_WHITE, width=LEFT_W)
        left.pack(side="left", fill="both", expand=False)
        left.pack_propagate(False)

        top_row = tk.Frame(left, bg=CARD_WHITE)
        top_row.pack(anchor="w", padx=40, pady=(28, 4))
        logo_box = tk.Frame(top_row, bg=BLUE, width=34, height=34)
        logo_box.pack(side="left")
        logo_box.pack_propagate(False)
        tk.Label(logo_box, text="F", bg=BLUE, fg="white",
                 font=("Segoe UI", 16, "bold")).pack(expand=True)
        tk.Label(top_row, text="FinAuditPro", bg=CARD_WHITE, fg=TEXT_DARK,
                 font=self.logo_font).pack(side="left", padx=10)

        img_holder = tk.Frame(left, bg=CARD_WHITE)
        img_holder.pack(fill="both", expand=True, padx=10, pady=10)

        self._img_ref = None  # keep a reference so it isn't garbage-collected
        self.img_holder = img_holder
        img_holder.bind("<Configure>", self._render_illustration)

    def _render_illustration(self, event=None):
        holder = self.img_holder
        w = holder.winfo_width()
        h = holder.winfo_height()
        if w < 20 or h < 20 or not os.path.exists(IMAGE_PATH):
            return

        target = min(w - 20, h - 20)
        target = max(target, 50)

        for child in holder.winfo_children():
            child.destroy()

        if PIL_AVAILABLE:
            pil_img = Image.open(IMAGE_PATH).convert("RGB")
            pil_img = pil_img.resize((target, target), Image.LANCZOS)
            photo = ImageTk.PhotoImage(pil_img)
        else:
            raw = tk.PhotoImage(file=IMAGE_PATH)
            factor = max(1, round(raw.width() / target))
            photo = raw.subsample(factor, factor)

        self._img_ref = photo  # prevent garbage collection
        lbl = tk.Label(holder, image=photo, bg=CARD_WHITE)
        lbl.place(relx=0.5, rely=0.5, anchor="center")

    # ---------------- Right login panel ----------------
    def _build_right_panel(self):
        right = tk.Frame(self, bg=PANEL_LILAC)
        right.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(right, bg=PANEL_LILAC)
        outer.place(relx=0.5, rely=0.46, anchor="center")

        # subtle "shadow" effect: slightly offset gray frame behind the white card
        shadow = tk.Frame(outer, bg="#C7D0E4")
        shadow.place(x=6, y=8, relwidth=1, relheight=1)

        card = tk.Frame(outer, bg=CARD_WHITE, padx=48, pady=40,
                         highlightbackground=BORDER_GRAY, highlightthickness=1)
        card.pack()

        tk.Label(card, text="Welcome Back", bg=CARD_WHITE, fg=TEXT_DARK,
                 font=self.title_font).pack(anchor="w")
        tk.Label(card, text="Login to access your intelligent audit workspace.",
                 bg=CARD_WHITE, fg=TEXT_GRAY,
                 font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 26))

        # Email
        tk.Label(card, text="Email Address", bg=CARD_WHITE, fg=TEXT_DARK,
                 font=self.label_font).pack(anchor="w", pady=(0, 6))
        self.email_field = RoundedEntry(card, "Email Address")
        self.email_field.pack(fill="x")

        tk.Frame(card, bg=CARD_WHITE, height=20).pack()

        # Password
        tk.Label(card, text="Password", bg=CARD_WHITE, fg=TEXT_DARK,
                 font=self.label_font).pack(anchor="w", pady=(0, 6))
        self.password_field = RoundedEntry(card, "Password", show="*")
        self.password_field.pack(fill="x")

        # Remember me / forgot password row
        row = tk.Frame(card, bg=CARD_WHITE)
        row.pack(fill="x", pady=(18, 22))

        self.remember_var = tk.BooleanVar()
        chk = tk.Checkbutton(
            row, text=" Remember Me", variable=self.remember_var,
            bg=CARD_WHITE, fg=TEXT_DARK, font=self.small_font,
            activebackground=CARD_WHITE, selectcolor=CARD_WHITE,
            bd=0, highlightthickness=0,
        )
        chk.pack(side="left")

        forgot = tk.Label(row, text="Forgot Password", bg=CARD_WHITE, fg=BLUE,
                           font=self.small_font, cursor="hand2")
        forgot.pack(side="right")

        # Sign In button
        signin = HoverButton(card, "Sign In", command=self._on_sign_in,
                              font=("Segoe UI", 13, "bold"), pady=13)
        signin.pack(fill="x")

        offline = tk.Label(card, text="Continue Offline", bg=CARD_WHITE, fg=BLUE,
                            font=self.small_font, cursor="hand2", pady=16)
        offline.pack()

        # Bottom links
        bottom = tk.Frame(self, bg=PANEL_LILAC)
        bottom.place(relx=1.0, rely=1.0, anchor="se", x=-24, y=-14)
        for txt in ["Privacy Policy", "Security", "Support"]:
            tk.Label(bottom, text=txt, bg=PANEL_LILAC, fg=TEXT_GRAY,
                     font=self.small_font).pack(side="left", padx=10)

    def _on_sign_in(self):
        email = self.email_field.get_value()
        password = self.password_field.get_value()
        print(f"Sign In clicked -> email: {email!r}, password length: {len(password)}")


if __name__ == "__main__":
    app = FinAuditProLogin()
    app.mainloop()