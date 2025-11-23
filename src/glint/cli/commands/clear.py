"""This is a command to clear the terminal screen"""
import typer
import os

app = typer.Typer()

@app.command()
def clear():
    """Clear the terminal screen"""
    # 'cls' is for windows and 'clear' is for linux and mac
    os.system("cls" if os.name == "nt" else "clear")

    
