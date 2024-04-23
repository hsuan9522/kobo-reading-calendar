#!/bin/sh
fbink -pm -y -2 "Start Generating..."

FORCE_ANALYZE=false
FORCE_CONTENT=false
FOLDER="/mnt/onboard/.adds/utils"
EXPORT="$FOLDER/analytics/data/"
SQLITE="${FOLDER}/sqlite3"

LD_LIBRARY_PATH="${FOLDER}/lib:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

# Source and destination database file paths
KOBO_DB="/mnt/onboard/.kobo/KoboReader.sqlite"
MY_DB="$FOLDER/analytics/Analytics.sqlite"

CURRENT_MONTH=$(date +"%Y-%m")
CURRENT_TIMESTAMP=$(date +"%s")

tmp_year=${CURRENT_MONTH%-*}
tmp_month=$((${CURRENT_MONTH#*-} - 1)) 
if [ $tmp_month -eq 0 ]; then
    tmp_month=12
    tmp_year=$((tmp_year - 1))
fi
LAST_MONTH=$(printf "%d-%02d" $tmp_year $tmp_month)

# Set locking mode to NORMAL
locking_mode_sql="PRAGMA locking_mode = NORMAL;"

# Set journal mode to WAL (Write-Ahead Logging)
journal_mode_sql="PRAGMA journal_mode = WAL;"


copyAnalyze() {
    $SQLITE $MY_DB <<EOF
    $locking_mode_sql
    $journal_mode_sql
    -- 寫入執行時間
    INSERT OR REPLACE INTO TimeInfo(Timestamp, Type) VALUES('$CURRENT_TIMESTAMP', 'analyzeTime');

    ATTACH DATABASE '$KOBO_DB' AS src;
    ATTACH DATABASE '$MY_DB' AS target;

    INSERT OR IGNORE INTO target.Analytics
    SELECT 
        Id,
        t1.Timestamp,
        Attributes,
        Metrics, 
        strftime('%Y-%m-%d', datetime(t1.Timestamp, '+08:00')) AS Date,
        COALESCE(json_extract(Attributes, '$.title'),t2.Title) AS Title,
        COALESCE(json_extract(Attributes, '$.author'),t2.Author) AS Author,
        json_extract(Metrics, '$.SecondsRead') As ReadingTime
    FROM src.AnalyticsEvents As t1
    LEFT JOIN Books As t2 ON t2.ContentId = json_extract(Attributes, '$.volumeid')
    WHERE Type = 'LeaveContent'
    AND t1.Timestamp > COALESCE((
        SELECT Timestamp
        FROM target.TimeInfo
        WHERE Type = 'analyticsMaxTime'
    ), 0);

    DETACH DATABASE src;
    DETACH DATABASE target;

    -- 寫入 analytics 最後一筆的時間
    INSERT OR REPLACE INTO TimeInfo(Timestamp, Type) VALUES((SELECT MAX(Timestamp) FROM Analytics), 'analyticsMaxTime');
EOF
}


copyContent() {
    $SQLITE $MY_DB <<EOF
    $locking_mode_sql
    $journal_mode_sql
    ATTACH DATABASE '$KOBO_DB' AS src;
    ATTACH DATABASE '$MY_DB' AS target;

    INSERT OR IGNORE INTO target.Books
    SELECT ContentID, Title, Attribution As Author, ___SyncTime As Timestamp FROM src.content As t1
    WHERE ContentType = 6
    AND ContentID NOT LIKE 'file://%'
    AND isDownloaded = 'true'
    AND Timestamp > COALESCE((SELECT Timestamp FROM TimeInfo WHERE Type = 'contentMaxTime'), 0);

    DETACH DATABASE src;
    DETACH DATABASE target;

    INSERT OR REPLACE INTO TimeInfo(Timestamp, Type) VALUES('$CURRENT_TIMESTAMP', 'contentTime');
    INSERT OR REPLACE INTO TimeInfo(Timestamp, Type) VALUES((SELECT MAX(Timestamp) FROM Books), 'contentMaxTime');
EOF
}

calculateReading() {
    month="${1:-$CURRENT_MONTH}"
    export_file_name="$EXPORT$month.json"
    # 計算每本書在同一天閱讀的時間
    $SQLITE "$MY_DB" <<EOF > $export_file_name
.headers on
.mode json

SELECT Date, Title, Author,
CAST(printf('%.1f', SUM(ReadingTime) / 60.0) AS REAL) AS TotalMinutesRead
FROM Analytics t1
WHERE strftime('%Y-%m', datetime(Date)) = '$month'
GROUP BY Date, Title
HAVING TotalMinutesRead >= 1;

.quit
EOF
}

$SQLITE <<EOF > /tmp/sqlite_output.txt
.headers off
ATTACH DATABASE '$MY_DB' AS my;
ATTACH DATABASE '$KOBO_DB' AS kobo;
SELECT 
    -- 存在自己 db 裡的最後時間
    COALESCE(MAX(CASE WHEN Type = 'contentMaxTime' THEN Timestamp END), 0),
    COALESCE(MAX(CASE WHEN Type = 'analyticsMaxTime' THEN Timestamp END), 0),
    -- Kobo 裡的最新資料
    (SELECT MAX(___SyncTime) FROM kobo.content WHERE ContentType = 6 AND ContentID NOT LIKE 'file://%' AND isDownloaded = 'true' ),
    (SELECT MAX(Timestamp) FROM kobo.AnalyticsEvents WHERE Type = 'LeaveContent') AS kobo_data
FROM my.TimeInfo;
DETACH DATABASE my;
DETACH DATABASE kobo;
EOF

# Read the output from the temporary file into variables
while IFS='|' read -r cs_content_time cs_analytics_time new_content_time new_analytics_time; do
    break  # Break after the first line
done < /tmp/sqlite_output.txt
# Remove the temporary file
rm /tmp/sqlite_output.txt

if [ -n "$cs_analytics_time" ] || [ -n "$cs_content_time" ]; then
    if [ -n "$cs_content_time" ]; then

        # 與最新的時間不同才做
        if [ "$new_content_time" ">" "$cs_content_time" ] || [ "$FORCE_CONTENT" = true ]; then
            fbink -pm -y -2 "Refresh Books map..."
            copyContent
            echo "Refresh Books map..."
        else
            fbink -pm -y -2 "There are no new books."
            echo "There are no new books."
        fi
    fi

    if [ -n "$cs_analytics_time" ]; then
        # 與最新的時間不同才做
        if [ "$new_analytics_time" ">" "$cs_analytics_time" ] || [ "$FORCE_ANALYZE" = true ]; then
            fbink -pm -y -2 "Generating analytics file..."
            copyAnalyze
            calculateReading
            echo "Generating analytics file..."
        else
            fbink -pm -y -2 "No new analytics events."
            echo "No new analytics events."
        fi
    fi
else
    copyContent
    copyAnalyze
    calculateReading
    echo "First time..."
fi

last_month_file="$EXPORT$LAST_MONTH.json"
if [ ! -f "$last_month_file" ]; then
    fbink -pm -y -2 "Last month's file is generating..."

    calculateReading $LAST_MONTH
    echo "Last month's file is generating..."
else
    fbink -pm -y -2 "No need to generate last month's file."
    echo "No need to generate last month's file."
fi