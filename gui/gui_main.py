import customtkinter as ctk

def launch_gui():
    app = ctk.CTk()
    app.title("Unified Device Control GUI")
    app.geometry("1200x800")
    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(1, weight=1)

    label = ctk.CTkLabel(app, text="Welcome to Unified Device Control GUI!")
    label.pack(pady=20)

    app.mainloop()
