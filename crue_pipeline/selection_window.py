import tkinter as tk
from tkinter import messagebox

def selection_window(recommendations):

    def show_selection():
        selected = choice_var.get()
        if selected:
            return selected
        else:
            return None

    # Create the main window
    root = tk.Tk()
    root.title("EMPFI Option Selector")
    root.geometry("300x200")  # Width x Height
    root.configure(bg='white')

    # Style configuration
    button_bg = '#0078d7'  # Blue color
    button_fg = 'white'
    font_style = ('Arial', 10)

    # Variable to hold the selected choice
    choice_var = tk.StringVar()
    choice_var.set('')

    # Add a label
    label = tk.Label(root, text="Please select an option:", 
                    bg='white', font=font_style)
    label.pack(pady=10)

    # Create radio button frame
    radio_frame = tk.Frame(root, bg='white')
    radio_frame.pack()

    # Create radio buttons with white and blue theme
    choices = []

    for title, i in recommendations:
        choices.append({f"{title}", i})

    print(f"Choices: {choices}")

    for text, value in choices:
        rb = tk.Radiobutton(
            radio_frame, 
            text=text, 
            variable=choice_var, 
            value=value,
            state= "normal",
            bg='white',
            activebackground='white',
            selectcolor='white',
            font=font_style,
            highlightthickness=0,
            indicatoron=1,
            tristatevalue=0
        )
        rb.pack(anchor='w', padx=50)

    # Submit button
    submit_btn = tk.Button(
        root, 
        text="Submit", 
        command=show_selection,
        bg=button_bg,
        fg=button_fg,
        font=font_style,
        activebackground='#005fa3',
        relief='flat',
        padx=15
    )
    submit_btn.pack(pady=15)

    # Run the application
    root.mainloop()