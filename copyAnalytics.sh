#!/bin/sh

FOLDER="/mnt/onboard/.adds/utils"
EXPORT="$FOLDER/analytics/analytics.json"
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

    -- Copy Rows from Table A
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

    -- Detach Databases
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

    -- Copy Rows from Table B
    ATTACH DATABASE '$KOBO_DB' AS src;
    ATTACH DATABASE '$MY_DB' AS target;

    INSERT OR IGNORE INTO target.content
    SELECT * FROM src.content AS src_content
    WHERE ContentType = 6 AND isDownloaded = true
    AND src_content.___SyncTime > (
        SELECT Timestamp
        FROM target.TimeInfo
        WHERE Type = 'contentMaxTime'
    );

    -- Detach Databases
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
strftime('%Y-%m-%d', t1.Timestamp) AS Date,
COALESCE(json_extract(t1.Attributes, '$.title'), t2.Title) AS Title,
CAST(printf('%.1f', SUM(json_extract(t1.Metrics, '$.SecondsRead')) / 60.0) AS REAL) AS TotalMinutesRead
FROM AnalyticsEvents t1
LEFT JOIN content t2 
ON json_extract(t1.Attributes, '$.volumeid') = t2.ContentId -- Adjust the join condition
WHERE t1.Type = 'LeaveContent'
GROUP BY Date, Title
HAVING TotalMinutesRead >= 1;

.quit
EOF
}

current_time=$(date +"%s")
last_running_analyze_time=$($SQLITE "$MY_DB" "SELECT IFNULL(CAST(Timestamp AS INTEGER), 0) FROM TimeInfo WHERE Type = 'analyzeTime';")
last_running_content_time=$($SQLITE "$MY_DB" "SELECT IFNULL(CAST(Timestamp AS INTEGER), 0) FROM TimeInfo WHERE Type = 'contentTime';")

if [ -n "$last_running_analyze_time" ] || [ -n "$last_running_content_time" ]; then
    if [ -n "$last_running_analyze_time" ]; then
        time_difference=$((current_time - last_running_analyze_time))

        # 與上次超過 6 hrs 就可以再做一次
        if [ "$time_difference" -gt 21600 ]; then
            copyAnalyze
            calculateReading
            echo "Do analyze again..."
        else
            echo "Doesn't need to do analyze."
        fi
    fi

    if [ -n "$last_running_content_time" ]; then
        time_difference=$((current_time - last_running_content_time))

        # 與上次超過 12 hrs 就可以再做一次
        if [ "$time_difference" -gt 43200 ]; then
            copyContent
            
            echo "Do content refresh again..."
        else
            echo "Doesn't need to do content refresh."
        fi
    fi

else
    copyAnalyze
    copyContent
    calculateReading
    echo "First time..."
fi