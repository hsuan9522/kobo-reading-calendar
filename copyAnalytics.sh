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
MY_DB="$FOLDER/analytics/AnalyticsEvent.sqlite"

current_time=$(date +"%s")

copyAnalyze() {
    max_timestamp=$($SQLITE $MY_DB "SELECT MAX(Timestamp) FROM AnalyticsEvents");

    $SQLITE $MY_DB <<EOF
	UPDATE TimeInfo SET Timestamp = '$current_time' WHERE Type = 'analyzeTime';
    INSERT OR REPLACE INTO TimeInfo (Timestamp, Type) SELECT '$current_time', 'analyzeTime' WHERE changes() = 0;

    UPDATE TimeInfo SET Timestamp = '$max_timestamp' WHERE Type = 'analyticsMaxTime';
    INSERT OR REPLACE INTO TimeInfo (Timestamp, Type) SELECT '$max_timestamp', 'analyticsMaxTime' WHERE changes() = 0;

    ATTACH DATABASE '$KOBO_DB' AS src;
    ATTACH DATABASE '$MY_DB' AS target;

    INSERT OR IGNORE INTO target.AnalyticsEvents
    SELECT * FROM src.AnalyticsEvents As src_event
    WHERE Type IN ('OpenContent', 'LeaveContent')
    AND src_event.Timestamp > (
        SELECT Timestamp
        FROM target.TimeInfo
        WHERE Type = 'analyticsMaxTime'
    );

    DETACH DATABASE src;
    DETACH DATABASE target;
EOF
}


copyContent() {
    max_timestamp=$($SQLITE $MY_DB "SELECT MAX(___SyncTime) FROM content");

    $SQLITE $MY_DB <<EOF
	UPDATE TimeInfo SET Timestamp = '$current_time' WHERE Type = 'contentTime';
    INSERT OR REPLACE INTO TimeInfo (Timestamp, Type) SELECT '$current_time', 'contentTime' WHERE changes() = 0;

    UPDATE TimeInfo SET Timestamp = '$max_timestamp' WHERE Type = 'contentMaxTime';
    INSERT OR REPLACE INTO TimeInfo (Timestamp, Type) SELECT '$max_timestamp', 'contentMaxTime' WHERE changes() = 0;

    ATTACH DATABASE '$KOBO_DB' AS src;
    ATTACH DATABASE '$MY_DB' AS target;

    INSERT OR IGNORE INTO target.content
    SELECT * FROM src.content AS src_content
    WHERE ContentType = 6 AND isDownloaded = 'true'
    AND src_content.___SyncTime > (
        SELECT Timestamp
        FROM target.TimeInfo
        WHERE Type = 'contentMaxTime'
    );

    DETACH DATABASE src;
    DETACH DATABASE target;
EOF
}

calculateReading() {
    # 計算每本書在同一天閱讀的時間
    $SQLITE "$MY_DB" <<EOF > $EXPORT
.headers on
.mode json

SELECT
strftime('%Y-%m-%d', datetime(t1.Timestamp, '+08:00')) AS Date,
COALESCE(
	json_extract(t1.Attributes, '$.title'),
	(SELECT Title 
	 FROM content
	 WHERE ContentId = json_extract(t1.Attributes, '$.volumeid')
	)
) AS Title,
COALESCE(
	json_extract(t1.Attributes, '$.author'),
	(SELECT Attribution 
	 FROM content
	 WHERE ContentId = json_extract(t1.Attributes, '$.volumeid')
	)
) AS Author,
CAST(printf('%.1f', SUM(json_extract(t1.Metrics, '$.SecondsRead')) / 60.0) AS REAL) AS TotalMinutesRead
FROM AnalyticsEvents t1
WHERE t1.Type = 'LeaveContent'
GROUP BY Date, Title
HAVING TotalMinutesRead >= 1;

.quit
EOF
}

current_time=$(date +"%s")
query_result=$($SQLITE "$MY_DB" "
    SELECT
        IFNULL(MAX(CASE WHEN Type = 'analyzeTime' THEN CAST(Timestamp AS INTEGER) END), 0),
        MAX(CASE WHEN Type = 'contentMaxTime' THEN Timestamp END)
    FROM TimeInfo;
")
last_running_analyze_time=$(echo "$query_result" | awk -F '|' '{print $1}')
has_content_time=$(echo "$query_result" | awk -F '|' '{print $2}')
new_content_time=$($SQLITE "$KOBO_DB" "SELECT MAX(___SyncTime) FROM content WHERE ContentType = 6 AND isDownloaded = 'true'");

if [ -n "$last_running_analyze_time" ] || [ -n "$has_content_time" ]; then
    current_date=$(date -u -d "@$current_time" "+%Y-%m-%d")

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

    if [ -n "$has_content_time" ]; then

        # 與最新的 content 時間不同才做
        if [ "$new_content_time" ">" "$has_content_time" ] || [ "$FORCE_CONTENT" = true ]; then
            copyContent
            echo "Do content refresh again..."
        else
            echo "Doesn't need to do content refresh."
        fi
    fi

else
    copyContent
    copyAnalyze
    calculateReading
    echo "First time..."
fi