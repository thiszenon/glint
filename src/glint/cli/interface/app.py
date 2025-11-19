"""Main interface application with mode switching"""

from enum import Enum
from typing import Optional
import sys
import os

from rich.console import Console
from rich.layout import Layout 
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

try:
    from .config_mode import ConfigMode
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from config_mode import ConfigMode

class AppMode(Enum):
    CONFIG = "config"
    TERMINAL = "terminal"
#end AppMode

class GlintInterface:
    """Main interface application with switching mode"""
    def __init__(self):
        self.console = Console()
        self.current_mode :AppMode = AppMode.CONFIG
        self.config_mode = ConfigMode()
        #self.terminal_mode = TerminalMode()
        self.running = True
    #end __init__

    def display_header(self) -> Text:
        """Display the current mode header"""
        header = Text()
        header.append("GLINT INTERFACE",style = "bold blue")
        header.append(" | ")
        header.append("Mode: ",style = "bold")

        if self.current_mode == AppMode.CONFIG:
            header.append("CONFIGURATION", style = "bold green")
        else:
            header.append("TERMINAL",style = "bold yellow")
        
        header.append(" | ")
        header.append("(C)onfig ", style = "dim")
        header.append("(T)erminal ", style="dim")
        header.append("(Q)uit ", style = "dim")
        return header
    #end display_header

    def handle_input(self) -> bool:
        """Handle keyboard input for mode switching"""
        try:
            #Affiche les instructions selon le mode
            if self.current_mode == AppMode.CONFIG:
                self.console.print("\nActions: (1) Topics • (2) Dates • (3) Heures • (S) Save • (T) Terminal • (Q) Quite")
            else:
                self.console.print("\nActions: (C) Config • (Q) Quit")
            key = self.console.input("\nChoix: ").lower()

            if self.current_mode == AppMode.CONFIG:
                #actions in CONFIG mode
                if key == '1':
                    self._edit_topics()
                elif key == '2':
                    self._edit_date_range()
                elif key == '3':
                    self._edit_time_ranges()
                elif key == 's':
                    self._save_config()
                elif key == 't':
                    self.current_mode = AppMode.TERMINAL
                elif key == 'q':
                    return False
            else:
                #Actions in TERMNAL mode

                if key == 'c':
                    self.current_mode = AppMode.CONFIG
                elif key == 'q':
                    return False
        except (EOFError, KeyboardInterrupt):
            return False
        return True
    #end handle_input

    def _edit_topics(self):
        """Edit topics list """
        self.console.print("\n Modification des topics")
        self.console.print("Topics actuels:", ", ".join(self.config_mode.topics) if self.config_mode.topics else "Aucun")
        #new topics
        new_topics = self.console.input("Nouveaux topics : ")
        if new_topics.strip():
            self.config_mode.topics = [topic.strip() for topic in new_topics.split(" ") if topic.strip()]
            self.console.print(f" Topics mis à jour: {','.join(self.config_mode.topics)}")
        else:
            self.console.print("aucun topic saisi")
    #end _edit_topics

    def _edit_date_range(self):
        """Edit date range """
        self.console.print("\n Modification de l'intervalle de dates")
        self.console.print(f"Intervalle actuel: {self.config_mode.date_range}")
        self.console.print("\nOptions:")
        self.console.print("1. < 24 heures")
        self.console.print("2. < 7 jours")
        self.console.print("3. < 30 jours")
        self.console.print("4. Toutes dates")

        choice = self.console.input("choix (1-4): ")
        date_options = {
            '1': '< 24 heures',
            '2': '< 7 jours',
            '3': '< 30 jours',
            '4': 'Toutes dates'
        }
        if choice in date_options:
            self.config_mode.date_range = date_options[choice]
            self.console.print(f"Intervalle mis à jour: {self.config_mode.date_range}")
        else:
            self.console.print("choix invalide")
    #end _edit_date_range
    
    def _edit_time_ranges(self):
        """Edit time ranges"""
        self.console.print("\nModification des plages horaires")
        self.console.print(f"Plages actuelles: {', '.join(self.config_mode.time_ranges)}")
        self.console.print("\nOptions:")
        self.console.print("1. 08h-18h (Bureau)")
        self.console.print("2. 18h-22h (Soirée)")
        self.console.print("3. 22h-08h (Nuit)")
        self.console.print("4. Saisir une plage personnalisée")

        choice = self.console.input("Choix (1-4): ")
        time_options = {
            '1': '08h-18h',
            '2': '18h-22h',
            '3': '22h-08h'
        }
        if choice in time_options:
            self.config_mode.time_ranges = [time_options[choice]]
            self.console.print(f"Plage mis à jour: {self.config_mode.time_ranges[0]}")
        elif choice == '4':
            custom_range = self.console.input("Plage personnalisée")
            if custom_range.strip():
                self.config_mode.time_ranges = [custom_range.strip()]
                self.console.print(f"Plage personnalisée ajoutée: {custom_range}")
        else:
            self.console.print("Choix invalide")
    #end _edit_time_ranges

    def _save_config(self):
        """save configuration"""
        self.console.print("\n Sauvegarde de la configuration...")
        self.console.print(f"Topics: {', '.join(self.config_mode.topics) if self.config_mode.topics else 'Aucun'}")
        self.console.print(f"Intervalle: {self.config_mode.date_range}")
        self.console.print(f"Plages horaires: {', '.join(self.config_mode.time_ranges)}")
        self.console.print("Configuration sauvegardée ")

    def run(self):
        """Main application loop """
        self.console.clear()

        while self.running:
            #display current mode
            header = self.display_header()
            self.console.print(header)
            self.console.print()

            #render current mode
            if self.current_mode == AppMode.CONFIG:
                self.config_mode.render(self.console)
            """
            else:
                self.terminal_mode.render(self.console)
            """
            #handle mode switching
            self.running = self.handle_input()
            self.console.clear()
        #end run
def main():
    """Entry point for the Glint interface"""
    app = GlintInterface()
    app.run()

if __name__ == "__main__":
    main()
