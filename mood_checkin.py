"""
mood_checkin.py

The DAILY mood check-in — completely separate from the one-time personality
quiz in quiz.py / quiz_data.py. This file does not touch those.

Visual language now matches quiz.py (same blue/white/yellow palette,
rounded panels, logo instead of an animation) so the two screens feel like
one app instead of two different apps stitched together.

Flow:
    MoodCheckinPage(username)
        -> if today's check-in already exists in Mongo:
               show a "welcome back" screen with today's mood + 3 buttons
        -> else:
               intro -> 1 broad question -> 1 pinpoint question (picked
               based on the broad answer's category) -> result -> save

Exposes: MoodCheckinPage(username)
"""

# DPI-awareness fix, same as quiz.py — must run before the first Tk/CTk
# window is created in the process, in case this file is ever launched
# on its own instead of via quiz.py.
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

import random
from datetime import date

import customtkinter as ctk
from PIL import Image
from db import users_collection
from quiz_data import PERSONALITY_DESCRIPTIONS  # reused for the "view profile" screen

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Same palette as quiz.py — sky blue background, white cards, yellow for
# the main actions, sky blue for secondary accents.
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

WINDOW_W = 880
CARD_W = 760
STAGE_MARGIN = WINDOW_W - CARD_W  # 120 total = 60px top + 60px bottom, matches quiz.py
# Intro/result screens use a fixed height (like quiz.py's shark screen) so
# their content can sit nicely centered. Question/welcome-back/profile
# screens measure their real content height instead of guessing.
STAGE_CARD_H = 460
CARD_MIN_H = 380
CARD_MAX_H = 760

MAX_RECENT_QUESTIONS = 7  # how many recently-used question ids we remember per user


# ======================================================================
# QUESTION POOL
# ======================================================================
# Each broad option carries its own "category" — the category is NOT
# inferred from the option's letter, since that pattern isn't consistent
# question to question.

BROAD_QUESTIONS = [
    {
        "id": "B1",
        "text": "Someone gives you a completely free evening. What sounds best?",
        "options": [
            {"label": "A", "text": "Going out and doing something with people", "category": "Connection", "scoring": {"Social": 3, "Romantic": 1}},
            {"label": "B", "text": "Watching something and completely disappearing into it", "category": "Positive", "scoring": {"Relaxed": 3, "Whimsical": 1}},
            {"label": "C", "text": "Finally doing something I've been putting off", "category": "Growth", "scoring": {"Motivated": 3, "Focused": 1}},
            {"label": "D", "text": "Wandering around with no plan", "category": "Reflective", "scoring": {"Curious": 3, "Reflective": 1}},
            {"label": "E", "text": "Staying home, no noise, no people", "category": "LowMood", "scoring": {"Burnt Out": 2, "Empty": 2}},
        ],
    },
    {
        "id": "B2",
        "text": "Pick a place you'd rather be right now.",
        "options": [
            {"label": "A", "text": "A crowded night market", "category": "Connection", "scoring": {"Social": 3, "Energetic": 1}},
            {"label": "B", "text": "A quiet cabin while it's raining", "category": "Positive", "scoring": {"Relaxed": 3, "Hopeful": 1}},
            {"label": "C", "text": "Your childhood bedroom", "category": "Reflective", "scoring": {"Nostalgic": 3, "Reflective": 1}},
            {"label": "D", "text": "The top of a mountain you just finished climbing", "category": "Growth", "scoring": {"Motivated": 3, "Focused": 1}},
            {"label": "E", "text": "A waiting room with nothing to do and nowhere to be", "category": "LowMood", "scoring": {"Empty": 2, "Restless": 2}},
        ],
    },
    {
        "id": "B3",
        "text": "A song comes on that instantly changes your whole mood. What's it doing?",
        "options": [
            {"label": "A", "text": "Making you want to dance or call someone", "category": "Connection", "scoring": {"Social": 2, "Energetic": 1}},
            {"label": "B", "text": "Making everything feel lighter for a second", "category": "Positive", "scoring": {"Joyful": 3, "Hopeful": 1}},
            {"label": "C", "text": "Pulling up a memory you weren't expecting", "category": "Reflective", "scoring": {"Nostalgic": 3, "Reflective": 1}},
            {"label": "D", "text": "Making you want to actually get things done", "category": "Growth", "scoring": {"Motivated": 3, "Energetic": 1}},
            {"label": "E", "text": "Making you want to turn it off", "category": "LowMood", "scoring": {"Frustrated": 2, "Anxious": 1}},
        ],
    },
    {
        "id": "B4",
        "text": "Pick the weather (or the feeling of one) that matches today.",
        "options": [
            {"label": "A", "text": "Bright sunshine, clear skies", "category": "Positive", "scoring": {"Joyful": 3, "Hopeful": 1}},
            {"label": "B", "text": "Grey skies, steady rain", "category": "LowMood", "scoring": {"Sad": 2, "Empty": 2}},
            {"label": "C", "text": "Golden hour light, everything looks softer than usual", "category": "Reflective", "scoring": {"Nostalgic": 3, "Reflective": 1}},
            {"label": "D", "text": "Crisp, clear morning air, the kind that makes you want to get moving", "category": "Growth", "scoring": {"Motivated": 3, "Focused": 1}},
            {"label": "E", "text": "Warm evening, string lights, people nearby", "category": "Connection", "scoring": {"Social": 2, "Romantic": 2}},
        ],
    },
    {
        "id": "B5",
        "text": "Pick the interruption you'd least mind right now.",
        "options": [
            {"label": "A", "text": "A friend showing up unannounced", "category": "Connection", "scoring": {"Social": 3, "Lonely": 1}},
            {"label": "B", "text": "Someone telling you to take the rest of the day off", "category": "LowMood", "scoring": {"Burnt Out": 3, "Restless": 1}},
            {"label": "C", "text": "A random memory popping into your head", "category": "Reflective", "scoring": {"Nostalgic": 3, "Curious": 1}},
            {"label": "D", "text": "A reminder about a goal you set for yourself", "category": "Growth", "scoring": {"Motivated": 2, "Focused": 2}},
            {"label": "E", "text": "Good news you weren't expecting", "category": "Positive", "scoring": {"Hopeful": 3, "Joyful": 1}},
        ],
    },
]

PINPOINT_QUESTIONS = {
    "Positive": [
        {
            "id": "P1", "text": "Pick the kind of good day you're having.",
            "options": [
                {"label": "A", "text": "The kind where everything's just easy and fun", "scoring": {"Joyful": 3, "Relaxed": 1}},
                {"label": "B", "text": "The kind where something small and magical just happened", "scoring": {"Whimsical": 3, "Joyful": 1}},
                {"label": "C", "text": "The kind where things finally seem to be looking up", "scoring": {"Hopeful": 3, "Motivated": 1}},
                {"label": "D", "text": "The kind where nothing's urgent and you can just exist", "scoring": {"Relaxed": 3, "Joyful": 1}},
                {"label": "E", "text": "The kind where you feel like you could do anything", "scoring": {"Energetic": 3, "Motivated": 1}},
            ],
        },
        {
            "id": "P2", "text": "Pick a drink for how you're feeling.",
            "options": [
                {"label": "A", "text": "Champagne", "scoring": {"Joyful": 3, "Energetic": 1}},
                {"label": "B", "text": "Something weird you've never tried before", "scoring": {"Whimsical": 3, "Curious": 1}},
                {"label": "C", "text": "A warm tea, something steady", "scoring": {"Hopeful": 2, "Relaxed": 2}},
                {"label": "D", "text": "Iced water, slow sips, no rush", "scoring": {"Relaxed": 3, "Joyful": 1}},
                {"label": "E", "text": "A strong coffee, ready to go", "scoring": {"Energetic": 3, "Motivated": 1}},
            ],
        },
        {
            "id": "P3", "text": "Pick a soundtrack for your afternoon.",
            "options": [
                {"label": "A", "text": "Something upbeat you can't help but sing along to", "scoring": {"Joyful": 3, "Energetic": 1}},
                {"label": "B", "text": "Something a little strange and playful", "scoring": {"Whimsical": 3, "Curious": 1}},
                {"label": "C", "text": "Something with a hopeful, building kind of feeling", "scoring": {"Hopeful": 3, "Motivated": 1}},
                {"label": "D", "text": "Something slow and easy, barely there", "scoring": {"Relaxed": 3, "Joyful": 1}},
                {"label": "E", "text": "Something fast, loud, gets your blood moving", "scoring": {"Energetic": 3, "Joyful": 1}},
            ],
        },
        {
            "id": "P4", "text": "If today had a texture, what would it feel like?",
            "options": [
                {"label": "A", "text": "Fizzy, like it's bubbling over", "scoring": {"Joyful": 3, "Energetic": 1}},
                {"label": "B", "text": "Soft and a little strange, like static or velvet", "scoring": {"Whimsical": 3, "Relaxed": 1}},
                {"label": "C", "text": "Warm, like something good is on its way", "scoring": {"Hopeful": 3, "Joyful": 1}},
                {"label": "D", "text": "Smooth, like nothing can rush you", "scoring": {"Relaxed": 3}},
                {"label": "E", "text": "Electric, like something's about to happen", "scoring": {"Energetic": 3, "Whimsical": 1}},
            ],
        },
    ],
    "LowMood": [
        {
            "id": "L1", "text": "Pick the kind of tired you are.",
            "options": [
                {"label": "A", "text": "The kind sleep won't fix", "scoring": {"Burnt Out": 3, "Empty": 1}},
                {"label": "B", "text": "The kind where nothing feels like it matters", "scoring": {"Empty": 3, "Sad": 1}},
                {"label": "C", "text": "The kind where you can't sit still", "scoring": {"Restless": 3, "Frustrated": 1}},
                {"label": "D", "text": "The kind where your chest feels tight", "scoring": {"Anxious": 3, "Restless": 1}},
                {"label": "E", "text": "The kind where you just want to cry it out", "scoring": {"Sad": 3, "Empty": 1}},
                {"label": "F", "text": "The kind where everything is mildly infuriating", "scoring": {"Frustrated": 3, "Anxious": 1}},
            ],
        },
        {
            "id": "L2", "text": "Pick the noise that matches your head right now.",
            "options": [
                {"label": "A", "text": "Static, low and constant", "scoring": {"Burnt Out": 3, "Anxious": 1}},
                {"label": "B", "text": "Silence, too much of it", "scoring": {"Empty": 3, "Sad": 1}},
                {"label": "C", "text": "A drumbeat that won't stop", "scoring": {"Restless": 3, "Anxious": 1}},
                {"label": "D", "text": "A buzzing alarm you can't turn off", "scoring": {"Anxious": 3, "Restless": 1}},
                {"label": "E", "text": "A song that makes you want to cry", "scoring": {"Sad": 3, "Empty": 1}},
                {"label": "F", "text": "Someone talking over you", "scoring": {"Frustrated": 3, "Anxious": 1}},
            ],
        },
        {
            "id": "L3", "text": "Pick the thing you're most short on right now.",
            "options": [
                {"label": "A", "text": "Energy", "scoring": {"Burnt Out": 3, "Empty": 1}},
                {"label": "B", "text": "Motivation to feel anything", "scoring": {"Empty": 3, "Sad": 1}},
                {"label": "C", "text": "Stillness", "scoring": {"Restless": 3, "Anxious": 1}},
                {"label": "D", "text": "Reassurance", "scoring": {"Anxious": 3, "Sad": 1}},
                {"label": "E", "text": "Comfort", "scoring": {"Sad": 3, "Empty": 1}},
                {"label": "F", "text": "Patience", "scoring": {"Frustrated": 3, "Restless": 1}},
            ],
        },
        {
            "id": "L4", "text": "If you had to describe today in weather, what would it be?",
            "options": [
                {"label": "A", "text": "Overcast, heavy, low pressure", "scoring": {"Burnt Out": 3, "Sad": 1}},
                {"label": "B", "text": "Flat calm, nothing moving", "scoring": {"Empty": 3, "Burnt Out": 1}},
                {"label": "C", "text": "Gusty, can't settle", "scoring": {"Restless": 3, "Anxious": 1}},
                {"label": "D", "text": "A storm you can feel coming", "scoring": {"Anxious": 3, "Restless": 1}},
                {"label": "E", "text": "Cold rain that won't let up", "scoring": {"Sad": 3, "Empty": 1}},
                {"label": "F", "text": "Static in the air before lightning", "scoring": {"Frustrated": 3, "Anxious": 1}},
            ],
        },
    ],
    "Reflective": [
        {
            "id": "R1", "text": "Pick what's actually on your mind right now.",
            "options": [
                {"label": "A", "text": "Something from a long time ago", "scoring": {"Nostalgic": 3, "Reflective": 1}},
                {"label": "B", "text": "A question you don't have the answer to yet", "scoring": {"Reflective": 3, "Curious": 1}},
                {"label": "C", "text": "Something you just want to learn more about", "scoring": {"Curious": 3, "Reflective": 1}},
            ],
        },
        {
            "id": "R2", "text": "Pick a photograph you'd want to look at right now.",
            "options": [
                {"label": "A", "text": "An old one, from years ago", "scoring": {"Nostalgic": 3, "Reflective": 1}},
                {"label": "B", "text": "One of somewhere you've never been", "scoring": {"Curious": 3, "Whimsical": 1}},
                {"label": "C", "text": "A blank one, just so you can think", "scoring": {"Reflective": 3, "Nostalgic": 1}},
            ],
        },
        {
            "id": "R3", "text": "Pick the kind of question you'd rather sit with.",
            "options": [
                {"label": "A", "text": "What if things had gone differently", "scoring": {"Nostalgic": 3, "Reflective": 1}},
                {"label": "B", "text": "What don't I know yet", "scoring": {"Curious": 3, "Motivated": 1}},
                {"label": "C", "text": "What actually matters to me right now", "scoring": {"Reflective": 3, "Curious": 1}},
            ],
        },
        {
            "id": "R4", "text": "Pick a room to sit in for an hour, alone with your thoughts.",
            "options": [
                {"label": "A", "text": "A room full of old photographs and things you used to own", "scoring": {"Nostalgic": 3, "Reflective": 1}},
                {"label": "B", "text": "A room with a single locked door you're curious about", "scoring": {"Curious": 3, "Whimsical": 1}},
                {"label": "C", "text": "An empty, quiet room with just a chair", "scoring": {"Reflective": 3, "Nostalgic": 1}},
            ],
        },
    ],
    "Growth": [
        {
            "id": "G1", "text": "Pick what's pulling at you today.",
            "options": [
                {"label": "A", "text": "A big goal you want to chase", "scoring": {"Motivated": 3, "Energetic": 1}},
                {"label": "B", "text": "One task you just want to finish properly", "scoring": {"Focused": 3, "Motivated": 1}},
            ],
        },
        {
            "id": "G2", "text": "Pick the version of productive you want today.",
            "options": [
                {"label": "A", "text": "Fired up, tackling everything at once", "scoring": {"Motivated": 3, "Energetic": 1}},
                {"label": "B", "text": "Locked in on one thing, blocking everything else out", "scoring": {"Focused": 3, "Motivated": 1}},
            ],
        },
        {
            "id": "G3", "text": "Pick a tool for today.",
            "options": [
                {"label": "A", "text": "A map, you're plotting the whole route", "scoring": {"Motivated": 3, "Hopeful": 1}},
                {"label": "B", "text": "A magnifying glass, you just need to zoom in on one thing", "scoring": {"Focused": 3, "Curious": 1}},
            ],
        },
        {
            "id": "G4", "text": "Pick the feeling you want to end today with.",
            "options": [
                {"label": "A", "text": "Like you moved closer to something big", "scoring": {"Motivated": 3, "Hopeful": 1}},
                {"label": "B", "text": "Like you actually finished what you started", "scoring": {"Focused": 3, "Motivated": 1}},
            ],
        },
    ],
    "Connection": [
        {
            "id": "C1", "text": "Pick what you're actually craving today.",
            "options": [
                {"label": "A", "text": "Company, any company", "scoring": {"Social": 3, "Lonely": 1}},
                {"label": "B", "text": "One specific person", "scoring": {"Romantic": 3, "Lonely": 1}},
                {"label": "C", "text": "Nobody, but you notice the quiet more than usual", "scoring": {"Lonely": 3, "Reflective": 1}},
            ],
        },
        {
            "id": "C2", "text": "Pick the text you'd most want to get right now.",
            "options": [
                {"label": "A", "text": "A group chat blowing up with plans", "scoring": {"Social": 3, "Joyful": 1}},
                {"label": "B", "text": "\u201cI miss you\u201d from someone specific", "scoring": {"Romantic": 3, "Nostalgic": 1}},
                {"label": "C", "text": "Anyone, honestly, just to know someone's thinking of you", "scoring": {"Lonely": 3, "Social": 1}},
            ],
        },
        {
            "id": "C3", "text": "Pick the scene you'd want to be in.",
            "options": [
                {"label": "A", "text": "A packed table, everyone talking over each other", "scoring": {"Social": 3, "Joyful": 1}},
                {"label": "B", "text": "Just two chairs, quiet conversation", "scoring": {"Romantic": 3, "Reflective": 1}},
                {"label": "C", "text": "A window seat, watching everyone else together", "scoring": {"Lonely": 3, "Reflective": 1}},
            ],
        },
        {
            "id": "C4", "text": "Pick the kind of plans you wish you had tonight.",
            "options": [
                {"label": "A", "text": "Anything with a group", "scoring": {"Social": 3, "Energetic": 1}},
                {"label": "B", "text": "Dinner with one person who gets you", "scoring": {"Romantic": 3, "Hopeful": 1}},
                {"label": "C", "text": "Honestly, just someone checking in", "scoring": {"Lonely": 3, "Social": 1}},
            ],
        },
    ],
}


# ======================================================================
# Question selection helpers (avoid repeating recent questions)
# ======================================================================
def _pick_broad_question(recent_ids):
    available = [q for q in BROAD_QUESTIONS if q["id"] not in recent_ids]
    if not available:
        available = BROAD_QUESTIONS
    return random.choice(available)


def _pick_pinpoint_question(category, recent_ids):
    pool = PINPOINT_QUESTIONS[category]
    available = [q for q in pool if q["id"] not in recent_ids]
    if not available:
        available = pool
    return random.choice(available)


def _top_moods(combined_scores, n=2, tie_margin=1):
    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    if not ranked:
        return []
    top = [ranked[0]]
    if len(ranked) > 1 and (ranked[0][1] - ranked[1][1]) <= tie_margin:
        top.append(ranked[1])
    elif n > 1 and len(ranked) > 1:
        pass  # second place isn't close enough — only keep the clear winner
    return top


class MoodCheckinPage(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.title("Your daily Mood Check-in")
        self.geometry(f"{WINDOW_W}x{STAGE_CARD_H + STAGE_MARGIN}")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.card = ctk.CTkFrame(self, width=CARD_W, height=STAGE_CARD_H, corner_radius=24, fg_color=CARD)
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        self.user_doc = users_collection.find_one({"username": username}) or {}
        self.broad_answer_scoring = None
        self.broad_answer_category = None
        self.broad_question_id = None
        self.pinpoint_question_id = None

        today_str = date.today().isoformat()
        existing_mood = self.user_doc.get("daily_mood")
        if existing_mood and existing_mood.get("date") == today_str:
            self.show_welcome_back(existing_mood)
        else:
            self.show_intro()

    # ------------------------------------------------------------------
    # Resizes both the window and the card together, same helper as
    # quiz.py — keeps the blue margin even on every screen.
    # ------------------------------------------------------------------
    def _resize_stage(self, card_h):
        window_h = card_h + STAGE_MARGIN
        self.geometry(f"{WINDOW_W}x{window_h}")
        self.card.configure(height=card_h)

    # ------------------------------------------------------------------
    # Measures whatever was just packed into the card and resizes ONCE
    # to fit it — same "build, measure, resize once" approach used in
    # quiz.py, so screens with variable-length content (a 6-option
    # question, a longer personality description) never show dead space
    # or clip, and there's no flicker from resizing twice.
    # ------------------------------------------------------------------
    def _fit_card(self, min_h=CARD_MIN_H, max_h=CARD_MAX_H, bottom_pad=30):
        self.update_idletasks()
        max_bottom = 0
        for child in self.card.winfo_children():
            bottom = child.winfo_y() + child.winfo_height()
            if bottom > max_bottom:
                max_bottom = bottom
        card_h = min(max_h, max(min_h, max_bottom + bottom_pad))
        self._resize_stage(card_h)

    # ------------------------------------------------------------------
    # Small rounded panel helper, same visual language as quiz.py.
    # ------------------------------------------------------------------
    def _panel(self, parent, title, accent=BLUE, fg_color=ROW_BG, pady=(0, 14), padx=32):
        frame = ctk.CTkFrame(parent, fg_color=fg_color, corner_radius=16)
        frame.pack(fill="x", padx=padx, pady=pady)

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        if title:
            ctk.CTkLabel(
                body, text=title, font=("Arial", 11, "bold"), text_color=accent
            ).pack(anchor="w", pady=(0, 6))
        return body

    def _clear_card(self):
        for widget in self.card.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # Intro screen — logo instead of an animation, matches quiz.py's
    # shark-screen layout (a rounded stage box + headline + buttons, all
    # vertically centered).
    # ------------------------------------------------------------------
    def show_intro(self):
        self._resize_stage(STAGE_CARD_H)
        self._clear_card()

        centered = ctk.CTkFrame(self.card, fg_color="transparent")
        centered.pack(expand=True)

        ctk.CTkLabel(
            centered, text="Your daily Mood Check-in", font=("Arial", 12, "bold"), text_color=BLUE
        ).pack(pady=(0, 16))

        stage = ctk.CTkFrame(centered, width=640, height=170, fg_color=ROW_BG, corner_radius=18)
        stage.pack(pady=(0, 26))
        stage.pack_propagate(False)

        try:
            logo_img = ctk.CTkImage(
                light_image=Image.open("assets/logo.png"),
                dark_image=Image.open("assets/logo.png"),
                size=(650, 200)
            )
            logo_lbl = ctk.CTkLabel(stage, image=logo_img, text="")
            logo_lbl.image = logo_img
        except Exception:
            logo_lbl = ctk.CTkLabel(stage, text="MOODSHARK", font=("Arial", 22, "bold"), text_color=BLUE)
        logo_lbl.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            centered, text="What’s swimming through your mind today?", font=("Arial", 22, "bold"), text_color=BLUE
        ).pack(pady=(0, 6))
        ctk.CTkLabel(
            centered, text="Help MoodShark tune today's picks to how you're feeling.",
            font=("Arial", 12), text_color=MUTED, wraplength=560, width=560, justify="center"
        ).pack()

        btn_frame = ctk.CTkFrame(centered, fg_color="transparent")
        btn_frame.pack(pady=(24, 0))
        ctk.CTkButton(
            btn_frame, text="START CHECK-IN", width=240, height=46, corner_radius=12,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            font=("Arial", 14, "bold"), command=self.show_broad_question
        ).pack(pady=6)
        ctk.CTkButton(
            btn_frame, text="Skip for now", width=240, height=32, corner_radius=10,
            fg_color="transparent", hover_color=ROW_BG, text_color=MUTED,
            font=("Arial", 12), command=self.finish
        ).pack(pady=4)

    # ------------------------------------------------------------------
    # Question 1 — broad / funnel
    # ------------------------------------------------------------------
    def show_broad_question(self):
        recent = self.user_doc.get("last_used_question_ids", [])
        question = _pick_broad_question(recent)
        self.broad_question_id = question["id"]
        self._render_question(question, step_index=0, on_pick=self._handle_broad_answer)

    def _handle_broad_answer(self, option):
        self.broad_answer_scoring = option["scoring"]
        self.broad_answer_category = option["category"]
        self.show_pinpoint_question()

    # ------------------------------------------------------------------
    # Question 2 — pinpoint, chosen from the category the broad answer fell into
    # ------------------------------------------------------------------
    def show_pinpoint_question(self):
        recent = self.user_doc.get("last_used_question_ids", [])
        question = _pick_pinpoint_question(self.broad_answer_category, recent)
        self.pinpoint_question_id = question["id"]
        self._render_question(question, step_index=1, on_pick=self._handle_pinpoint_answer)

    def _handle_pinpoint_answer(self, option):
        combined = dict(self.broad_answer_scoring)
        for tag, points in option["scoring"].items():
            combined[tag] = combined.get(tag, 0) + points
        self.show_result(combined)

    # ------------------------------------------------------------------
    # Shared question renderer — same visual pattern as quiz.py's
    # show_question (progress bar, question text, clickable option rows),
    # sized to its real content instead of a scrollable frame with a
    # fixed height.
    # ------------------------------------------------------------------
    def _render_question(self, question, step_index, on_pick):
        self._clear_card()

        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 0))
        ctk.CTkLabel(
            header, text=f"QUESTION {step_index + 1} / 2", font=("Arial", 12, "bold"), text_color=BLUE
        ).pack(anchor="w")

        progress_bg = ctk.CTkFrame(self.card, height=8, fg_color=ROW_BG, corner_radius=4)
        progress_bg.pack(fill="x", padx=32, pady=(8, 22))
        progress_bg.pack_propagate(False)
        fill_width = max(6, int(696 * (step_index / 2)))
        ctk.CTkFrame(progress_bg, width=fill_width, height=8, fg_color=YELLOW, corner_radius=4).place(x=0, y=0)

        ctk.CTkLabel(
            self.card, text=question["text"], font=("Arial", 20, "bold"),
            text_color=TEXT_DARK, wraplength=680, width=680, justify="center"
        ).pack(padx=32, pady=(0, 18))

        options_container = ctk.CTkFrame(self.card, fg_color="transparent")
        options_container.pack(fill="both", expand=True, padx=32)

        for option in question["options"]:
            self._build_option_row(options_container, option, on_pick)

        self._fit_card(bottom_pad=30)

    def _build_option_row(self, parent, option, on_pick):
        row = ctk.CTkFrame(parent, fg_color=ROW_BG, corner_radius=12)
        row.pack(fill="x", pady=5)

        letter_lbl = ctk.CTkLabel(row, text=option["label"], font=("Arial", 13, "bold"), text_color=BLUE, width=26, anchor="n")
        letter_lbl.pack(side="left", padx=(16, 4), pady=12, anchor="n")

        text_lbl = ctk.CTkLabel(
            row, text=option["text"], font=("Arial", 13), text_color=TEXT_DARK,
            wraplength=580, width=580, justify="left", anchor="w"
        )
        text_lbl.pack(side="left", fill="x", expand=True, padx=(0, 16), pady=12)

        widgets = [row, letter_lbl, text_lbl]

        def on_click(event=None):
            on_pick(option)

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

    # ------------------------------------------------------------------
    # Welcome back screen (today's check-in already exists)
    # ------------------------------------------------------------------
    def show_welcome_back(self, existing_mood):
        self._clear_card()

        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(32, 0))
        ctk.CTkLabel(
            header, text=f"Welcome back, {self.username}", font=("Arial", 22, "bold"), text_color=TEXT_DARK
        ).pack(anchor="w")

        mood_text = existing_mood.get("mood", "unknown")
        panel = self._panel(self.card, "TODAY'S MOOD", accent=BLUE, pady=(18, 0))
        ctk.CTkLabel(
            panel, text=f'We sense a {mood_text.lower()} mood today.',
            font=("Arial", 18, "bold"), text_color=YELLOW, wraplength=660, width=660, justify="left"
        ).pack(anchor="w")
        secondary = existing_mood.get("secondary_mood")
        if secondary:
            ctk.CTkLabel(
                panel, text=f"with a little {secondary.lower()} mixed in",
                font=("Arial", 12), text_color=MUTED
            ).pack(anchor="w", pady=(6, 0))

        btn_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        btn_frame.pack(padx=32, pady=(24, 0), fill="x")

        ctk.CTkButton(
            btn_frame, text="VIEW MY PROFILE", height=44, corner_radius=12,
            fg_color=BLUE, hover_color="#1BA6DB", text_color="white",
            font=("Arial", 13, "bold"), command=self.show_profile
        ).pack(fill="x", pady=6)
        ctk.CTkButton(
            btn_frame, text="RETAKE CHECK-IN", height=44, corner_radius=12,
            fg_color=ROW_BG, hover_color="#C3E0FB", text_color=TEXT_DARK,
            font=("Arial", 13, "bold"), command=self.show_intro
        ).pack(fill="x", pady=6)
        ctk.CTkButton(
            btn_frame, text="SEE RECOMMENDATIONS", height=46, corner_radius=12,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            font=("Arial", 13, "bold"), command=self.finish
        ).pack(fill="x", pady=(6, 30))

        self._fit_card(bottom_pad=20)

    # ------------------------------------------------------------------
    # Result screen — mood is now a sentence instead of a boxed stat,
    # e.g. "Well, aren't you in a 'joyful' mood today." Fixed height,
    # vertically centered, same feel as the intro/shark screens.
    # ------------------------------------------------------------------
        # ------------------------------------------------------------------
    # Result screen — mood is now a sentence instead of a boxed stat,
    # e.g. "We sense a 'joyful' mood today."
    # Fixed height, vertically centered, same feel as the intro/shark screens.
    # ------------------------------------------------------------------
    def show_result(self, combined_scores):
        self._clear_card()

        top = _top_moods(combined_scores, n=2, tie_margin=1)
        primary_mood = top[0][0]
        today_str = date.today().isoformat()

        centered = ctk.CTkFrame(self.card, fg_color="transparent")
        centered.pack(expand=True)

        ctk.CTkLabel(
            centered, text="TODAY'S SIGNAL", font=("Arial", 12, "bold"), text_color=YELLOW
        ).pack(pady=(0, 18))

        ctk.CTkLabel(
            centered, text=f'We sense a {primary_mood.lower()} mood today.',
            font=("Arial", 26, "bold"), text_color=BLUE,
            wraplength=640, width=640, justify="center"
        ).pack()

        if len(top) > 1:
            ctk.CTkLabel(
                centered, text=f"With a little {top[1][0].lower()} mixed in.",
                font=("Arial", 13), text_color=MUTED
            ).pack(pady=(8, 0))

        ctk.CTkButton(
            centered, text="CONTINUE", width=260, height=46, corner_radius=12,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            font=("Arial", 14, "bold"), command=self.finish
        ).pack(pady=(30, 0))

        self._resize_stage(STAGE_CARD_H)

        # save to Mongo — never let a hiccup here block the result from showing
        daily_mood_doc = {
            "mood": primary_mood,
            "scores": combined_scores,
            "date": today_str,
        }
        if len(top) > 1:
            daily_mood_doc["secondary_mood"] = top[1][0]

        recent = self.user_doc.get("last_used_question_ids", [])
        recent = (recent + [self.broad_question_id, self.pinpoint_question_id])[-MAX_RECENT_QUESTIONS:]

        try:
            users_collection.update_one(
                {"username": self.username},
                {"$set": {"daily_mood": daily_mood_doc, "last_used_question_ids": recent}}
            )
        except Exception as e:
            print(f"Warning: could not save today's mood to MongoDB: {e}")

    # ------------------------------------------------------------------
    # View profile (reuses the saved personality result from quiz.py)
    # ------------------------------------------------------------------
    def show_profile(self):
        self._clear_card()
        personality = self.user_doc.get("personality")

        if not personality or not personality.get("top_traits"):
            centered = ctk.CTkFrame(self.card, fg_color="transparent")
            centered.pack(expand=True)
            ctk.CTkLabel(
                centered, text="No personality profile found yet.", font=("Arial", 14), text_color=MUTED
            ).pack(pady=(0, 16))
            ctk.CTkButton(
                centered, text="BACK", width=200, height=40, corner_radius=12,
                fg_color=BLUE, hover_color="#1BA6DB", text_color="white", font=("Arial", 13, "bold"),
                command=lambda: self.show_welcome_back(self.user_doc.get("daily_mood", {}))
            ).pack()
            self._resize_stage(STAGE_CARD_H)
            return

        top_trait = personality["top_traits"][0]
        desc = PERSONALITY_DESCRIPTIONS.get(top_trait, {})

        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(32, 0))
        ctk.CTkLabel(header, text="YOUR PERSONALITY", font=("Arial", 11, "bold"), text_color=MUTED).pack(anchor="w")
        ctk.CTkLabel(
            header, text=f"You are a {top_trait}", font=("Arial", 24, "bold"), text_color=TEXT_DARK
        ).pack(anchor="w", pady=(2, 0))

        panel = self._panel(self.card, None, accent=BLUE, fg_color=ROW_BG, pady=(18, 0))
        if desc:
            ctk.CTkLabel(
                panel, text=desc["text"], font=("Arial", 13), text_color=TEXT_DARK,
                wraplength=660, width=660, justify="left"
            ).pack(anchor="w")
            ctk.CTkLabel(
                panel, text="You might like: " + desc["likes"], font=("Arial", 12, "italic"), text_color=MUTED,
                wraplength=660, width=660, justify="left"
            ).pack(anchor="w", pady=(12, 0))

        ctk.CTkButton(
            self.card, text="BACK", width=200, height=40, corner_radius=12,
            fg_color=ROW_BG, hover_color="#C3E0FB", text_color=TEXT_DARK, font=("Arial", 13, "bold"),
            command=lambda: self.show_welcome_back(self.user_doc.get("daily_mood", {}))
        ).pack(padx=32, pady=(24, 0), anchor="w")

        self._fit_card(bottom_pad=30)

    # ------------------------------------------------------------------
    def finish(self):
        # Mood check-in is done — hand off to the Home/dashboard screen,
        # which pulls personality + mood recommendations via recommendations.py.
        from home import HomePage
        username = self.username
        self.destroy()
        HomePage(username=username).mainloop()


if __name__ == "__main__":
    MoodCheckinPage(username="test_user").mainloop()