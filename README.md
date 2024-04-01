# kobo-reading-calendar
嘗試寫出如 KOReader 一樣的閱讀日曆。

### 資料夾結構
```
├── data // 執行 copyAnalytics.sh，存放匯出的資料
│   ├── analytics.json // 計算同一天內單一本書的閱讀時間(分)
│   ├── fake.json // 假資料
│  
├──  fonts // 字體資料夾
│   ├── msjh.ttc // 中文字體，python 畫圖的時候會需要
│  
├── image // 
│   ├── calendar.png // 輸出結果範例圖
│ 
├── AnalyticsEvent.sqlite
├── copyAnalytics.sh // 拷貝 kobo 的 content、AnalyticsEvent 兩張表
├── readingCalendar.sh // 執行 python
├── readingCalendar.py // 畫日曆的主要檔案
├── readingCalendar_local.py // for local
```


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







