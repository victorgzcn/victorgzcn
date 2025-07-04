import shutil
from datetime import datetime

def backup_database():
    backup_file = f"backups/email_recipients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DATABASE, backup_file)
    print(f"✓ Database backed up to {backup_file}")