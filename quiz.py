import math
import customtkinter as ctk
from PIL import Image
from db import users_collection
from quiz_data import QUESTIONS, PERSONALITY_DESCRIPTIONS, calculate_scores, get_result_summary

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#111111"
CARD = "#1B1B1B"
YELLOW = "#E8FF2A"
SKY_BLUE = "#2AC7FF"
WHITE = "#FFFFFF"
GRAY = "#A0A0A0"
RED = "#FF5C5C"       # only ever used for the rare "couldn't save" warning
ROW_BG = "#242424"


class QuizPage(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title("MoodShark - Personality Quiz")
        # Bigger stage overall so the result screen has room to breathe
        # without needing to scroll.
        self.geometry("1150x960")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.current_question = 0
        self.answers = []
        self._shark_animation_running = False

        self.card = ctk.CTkFrame(self, width=980, height=880, corner_radius=20, fg_color=CARD)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        self.show_shark_screen(
            message="Something's circling. Might as well find out what it wants.",
            button_text="START QUIZ",
            on_continue=self.show_question
        )

    # ------------------------------------------------------------------
    # Small retro "pixel window" helper — a bordered box with a colored
    # titlebar, reused across the result screen to match the login/register
    # screens' aesthetic instead of showing raw text.
    # ------------------------------------------------------------------
    def _pixel_window(self, parent, title, border_color=YELLOW, pady=(0, 18)):
        frame = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=0, border_width=2, border_color=border_color)
        frame.pack(fill="x", pady=pady)

        titlebar = ctk.CTkFrame(frame, height=30, fg_color=border_color, corner_radius=0)
        titlebar.pack(side="top", fill="x")
        titlebar.pack_propagate(False)
        ctk.CTkLabel(titlebar, text=title, font=("Consolas", 12, "bold"), text_color="#111111").pack(side="left", padx=12)
        dots = ctk.CTkFrame(titlebar, fg_color=border_color)
        dots.pack(side="right", padx=10)
        ctk.CTkFrame(dots, width=8, height=8, fg_color="#111111").pack(side="left", padx=2)
        ctk.CTkFrame(dots, width=8, height=8, fg_color="#111111").pack(side="left", padx=2)

        body = ctk.CTkFrame(frame, fg_color=CARD, corner_radius=0)
        body.pack(side="top", fill="both", expand=True, padx=20, pady=20)
        return body

    # ------------------------------------------------------------------
    # Shark fin circling screen
    # ------------------------------------------------------------------
    def show_shark_screen(self, message, button_text, on_continue):
        self._shark_animation_running = False
        for widget in self.card.winfo_children():
            widget.destroy()

        stage = ctk.CTkFrame(self.card, width=900, height=280, fg_color="#151515", corner_radius=0)
        stage.pack(pady=(70, 30))
        stage.pack_propagate(False)

        try:
            shark_img = ctk.CTkImage(
                light_image=Image.open("assets/shark_fin.png"),
                dark_image=Image.open("assets/shark_fin.png"),
                size=(44, 44)
            )
            shark_label = ctk.CTkLabel(stage, image=shark_img, text="")
            shark_label.image = shark_img
        except Exception:
            # No emoji fallback — a simple filled circle keeps the retro,
            # icon-free look even if the fin asset is missing.
            shark_label = ctk.CTkLabel(
                stage, text="", width=30, height=30,
                fg_color=SKY_BLUE, corner_radius=15
            )

        shark_label.place(x=428, y=118)

        center_x, center_y = 450, 140
        radius = 90
        angle = {"value": 0}
        self._shark_animation_running = True

        def animate():
            if not self._shark_animation_running:
                return
            angle["value"] += 6
            rad = math.radians(angle["value"])
            x_pos = center_x + radius * math.cos(rad) - 22
            y_pos = center_y + radius * math.sin(rad) - 22
            try:
                shark_label.place(x=x_pos, y=y_pos)
            except Exception:
                return
            self.after(40, animate)

        animate()

        ctk.CTkLabel(
            self.card, text=message, font=("Consolas", 15, "bold"), text_color=YELLOW,
            wraplength=820, justify="center"
        ).pack(pady=(0, 30))

        def handle_continue():
            self._shark_animation_running = False
            self.after(10, on_continue)

        ctk.CTkButton(
            self.card, text=button_text, width=240, height=44,
            fg_color=SKY_BLUE, hover_color="#1BA6DB", text_color="#111111",
            command=handle_continue
        ).pack()

    # ------------------------------------------------------------------
    # Question flow — clickable "rows" instead of CTkButton, so long
    # option text wraps onto multiple lines instead of getting cut off,
    # and every row stays a consistent, aligned width.
    # ------------------------------------------------------------------
    def show_question(self):
        self._shark_animation_running = False
        for widget in self.card.winfo_children():
            widget.destroy()

        q_index = self.current_question
        q_data = QUESTIONS[q_index]

        ctk.CTkLabel(self.card, text=f"QUESTION {q_index + 1} / {len(QUESTIONS)}", font=("Consolas", 12, "bold"), text_color=SKY_BLUE).pack(pady=(28, 6))

        progress_bg = ctk.CTkFrame(self.card, width=880, height=8, fg_color="#333333", corner_radius=0)
        progress_bg.pack(pady=(0, 20))
        fill_width = int(880 * (q_index / len(QUESTIONS)))
        ctk.CTkFrame(progress_bg, width=fill_width, height=8, fg_color=YELLOW, corner_radius=0).place(x=0, y=0)

        ctk.CTkLabel(
            self.card, text=q_data["question"], font=("Arial", 20, "bold"),
            text_color=WHITE, wraplength=860, justify="center"
        ).pack(pady=(0, 20))

        options_container = ctk.CTkScrollableFrame(self.card, width=900, height=420, fg_color="transparent")
        options_container.pack(fill="both", expand=True, padx=10)

        for letter, text, scores in q_data["options"]:
            self._build_option_row(options_container, letter, text, scores)

    def _build_option_row(self, parent, letter, text, scores):
        row = ctk.CTkFrame(parent, fg_color=ROW_BG, corner_radius=8)
        row.pack(fill="x", pady=6, padx=4)

        letter_lbl = ctk.CTkLabel(row, text=letter, font=("Arial", 14, "bold"), text_color=SKY_BLUE, width=28, anchor="n")
        letter_lbl.pack(side="left", padx=(16, 4), pady=14, anchor="n")

        text_lbl = ctk.CTkLabel(
            row, text=text, font=("Arial", 13), text_color=WHITE,
            wraplength=740, justify="left", anchor="w"
        )
        text_lbl.pack(side="left", fill="x", expand=True, padx=(0, 16), pady=14)

        widgets = [row, letter_lbl, text_lbl]

        def on_click(event=None):
            self.handle_answer(scores)

        def on_enter(event=None):
            row.configure(fg_color=SKY_BLUE)
            letter_lbl.configure(text_color="#111111")
            text_lbl.configure(text_color="#111111")

        def on_leave(event=None):
            row.configure(fg_color=ROW_BG)
            letter_lbl.configure(text_color=SKY_BLUE)
            text_lbl.configure(text_color=WHITE)

        for w in widgets:
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

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
    # Result screen — retro pixel-window styling, no scrolling (the card
    # is sized generously enough to fit everything at once), only the
    # TOP trait's description shown (never two stacked paragraphs), and
    # a "top two" framing instead of "mix" when two traits are close.
    # ------------------------------------------------------------------
    def show_result(self):
        try:
            self._build_result_screen()
        except Exception as e:
            import traceback
            traceback.print_exc()
            for widget in self.card.winfo_children():
                widget.destroy()
            ctk.CTkLabel(
                self.card, text=f"Something broke building your result:\n{e}",
                font=("Consolas", 12), text_color=RED, wraplength=860, justify="center"
            ).pack(pady=200)

    def _build_result_screen(self):
        self._shark_animation_running = False
        for widget in self.card.winfo_children():
            widget.destroy()

        raw_totals, percentages = calculate_scores(self.answers)
        summary = get_result_summary(percentages)
        top_trait = summary["traits"][0]
        top_pct = summary["percentages"][top_trait]

        # No CTkScrollableFrame here — a plain frame, since the card is
        # now sized to hold headline + description + breakdown without
        # needing to scroll.
        content = ctk.CTkFrame(self.card, fg_color=CARD)
        content.pack(pady=20, padx=20, fill="both", expand=True)

        # --- headline window ---
        headline_body = self._pixel_window(content, "RESULT.EXE", border_color=YELLOW)
        if summary["type"] == "single":
            headline = f"YOU ARE A {top_trait.upper()}"
            subline = None
        else:
            second_trait = summary["traits"][1]
            second_pct = summary["percentages"][second_trait]
            headline = "TOP TWO PERSONALITIES THAT MATCH YOU"
            subline = f"{top_trait.upper()} {top_pct}%  •  {second_trait.upper()} {second_pct}%"

        ctk.CTkLabel(headline_body, text="SCAN COMPLETE", font=("Consolas", 11, "bold"), text_color=GRAY).pack(anchor="w")
        ctk.CTkLabel(headline_body, text=headline, font=("Arial", 26, "bold"), text_color=YELLOW, wraplength=880, justify="left").pack(anchor="w", pady=(8, 0))
        if subline:
            ctk.CTkLabel(headline_body, text=subline, font=("Consolas", 14), text_color=SKY_BLUE).pack(anchor="w", pady=(8, 0))

        # --- description window (top trait only, ever) ---
        desc = PERSONALITY_DESCRIPTIONS[top_trait]
        desc_body = self._pixel_window(content, f"{top_trait.upper()}.EXE", border_color=SKY_BLUE)
        ctk.CTkLabel(
            desc_body, text=desc["text"], font=("Arial", 14), text_color=WHITE,
            wraplength=880, justify="left"
        ).pack(anchor="w")
        ctk.CTkLabel(
            desc_body, text="You might like: " + desc["likes"], font=("Arial", 12, "italic"),
            text_color=GRAY, wraplength=880, justify="left"
        ).pack(anchor="w", pady=(12, 0))

        # --- breakdown window: bigger, rounded bars, each trait in its
        # own card-like row instead of a tight, cramped list ---
        breakdown_body = self._pixel_window(content, "BREAKDOWN.EXE", border_color=YELLOW, pady=(0, 10))
        for trait, pct in summary["ranked"]:
            row_wrap = ctk.CTkFrame(breakdown_body, fg_color=ROW_BG, corner_radius=8)
            row_wrap.pack(fill="x", pady=5)

            row = ctk.CTkFrame(row_wrap, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=10)

            ctk.CTkLabel(row, text=trait, width=130, font=("Consolas", 14, "bold"), text_color=WHITE, anchor="w").pack(side="left")

            bar_bg = ctk.CTkFrame(row, width=480, height=20, fg_color="#333333", corner_radius=10)
            bar_bg.pack(side="left", padx=10)
            bar_bg.pack_propagate(False)
            bar_width = max(10, int(480 * (pct / 100)))
            ctk.CTkFrame(bar_bg, width=bar_width, height=20, fg_color=SKY_BLUE, corner_radius=10).place(x=0, y=0)

            ctk.CTkLabel(row, text=f"{pct}%", font=("Consolas", 13, "bold"), text_color=YELLOW, width=60).pack(side="left", padx=6)

        save_status = ctk.CTkLabel(content, text="", font=("Consolas", 11), text_color=GRAY)
        save_status.pack(pady=(14, 0))

        ctk.CTkButton(
            content, text="CONTINUE TO MOODSHARK", width=320, height=46,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            command=self.finish_quiz
        ).pack(pady=26)

        # save to MongoDB last — never let a DB hiccup block the result
        # the person already earned from being displayed
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
            save_status.configure(
                text="\u26A0 Result couldn't be saved to your account — check your connection.",
                text_color=RED
            )

    def finish_quiz(self):
        # New users land here right after their personality result. Next
        # stop in the flow is the daily mood check-in (per the user flow:
        # Register -> Quiz -> Mood Check-in -> Home).
        from mood_checkin import MoodCheckinPage
        username = self.username
        self.destroy()
        MoodCheckinPage(username=username).mainloop()


if __name__ == "__main__":
    QuizPage(username="test_user").mainloop()