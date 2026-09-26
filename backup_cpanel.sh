#!/bin/bash
# Respaldo de la base de datos (leads) y de las imágenes subidas.
# Uso manual:  bash ~/calculadora-inmobiliaria/backup_cpanel.sh
# Cron diario sugerido (cPanel -> Cron Jobs), a las 03:00:
#   0 3 * * * bash $HOME/calculadora-inmobiliaria/backup_cpanel.sh >> $HOME/logs/backup.log 2>&1
# Los respaldos quedan en ~/backups/calculadora (fuera de public_html) y se
# conservan KEEP_DAYS días.
set -e

APP_DIR="$HOME/calculadora-inmobiliaria"
BACKUP_DIR="$HOME/backups/calculadora"
KEEP_DAYS=30
STAMP=$(date +%Y%m%d-%H%M%S)

umask 077
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

# Copia consistente de SQLite aunque la app esté escribiendo (API de backup
# de sqlite3, en vez de copiar el archivo a medio escribir).
if [ -f "$APP_DIR/db.sqlite3" ]; then
    python3 - "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db-$STAMP.sqlite3" <<'EOF'
import sqlite3, sys
src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close()
src.close()
EOF
    gzip "$BACKUP_DIR/db-$STAMP.sqlite3"
fi

if [ -d "$APP_DIR/media" ]; then
    tar -czf "$BACKUP_DIR/media-$STAMP.tar.gz" -C "$APP_DIR" media
fi

find "$BACKUP_DIR" -type f -mtime +$KEEP_DAYS -delete

echo "$(date '+%F %T') respaldo OK en $BACKUP_DIR ($STAMP)"
