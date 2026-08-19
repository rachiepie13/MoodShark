# DPI-awareness fix: this MUST run before the first Tk/CTk window is
# created in the process. When quiz.py is launched on its own (instead of
# via login.py), QuizPage is the first window created — if the process
# hasn't been marked DPI-aware yet at that point, Windows can render the
# whole interface at a smaller, unscaled size. Doing this here, before the
# customtkinter import even fires its own internal DPI calls, makes the
# window render at a consistent size no matter which script starts it.
import sys
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import math
import customtkinter as ctk
from PIL import Image
from db import users_collection
from quiz_data import QUESTIONS, PERSONALITY_DESCRIPTIONS, calculate_scores, get_result_summary

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Same palette as login.py / register.py — sky blue background, white
# cards, yellow for the main actions, sky blue for secondary accents.
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

# Every screen sizes itself to what it actually needs. Question/shark
# screens use the compact width below; the result screen gets its own,
# wider size (see RESULT_CARD_W / RESULT_CARD_MAX) since it has to fit
# two match cards side by side plus a 10-row breakdown — the old shared
# 760px width made that section feel cramped and forced it to scroll
# more than it needed to.
WINDOW_W = 880
CARD_W = 760
STAGE_MARGIN = WINDOW_W - CARD_W  # 120 total = 60px top/bottom, 60px sides
SHARK_CARD_H = 440

RESULT_CARD_W = CARD_W
RESULT_CARD_MAX = 880
RESULT_CARD_MIN = 880


class QuizPage(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title("MoodShark - Personality Quiz")
        self.geometry(f"{WINDOW_W}x{SHARK_CARD_H + STAGE_MARGIN}")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.current_question = 0
        self.answers = []
        self._shark_animation_running = False

        self.card = ctk.CTkFrame(self, width=CARD_W, height=SHARK_CARD_H, corner_radius=24, fg_color=CARD)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        self.show_shark_screen(
            message="Something's circling. Might as well find out what it wants.",
            button_text="START QUIZ",
            on_continue=self.show_question
        )

    # ------------------------------------------------------------------
    # Resizes both the window and the card together. card_w defaults to
    # the standard compact width; the result screen passes RESULT_CARD_W
    # to get its own wider stage.
    # ------------------------------------------------------------------
    def _resize_stage(self, card_h, card_w=CARD_W):
        window_w = card_w + STAGE_MARGIN
        window_h = card_h + STAGE_MARGIN
        max_window_h = self.winfo_screenheight() - 100  # leave room for menu bar + dock
        window_h = min(window_h, max_window_h)
        card_h = window_h - STAGE_MARGIN
        self.geometry(f"{window_w}x{window_h}")
        self.card.configure(width=card_w, height=card_h)

    # ------------------------------------------------------------------
    # Small rounded panel helper, used anywhere we need a soft light-blue
    # block with an optional title above it (the breakdown section uses
    # this too).
    # ------------------------------------------------------------------
    def _panel(self, parent, title, accent=BLUE, fg_color=ROW_BG, pady=(0, 14)):
        frame = ctk.CTkFrame(parent, fg_color=fg_color, corner_radius=16)
        frame.pack(fill="x", pady=pady)

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        if title:
            ctk.CTkLabel(
                body, text=title, font=("Arial", 11, "bold"),
                text_color=accent
            ).pack(anchor="w", pady=(0, 6))
        return body

    # ------------------------------------------------------------------
    # Bordered section with a colored titlebar and decorative dots,
    # modernized from the old retro pixel-window style with rounded
    # corners to match the current aesthetic.
    # ------------------------------------------------------------------
    def _pixel_window(self, parent, title, accent=BLUE, pady=(0, 16)):
        frame = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14, border_width=2, border_color=accent)
        frame.pack(fill="x", pady=pady)

        titlebar = ctk.CTkFrame(frame, height=32, fg_color=accent, corner_radius=14)
        titlebar.pack(side="top", fill="x")
        titlebar.pack_propagate(False)
        ctk.CTkLabel(titlebar, text=title, font=("Consolas", 11, "bold"), text_color="#111111").pack(side="left", padx=12)

        dots = ctk.CTkFrame(titlebar, fg_color=accent)
        dots.pack(side="right", padx=10)
        ctk.CTkFrame(dots, width=8, height=8, fg_color="#111111", corner_radius=4).pack(side="left", padx=2)
        ctk.CTkFrame(dots, width=8, height=8, fg_color="#111111", corner_radius=4).pack(side="left", padx=2)

        body = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=0)
        body.pack(side="top", fill="both", expand=True, padx=18, pady=18)
        return body

    # ------------------------------------------------------------------
    # Shark fin circling screen.
    # ------------------------------------------------------------------
    def show_shark_screen(self, message, button_text, on_continue):
        self._resize_stage(SHARK_CARD_H)
        self._shark_animation_running = False
        for widget in self.card.winfo_children():
            widget.destroy()

        centered = ctk.CTkFrame(self.card, fg_color="transparent")
        centered.pack(expand=True)

        stage = ctk.CTkFrame(centered, width=640, height=200, fg_color=ROW_BG, corner_radius=18)
        stage.pack(pady=(0, 26))
        stage.pack_propagate(False)

        try:
            shark_img = ctk.CTkImage(
                light_image=Image.open("assets/shark_fin.png"),
                dark_image=Image.open("assets/shark_fin.png"),
                size=(40, 40)
            )
            shark_label = ctk.CTkLabel(stage, image=shark_img, text="")
            shark_label.image = shark_img
        except Exception:
            shark_label = ctk.CTkLabel(
                stage, text="", width=28, height=28,
                fg_color=BLUE, corner_radius=14
            )

        shark_label.place(x=300, y=80)

        center_x, center_y = 320, 100
        radius = 70
        angle = {"value": 0}
        self._shark_animation_running = True

        def animate():
            if not self._shark_animation_running:
                return
            angle["value"] += 6
            rad = math.radians(angle["value"])
            x_pos = center_x + radius * math.cos(rad) - 20
            y_pos = center_y + radius * math.sin(rad) - 20
            try:
                shark_label.place(x=x_pos, y=y_pos)
            except Exception:
                return
            self.after(40, animate)

        animate()

        ctk.CTkLabel(
            centered, text=message, font=("Arial", 15, "bold"), text_color=TEXT_DARK,
            wraplength=620, width=620, justify="center"
        ).pack(pady=(0, 26))

        def handle_continue():
            self._shark_animation_running = False
            self.after(10, on_continue)

        ctk.CTkButton(
            centered, text=button_text, width=240, height=46, corner_radius=12,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            font=("Arial", 14, "bold"), command=handle_continue
        ).pack()

    # ------------------------------------------------------------------
    # Question flow — card height is calculated from how many options
    # this specific question actually has, so a 4-option question isn't
    # stretched into empty space and a 6-option one doesn't get clipped.
    # ------------------------------------------------------------------
    def show_question(self):
        q_index = self.current_question
        q_data = QUESTIONS[q_index]

        self._shark_animation_running = False
        for widget in self.card.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 0))

        ctk.CTkLabel(
            header, text=f"QUESTION {q_index + 1} / {len(QUESTIONS)}",
            font=("Arial", 12, "bold"), text_color=BLUE
        ).pack(anchor="w")

        progress_bg = ctk.CTkFrame(self.card, height=8, fg_color=ROW_BG, corner_radius=4)
        progress_bg.pack(fill="x", padx=32, pady=(8, 22))
        progress_bg.pack_propagate(False)
        fill_frac = q_index / len(QUESTIONS)
        fill_width = max(6, int(696 * fill_frac))
        ctk.CTkFrame(progress_bg, width=fill_width, height=8, fg_color=YELLOW, corner_radius=4).place(x=0, y=0)

        ctk.CTkLabel(
            self.card, text=q_data["question"], font=("Arial", 21, "bold"),
            text_color=TEXT_DARK, wraplength=680, width=680, justify="center"
        ).pack(padx=32, pady=(0, 18))

        options_container = ctk.CTkFrame(self.card, fg_color="transparent")
        options_container.pack(fill="both", expand=True, padx=32)

        last_row = None
        for letter, text, scores in q_data["options"]:
            last_row = self._build_option_row(options_container, letter, text, scores)

        self.update_idletasks()
        content_bottom = options_container.winfo_y() + last_row.winfo_y() + last_row.winfo_height()
        card_h = max(300, content_bottom + 32)
        self._resize_stage(card_h)

    def _build_option_row(self, parent, letter, text, scores):
        row = ctk.CTkFrame(parent, fg_color=ROW_BG, corner_radius=12)
        row.pack(fill="x", pady=5)

        letter_lbl = ctk.CTkLabel(row, text=letter, font=("Arial", 13, "bold"), text_color=BLUE, width=26, anchor="n")
        letter_lbl.pack(side="left", padx=(16, 4), pady=12, anchor="n")

        text_lbl = ctk.CTkLabel(
            row, text=text, font=("Arial", 13), text_color=TEXT_DARK,
            wraplength=580, width=580, justify="left", anchor="w"
        )
        text_lbl.pack(side="left", fill="x", expand=True, padx=(0, 16), pady=12)

        widgets = [row, letter_lbl, text_lbl]

        def on_click(event=None):
            self.handle_answer(scores)

        def on_enter(event=None):
            row.configure(fg_color=ROW_HOVER)
            letter_lbl.configure(text_color="#0B1220")
            text_lbl.configure(text_color="#0B1220")

        def on_leave(event=None):
            row.configure(fg_color=ROW_BG)
            letter_lbl.configure(text_color=BLUE)
            text_lbl.configure(text_color=TEXT_DARK)

        for w in widgets:
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        return row

    def handle_answer(self, scores):
        self.answers.append(scores)
        self.current_question += 1

        if self.current_question < len(QUESTIONS):
            self.show_question()
        else:
            self.show_shark_screen(
                message="The shark has caught your scent. Time to see what it discovered.",
                button_text="REVEAL RESULT",
                on_continue=self.show_result
            )

    # ------------------------------------------------------------------
    # Result screen — now gets its own wider stage (RESULT_CARD_W) and a
    # taller cap (RESULT_CARD_MAX) than the question/shark screens, so
    # the two match cards and full breakdown have real room to breathe
    # instead of everything getting squeezed into the same 760px box.
    # ------------------------------------------------------------------
    def show_result(self):
        try:
            self._build_result_screen()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._resize_stage(RESULT_CARD_MAX, card_w=RESULT_CARD_W)
            for widget in self.card.winfo_children():
                widget.destroy()
            ctk.CTkLabel(
                self.card, text=f"Something broke building your result:\n{e}",
                font=("Arial", 12), text_color=RED, wraplength=680, width=680, justify="center"
            ).pack(pady=200)

    def _build_result_screen(self):
        self._shark_animation_running = False
        for widget in self.card.winfo_children():
            widget.destroy()

        raw_totals, percentages = calculate_scores(self.answers)
        summary = get_result_summary(percentages)
        top_trait = summary["traits"][0]
        top_pct = summary["percentages"][top_trait]

        scroll = ctk.CTkScrollableFrame(self.card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # ── headline section ──
        headline_body = self._pixel_window(scroll, "RESULT.EXE", accent=YELLOW)
        ctk.CTkLabel(headline_body, text="\U0001F988 SCAN COMPLETE", font=("Consolas", 10, "bold"), text_color=MUTED).pack(anchor="w")

        if summary["type"] == "mix":
            second_trait = summary["traits"][1]
            second_pct = summary["percentages"][second_trait]
            ctk.CTkLabel(
                headline_body,
                text=f"YOU'RE A MIX OF A {top_trait.upper()} & {second_trait.upper()}",
                font=("Arial", 22, "bold"), text_color=TEXT_DARK, wraplength=620, justify="left"
            ).pack(anchor="w", pady=(6, 0))
            ctk.CTkLabel(
                headline_body,
                text=f"{top_trait} {top_pct}%  •  {second_trait} {second_pct}%",
                font=("Consolas", 12), text_color=BLUE
            ).pack(anchor="w", pady=(6, 0))
        else:
            ctk.CTkLabel(
                headline_body,
                text=f"YOU ARE A {top_trait.upper()}",
                font=("Arial", 22, "bold"), text_color=TEXT_DARK, wraplength=620, justify="left"
            ).pack(anchor="w", pady=(6, 0))

        # ── match cards ──
        if summary["type"] == "mix":
            second_trait = summary["traits"][1]
            second_pct = summary["percentages"][second_trait]
            cards_row = ctk.CTkFrame(scroll, fg_color="transparent")
            cards_row.pack(fill="x", pady=(0, 12))
            self._build_match_card(cards_row, "#1 BEST MATCH", top_trait, top_pct, accent=YELLOW, side="left", pad=(0, 10))
            self._build_match_card(cards_row, "#2 BEST MATCH", second_trait, second_pct, accent=BLUE, side="left", pad=(10, 0))
        else:
            self._build_match_card(scroll, "YOUR MATCH", top_trait, top_pct, accent=YELLOW, side="top", full_width=True)

        # ── description section ──
        desc = PERSONALITY_DESCRIPTIONS[top_trait]
        desc_body = self._pixel_window(scroll, f"{top_trait.upper()}.EXE", accent=BLUE)
        ctk.CTkLabel(
            desc_body, text=desc["text"], font=("Arial", 13), text_color=TEXT_DARK,
            wraplength=620, justify="left"
        ).pack(anchor="w")
        ctk.CTkLabel(
            desc_body, text="You might like: " + desc["likes"], font=("Arial", 12, "italic"),
            text_color=MUTED, wraplength=620, justify="left"
        ).pack(anchor="w", pady=(10, 0))

        # ── breakdown section ──
        breakdown_body = self._pixel_window(scroll, "BREAKDOWN.EXE", accent=YELLOW)
        for trait, pct in summary["ranked"]:
            self._build_breakdown_row(breakdown_body, trait, pct)

        self.save_status = ctk.CTkLabel(scroll, text="", font=("Arial", 11), text_color=MUTED)
        self.save_status.pack(pady=(12, 0))

        continue_btn = ctk.CTkButton(
            scroll, text="CONTINUE TO MOODSHARK", width=320, height=48, corner_radius=12,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            font=("Arial", 13, "bold"), command=self.finish_quiz
        )
        continue_btn.pack(pady=(16, 40))

        self._resize_stage(RESULT_CARD_MAX, card_w=RESULT_CARD_W)

        self.personality_result = {
            "raw_totals": raw_totals,
            "percentages": percentages,
            "top_traits": summary["traits"]
        }
        try:
            users_collection.update_one(
                {"username": self.username},
                {"$set": {"quiz_done": True, "personality": self.personality_result}}
            )
        except Exception as e:
            print(f"Warning: could not save personality result to MongoDB: {e}")
            self.save_status.configure(
                text="\u26A0 Result couldn't be saved to your account — check your connection.",
                text_color=RED
            )

    def _build_match_card(self, parent, label, trait, pct, accent, side="left", pad=(0, 0), full_width=False):
        desc = PERSONALITY_DESCRIPTIONS[trait]
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=18, border_width=2, border_color=accent)
        if full_width:
            card.pack(fill="x")
        else:
            card.pack(side=side, fill="both", expand=True, padx=pad)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=26, pady=24)

        label_color = "#B8A900" if accent == YELLOW else accent
        ctk.CTkLabel(inner, text=label, font=("Arial", 11, "bold"), text_color=label_color).pack(anchor="w")
        ctk.CTkLabel(inner, text=trait, font=("Arial", 24, "bold"), text_color=TEXT_DARK).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(inner, text=f"{pct}% match", font=("Arial", 12, "bold"), text_color=MUTED).pack(anchor="w", pady=(0, 12))

        # width must match wraplength — CTkLabel draws onto an internal
        # canvas sized from `width`, separate from where `wraplength`
        # wraps the text. Without width, the canvas can end up narrower
        # than the wrapped text needs, clipping it on the left.
        # These widths are bigger now to match the wider result card:
        # two side-by-side cards on a 940px stage get ~360px each of
        # usable text width instead of the old ~290px on a 760px stage.
        desc_w = 300 if not full_width else 650
        ctk.CTkLabel(
            inner, text=desc["text"], font=("Arial", 13), text_color=TEXT_DARK,
            wraplength=desc_w, width=desc_w, justify="left"
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    # One row in the "full breakdown" list. Only the trait NAME opens the
    # popup now — the bar and percentage are visual only, not click targets.
    # ------------------------------------------------------------------
    def _build_breakdown_row(self, parent, trait, pct):
        row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8)
        row.pack(fill="x", pady=3)

        name_lbl = ctk.CTkLabel(row, text=trait, width=100, font=("Arial", 11, "bold"), text_color=BLUE, anchor="w")
        name_lbl.pack(side="left")

        bar_bg = ctk.CTkFrame(row, height=10, fg_color="#FFFFFF", corner_radius=5)
        bar_bg.pack(side="left", fill="x", expand=True, padx=8)
        bar_bg.pack_propagate(False)
        bar_width = max(4, int(560 * (pct / 100)))
        ctk.CTkFrame(bar_bg, width=bar_width, height=10, fg_color=BLUE, corner_radius=5).place(x=0, y=0)

        ctk.CTkLabel(row, text=f"{pct}%", font=("Arial", 11, "bold"), text_color=MUTED, width=44).pack(side="left")

        def open_popup(event=None, t=trait):
            self._show_personality_popup(t)

        def on_enter(event=None):
            name_lbl.configure(text_color="#0B1220")

        def on_leave(event=None):
            name_lbl.configure(text_color=BLUE)

        name_lbl.configure(cursor="hand2")
        name_lbl.bind("<Button-1>", open_popup)
        name_lbl.bind("<Enter>", on_enter)
        name_lbl.bind("<Leave>", on_leave)

    # ------------------------------------------------------------------
    # Personality detail popup.
    # ------------------------------------------------------------------
    def _show_personality_popup(self, trait):
        desc = PERSONALITY_DESCRIPTIONS[trait]

        popup = ctk.CTkToplevel(self)
        popup.title(trait)
        popup.resizable(False, False)
        popup.configure(fg_color=BG)

        popup.withdraw()

        w, h = 460, 340
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        popup.geometry(f"{w}x{h}+{x}+{y}")

        card = ctk.CTkFrame(popup, fg_color=CARD, corner_radius=20, border_width=2, border_color=YELLOW)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        header = ctk.CTkFrame(card, fg_color=ROW_BG, corner_radius=14)
        header.pack(fill="x", padx=18, pady=(18, 0))

        header_inner = ctk.CTkFrame(header, fg_color="transparent")
        header_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            header_inner, text="PERSONALITY", font=("Arial", 10, "bold"), text_color=MUTED
        ).pack(anchor="w")
        ctk.CTkLabel(
            header_inner, text=trait, font=("Arial", 24, "bold"), text_color=TEXT_DARK
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            card, text=desc["text"], font=("Arial", 13), text_color=TEXT_DARK,
            wraplength=390, width=390, justify="left", anchor="w"
        ).pack(fill="x", padx=18, pady=(16, 8))

        ctk.CTkButton(
            card, text="Close", width=120, height=38, corner_radius=12,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            font=("Arial", 13, "bold"), command=popup.destroy
        ).pack(pady=(6, 18))

        popup.update_idletasks()

        def reveal():
            popup.attributes("-topmost", True)
            popup.deiconify()
            popup.lift()
            popup.focus_force()
            popup.grab_set()

        popup.after(30, reveal)

    def finish_quiz(self):
        from mood_checkin import MoodCheckinPage
        username = self.username
        self.destroy()
        MoodCheckinPage(username=username).mainloop()


if __name__ == "__main__":
    QuizPage(username="test_user").mainloop()
