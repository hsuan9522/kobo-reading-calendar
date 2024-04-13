#!/bin/sh
FORCE_ANALYZE=true
FORCE_CONTENT=false
FOLDER="/mnt/onboard/.adds/utils"
EXPORT="$FOLDER/analytics/data/analytics.json"
SQLITE="${FOLDER}/sqlite3"

LD_LIBRARY_PATH="${FOLDER}/lib:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

# Source and destination database file paths
KOBO_DB="/mnt/onboard/.kobo/KoboReader.sqlite"
MY_DB="$FOLDER/analytics/Analytics.sqlite"

current_time=$(date +"%s")

# Set locking mode to NORMAL
locking_mode_sql="PRAGMA locking_mode = NORMAL;"

# Set journal mode to WAL (Write-Ahead Logging)
journal_mode_sql="PRAGMA journal_mode = WAL;"


copyAnalyze() {
    $SQLITE $MY_DB <<EOF
    $locking_mode_sql
    $journal_mode_sql
    -- 寫入執行時間
    INSERT OR REPLACE INTO TimeInfo(Timestamp, Type) VALUES('$current_time', 'analyzeTime');

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

    INSERT OR REPLACE INTO TimeInfo(Timestamp, Type) VALUES('$current_time', 'contentTime');
    INSERT OR REPLACE INTO TimeInfo(Timestamp, Type) VALUES((SELECT MAX(Timestamp) FROM Books), 'contentMaxTime');
EOF
}

calculateReading() {
    # 計算每本書在同一天閱讀的時間
    $SQLITE "$MY_DB" <<EOF > $EXPORT
.headers on
.mode json

SELECT Date, Title, Author,
CAST(printf('%.1f', SUM(ReadingTime) / 60.0) AS REAL) AS TotalMinutesRead
FROM Analytics t1
GROUP BY Date, Title
HAVING TotalMinutesRead >= 1;

.quit
EOF
}

current_time=$(date +"%s")
query_result=$($SQLITE "$MY_DB" "
    SELECT
        IFNULL(MAX(CASE WHEN Type = 'analyzeTime' THEN CAST(Timestamp AS INTEGER) END), NULL),
        MAX(CASE WHEN Type = 'contentMaxTime' THEN Timestamp END)
    FROM TimeInfo;
")
last_running_analyze_time=$(echo "$query_result" | awk -F '|' '{print $1}')
has_content_time=$(echo "$query_result" | awk -F '|' '{print $2}')
new_content_time=$($SQLITE "$KOBO_DB" "SELECT MAX(___SyncTime) FROM content WHERE ContentType = 6 AND isDownloaded = 'true'");

if [ -n "$last_running_analyze_time" ] || [ -n "$has_content_time" ]; then
    current_date=$(date -u -d "@$current_time" "+%Y-%m-%d")

    if [ -n "$has_content_time" ]; then

        # 與最新的 content 時間不同才做
        if [ "$new_content_time" ">" "$has_content_time" ] || [ "$FORCE_CONTENT" = true ]; then
            copyContent
            echo "Do content refresh again..."
        else
            echo "Doesn't need to do content refresh."
        fi
    fi

    if [ -n "$last_running_analyze_time" ]; then
        time_difference=$((current_time - last_running_analyze_time))
        analyze_date=$(date -u -d "@$last_running_analyze_time" "+%Y-%m-%d")

        # 與上次超過 2 hrs 或不同天，就可以再做一次
        if [ "$time_difference" -gt 7200 ] || [ "$current_date" != "$analyze_date" ] || [ "$FORCE_ANALYZE" = true ]; then
            copyAnalyze
            calculateReading
            echo "Do analyze again..."
        else
            echo "Doesn't need to do analyze."
        fi
    fi

else
    copyContent
    copyAnalyze
    calculateReading
    echo "First time..."
fi