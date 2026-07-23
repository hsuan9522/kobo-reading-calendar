#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PACKAGE_NAME="kobo-reading-calendar"
OUTPUT_DIR="$PROJECT_DIR/dist"
STAGING_DIR=$(mktemp -d)

cleanup() {
    rm -rf "$STAGING_DIR"
}
trap cleanup EXIT INT TERM

PACKAGE_DIR="$STAGING_DIR/$PACKAGE_NAME"
UTILS_DIR="$PACKAGE_DIR/utils"
ANALYTICS_DIR="$UTILS_DIR/analytics"

mkdir -p "$ANALYTICS_DIR"
mkdir -p "$OUTPUT_DIR"

# readingCalendar 與 utils 位於同一層
cp -p "$PROJECT_DIR/readingCalendar" "$PACKAGE_DIR/"

# analytics 相關內容
cp -p "$PROJECT_DIR/HsKobo.sqlite"      "$ANALYTICS_DIR/"
cp -p "$PROJECT_DIR/copyAnalytics.sh"   "$ANALYTICS_DIR/"
cp -p "$PROJECT_DIR/readingCalendar.py" "$ANALYTICS_DIR/"
cp -p "$PROJECT_DIR/readingCalendar.sh" "$ANALYTICS_DIR/"
cp -p "$PROJECT_DIR/config.ini"         "$ANALYTICS_DIR/"

cp -R "$PROJECT_DIR/fonts" "$ANALYTICS_DIR/"
cp -R "$PROJECT_DIR/image" "$ANALYTICS_DIR/"
cp -R "$PROJECT_DIR/data"  "$ANALYTICS_DIR/"

# sqlite3 與 analytics 位於同一層
cp -p "$PROJECT_DIR/sqlite3" "$UTILS_DIR/"

# 設定執行權限
chmod +x "$PACKAGE_DIR/readingCalendar"
chmod +x "$ANALYTICS_DIR/copyAnalytics.sh"
chmod +x "$ANALYTICS_DIR/readingCalendar.sh"
chmod +x "$UTILS_DIR/sqlite3"

# 移除 macOS 隱藏檔案
find "$STAGING_DIR" -name ".DS_Store" -delete

OUTPUT_FILE="$OUTPUT_DIR/$PACKAGE_NAME.zip"
rm -f "$OUTPUT_FILE"

ditto -c -k --norsrc --keepParent \
    "$PACKAGE_DIR" \
    "$OUTPUT_FILE"

echo "打包完成：$OUTPUT_FILE"