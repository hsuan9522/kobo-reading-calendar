#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUTPUT_DIR="$PROJECT_DIR/dist"
STAGING_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$STAGING_DIR"
}
trap cleanup EXIT INT TERM

ONBOARD_DIR="$STAGING_DIR/mnt/onboard"
NM_DIR="$ONBOARD_DIR/.adds/nm"
UTILS_DIR="$ONBOARD_DIR/.adds/utils"
ANALYTICS_DIR="$UTILS_DIR/analytics"

mkdir -p "$NM_DIR" "$ANALYTICS_DIR"
mkdir -p "$OUTPUT_DIR"

# NickelMenu configuration
cp -p "$PROJECT_DIR/readingCalendar" "$NM_DIR/"

# Application files. Mutable working files are intentionally not packaged:
# HsKobo.sqlite, config.ini, data/, image/, and log.
cp -p "$PROJECT_DIR/HsKobo.sqlite"      "$UTILS_DIR/HsKobo.sqlite.template"
cp -p "$PROJECT_DIR/copyAnalytics.sh"   "$ANALYTICS_DIR/"
cp -p "$PROJECT_DIR/readingCalendar.py" "$ANALYTICS_DIR/"
cp -p "$PROJECT_DIR/readingCalendar.sh" "$ANALYTICS_DIR/"
cp -p "$PROJECT_DIR/config.ini"         "$ANALYTICS_DIR/config.ini.default"

cp -R "$PROJECT_DIR/fonts" "$ANALYTICS_DIR/"

cp -p "$PROJECT_DIR/sqlite3" "$UTILS_DIR/"

chmod +x "$NM_DIR/readingCalendar"
chmod +x "$ANALYTICS_DIR/copyAnalytics.sh"
chmod +x "$ANALYTICS_DIR/readingCalendar.sh"
chmod +x "$UTILS_DIR/sqlite3"

# 移除 macOS 隱藏檔案
find "$STAGING_DIR" -name ".DS_Store" -delete

OUTPUT_FILE="$OUTPUT_DIR/KoboRoot.tgz"
rm -f "$OUTPUT_FILE"

tar -C "$STAGING_DIR" -czf "$OUTPUT_FILE" mnt

echo "打包完成：$OUTPUT_FILE"
