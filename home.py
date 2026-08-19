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
import queue
import re
import threading
import customtkinter as ctk
import tkinter as tk
from PIL import Image
import billboard_charts
import requests
from bs4 import BeautifulSoup

from recommendations import get_recommendations, CATEGORY_CONFIG

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Same palette as login.py / register.py / quiz.py — sky blue background,
# white cards, yellow for primary actions, sky blue for secondary accents.
# This is the one thing that's actually changed from page to page before:
# home.py used to run its own dark/neon theme that didn't match the rest
# of the app. Now every screen shares this palette.
BG = "#B1C8EF"
CARD = "#FFFFFF"
ROW_BG = "#D6ECFF"
ROW_HOVER = "#2AC7FF"
YELLOW = "#E8FF2A"
BLUE = "#2AC7FF"
TEXT_DARK = "#0B1220"
MUTED = "#5A7096"
RED = "#FF5C5C"
GREEN = "#6BFF8F"

# Bigger cards than before, per feedback that the old ones felt cramped.
CARD_W = 270
CARD_H = 230
CARD_PADX = 12
CARD_PADY = 12


class HomePage(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title("MoodShark - Home")
        self.geometry("1320x880")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        self.data = get_recommendations(username)

        if not self.data:
            ctk.CTkLabel(
                self, text="Couldn't load your MoodShark profile.\nCheck your connection and try again.",
                font=("Arial", 14, "bold"), text_color=RED, justify="center"
            ).pack(pady=320)
            return

        self._build_topbar()
        self._build_wave_band()
        self._build_body()

    # ------------------------------------------------------------------
    # Clean rounded panel — same visual language as quiz.py's _panel /
    # match cards. Replaces the old dark "pixel window" titlebar look.
    # ------------------------------------------------------------------
    def _panel(self, parent, title, accent=BLUE, pady=(0, 24)):
        frame = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=20, border_width=2, border_color=accent)
        frame.pack(fill="x", pady=pady)

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=26, pady=22)

        if title:
            label_color = "#B8A900" if accent == YELLOW else accent
            ctk.CTkLabel(
                body, text=title, font=("Arial", 12, "bold"), text_color=label_color
            ).pack(anchor="w", pady=(0, 12))
        return body

    # ------------------------------------------------------------------
    # Top bar — kept the logo, just gave it a bright card to sit on
    # instead of a dark one so it actually reads clearly.
    # ------------------------------------------------------------------
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, height=76, fg_color=CARD, corner_radius=0)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        try:
            logo_img = ctk.CTkImage(
                light_image=Image.open("assets/logo.png"),
                dark_image=Image.open("assets/logo.png"),
                size=(450, 200)
            )
            logo_label = ctk.CTkLabel(bar, image=logo_img, text="")
            logo_label.image = logo_img
            logo_label.pack(side="left", padx=24)
        except Exception:
            ctk.CTkLabel(bar, text="MOODSHARK", font=("Arial", 20, "bold"), text_color=TEXT_DARK).pack(side="left", padx=24)

        btns = ctk.CTkFrame(bar, fg_color="transparent")
        btns.pack(side="right", padx=24)

        checkin_label = "RETAKE MOOD CHECK-IN" if self.data["todays_moods"] else "DAILY MOOD CHECK-IN"
        ctk.CTkButton(
            btns, text=checkin_label, width=220, height=40, corner_radius=10,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            font=("Arial", 12, "bold"), command=self._open_mood_checkin
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btns, text="RETAKE QUIZ", width=150, height=40, corner_radius=10,
            fg_color=BLUE, hover_color="#1BA6DB", text_color="#0B1220",
            font=("Arial", 12, "bold"), command=self._retake_quiz
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btns, text="LOG OUT", width=110, height=40, corner_radius=10,
            fg_color=ROW_BG, hover_color="#C3E4FF", text_color=TEXT_DARK,
            font=("Arial", 12, "bold"), command=self._logout
        ).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Decorative wave band — kept the shark fin and the wave/sparkle
    # motif exactly as designed, just recolored the lines so they read
    # against the light sky-blue background instead of a dark one.
    # ------------------------------------------------------------------
    def _build_wave_band(self):
        band = ctk.CTkFrame(self, height=58, fg_color=BG, corner_radius=0)
        band.pack(side="top", fill="x")
        band.pack_propagate(False)

        canvas = tk.Canvas(band, height=58, bg=BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        def draw(event=None):
            canvas.delete("wave")
            w = canvas.winfo_width()
            if w <= 1:
                return

            amplitude = 8
            wavelength = 90
            y_base = 28

            front = []
            for x in range(0, w + 10, 6):
                y = y_base + amplitude * math.sin((x / wavelength) * 2 * math.pi)
                front.extend([x, y])
            if len(front) >= 4:
                canvas.create_line(*front, fill="#FFFFFF", width=2, smooth=True, tags="wave")

            back = []
            for x in range(0, w + 10, 6):
                y = y_base + 8 + (amplitude * 0.6) * math.sin((x / wavelength) * 2 * math.pi + 1.6)
                back.extend([x, y])
            if len(back) >= 4:
                canvas.create_line(*back, fill="#D6ECFF", width=2, smooth=True, tags="wave")

            canvas.create_text(24, 16, text="\u2726", fill=YELLOW, font=("Arial", 13), tags="wave")
            canvas.create_text(w - 24, 42, text="\u2605", fill=YELLOW, font=("Arial", 11), tags="wave")

        canvas.bind("<Configure>", draw)

        try:
            fin_img = ctk.CTkImage(
                light_image=Image.open("assets/shark_fin.png"),
                dark_image=Image.open("assets/shark_fin.png"),
                size=(32, 32)
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
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG,
            scrollbar_button_color=BLUE, scrollbar_button_hover_color="#1BA6DB"
        )
        self.scroll.pack(fill="both", expand=True, padx=36, pady=24)

        # The page itself scrolls vertically by default. Each category row
        # below scrolls horizontally instead — _new_horizontal_row() swaps
        # the mouse wheel over to that row while hovering it, and this
        # handler is what restores normal page scrolling once you leave it.
        self._vertical_wheel = self._make_wheel_handler(self.scroll._parent_canvas, "vertical")
        self.bind_all("<MouseWheel>", self._vertical_wheel)

        self._build_header()
        self._build_today_section()
        self._build_personality_sections()
        self._build_trending_section()

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

    def _new_horizontal_row(self, parent, height=254):
        row = ctk.CTkScrollableFrame(
            parent, orientation="horizontal", height=height, fg_color="transparent",
            scrollbar_button_color=ROW_BG, scrollbar_button_hover_color=ROW_HOVER
        )
        row.pack(fill="x")

        horizontal_wheel = self._make_wheel_handler(row._parent_canvas, "horizontal")
        row.bind("<Enter>", lambda e: self.bind_all("<MouseWheel>", horizontal_wheel))
        row.bind("<Leave>", lambda e: self.bind_all("<MouseWheel>", self._vertical_wheel))
        return row

    def _build_header(self):
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 28))

        name = self.data["user"].get("name") or self.username
        ctk.CTkLabel(header, text=f"HI, {name.upper()}", font=("Arial", 32, "bold"), text_color=TEXT_DARK).pack(anchor="w")

        top_traits = self.data["top_traits"]
        if top_traits:
            trait_text = " + ".join(t.upper() for t in top_traits)
            ctk.CTkLabel(header, text=trait_text, font=("Arial", 16, "bold"), text_color=BLUE).pack(anchor="w", pady=(6, 0))

        ctk.CTkFrame(header, height=2, fg_color=ROW_BG).pack(fill="x", pady=(18, 0))

    # ------------------------------------------------------------------
    # "WEEKLY TRENDS" — Billboard Hot 100 + Apple Podcasts top charts,
    # both loaded in a background thread.
    # ------------------------------------------------------------------
    def _build_trending_section(self):
        self._trending_body = self._panel(self.scroll, "TRENDING THIS WEEK", accent=GREEN, pady=(0, 30))
        ctk.CTkLabel(self._trending_body, text="TRENDING THIS WEEK", font=("Arial", 20, "bold"), text_color=TEXT_DARK).pack(anchor="w")

        # --- music sub-section ---
        ctk.CTkLabel(self._trending_body, text="BILLBOARD HOT 100", font=("Consolas", 12, "bold"), text_color=BLUE).pack(anchor="w", pady=(14, 0))
        self._music_container = ctk.CTkFrame(self._trending_body, fg_color="transparent")
        self._music_container.pack(fill="x", pady=(6, 0))
        self._music_loading = ctk.CTkLabel(
            self._music_container, text="Fetching this week's Billboard Hot 100...",
            font=("Consolas", 11), text_color=MUTED
        )
        self._music_loading.pack(anchor="w")

        # --- podcast sub-section ---
        ctk.CTkLabel(self._trending_body, text="TOP PODCASTS", font=("Consolas", 12, "bold"), text_color=BLUE).pack(anchor="w", pady=(18, 0))
        self._podcast_container = ctk.CTkFrame(self._trending_body, fg_color="transparent")
        self._podcast_container.pack(fill="x", pady=(6, 0))
        self._podcast_loading = ctk.CTkLabel(
            self._podcast_container, text="Fetching top podcasts from Apple Podcasts...",
            font=("Consolas", 11), text_color=MUTED
        )
        self._podcast_loading.pack(anchor="w")

        self._music_queue = queue.Queue()
        self._podcast_queue = queue.Queue()
        threading.Thread(target=self._fetch_trending, daemon=True).start()
        self.after(500, self._poll_music)
        self.after(500, self._poll_podcast)

    def _fetch_trending(self):
        # Billboard Hot 100
        try:
            chart = billboard_charts.fetch_chart("hot-100")
            songs = [(e["Rank"], e["Song"], e["Artist"]) for e in chart[:10]]
            self._music_queue.put(("ok", songs))
        except Exception:
            self._music_queue.put(("err", None))

        # Apple Podcasts top charts
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/131.0.0.0 Safari/537.36",
            }
            resp = requests.get("https://podcasts.apple.com/us/charts", headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            lines = soup.get_text(separator="\n", strip=True).split("\n")
            podcasts = []
            for i, line in enumerate(lines):
                if line.strip() == "Top Shows":
                    j = i + 1
                    while j + 3 < len(lines) and lines[j].strip() != "Top Subscriber Shows":
                        name = lines[j].strip()
                        rank = lines[j + 1].strip()
                        publisher = lines[j + 3].strip()
                        if rank.isdigit():
                            podcasts.append((int(rank), name, publisher))
                        j += 4
                    break
            self._podcast_queue.put(("ok", podcasts[:10]))
        except Exception:
            self._podcast_queue.put(("err", None))

    def _poll_music(self):
        try:
            status, data = self._music_queue.get_nowait()
        except queue.Empty:
            self.after(500, self._poll_music)
            return
        if status == "ok":
            self._populate_music(data)
        else:
            if self._music_loading.winfo_exists():
                self._music_loading.configure(text="Couldn't load Billboard data.", text_color=RED)

    def _populate_music(self, songs):
        if self._music_loading.winfo_exists():
            self._music_loading.destroy()

        row = self._new_horizontal_row(self._music_container, height=180)

        for rank, title, artist in songs:
            card = ctk.CTkFrame(row, width=200, height=160, fg_color=ROW_BG, corner_radius=8)
            card.pack(side="left", padx=8, pady=10)
            card.pack_propagate(False)

            ctk.CTkLabel(
                card, text=f"#{rank}", font=("Arial", 22, "bold"), text_color=YELLOW, anchor="w"
            ).pack(anchor="w", padx=12, pady=(10, 0))

            ctk.CTkLabel(
                card, text=title, font=("Arial", 13, "bold"), text_color=TEXT_DARK,
                wraplength=170, justify="left", anchor="w"
            ).pack(anchor="w", padx=12, pady=(4, 0))

            ctk.CTkLabel(
                card, text=artist, font=("Consolas", 10), text_color=BLUE,
                wraplength=170, justify="left", anchor="w"
            ).pack(anchor="w", padx=12, pady=(2, 0))

    # ------------------------------------------------------------------
    # "BEST PICK FOR YOU TODAY" — mood-based, top 3, visually distinct
    # ------------------------------------------------------------------
    def _build_today_section(self):
        body = self._panel(self.scroll, "TODAY'S SIGNAL", accent=YELLOW, pady=(0, 30))
        ctk.CTkLabel(body, text="Best Pick For You Today", font=("Arial", 22, "bold"), text_color=TEXT_DARK).pack(anchor="w")

        if not self.data["todays_moods"]:
            ctk.CTkLabel(
                body, text="No mood check-in yet today — everything below is personality-only until you check in.",
                font=("Arial", 12), text_color=MUTED, wraplength=900, justify="left"
            ).pack(anchor="w", pady=(10, 16))
            ctk.CTkButton(
                body, text="START TODAY'S CHECK-IN", width=240, height=40, corner_radius=10,
                fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
                font=("Arial", 12, "bold"), command=self._open_mood_checkin
            ).pack(anchor="w")
            return

        mood_text = " + ".join(m.upper() for m in self.data["todays_moods"])
        ctk.CTkLabel(body, text=f"Based on today's mood: {mood_text}", font=("Arial", 12), text_color=MUTED).pack(anchor="w", pady=(6, 18))

        any_items = False
        for key, cfg in CATEGORY_CONFIG.items():
            items = self.data["mood"][key]
            if not items:
                continue
            any_items = True
            ctk.CTkLabel(body, text=cfg["label"].upper(), font=("Arial", 12, "bold"), text_color=BLUE).pack(anchor="w", pady=(14, 6))
            row = self._new_horizontal_row(body)
            for item in items:
                self._item_card(row, item, key)

        if not any_items:
            ctk.CTkLabel(body, text="Nothing matched today's mood strongly enough yet.", font=("Arial", 12), text_color=MUTED).pack(anchor="w")

    # ------------------------------------------------------------------
    # "BEST PICKS FOR YOU" — personality-based, top 10, one row per category
    # ------------------------------------------------------------------
    def _build_personality_sections(self):
        ctk.CTkLabel(self.scroll, text="Best Picks For You", font=("Arial", 24, "bold"), text_color=TEXT_DARK).pack(anchor="w", pady=(8, 4))
        ctk.CTkLabel(self.scroll, text="Based on your personality", font=("Arial", 12), text_color=MUTED).pack(anchor="w", pady=(0, 20))

        for key, cfg in CATEGORY_CONFIG.items():
            items = self.data["personality"][key]
            body = self._panel(self.scroll, cfg["label"].upper(), accent=BLUE, pady=(0, 22))

            if not items:
                ctk.CTkLabel(body, text="Nothing here yet.", font=("Arial", 12), text_color=MUTED).pack(anchor="w")
                continue

            row = self._new_horizontal_row(body)
            for item in items:
                self._item_card(row, item, key)

    # ------------------------------------------------------------------
    # A single media/activity card — bigger than before, and hover is
    # now a simple "light up" (white fill + blue border) instead of a
    # grow animation, per feedback that the resize effect felt off.
    # ------------------------------------------------------------------
    def _item_card(self, parent, item, category_key):
        card = ctk.CTkFrame(parent, width=CARD_W, height=CARD_H, fg_color=ROW_BG, corner_radius=14)
        card.pack(side="left", padx=CARD_PADX, pady=CARD_PADY)
        card.pack_propagate(False)
        card._leave_job = None

        hover_targets = [card]

        title = item.get("title", "Untitled")
        title_lbl = ctk.CTkLabel(
            card, text=title, font=("Arial", 15, "bold"), text_color=TEXT_DARK,
            wraplength=230, width=230, justify="left", anchor="w"
        )
        title_lbl.pack(anchor="w", padx=16, pady=(16, 4))
        hover_targets.append(title_lbl)

        if category_key == "music":
            artist = item.get("artist", "")
            if artist:
                artist_lbl = ctk.CTkLabel(card, text=artist, font=("Arial", 12, "bold"), text_color=BLUE, anchor="w")
                artist_lbl.pack(anchor="w", padx=16)
                hover_targets.append(artist_lbl)
            genre = item.get("genre", "")
            if genre:
                genre_lbl = ctk.CTkLabel(card, text=genre, font=("Arial", 11), text_color=MUTED, anchor="w")
                genre_lbl.pack(anchor="w", padx=16, pady=(2, 6))
                hover_targets.append(genre_lbl)
        elif category_key == "activities":
            popup = item.get("popupMessage", "")
            if popup:
                popup_lbl = ctk.CTkLabel(
                    card, text=popup, font=("Arial", 12, "italic"), text_color="#B8A900",
                    wraplength=230, width=230, justify="left", anchor="w"
                )
                popup_lbl.pack(anchor="w", padx=16, pady=(2, 6))
                hover_targets.append(popup_lbl)
        else:
            genre = item.get("genre", "")
            if genre:
                genre_lbl = ctk.CTkLabel(card, text=genre.upper(), font=("Arial", 11, "bold"), text_color=BLUE, anchor="w")
                genre_lbl.pack(anchor="w", padx=16, pady=(2, 6))
                hover_targets.append(genre_lbl)

        desc = item.get("description", "")
        if desc:
            desc_lbl = ctk.CTkLabel(
                card, text=desc, font=("Arial", 12), text_color=MUTED,
                wraplength=230, width=230, justify="left", anchor="nw"
            )
            desc_lbl.pack(anchor="w", padx=16, pady=(0, 14), fill="both", expand=True)
            hover_targets.append(desc_lbl)

        # bind every child too, not just the card frame, and debounce the
        # leave check so moving between labels inside the same card
        # doesn't flicker the highlight on and off.
        for widget in hover_targets:
            widget.bind("<Enter>", lambda e, c=card: self._on_card_enter(c))
            widget.bind("<Leave>", lambda e, c=card: self._on_card_leave(c))

        return card

    def _on_card_enter(self, card):
        if card._leave_job:
            card.after_cancel(card._leave_job)
            card._leave_job = None
        card.configure(fg_color=CARD, border_width=2, border_color=BLUE)

    def _on_card_leave(self, card):
        def check_leave():
            x, y = card.winfo_pointerxy()
            widget_under = card.winfo_containing(x, y)
            if widget_under is not None and self._is_descendant(widget_under, card):
                return  # still inside the card somewhere — not a real leave
            card.configure(fg_color=ROW_BG, border_width=0)

        card._leave_job = card.after(30, check_leave)

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

    # ------------------------------------------------------------------
    # Podcast trending (polled from queue like music)
    # ------------------------------------------------------------------
    def _poll_podcast(self):
        try:
            status, data = self._podcast_queue.get_nowait()
        except queue.Empty:
            self.after(500, self._poll_podcast)
            return
        if status == "ok":
            self._populate_podcast(data)
        else:
            if self._podcast_loading.winfo_exists():
                self._podcast_loading.configure(text="Couldn't load podcast data.", text_color=RED)

    def _populate_podcast(self, podcasts):
        if self._podcast_loading.winfo_exists():
            self._podcast_loading.destroy()

        if not podcasts:
            ctk.CTkLabel(self._podcast_container, text="No podcast data available.", font=("Consolas", 11), text_color=MUTED).pack(anchor="w")
            return

        row = self._new_horizontal_row(self._podcast_container, height=180)

        for rank, name, publisher in podcasts:
            card = ctk.CTkFrame(row, width=200, height=160, fg_color=ROW_BG, corner_radius=8)
            card.pack(side="left", padx=8, pady=10)
            card.pack_propagate(False)

            ctk.CTkLabel(
                card, text=f"#{rank}", font=("Arial", 22, "bold"), text_color=YELLOW, anchor="w"
            ).pack(anchor="w", padx=12, pady=(10, 0))

            ctk.CTkLabel(
                card, text=name, font=("Arial", 13, "bold"), text_color=TEXT_DARK,
                wraplength=170, justify="left", anchor="w"
            ).pack(anchor="w", padx=12, pady=(4, 0))

            ctk.CTkLabel(
                card, text=publisher, font=("Consolas", 10), text_color=BLUE,
                wraplength=170, justify="left", anchor="w"
            ).pack(anchor="w", padx=12, pady=(2, 0))


if __name__ == "__main__":
    test_username = input("Enter username: ").strip()
    HomePage(username=test_username).mainloop()