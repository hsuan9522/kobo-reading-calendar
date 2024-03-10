# kobo-reading-calendar
嘗試寫出如 KOReader 一樣的閱讀日曆。


### 資料結構
* copyAnalytics.sh
> 因為在我的 Kobo DB 裡的 AnayticsEvent Table 存的資料會不定時消失（目前不知道原因），所以特別寫了這個，可以手動每次都複製裡面的特定資料，存在一個叫 AnalyticsEvent 的 DB（自己新增的）。

* readingCalendar.sh
> 用來呼叫跑 python 的檔案

* example.json
> 在跑 copyAnalytics.sh 的時候，會順便匯出需要的資料，是計算同一天內單一本書的閱讀時間(分)

* readingCalendar_local.py
> 在本地開發時用的，因為本地沒有裝 FBInk，不好測試。

* readingCalendar.py
> 基本上於上面的沒有不同，只是多了 FBInk 的東西。

* msjh.ttc
> 字型檔案，目前還在想辦法用 pillow 畫出中文字。