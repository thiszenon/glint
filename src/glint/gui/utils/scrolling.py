import customtkinter as ctk

class ScrollHandler:
    def __init__(self, app):
        self.app = app
        self.dashboard = None # Reference to dashboard to check active tab
        self.frames = {} # Map tab names to canvas objects
        self.ignored_widgets = [] # List of widgets to ignore (allow default scroll)

    def set_dashboard(self, dashboard):
        """Set the dashboard reference to check active tabs."""
        self.dashboard = dashboard

    def add_ignored_widget(self, widget):
        """Register a widget to be ignored by the global scroll handler."""
        self.ignored_widgets.append(widget)

    def register_frame(self, tab_name, frame):
        """Register a scrollable frame's canvas."""
        self.frames[tab_name] = frame._parent_canvas
        
        # Bind global handler directly to canvas and frame
        frame._parent_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        frame.bind("<MouseWheel>", self.on_mouse_wheel)

    def on_mouse_wheel(self, event):
        """Global mouse wheel handler that works from anywhere in the window."""
        # Check if event is from an ignored widget (or its children)
        for ignored in self.ignored_widgets:
            # Check if event.widget is the ignored widget or a child of it
            # Tkinter widget names are paths, so we can check if the path starts with the ignored widget's path
            if str(event.widget).startswith(str(ignored)):
                return  # Allow default behavior (don't break)

        if not self.dashboard:
            return "break"

        try:
            active_tab = self.dashboard.get()
            canvas = self.frames.get(active_tab)
            
            if not canvas:
                return "break"
            
            # Smooth scroll with consistent speed everywhere
            scroll_amount = -6 if event.delta > 0 else 6
            canvas.yview_scroll(scroll_amount, "units")
        except Exception as e:
            pass  # Silently ignore errors
        
        return "break"  # Prevent default scrolling

    def setup_global_handler(self):
        """Bind to the main window so it works from anywhere."""
        self.app.bind_all("<MouseWheel>", self.on_mouse_wheel)

    def bind_recursive(self, widget):
        """Recursively bind global scroll to a widget and all its children."""
        try:
            widget.bind("<MouseWheel>", self.on_mouse_wheel, add="+")
        except:
            pass
        for child in widget.winfo_children():
            self.bind_recursive(child)
