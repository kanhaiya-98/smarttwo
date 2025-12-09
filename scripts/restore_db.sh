#!/bin/bash
# Restore pharmacy_db
# Usage: ./scripts/restore_db.sh <path_to_backup_file.sql>

if [ -z "$1" ]; then
    echo "Error: no backup file specified."
    echo "Usage: ./scripts/restore_db.sh <backup_file.sql>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: File $BACKUP_FILE not found."
    exit 1
fi

echo "Restoring database from $BACKUP_FILE..."
cat "$BACKUP_FILE" | docker exec -i pharmacy_db psql -U pharmacy_user pharmacy_db

if [ $? -eq 0 ]; then
    echo "Restore successful."
else
    echo "Restore failed!"
    exit 1
fi
