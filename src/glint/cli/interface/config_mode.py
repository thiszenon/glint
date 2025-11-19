"""Configuration mode for Glint interface """

from rich.console import Console
from rich.panel import Panel
from rich import box

class ConfigMode:
    """configuration mode with settings form"""

    def __init__(self):
        self.topics = []
        self.date_range = "< 7 jours "
        self.time_ranges = ["08h-18h"]
    #end def

    def render(self, console: Console):
        """render the configuration interface"""
        content = [
            "Topics à surveiller :",
            " python , ai, rust" if self.topics else " Aucun topic défini",
            " ",
            " Intervalle de dates:",
            f" {self.date_range}",
            "",
            " Plages horaires de notification:",
        ]

        for tr in self.time_ranges:
            content.append(f" {tr}")
        if not self.time_ranges:
            content.append(" aucune plage définie")
        #end if
        content.extend([
            "",
            "[save]     [Ajouter Topic]     [Modifier plages]"
        ])

        panel = Panel(
            "\n".join(content),
            title = "Configuration",
            box = box.ROUNDED,
            border_style= "green"
        )

        console.print(panel)

if __name__ == "__main__":
    mode = ConfigMode()
    mode.render(Console())