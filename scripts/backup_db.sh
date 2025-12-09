#!/bin/bash
# Backup pharmacy_db
# Usage: ./scripts/backup_db.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/pharmacy_db_backup_$TIMESTAMP.sql"

# Create backups directory if it doesn't exist
mkdir -p backups

echo "Creating backup at $BACKUP_FILE..."
docker exec -t pharmacy_db pg_dump -U pharmacy_user pharmacy_db > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
else
    echo "Backup failed!"
    exit 1
fi
