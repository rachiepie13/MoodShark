import customtkinter as ctk

ctk.set_appearance_mode("dark")

CARD_W, CARD_H = 230, 190

app = ctk.CTk()
app.geometry("900x350")
app.configure(fg_color="#111111")

row = ctk.CTkFrame(app, fg_color="#111111")
row.pack(fill="x", pady=40, padx=20)

for i in range(4):
    slot = ctk.CTkFrame(row, width=CARD_W, height=CARD_H, fg_color="transparent")
    slot.pack(side="left", padx=10)
    slot.pack_propagate(False)

    card = ctk.CTkFrame(slot, width=CARD_W, height=CARD_H, fg_color="#3A3D40", corner_radius=8)
    card.pack_propagate(False)
    card.place(x=0, y=0)

    ctk.CTkLabel(card, text=f"Card {i+1}", text_color="white").pack(pady=20)

app.mainloop()