"""
home.py

The MoodShark home/dashboard screen. Shown after:
  - a brand-new user finishes the mood check-in (via quiz.py -> mood_checkin.py -> here)
  - a returning user finishes or skips the mood check-in (via mood_checkin.py -> here)

This file only DISPLAYS data. All scoring/caching logic lives in
recommendations.py — this file never talks to score_* functions directly.

Exposes: HomePage(username)
"""

import math
import customtkinter as ctk
import tkinter as tk
from PIL import Image

from recommendations import get_recommendations, CATEGORY_CONFIG

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#111111"
CARD = "#1B1B1B"
YELLOW = "#E8FF2A"
BLUE = "#2AC7FF"
WHITE = "#FFFFFF"
GRAY = "#A0A0A0"
RED = "#FF5C5C"
GREEN = "#6BFF8F"
ROW_BG = "#3A3D40"

CARD_W = 230
CARD_H = 190
CARD_PADX = 10
CARD_PADY = 10

# hover target size: grows the card while shrinking its own padding by the
# same amount, so its total reserved footprint in the row never changes and
# neighboring cards never shift. Height is capped so it never exceeds the
# row's fixed height (210 = CARD_H + 2*CARD_PADY) and gets clipped.
CARD_HOVER_W = 246
CARD_HOVER_PADX = 2
CARD_HOVER_H = 204
CARD_HOVER_PADY = 3

DIM_BG = "#242628"


class HomePage(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title("MoodShark - Home")
        self.geometry("1200x780")
        self.minsize(1000, 650)
        self.configure(fg_color=BG)

        self.data = get_recommendations(username)

        if not self.data:
            ctk.CTkLabel(
                self, text="Couldn't load your MoodShark profile.\nCheck your connection and try again.",
                font=("Consolas", 14), text_color=RED, justify="center"
            ).pack(pady=320)
            return

        self._build_topbar()
        self._build_wave_band()
        self._build_body()

    # ------------------------------------------------------------------
    # Retro pixel-window helper (same visual language as quiz.py / mood_checkin.py)
    # ------------------------------------------------------------------
    def _pixel_window(self, parent, title, border_color=YELLOW, pady=(0, 24)):
        frame = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=0, border_width=2, border_color=border_color)
        frame.pack(fill="x", pady=pady)

        titlebar = ctk.CTkFrame(frame, height=26, fg_color=border_color, corner_radius=0)
        titlebar.pack(side="top", fill="x")
        titlebar.pack_propagate(False)
        ctk.CTkLabel(titlebar, text=title, font=("Consolas", 11, "bold"), text_color="#111111").pack(side="left", padx=10)
        dots = ctk.CTkFrame(titlebar, fg_color=border_color)
        dots.pack(side="right", padx=8)
        ctk.CTkFrame(dots, width=8, height=8, fg_color="#111111").pack(side="left", padx=2)
        ctk.CTkFrame(dots, width=8, height=8, fg_color="#111111").pack(side="left", padx=2)

        body = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=0)
        body.pack(side="top", fill="both", expand=True, padx=18, pady=18)
        return body

    # ------------------------------------------------------------------
    # Top bar (stays fixed while the body below scrolls)
    # ------------------------------------------------------------------
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, height=64, fg_color=CARD, corner_radius=0)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        try:
            logo_img = ctk.CTkImage(
                light_image=Image.open("assets/logo.png"),
                dark_image=Image.open("assets/logo.png"),
                size=(140, 56)
            )
            logo_label = ctk.CTkLabel(bar, image=logo_img, text="")
            logo_label.image = logo_img
            logo_label.pack(side="left", padx=20)
        except Exception:
            ctk.CTkLabel(bar, text="MOODSHARK", font=("Arial", 18, "bold"), text_color=YELLOW).pack(side="left", padx=20)

        btns = ctk.CTkFrame(bar, fg_color="transparent")
        btns.pack(side="right", padx=20)

        checkin_label = "RETAKE MOOD CHECK-IN" if self.data["todays_moods"] else "DAILY MOOD CHECK-IN"
        ctk.CTkButton(
            btns, text=checkin_label, width=210, height=36,
            fg_color=BLUE, hover_color="#1BA6DB", text_color="#111111",
            command=self._open_mood_checkin
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btns, text="RETAKE QUIZ", width=150, height=36,
            fg_color=ROW_BG, hover_color="#4a4d50", text_color=WHITE,
            command=self._retake_quiz
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btns, text="LOG OUT", width=110, height=36,
            fg_color=ROW_BG, hover_color="#4a4d50", text_color=WHITE,
            command=self._logout
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Decorative wave band — sits between the top bar and the scrollable
    # content. Subtle nautical touch per the design brief (waves + shark
    # motif), purely visual, redraws itself if the window is resized.
    # ------------------------------------------------------------------
    def _build_wave_band(self):
        band = ctk.CTkFrame(self, height=54, fg_color=BG, corner_radius=0)
        band.pack(side="top", fill="x")
        band.pack_propagate(False)

        canvas = tk.Canvas(band, height=54, bg=BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        def draw(event=None):
            canvas.delete("wave")
            w = canvas.winfo_width()
            if w <= 1:
                return

            amplitude = 8
            wavelength = 90
            y_base = 26

            front = []
            for x in range(0, w + 10, 6):
                y = y_base + amplitude * math.sin((x / wavelength) * 2 * math.pi)
                front.extend([x, y])
            if len(front) >= 4:
                canvas.create_line(*front, fill="#1c3b45", width=2, smooth=True, tags="wave")

            back = []
            for x in range(0, w + 10, 6):
                y = y_base + 8 + (amplitude * 0.6) * math.sin((x / wavelength) * 2 * math.pi + 1.6)
                back.extend([x, y])
            if len(back) >= 4:
                canvas.create_line(*back, fill="#142a30", width=2, smooth=True, tags="wave")

            canvas.create_text(24, 14, text="\u2726", fill=YELLOW, font=("Arial", 12), tags="wave")
            canvas.create_text(w - 24, 40, text="\u2605", fill=YELLOW, font=("Arial", 10), tags="wave")

        canvas.bind("<Configure>", draw)

        try:
            fin_img = ctk.CTkImage(
                light_image=Image.open("assets/shark_fin.png"),
                dark_image=Image.open("assets/shark_fin.png"),
                size=(30, 30)
            )
            fin_label = ctk.CTkLabel(band, image=fin_img, text="")
            fin_label.image = fin_img
            fin_label.place(relx=0.5, y=4, anchor="n")
        except Exception:
            pass  # no fin asset found — the wave line alone still reads fine

    def _open_mood_checkin(self):
        from mood_checkin import MoodCheckinPage
        username = self.username
        self.destroy()
        MoodCheckinPage(username=username).mainloop()

    def _retake_quiz(self):
        # Retaking overwrites personality/top_traits in quiz.py's own save
        # step. recommendations.py already checks the stored top_traits
        # against a fresh quiz result and force-refreshes automatically —
        # no changes needed there or in quiz.py for this to work correctly.
        from quiz import QuizPage
        username = self.username
        self.destroy()
        QuizPage(username=username).mainloop()

    def _logout(self):
        from login import LoginPage
        self.destroy()
        LoginPage().mainloop()

    # ------------------------------------------------------------------
    # Scrollable body
    # ------------------------------------------------------------------
    def _build_body(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # The page itself scrolls vertically by default. Each category row
        # below scrolls horizontally instead — _new_horizontal_row() swaps
        # the mouse wheel over to that row while hovering it, and this
        # handler is what restores normal page scrolling once you leave it.
        self._vertical_wheel = self._make_wheel_handler(self.scroll._parent_canvas, "vertical")
        self.bind_all("<MouseWheel>", self._vertical_wheel)

        self._build_header()
        self._build_today_section()
        self._build_personality_sections()

    def _make_wheel_handler(self, canvas, orientation):
        def on_wheel(event):
            if event.delta == 0:
                return "break"
            step = -1 if event.delta > 0 else 1
            if orientation == "horizontal":
                canvas.xview_scroll(step, "units")
            else:
                canvas.yview_scroll(step, "units")
            return "break"
        return on_wheel

    def _new_horizontal_row(self, parent, height=210):
        row = ctk.CTkScrollableFrame(parent, orientation="horizontal", height=height, fg_color="transparent")
        row.pack(fill="x")

        horizontal_wheel = self._make_wheel_handler(row._parent_canvas, "horizontal")
        row.bind("<Enter>", lambda e: self.bind_all("<MouseWheel>", horizontal_wheel))
        row.bind("<Leave>", lambda e: self.bind_all("<MouseWheel>", self._vertical_wheel))
        return row

    def _build_header(self):
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 26))

        name = self.data["user"].get("name") or self.username
        ctk.CTkLabel(header, text=f"HI, {name.upper()}", font=("Arial", 30, "bold"), text_color=WHITE).pack(anchor="w")

        top_traits = self.data["top_traits"]
        if top_traits:
            trait_text = " + ".join(t.upper() for t in top_traits)
            ctk.CTkLabel(header, text=trait_text, font=("Consolas", 16, "bold"), text_color=BLUE).pack(anchor="w", pady=(4, 0))

        ctk.CTkFrame(header, height=2, fg_color="#2a2a2a").pack(fill="x", pady=(16, 0))

    # ------------------------------------------------------------------
    # "BEST PICK FOR YOU TODAY" — mood-based, top 3, visually distinct
    # ------------------------------------------------------------------
    def _build_today_section(self):
        body = self._pixel_window(self.scroll, "TODAY'S SIGNAL", border_color=YELLOW, pady=(0, 30))
        ctk.CTkLabel(body, text="BEST PICK FOR YOU TODAY", font=("Arial", 20, "bold"), text_color=YELLOW).pack(anchor="w")

        if not self.data["todays_moods"]:
            ctk.CTkLabel(
                body, text="No mood check-in yet today — everything below is personality-only until you check in.",
                font=("Consolas", 11), text_color=GRAY, wraplength=900, justify="left"
            ).pack(anchor="w", pady=(10, 14))
            ctk.CTkButton(
                body, text="START TODAY'S CHECK-IN", width=240, height=38,
                fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
                command=self._open_mood_checkin
            ).pack(anchor="w")
            return

        mood_text = " + ".join(m.upper() for m in self.data["todays_moods"])
        ctk.CTkLabel(body, text=f"Based on today's mood: {mood_text}", font=("Consolas", 11), text_color=GRAY).pack(anchor="w", pady=(6, 16))

        any_items = False
        for key, cfg in CATEGORY_CONFIG.items():
            items = self.data["mood"][key]
            if not items:
                continue
            any_items = True
            ctk.CTkLabel(body, text=cfg["label"].upper(), font=("Consolas", 11, "bold"), text_color=BLUE).pack(anchor="w", pady=(12, 4))
            row = self._new_horizontal_row(body)
            for item in items:
                self._item_card(row, item, key)

        if not any_items:
            ctk.CTkLabel(body, text="Nothing matched today's mood strongly enough yet.", font=("Consolas", 11), text_color=GRAY).pack(anchor="w")

    # ------------------------------------------------------------------
    # "BEST PICKS FOR YOU" — personality-based, top 10, one row per category
    # ------------------------------------------------------------------
    def _build_personality_sections(self):
        ctk.CTkLabel(self.scroll, text="BEST PICKS FOR YOU", font=("Arial", 22, "bold"), text_color=WHITE).pack(anchor="w", pady=(6, 4))
        ctk.CTkLabel(self.scroll, text="Based on your personality", font=("Consolas", 11), text_color=GRAY).pack(anchor="w", pady=(0, 18))

        for key, cfg in CATEGORY_CONFIG.items():
            items = self.data["personality"][key]
            body = self._pixel_window(self.scroll, f"{cfg['label'].upper()}.EXE", border_color=BLUE, pady=(0, 20))

            if not items:
                ctk.CTkLabel(body, text="Nothing here yet.", font=("Consolas", 11), text_color=GRAY).pack(anchor="w")
                continue

            row = self._new_horizontal_row(body)
            for item in items:
                self._item_card(row, item, key)

    # ------------------------------------------------------------------
    # A single media/activity card — metadata shown depends on category.
    # Packed directly into the row at a fixed size (same structure that
    # was already proven to render correctly). Hover is border + color +
    # lift only — no size animation, since that fought with how the
    # horizontally-scrolling row handles place()-based children.
    # ------------------------------------------------------------------
    def _item_card(self, parent, item, category_key):
        card = ctk.CTkFrame(parent, width=CARD_W, height=CARD_H, fg_color=ROW_BG, corner_radius=8)
        card.pack(side="left", padx=CARD_PADX, pady=CARD_PADY)
        card.pack_propagate(False)

        card._row = parent
        card._anim_job = None
        card._cur_w, card._cur_h = CARD_W, CARD_H
        card._cur_padx, card._cur_pady = CARD_PADX, CARD_PADY
        if not hasattr(parent, "_cards"):
            parent._cards = []
        parent._cards.append(card)

        hover_targets = [card]

        title = item.get("title", "Untitled")
        title_lbl = ctk.CTkLabel(
            card, text=title, font=("Arial", 14, "bold"), text_color=WHITE,
            wraplength=200, justify="left", anchor="w"
        )
        title_lbl.pack(anchor="w", padx=12, pady=(12, 2))
        hover_targets.append(title_lbl)

        if category_key == "music":
            artist = item.get("artist", "")
            if artist:
                artist_lbl = ctk.CTkLabel(card, text=artist, font=("Consolas", 11), text_color=BLUE, anchor="w")
                artist_lbl.pack(anchor="w", padx=12)
                hover_targets.append(artist_lbl)
            genre = item.get("genre", "")
            if genre:
                genre_lbl = ctk.CTkLabel(card, text=genre, font=("Consolas", 10), text_color=GRAY, anchor="w")
                genre_lbl.pack(anchor="w", padx=12, pady=(2, 4))
                hover_targets.append(genre_lbl)
        elif category_key == "activities":
            popup = item.get("popupMessage", "")
            if popup:
                popup_lbl = ctk.CTkLabel(
                    card, text=popup, font=("Arial", 11, "italic"), text_color=YELLOW,
                    wraplength=200, justify="left", anchor="w"
                )
                popup_lbl.pack(anchor="w", padx=12, pady=(2, 4))
                hover_targets.append(popup_lbl)
        else:
            genre = item.get("genre", "")
            if genre:
                genre_lbl = ctk.CTkLabel(card, text=genre.upper(), font=("Consolas", 10, "bold"), text_color=BLUE, anchor="w")
                genre_lbl.pack(anchor="w", padx=12, pady=(2, 4))
                hover_targets.append(genre_lbl)

        desc = item.get("description", "")
        if desc:
            desc_lbl = ctk.CTkLabel(
                card, text=desc, font=("Arial", 11), text_color=GRAY,
                wraplength=200, justify="left", anchor="nw"
            )
            desc_lbl.pack(anchor="w", padx=12, pady=(0, 10), fill="both", expand=True)
            hover_targets.append(desc_lbl)

        # bind every child too, not just the card frame — a debounced leave
        # check (below) is what actually stops this from flickering when the
        # mouse crosses from one child label to another inside the card
        for widget in hover_targets:
            widget.bind("<Enter>", lambda e, c=card: self._on_card_enter(c))
            widget.bind("<Leave>", lambda e, c=card: self._on_card_leave(c))

        return card

    def _on_card_enter(self, card):
        if card._anim_job:
            self.after_cancel(card._anim_job)
            card._anim_job = None

        if getattr(card, "_hovering", False):
            return  # already grown — this is just a re-trigger from a child widget

        card._hovering = True
        card.lift()
        card.configure(border_width=2, border_color=BLUE, fg_color="#454850")
        self._animate_card(card, CARD_HOVER_W, CARD_HOVER_H, CARD_HOVER_PADX, CARD_HOVER_PADY)
        self._dim_siblings(card, True)

    def _on_card_leave(self, card):
        # the mouse might have just crossed from one child widget to another
        # still inside this same card, which fires Leave/Enter instantly and
        # would otherwise make the card snap back and forth. Wait a beat and
        # check where the pointer actually is before shrinking anything.
        def check_leave():
            x, y = card.winfo_pointerxy()
            widget_under = card.winfo_containing(x, y)
            if widget_under is not None and self._is_descendant(widget_under, card):
                return  # still inside the card somewhere — not a real leave

            card._hovering = False
            if card._anim_job:
                self.after_cancel(card._anim_job)
                card._anim_job = None
            card.configure(border_width=0, fg_color=ROW_BG)
            self._animate_card(card, CARD_W, CARD_H, CARD_PADX, CARD_PADY)
            self._dim_siblings(card, False)

        card.after(30, check_leave)

    def _is_descendant(self, widget, ancestor):
        w = widget
        while w is not None:
            if w == ancestor:
                return True
            w = getattr(w, "master", None)
        return False

    def _animate_card(self, card, target_w, target_h, target_padx, target_pady, steps=8, step_ms=12):
        start_w, start_h = card._cur_w, card._cur_h
        start_padx, start_pady = card._cur_padx, card._cur_pady

        def step(i=0):
            t = i / steps
            eased = 1 - (1 - t) ** 2
            w = int(start_w + (target_w - start_w) * eased)
            h = int(start_h + (target_h - start_h) * eased)
            px = int(start_padx + (target_padx - start_padx) * eased)
            py = int(start_pady + (target_pady - start_pady) * eased)

            card.configure(width=w, height=h)
            card.pack_configure(padx=px, pady=py)
            card._cur_w, card._cur_h = w, h
            card._cur_padx, card._cur_pady = px, py

            if i < steps:
                card._anim_job = self.after(step_ms, lambda: step(i + 1))
            else:
                card._anim_job = None

        step()

    def _dim_siblings(self, card, dim):
        for sibling in getattr(card._row, "_cards", []):
            if sibling is card:
                continue
            sibling.configure(fg_color=DIM_BG if dim else ROW_BG)


if __name__ == "__main__":
    test_username = input("Enter username: ").strip()
    HomePage(username=test_username).mainloop()