"""Script to clean up log files by removing test entries."""

# import re # F401: Remove unused import
# import argparse # F401
# import glob # F401
import os
from datetime import datetime  # timedelta was unused
from pathlib import Path

# Get the project root directory (one level up from scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
LOG_FILE = PROJECT_ROOT / "logs" / "scraper" / "scraper.log"
BACKUP_DIR = PROJECT_ROOT / "logs" / "backups"


def clean_log_file():
    """Clean up the log file by removing test entries."""
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Create backup of current log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"scraper_{timestamp}.log")

    try:
        # Read the log file
        with open(LOG_FILE, encoding="utf-8") as f:
            lines = f.readlines()

        # Filter out test.com entries
        cleaned_lines = [
            line
            for line in lines
            if "test.com" not in line
            and not line.strip().endswith('"url": "http://test.com"')
            and not line.strip().endswith('"url": "https://test.com"')
        ]

        # Create backup
        with open(backup_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # Write cleaned logs back to the original file
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)

        print(f"Successfully cleaned log file. Backup saved to {backup_file}")
        return True

    except Exception as e:
        print(f"Error cleaning log file: {e}")
        return False


if __name__ == "__main__":
    clean_log_file()
