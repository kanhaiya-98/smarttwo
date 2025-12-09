import logging
import logging.handlers
import os
from app.config import settings

def setup_logging():
    """Configure logging to write to both stdout and a rotating file."""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "app.log")
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(name)s - %(levelname)s - %(message)s'
    )
    
    # File Handler (Rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers to avoid duplicates if re-initialized
    root_logger.handlers = []
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").handlers = [] # Let root handle it or keep it separate? 
    # Usually uvicorn configures its own loggers. We might want to hijack them or leave them.
    # For now, let's just ensure OUR app logs go to file.
    
    logger = logging.getLogger("app")
    logger.info(f"Logging configured. Writing to {log_file}")
