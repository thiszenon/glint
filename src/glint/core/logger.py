import logging
import os
from pathlib import Path
from rich.logging import RichHandler

def setup_logging(verbose: bool = False):
    """
    Setup logging configuration.
    Logs to a file in .glint/glint.log and to console.
    """
    # Define log directory and file
    glint_dir = Path.home() / ".glint"
    if not glint_dir.exists():
        glint_dir.mkdir(parents=True, exist_ok=True)
        
    log_file = glint_dir / "glint.log"
    
    # Set log level
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG) # Always log debug to file
    
    # Console Handler (using Rich for pretty output)
    console_handler = RichHandler(rich_tracebacks=True, markup=True)
    console_handler.setLevel(level)
    
    # Root Logger
    root_logger = logging.getLogger("glint")
    root_logger.setLevel(logging.DEBUG) # Capture everything at root
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Prevent propagation to root if using other libraries
    root_logger.propagate = False
    
    return root_logger

def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logging.getLogger(f"glint.{name}")
