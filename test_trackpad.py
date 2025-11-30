"""
Simple test to detect what events your trackpad generates.
Run this and try scrolling with your trackpad to see what events are captured.
"""
import tkinter as tk

def on_event(event):
    """Print any event that occurs"""
    print(f"Event: {event.type} | Name: {event} | Delta: {getattr(event, 'delta', 'N/A')}")

root = tk.Tk()
root.title("Trackpad Event Tester")
root.geometry("400x300")

label = tk.Label(root, text="Hover mouse here and scroll with trackpad\nCheck terminal for events", 
                 font=("Arial", 14), pady=50)
label.pack(fill="both", expand=True)

# Bind all possible scroll-related events
label.bind("<MouseWheel>", on_event)  # Windows mouse wheel
label.bind("<Button-4>", on_event)     # Linux scroll up
label.bind("<Button-5>", on_event)     # Linux scroll down
label.bind("<Shift-MouseWheel>", on_event)  # Horizontal scroll
label.bind_all("<MouseWheel>", on_event)

instructions = tk.Label(root, text="Watch the terminal/console for event output", 
                       font=("Arial", 10), fg="blue")
instructions.pack(pady=10)

print("=" * 50)
print("Trackpad Event Tester Started")
print("=" * 50)
print("Try scrolling with your trackpad over the window...")
print("Events will appear below:\n")

root.mainloop()
