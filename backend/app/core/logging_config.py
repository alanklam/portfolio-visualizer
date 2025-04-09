import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    # Create logs directory in the project root if it doesn't exist
    project_root = Path(__file__).parent.parent.parent.parent
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s.%(funcName)s - %(message)s'
    )
    
    # Create handlers
    file_handler = RotatingFileHandler(
        logs_dir / 'portfolio.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers and add our handlers
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Set specific log levels for different modules if needed
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)