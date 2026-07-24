#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUTPUT_DIR="$PROJECT_DIR/dist"
STAGING_DIR=$(mktemp -d)

if [ -z "${BACKUP_SOURCE:-}" ]; then
    if [ -d "$PROJECT_DIR/vendor/hs-kobo-backup" ]; then
        BACKUP_SOURCE="$PROJECT_DIR/vendor/hs-kobo-backup"
    else
        BACKUP_SOURCE="$PROJECT_DIR/../hs-kobo-backup"
    fi
fi

cleanup() {
    rm -rf "$STAGING_DIR"
}
trap cleanup EXIT INT TERM

ONBOARD_DIR="$STAGING_DIR/mnt/onboard"
NM_DIR="$ONBOARD_DIR/.adds/nm"
NICKEL_HS_DIR="$ONBOARD_DIR/.adds/nickel-hs"
BACKUP_DIR="$NICKEL_HS_DIR/backup"
CALENDAR_DIR="$NICKEL_HS_DIR/reading-calendar"

if [ ! -d "$BACKUP_SOURCE" ]; then
    echo "找不到 hs-kobo-backup：$BACKUP_SOURCE" >&2
    exit 1
fi
if [ ! -f "$BACKUP_SOURCE/vendor/lib/libsqlite3.so.0" ]; then
    echo "找不到 SQLite runtime library：$BACKUP_SOURCE/vendor/lib/libsqlite3.so.0" >&2
    exit 1
fi

mkdir -p "$NM_DIR" "$BACKUP_DIR" "$CALENDAR_DIR"
mkdir -p "$OUTPUT_DIR"

# NickelMenu configuration
cp -p "$PROJECT_DIR/readingCalendar" "$NM_DIR/"
cp -p "$BACKUP_SOURCE/src/hsBackup" "$NM_DIR/"

# Application files. Mutable working files are intentionally not packaged:
# HsKobo.sqlite, config.ini, data/, image/, and log.
cp -p "$BACKUP_SOURCE/assets/HsKobo.sqlite.template" "$NICKEL_HS_DIR/"
cp -p "$BACKUP_SOURCE/vendor/sqlite3"                "$NICKEL_HS_DIR/"
cp -R "$BACKUP_SOURCE/vendor/lib"                    "$NICKEL_HS_DIR/"
cp -p "$BACKUP_SOURCE/src/env.sh"                    "$BACKUP_DIR/"
cp -p "$BACKUP_SOURCE/src/sync.sh"                   "$BACKUP_DIR/"
cp -p "$BACKUP_SOURCE/src/syncBooks.sh"              "$BACKUP_DIR/"
cp -p "$BACKUP_SOURCE/src/syncAnalytics.sh"          "$BACKUP_DIR/"
cp -p "$BACKUP_SOURCE/src/syncBookmarks.sh"          "$BACKUP_DIR/"
cp -p "$BACKUP_SOURCE/src/runBackup.sh"              "$BACKUP_DIR/"

cp -p "$PROJECT_DIR/calculateReadingStatistics.sh" "$CALENDAR_DIR/"
cp -p "$PROJECT_DIR/readingCalendar.py"            "$CALENDAR_DIR/"
cp -p "$PROJECT_DIR/readingCalendar.sh"            "$CALENDAR_DIR/"
cp -p "$PROJECT_DIR/config.ini"                    "$CALENDAR_DIR/config.ini.default"

cp -R "$PROJECT_DIR/fonts" "$CALENDAR_DIR/"

chmod +x "$NM_DIR/readingCalendar"
chmod +x "$NM_DIR/hsBackup"
chmod +x "$BACKUP_DIR/sync.sh"
chmod +x "$BACKUP_DIR/syncBooks.sh"
chmod +x "$BACKUP_DIR/syncAnalytics.sh"
chmod +x "$BACKUP_DIR/syncBookmarks.sh"
chmod +x "$BACKUP_DIR/runBackup.sh"
chmod +x "$CALENDAR_DIR/calculateReadingStatistics.sh"
chmod +x "$CALENDAR_DIR/readingCalendar.sh"
chmod +x "$NICKEL_HS_DIR/sqlite3"
chmod 755 "$NICKEL_HS_DIR/lib/libsqlite3.so.0"

# 移除 macOS 隱藏檔案
find "$STAGING_DIR" -name ".DS_Store" -delete

OUTPUT_FILE="$OUTPUT_DIR/KoboRoot.tgz"
rm -f "$OUTPUT_FILE"

tar -C "$STAGING_DIR" -czf "$OUTPUT_FILE" mnt

echo "打包完成：$OUTPUT_FILE"
