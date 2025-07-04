import logging
from pathlib import Path

LOG_DIR = Path("email_logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "email_system.log"),
        logging.StreamHandler()
    ]
)

def log_email(recipient_email, status, details=""):
    logging.info(f"Sent to {recipient_email} | Status: {status} | {details}")