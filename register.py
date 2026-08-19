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
import re
import bcrypt

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#B1C8EF"
CARD = "#FFFFFF"
YELLOW = "#E8FF2A"
WHITE = "#FFFFFF"
GRAY = "#D6ECFF"
RED = "#FF5C5C"
GREEN = "#6BFF8F"
LIGHT_BLUE = "#D6ECFF"

class RegisterPage(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MoodShark - Register")
        self.geometry("1320x880")
        self.after(50, lambda: self.geometry("1320x880"))
        self.resizable(False, False)
        self.configure(fg_color=BG)

        left_frame = ctk.CTkFrame(self, width=560, height=880, fg_color=BG, corner_radius=0)
        left_frame.place(x=0, y=0)
        left_frame.pack_propagate(False)

        right_frame = ctk.CTkFrame(self, width=760, height=880, fg_color=BG, corner_radius=0)
        right_frame.place(x=560, y=0)

        card = ctk.CTkFrame(left_frame, width=440, height=720, corner_radius=24, fg_color=CARD)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        self.eye_open = ctk.CTkImage(
            light_image=Image.open("assets/eye.png"),
            dark_image=Image.open("assets/eye.png"),
            size=(18, 18)
        )
        self.eye_closed = ctk.CTkImage(
            light_image=Image.open("assets/eye_off.png"),
            dark_image=Image.open("assets/eye_off.png"),
            size=(18, 18)
        )

        ctk.CTkLabel(card, text="Create an ID", font=("Arial", 26, "bold"), text_color=WHITE).pack(pady=(30, 5))
        ctk.CTkLabel(card, text="Join MoodShark and find your vibe.", font=("Arial", 13), text_color="#000000").pack(pady=(0, 20))

        self.name_entry = ctk.CTkEntry(card, width=360, height=38, placeholder_text="Full Name", fg_color=LIGHT_BLUE, border_width=0, text_color="#000000")
        self.name_entry.pack(pady=6)

        self.username_entry = ctk.CTkEntry(card, width=360, height=38, placeholder_text="Username", fg_color=LIGHT_BLUE, border_width=0, text_color="#000000")
        self.username_entry.pack(pady=6)

        self.email_entry = ctk.CTkEntry(card, width=360, height=38, placeholder_text="Email", fg_color=LIGHT_BLUE, border_width=0, text_color="#000000")
        self.email_entry.pack(pady=6)

        self.password_entry, self.password_eye_btn = self._build_password_field(card, "Password")
        self.confirm_entry, self.confirm_eye_btn = self._build_password_field(card, "Confirm Password")

        self.status_label = ctk.CTkLabel(card, text="", font=("Arial", 12), text_color=RED, wraplength=360)
        self.status_label.pack(pady=(10, 0))

        ctk.CTkButton(
            card, text="CREATE ACCOUNT", width=360, height=40,
            fg_color=YELLOW, hover_color="#D6EB00", text_color="black",
            command=self.handle_register
        ).pack(pady=(15, 15))

        ctk.CTkButton(
            card, text="Already have an ID? Log in", fg_color="transparent",
            hover=False, text_color="#000000", command=self.open_login
        ).pack()

        self._animating = True
        self._anim_job = None
        self._build_decorations(right_frame)
        self._animate_scene()

    def _build_password_field(self, parent, placeholder):
        frame = ctk.CTkFrame(parent, width=360, height=38, fg_color=LIGHT_BLUE, corner_radius=8)
        frame.pack(pady=6)
        frame.pack_propagate(False)

        entry = ctk.CTkEntry(
            frame, width=310, height=30, placeholder_text=placeholder,
            show="*", fg_color="transparent", border_width=0, text_color="#000000"
        )
        entry.pack(side="left", padx=(12, 0), pady=4)

        def toggle():
            showing = entry.cget("show") == "*"
            entry.configure(show="" if showing else "*")
            eye_btn.configure(image=self.eye_closed if showing else self.eye_open)

        eye_btn = ctk.CTkButton(
            frame, width=26, height=26, text="", image=self.eye_open,
            fg_color="transparent", hover_color="#555555", command=toggle
        )
        eye_btn.pack(side="right", padx=(0, 8))

        return entry, eye_btn

    # ------------------------------------------------------------------
    # Right panel: an ocean scene. On load, the shark rises up out of the
    # waves from below the frame (hidden at start, since anything placed
    # past the window's height just doesn't render) and the three category
    # icons rise up together with it, arriving at their floating spots at
    # the same time the shark settles. After that "entrance", everything
    # switches into a slow idle loop: waves keep scrolling, shark keeps
    # bobbing on the swell, icons keep drifting gently.
    #
    # CustomTkinter can't play video/gif layers, so this is the classic
    # sprite trick: nudge each label's x/y with .place() every ~40ms.
    # ------------------------------------------------------------------

    ENTRANCE_FRAMES = 45   # ~1.8s at 40ms/frame
    HIDDEN_Y = 850         # below the visible 880px-tall window -> invisible at start

    @staticmethod
    def _load_rotated_icon(path, size, angle):
        # resize to the target footprint first, then rotate — rotating
        # first would make the resize target the wrong (post-rotation)
        # bounding box. expand=True keeps corners from being clipped, so
        # the actual rendered image ends up slightly larger than `size`;
        # CTkImage is told the true post-rotation size so it doesn't stretch it.
        img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
        rotated = img.rotate(angle, expand=True, resample=Image.BICUBIC)
        return ctk.CTkImage(light_image=rotated, dark_image=rotated, size=rotated.size)

    def _build_decorations(self, parent):
        panel_w = 760
        self.panel_w = panel_w
        self.wave_y = 600

        self.waves_img = ctk.CTkImage(
            light_image=Image.open("assets/waves.png"),
            dark_image=Image.open("assets/waves.png"),
            size=(panel_w, 230)
        )
        # two copies chasing each other so the scroll can loop seamlessly
        self.wave_label_a = ctk.CTkLabel(parent, image=self.waves_img, text="")
        self.wave_label_a.place(x=0, y=self.wave_y)
        self.wave_label_b = ctk.CTkLabel(parent, image=self.waves_img, text="")
        self.wave_label_b.place(x=panel_w, y=self.wave_y)
        self.wave_offset = 0

        # shark — bigger now, and rises out of the waves on load
        self.shark_img = ctk.CTkImage(
            light_image=Image.open("assets/shark.png"),
            dark_image=Image.open("assets/shark.png"),
            size=(320, 305)
        )
        self.shark_base_y = 365
        self.shark_label = ctk.CTkLabel(parent, image=self.shark_img, text="")
        self.shark_label.place(relx=0.5, y=self.HIDDEN_Y, anchor="n")

        # floating icons — bigger, tilted, and clustered in close alongside
        # the shark's body (not scattered up near the top corners) so the
        # whole group reads as one bunch rather than three separate props
        self.mike_img = self._load_rotated_icon("assets/mike.png", (112, 112), 14)
        self.mike_base = (185, 155)
        self.mike_label = ctk.CTkLabel(parent, image=self.mike_img, text="", fg_color="transparent")
        self.mike_label.place(x=self.mike_base[0], y=self.HIDDEN_Y)

        self.movies_img = self._load_rotated_icon("assets/movies.png", (140, 140), -12)
        self.movies_base = (530, 65)
        self.movies_label = ctk.CTkLabel(parent, image=self.movies_img, text="", fg_color="transparent")
        self.movies_label.place(x=self.movies_base[0], y=self.HIDDEN_Y)

        self.note_img = self._load_rotated_icon("assets/note.png", (120, 120), 10)
        self.note_base = (560, 280)
        self.note_label = ctk.CTkLabel(parent, image=self.note_img, text="", fg_color="transparent")
        self.note_label.place(x=self.note_base[0], y=self.HIDDEN_Y)

        self._phase = "entrance"
        self._entrance_frame = 0
        self._tick = 0

    @staticmethod
    def _ease_out_cubic(x):
        return 1 - (1 - x) ** 3

    def _animate_scene(self):
        if not self._animating or not self.winfo_exists():
            return

        # waves scroll continuously, in both entrance and idle phases
        self.wave_offset -= 2
        if self.wave_offset <= -self.panel_w:
            self.wave_offset = 0
        self.wave_label_a.place(x=self.wave_offset, y=self.wave_y)
        self.wave_label_b.place(x=self.wave_offset + self.panel_w, y=self.wave_y)

        if self._phase == "entrance":
            self._entrance_frame += 1
            progress = min(self._entrance_frame / self.ENTRANCE_FRAMES, 1.0)
            eased = self._ease_out_cubic(progress)

            shark_y = self.HIDDEN_Y + (self.shark_base_y - self.HIDDEN_Y) * eased
            self.shark_label.place(relx=0.5, y=shark_y, anchor="n")

            # icons trail the shark up by a few frames so they feel "pulled
            # along" rather than arriving in lockstep
            icon_progress = min(max(self._entrance_frame - 5, 0) / self.ENTRANCE_FRAMES, 1.0)
            icon_eased = self._ease_out_cubic(icon_progress)

            mx, my = self.mike_base
            self.mike_label.place(x=mx, y=self.HIDDEN_Y + (my - self.HIDDEN_Y) * icon_eased)

            mvx, mvy = self.movies_base
            self.movies_label.place(x=mvx, y=self.HIDDEN_Y + (mvy - self.HIDDEN_Y) * icon_eased)

            nx, ny = self.note_base
            self.note_label.place(x=nx, y=self.HIDDEN_Y + (ny - self.HIDDEN_Y) * icon_eased)

            if progress >= 1.0:
                self._phase = "idle"

        else:
            self._tick += 1
            t = self._tick

            # shark rides the swell: two sine terms of different speed,
            # summed, so the bob doesn't look mechanical
            bob = math.sin(t * 0.045) * 10 + math.sin(t * 0.017) * 4
            self.shark_label.place(relx=0.5, y=self.shark_base_y + bob, anchor="n")

            mx, my = self.mike_base
            self.mike_label.place(x=mx, y=my + math.sin(t * 0.04) * 7)

            mvx, mvy = self.movies_base
            self.movies_label.place(x=mvx + math.sin(t * 0.03) * 5, y=mvy + math.cos(t * 0.05) * 7)

            nx, ny = self.note_base
            self.note_label.place(x=nx, y=ny + math.sin(t * 0.05 + 1.5) * 8)

        self._anim_job = self.after(40, self._animate_scene)

    def handle_register(self):
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        if not all([name, username, email, password, confirm]):
            self._set_status("Please fill in every field.", RED)
            return

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            self._set_status("Enter a valid email address.", RED)
            return

        if len(password) < 6:
            self._set_status("Password must be at least 6 characters.", RED)
            return

        if password != confirm:
            self._set_status("Passwords do not match.", RED)
            return

        if users_collection.find_one({"username": username}):
            self._set_status("That username is already taken.", RED)
            return

        # bcrypt turns the plain password into a scrambled, one-way hash before
        # it ever touches MongoDB. Nobody, not even us looking at the database,
        # can read the real password back out of this.
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        users_collection.insert_one({
            "name": name,
            "username": username,
            "email": email,
            "password": hashed_password,   # stored as a bcrypt hash, not plain text
            "quiz_done": False              # tracks first-time vs returning user
        })

        self._set_status("Account created! Let's find your type...", GREEN)
        self.after(1200, lambda: self.open_quiz(username))

    def _set_status(self, message, color):
        self.status_label.configure(text=message, text_color=color)

    def open_login(self):
        self._stop_animation()
        from login import LoginPage
        self.destroy()
        LoginPage().mainloop()

    def open_quiz(self, username):
        self._stop_animation()
        from quiz import QuizPage
        self.destroy()
        QuizPage(username=username).mainloop()

    def _stop_animation(self):
        self._animating = False
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

    def destroy(self):
        self._stop_animation()
        super().destroy()


if __name__ == "__main__":
    RegisterPage().mainloop()