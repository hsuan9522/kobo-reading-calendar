# kobo-reading-calendar
嘗試寫出如 KOReader 一樣的閱讀日曆。


### 資料結構
* **/data**
    > 在跑 copyAnalytics.sh 的時候，會順便匯出需要的資料，是計算同一天內單一本書的閱讀時間(分)

* **/fonts**
    > 字型檔案， 要畫出中文字，裡面目前只選用微軟正黑體。

* **/image**
    > 畫完後輸出的日曆圖檔。

* **AnalyticsEvent.sqlite**
    > 用來備份 KoboReader.sqlite 的資料，裡面有三張 table。

        AnalyticsEvent: 
        同於 KoboReader 裡同名的 table。
        但只選了 Type = OpenContent 或 = LeaveContent 的資料。
        
        content:
        同於 KoboReader 裡同名的 table。
        但只選了 ContentType = 6 且 isDownloaded = true 的。

        TimeInfo:
        存執行 copyAnalytics.sh 時間及上面兩張最後更新時間的 Table。


* **copyAnalytics.sh**
    > 因為在我的 Kobo DB 裡的 AnayticsEvent Table 存的資料會不定時消失（目前不知道原因），所以特別寫了這個，可以手動每次都複製裡面的特定資料，存在 AnalyticsEvent 的 DB 裡。

* **readingCalendar.sh**
    > 用來呼叫跑 python 的檔案


* **readingCalendar_local.py**
    > 在本地開發時用的，因為本地沒有裝 FBInk，不好測試。

* **readingCalendar.py**
    > 基本上於上面的沒有不同，只是多了 FBInk 的東西。

