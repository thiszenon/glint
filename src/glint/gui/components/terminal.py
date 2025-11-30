import customtkinter as ctk
import re
import io
from contextlib import redirect_stdout
from glint.cli.commands import topics, status, fetch, theme

class Terminal(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.welcome_message = "Glint v0.1.0 producted by xipher .\nType 'help' for commands.\n"
        
        # UI Setup
        self.output = ctk.CTkTextbox(self, height=150, font=("Consolas", 12))
        self.output.insert("0.0", self.welcome_message + "> ")
        self.output.configure(state="disabled")
        
        # Register terminal output as ignored by global scroll handler
        # This allows the terminal to scroll itself instead of the dashboard
        self.app.scroll_handler.add_ignored_widget(self.output)
        
        # Initially hide the terminal output
        self.terminal_visible = False
        
        # Auto-hide when mouse leaves the output area
        self.output.bind("<Leave>", self._on_mouse_leave)
        
        self.input = ctk.CTkEntry(self, placeholder_text="Enter command...", font=("Consolas", 12))
        self.input.pack(fill="x", padx=5, pady=5)
        self.input.bind("<Return>", self.process_command)
        
        # History
        self.command_history = []
        self.history_index = -1
        self.input.bind("<Up>", self.history_up)
        self.input.bind("<Down>", self.history_down)

    def log(self, message):
        self.output.configure(state="normal")
        self.output.insert("end", f"{message}\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _on_mouse_leave(self, event):
        """Hide terminal output when mouse leaves."""
        if self.terminal_visible:
            self.output.pack_forget()
            self.terminal_visible = False

    def strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def history_up(self, event):
        """Navigate up in the command history (older commands)"""
        if not self.command_history:
            return "break"
        
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input.delete(0, "end")
            self.input.insert(0, self.command_history[-(self.history_index + 1)])
        return "break"

    def history_down(self, event):
        """Navigate down in the command history (newer commands)"""
        if self.history_index > 0:
            self.history_index -= 1
            self.input.delete(0, "end")
            self.input.insert(0, self.command_history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self.input.delete(0, "end")
        return "break"

    def process_command(self, event):
        # Auto-expand terminal if hidden
        if not self.terminal_visible:
            self.output.pack(fill="x", padx=5, pady=5, before=self.input)
            self.terminal_visible = True

        cmd_text = self.input.get().strip()
        self.input.delete(0, "end")
        
        if not cmd_text:
            return
        self.command_history.append(cmd_text)
        self.history_index = -1

        # command to clear the terminal
        if cmd_text.lower() == "clear":
            self.output.configure(state="normal")
            self.output.delete("1.0", "end")
            self.output.insert("0.0", self.welcome_message)
            self.output.configure(state="disabled")
            return

        self.log(f"> {cmd_text}")
        
        parts = cmd_text.split()
        command = parts[0].lower()
        args = parts[1:]
        
        # Capture stdout to redirect to GUI terminal
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                if command == "add":
                    if args:
                        topics.add(args[0])
                        self.app.dashboard.refresh_notifications()  # Refresh dashboard
                    else:
                        print("Usage: add <topic>")
                        
                elif command == "list":
                    topics.list_topics()
                    
                elif command == "status":
                    status.status()
                    
                elif command == "fetch":
                    fetch.fetch()
                    self.app.dashboard.refresh_notifications()
                elif command == "theme":
                    if args:
                        if args[0].lower() in ["dark", "light"]:
                            mode = args[0]
                            theme.save_theme_preference(mode)
                            ctk.set_appearance_mode(mode)
                            print(f"Theme set to {mode} mode")
                        elif args[0] == "show":
                            current = theme.load_theme_preference()
                            print(f"Current theme: {current}")
                        else:
                            print("Usage: theme <dark|light|show>")
                    else:
                        # Toggle if no args
                        self.app.toggle_theme()
                    
                elif command == "config":
                    self._handle_config_command(args)
                    
                elif command == "help":
                    self._show_help()
                    
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
            except Exception as e:
                print(f"Error: {e}")
        
        output_str = f.getvalue()
        if output_str:
            clean_output = self.strip_ansi(output_str.strip())
            self.log(clean_output)

    def _handle_config_command(self, args):
        """Handle config subcommands"""
        from glint.cli.commands import config
        
        if len(args) == 0:
            print("Usage: config <subcommand>")
            print("Subcommands: topics, schedule")
            print("Type 'help' for more details.")
            return
        
        subcommand = args[0].lower()
        subargs = args[1:]
        
        if subcommand == "topics":
            if len(subargs) == 0:
                print("Usage: config topics <list|toggle|delete>")
                return
            
            action = subargs[0].lower()
            
            if action == "list":
                config.list_topics()
                
            elif action == "toggle":
                if len(subargs) < 2:
                    print("Usage: config topics toggle <topic_name>")
                else:
                    config.toggle_topic(subargs[1])
                    self.app.dashboard.refresh_notifications()  # Refresh GUI
                    
            elif action == "delete":
                if len(subargs) < 2:
                    print("Usage: config topics delete <topic_name>")
                else:
                    config.delete_topic(subargs[1])
                    self.app.dashboard.refresh_notifications()  # Refresh GUI
            else:
                print(f"Unknown topics action: {action}")
                print("Available: list, toggle, delete")
                
        elif subcommand == "schedule":
            if len(subargs) == 0:
                print("Usage: config schedule <set|show>")
                return
            
            action = subargs[0].lower()
            
            if action == "show":
                config.show_schedule()
                
            elif action == "set":
                if len(subargs) < 3:
                    print("Usage: config schedule set <start_time> <end_time>")
                    print("Example: config schedule set 09:00 18:00")
                else:
                    config.set_schedule(subargs[1], subargs[2])
            else:
                print(f"Unknown schedule action: {action}")
                print("Available: set, show")
        else:
            print(f"Unknown config subcommand: {subcommand}")
            print("Available: topics, schedule")

    def _show_help(self):
        """Display help information"""
        print("=== Glint Commands ===")
        print("")
        print("Core Commands:")
        print("  add <topic>          - Add a new topic to watch")
        print("  list                 - List all watched topics")
        print("  fetch                - Manually fetch latest trends")
        print("  status               - Show system status")
        print("  clear                - Clear terminal screen")
        print("")
        print("Config Commands:")
        print("  config topics list                    - List all topics with status")
        print("  config topics toggle <topic>          - Toggle topic active/inactive")
        print("  config topics delete <topic>          - Delete a topic")
        print("  config schedule set <start> <end>     - Set notification schedule")
        print("  config schedule show                  - Show notification schedule")
        print("")
        print("Examples:")
        print("  add python")
        print("  config topics toggle python")
        print("  config schedule set 09:00 18:00")
        print("  theme <dark|light|show> - Change or show current theme")
