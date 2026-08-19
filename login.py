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

import customtkinter as ctk
from PIL import Image
from register import RegisterPage
from db import users_collection
import bcrypt

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG = "#B1C8EF"
CARD = "#FFFFFF"
YELLOW = "#E8FF2A"
BLUE = "#2AC7FF"
LIGHT_BLUE = "#D6ECFF"
FIELD_TEXT = "#0B1220"
MUTED = "#5A7096"
WHITE = "#FFFFFF"
RED = "#FF5C5C"
GREEN = "#6BFF8F"


class LoginPage(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MoodShark")
        self.geometry("1320x880")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        card = ctk.CTkFrame(self, width=520, height=620, corner_radius=24, fg_color=CARD)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        self.logo_image = ctk.CTkImage(
            light_image=Image.open("assets/logo.png"),
            dark_image=Image.open("assets/logo.png"),
            size=(280, 112)
        )
        ctk.CTkLabel(card, image=self.logo_image, text="").pack(pady=(60, 12))

        self.eye_open = ctk.CTkImage(
            light_image=Image.open("assets/eye.png"),
            dark_image=Image.open("assets/eye.png"),
            size=(20, 20)
        )
        self.eye_closed = ctk.CTkImage(
            light_image=Image.open("assets/eye_off.png"),
            dark_image=Image.open("assets/eye_off.png"),
            size=(20, 20)
        )

        ctk.CTkLabel(card, text="Find your niche", font=("Arial", 15), text_color=MUTED).pack(pady=(0, 40))

        self.username = ctk.CTkEntry(
            card, width=380, height=44, placeholder_text="Username",
            fg_color=LIGHT_BLUE, text_color=FIELD_TEXT, placeholder_text_color="#5A7096",
            border_width=0, corner_radius=10
        )
        self.username.pack(pady=8)

        password_frame = ctk.CTkFrame(card, width=380, height=44, fg_color=LIGHT_BLUE, corner_radius=10)
        password_frame.pack(pady=8)
        password_frame.pack_propagate(False)

        self.password = ctk.CTkEntry(
            password_frame, width=290, height=36, placeholder_text="Password",
            placeholder_text_color="#5A7096", show="*",
            fg_color="transparent", text_color=FIELD_TEXT, border_width=0
        )
        self.password.pack(side="left", padx=(14, 0), pady=4)

        def toggle_password():
            showing = self.password.cget("show") == "*"
            self.password.configure(show="" if showing else "*")
            self.eye_button.configure(image=self.eye_closed if showing else self.eye_open)

        self.eye_button = ctk.CTkButton(
            password_frame, width=30, height=30, text="", image=self.eye_open,
            fg_color="transparent", hover_color="#BFDDFF", command=toggle_password
        )
        self.eye_button.pack(side="right", padx=(0, 10))

        self.status_label = ctk.CTkLabel(card, text="", font=("Arial", 12), text_color=RED, wraplength=380)
        self.status_label.pack(pady=(10, 0))

        ctk.CTkButton(
            card, text="LOGIN", width=380, height=44, fg_color=YELLOW,
            hover_color="#D6EB00", text_color="black", font=("Arial", 14, "bold"),
            command=self.handle_login
        ).pack(pady=(18, 16))

        ctk.CTkButton(
            card, text="Create an ID", fg_color="transparent", hover=False,
            text_color=BLUE, command=self.open_register
        ).pack()

    def handle_login(self):
        username = self.username.get().strip()
        password = self.password.get()

        if not username or not password:
            self.status_label.configure(text="Please enter both fields.", text_color=RED)
            return

        user = users_collection.find_one({"username": username})

        # user["password"] is a bcrypt hash, not plain text, so we can't use
        # "!=" — bcrypt.checkpw() re-scrambles the typed password the same
        # way and compares the scrambled versions instead.
        if not user or not bcrypt.checkpw(password.encode("utf-8"), user.get("password")):
            self.status_label.configure(text="Incorrect username or password.", text_color=RED)
            return

        self.status_label.configure(text="Login successful!", text_color=GREEN)

        if not user.get("quiz_done", False):
            self.after(800, lambda: self.open_quiz(user["username"]))
        else:
            self.after(800, lambda: self.open_mood_checkin(user["username"]))

    def open_quiz(self, username):
        from quiz import QuizPage
        self.destroy()
        QuizPage(username=username).mainloop()

    def open_mood_checkin(self, username):
        from mood_checkin import MoodCheckinPage
        self.destroy()
        MoodCheckinPage(username=username).mainloop()

    def _show_loading_popup(self, on_complete, duration_ms=1900, label="Setting the stage for your vibes..."):
        popup = ctk.CTkToplevel(self)
        popup.withdraw()
        popup.configure(fg_color=BLUE)

        w, h = 300, 120
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        popup.geometry(f"{w}x{h}+{x}+{y}")

        def reveal():
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.deiconify()
            popup.lift()
            popup.focus_force()

        popup.after(30, reveal)

        win = ctk.CTkFrame(
            popup, width=w, height=h, fg_color=CARD,
            border_width=2, border_color=YELLOW, corner_radius=2
        )
        win.place(x=0, y=0)
        win.pack_propagate(False)

        titlebar = ctk.CTkFrame(win, width=w, height=24, fg_color=YELLOW, corner_radius=0)
        titlebar.place(x=0, y=0)
        ctk.CTkLabel(titlebar, text="SYNC.EXE", font=("Consolas", 11, "bold"), text_color="#111111").place(x=10, y=4)

        ctk.CTkLabel(win, text=label, font=("Consolas", 11, "bold"), text_color=BLUE).place(x=16, y=40)

        bar_bg = ctk.CTkFrame(win, width=268, height=14, fg_color="#333333", corner_radius=0)
        bar_bg.place(x=16, y=64)
        bar_fill = ctk.CTkFrame(bar_bg, width=0, height=14, fg_color=YELLOW, corner_radius=0)
        bar_fill.place(x=0, y=0)

        pct_label = ctk.CTkLabel(win, text="0% COMPLETE", font=("Consolas", 10), text_color=MUTED)
        pct_label.place(x=16, y=86)

        steps = 30
        step_delay = max(1, duration_ms // steps)

        def animate(step=0):
            progress = step / steps
            bar_fill.configure(width=int(268 * progress))
            pct_label.configure(text=f"{int(progress * 100)}% COMPLETE")
            if step < steps:
                popup.after(step_delay, lambda: animate(step + 1))
            else:
                popup.after(150, finish)

        def finish():
            popup.destroy()
            on_complete()

        animate()

    def open_register(self):
        def go():
            self.destroy()
            RegisterPage().mainloop()

        self._show_loading_popup(on_complete=go)


if __name__ == "__main__":
    LoginPage().mainloop()