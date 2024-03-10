#!/bin/sh

FOLDER="/mnt/onboard/.adds/utils"
EXPORT="$FOLDER/analytics/analytics.json"
SQLITE="${FOLDER}/sqlite3"

LD_LIBRARY_PATH="${FOLDER}/lib:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

# Source and destination database file paths
KOBO_DB="/mnt/onboard/.kobo/KoboReader.sqlite"
MY_DB="$FOLDER/analytics/AnalyticsEvent.sqlite"


#複製 AnalyticsEvents & content table
$SQLITE $MY_DB <<EOF
ATTACH DATABASE '$KOBO_DB' AS src;
ATTACH DATABASE '$MY_DB' AS target;

-- Copy Rows from Table A
INSERT OR IGNORE INTO target.AnalyticsEvents
SELECT * FROM src.AnalyticsEvents
WHERE Type IN ('OpenContent', 'LeaveContent');

-- Copy Rows from Table B
INSERT OR IGNORE INTO target.content
SELECT * FROM src.content
WHERE ContentType = 6;

-- Detach Databases
DETACH DATABASE src;
DETACH DATABASE target;
EOF


# 計算每本書在同一天閱讀的時間
$SQLITE "$MY_DB" <<SQLITE_QUERY > $EXPORT
.headers on
.mode json

SELECT 
  strftime('%Y-%m-%d', t1.Timestamp) AS Date,
  COALESCE(json_extract(t1.Attributes, '$.title'), t2.Title) AS Title,
  CAST(printf('%.1f', SUM(json_extract(t1.Metrics, '$.SecondsRead')) / 60.0) AS REAL) AS TotalMinutesRead
FROM AnalyticsEvents t1
LEFT JOIN content t2 
  ON json_extract(t1.Attributes, '$.volumeid') = t2.ContentId -- Adjust the join condition
GROUP BY Date, Title
HAVING TotalMinutesRead >= 1;

.quit
SQLITE_QUERY