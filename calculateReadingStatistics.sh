#!/bin/sh
set -eu

target_month=${1:-}
mode=${2:-"--kobo"}
case "$target_month" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9])
        ;;
    *)
        echo "Usage: $0 YYYY-MM" >&2
        exit 2
        ;;
esac

case "$mode" in
    --kobo)
        NICKEL_HS_DIR="/mnt/onboard/.adds/nickel-hs"
        CALENDAR_DIR="$NICKEL_HS_DIR/reading-calendar"
        SQLITE="$NICKEL_HS_DIR/sqlite3"
        DATABASE="$NICKEL_HS_DIR/HsKobo.sqlite"
        export LD_LIBRARY_PATH="$NICKEL_HS_DIR/lib:${LD_LIBRARY_PATH:-}"
        ;;
    --dev)
        CALENDAR_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
        SQLITE="sqlite3"
        DATABASE="$CALENDAR_DIR/HsKobo.sqlite"
        ;;
    *)
        echo "Usage: $0 YYYY-MM [--kobo|--dev]" >&2
        exit 2
        ;;
esac

DATA_DIR="$CALENDAR_DIR/data"
CHANGE_MARKER="$DATA_DIR/.statistics-changed-$target_month"
output_file="$DATA_DIR/$target_month.json"
temporary_file="$DATA_DIR/.$target_month.json.$$"

cleanup() {
    rm -f "$temporary_file"
}
trap cleanup EXIT INT TERM

mkdir -p "$DATA_DIR"
rm -f "$CHANGE_MARKER"

"$SQLITE" "$DATABASE" <<EOF > "$temporary_file"
.headers on
.mode json
SELECT
    Date,
    Title,
    Author,
    CAST(printf('%.1f', SUM(ReadingTime) / 60.0) AS REAL) AS TotalMinutesRead
FROM Analytics
WHERE strftime('%Y-%m', datetime(Date)) = '$target_month'
GROUP BY Date, Title
HAVING TotalMinutesRead >= 1;
EOF

if [ ! -s "$temporary_file" ]; then
    printf '[]\n' > "$temporary_file"
fi

if [ ! -f "$output_file" ] || ! cmp -s "$temporary_file" "$output_file"; then
    mv "$temporary_file" "$output_file"
    : > "$CHANGE_MARKER"
fi
