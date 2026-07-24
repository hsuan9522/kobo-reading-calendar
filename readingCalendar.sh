#!/bin/sh
set -eu

NICKEL_HS_DIR="/mnt/onboard/.adds/nickel-hs"
BACKUP_DIR="$NICKEL_HS_DIR/backup"
CALENDAR_DIR="$NICKEL_HS_DIR/reading-calendar"
DATA_DIR="$CALENDAR_DIR/data"
IMAGE_DIR="$CALENDAR_DIR/image"
FINALIZED_DIR="$DATA_DIR/.finalized"

previousMonth() {
	current_month=$(date +"%Y-%m")
	year=${current_month%-*}
	month=${current_month#*-}
	month=${month#0}
	month=$((month - 1))

	if [ "$month" -eq 0 ]; then
		month=12
		year=$((year - 1))
	fi

	printf "%04d-%02d" "$year" "$month"
}

case "${1:-}" in
--current)
	target_month=$(date +"%Y-%m")
	python_argument=""
	finalize_previous=false
	;;
--previous)
	target_month=$(previousMonth)
	python_argument="-prev"
	finalize_previous=true
	;;
*)
	echo "Usage: $0 {--current|--previous} [--dev [model]]" >&2
	exit 2
	;;
esac

case "${2:-}" in
"")
	dev_mode=false
	;;
--dev)
	dev_mode=true
	;;
*)
	echo "Usage: $0 {--current|--previous} [--dev [model]]" >&2
	exit 2
	;;
esac

if [ "$dev_mode" = true ]; then
	CALENDAR_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
	model=${3:-nia}

	"$CALENDAR_DIR/calculateReadingStatistics.sh" "$target_month" --dev
	cd "$CALENDAR_DIR"
	python readingCalendar.py \
		--model "$model" \
		--data "$CALENDAR_DIR/data/$target_month.json" \
		--month "$target_month"
	exit 0
fi

if [ -n "${3:-}" ]; then
	echo "A preview model can only be used with --dev." >&2
	exit 2
fi

LOG_DIR="$NICKEL_HS_DIR/logs"
LOG_FILE="$LOG_DIR/reading-calendar.log"
mkdir -p "$LOG_DIR"
exec >"$LOG_FILE" 2>&1
echo "=== Reading Calendar started: $(date) ==="

showFailure() {
	status=$?
	if [ "$status" -ne 0 ]; then
		fbink -qpm -y -2 "Reading Calendar failed. Check logs."
	fi
}
trap showFailure EXIT

mkdir -p "$DATA_DIR" "$IMAGE_DIR" "$FINALIZED_DIR"
if [ ! -f "$CALENDAR_DIR/config.ini" ]; then
	cp "$CALENDAR_DIR/config.ini.default" "$CALENDAR_DIR/config.ini"
fi

fbink -qpm -y -2 "Start Generating..."
fbink -qpm -y -2 "Checking reading data..."
"$BACKUP_DIR/sync.sh" analytics

finalized_marker="$FINALIZED_DIR/$target_month"             #finalized_marker 表示該月份已經在下一個月完成最終統計 = data/.finalized/2026-03
change_marker="$DATA_DIR/.statistics-changed-$target_month" #JSON 有變更時，標記日曆圖片需要重新產生
image_file="$IMAGE_DIR/$target_month.png"

if [ "$finalize_previous" = false ] || [ ! -f "$finalized_marker" ]; then
	#當月 || 上個月沒有封存，則重新產生月度統計
	if [ "$finalize_previous" = true ]; then
		fbink -qpm -y -2 "Last month's file is generating..."
	else
		fbink -qpm -y -2 "Current month's file is generating..."
	fi

	"$CALENDAR_DIR/calculateReadingStatistics.sh" "$target_month"

	if [ -f "$change_marker" ]; then
		fbink -qpm -y -2 "Reading statistics updated."
	else
		fbink -qpm -y -2 "Reading statistics already up to date."
	fi

	if [ "$finalize_previous" = true ]; then
		: >"$finalized_marker" #建立一個零位元檔案，以標記上個月已經完成統計
		fbink -qpm -y -2 "Last month's file is finalized."
	fi
else
	fbink -qpm -y -2 "Last month's file is already finalized."
fi

if [ -f "$change_marker" ] || [ ! -f "$image_file" ]; then
	#JSON 有變更，圖片不存在，重畫
	fbink -qpm -y -2 "Start Drawing..." &
	cd "$CALENDAR_DIR"

	if [ -n "$python_argument" ]; then
		python readingCalendar.py "$python_argument"
	else
		python readingCalendar.py
	fi

	generated_file=$(awk -F': ' '/file_name:/ {print $2; exit}' "$LOG_FILE")
	if [ -z "$generated_file" ]; then
		fbink -qpm -y -2 "No file_name found." &
		echo "No file_name found in the log." >&2
		exit 1
	fi

	rm -f "$change_marker"
	fbink -g file="$generated_file"
else
	fbink -qpm -y -2 "Showing cached calendar..."
	fbink -q -g file="$image_file"
fi
