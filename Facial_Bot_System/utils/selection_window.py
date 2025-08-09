import tkinter as tk
from tkinter import messagebox

def selection_window(options):
    selected_result = {}
    print("[window] I opened")

    def on_submit():
        selected_index = choice_var.get()
        if selected_index != '':
            nonlocal selected_result
            selected_result = options[int(selected_index)]
            root.destroy()

    # Create the main window
    root = tk.Tk()
    root.title("EMPFI Option Selector")
    root.geometry("350x200")  # Width x Height
    root.configure(bg='white')

    # Style configuration
    button_bg = '#0078d7'  # Blue color
    button_fg = 'white'
    font_style = ('Arial', 10)

    # Variable to hold the selected choice
    choice_var = tk.StringVar(value='__unset__')

    # Add a label
    label = tk.Label(root, bg='white', text="Please select an option:", font=font_style)
    label.pack(pady=10)
 
    # Create radio button frame
    radio_frame = tk.Frame(root, bg='white')
    radio_frame.pack(padx=10, pady=5, fill='x')

    for idx, option in enumerate(options):
        text = f"{option['app_name']} - {option['search_query'] or 'No search query'}"
        rb = tk.Radiobutton(
            radio_frame,
            text=text,
            variable=choice_var,
            value=str(idx),
            bg='white',
            font=font_style,
            state= "normal",
            activebackground='white',
            highlightthickness=0,
            anchor='w',
            justify='left'
        )
        rb.pack(fill='x', anchor='w', padx=10, pady=2)

    submit_btn = tk.Button(
        root, 
        text="Submit", 
        command=on_submit,
        font=font_style,
        bg=button_bg,
        fg=button_fg,
        activebackground='#005fa3',
        relief='flat',
        padx=15
    )
    submit_btn.pack(pady=15)

    # Run the application
    root.mainloop()
    return selected_result
