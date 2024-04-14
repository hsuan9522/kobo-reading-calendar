# kobo-reading-calendar
The data source is the AnalyticsEvent table in Kobo's database. This table records the time from when a book is opened to when it is closed. The reading calendar is generated based on the total time recorded here, so there may be slight discrepancies compared to Kobo's own records of reading time for each book.

Since the data in the AnalyticsEvent table may disappear in some situations, it's not a bug if you can't find your previous reading statistics.

The only way to stop the touch event on Kobo is to shut down the Kobo process, but this leads to a long restart time and isn't user-friendly. Therefore, the reading calendar only displays an image cover on the screen; beneath it, Kobo remains active. You need to remember the previous screen and its button placement before opening the calendar. This ensures that when you want to close the calendar, you can simply touch the button to open a fullscreen dialog or book. After that, the screen will refresh, and the calendar will close.

![enter image description here](https://raw.githubusercontent.com/hsuan9522/kobo-reading-calendar/master/image/calendar.png)

### 資料夾結構
```
├── data // 執行 copyAnalytics.sh，存放匯出的資料
│   ├── YYYY-MM.json // 計算同一天內單一本書的閱讀時間(分)
│   ├── fake.json // 假資料
│  
├──  fonts // 字體資料夾
│   ├── msjh.ttc // 中文字體，python 畫圖的時候會需要
│  
├── image // 
│   ├── calendar.png // 輸出結果範例圖
│ 
├── Analytics.sqlite
├── copyAnalytics.sh // 截取 kobo 的 content、AnalyticsEvent 兩張表
├── readingCalendar.sh // 執行 python
├── readingCalendar.py // 畫日曆的主要檔案
├── readingCalendar_local.py // for local
├── success.py // for nickelMenu chain_success
├── config // nickelMenu's config
```


* **Analytics.sqlite**
    > 用來分析 KoboReader.sqlite 的資料。

        Analytics: 
        截取 KoboReader 裡 AnalyticsEvent table。
        
        Books:
        截取 KoboReader 裡 content table。

        TimeInfo:
        存執行 copyAnalytics.sh 時間及上面兩張最後更新時間的 Table。

## Install:
1. Install [all-in-one package](https://www.mobileread.com/forums/showthread.php?t=254214) (FBInk and other stuff)
2. Install [NickelMenu](https://pgaskin.net/NickelMenu/)
3. Python is not included in an all-in-one package. You need to use telnet to access Kobo and run `tmux new -s kobo update-kobostuff Python`.
4. Download this project ([kobo-reading-calendar](https://github.com/hsuan9522/kobo-reading-calendar/releases/tag/v1.0)).
	*  Copy `utils` folder to `.adds/`
5. Write the NickelMenu configuration.
    * Only the main menu, "Curr Month Cal," will refresh data and generate a new calendar.
    * Analyze in reader menu, refreshing the data will not open the calendar.
```
menu_item   :main   :Last Month Cal   :cmd_spawn      :quiet:python3 /mnt/onboard/.adds/utils/analytics/success.py     
    chain_success   :cmd_spawn   :quiet:/mnt/onboard/.adds/utils/analytics/readingCalendar.sh 1
menu_item   :main   :Curr Month Cal    :cmd_spawn      :quiet:/mnt/onboard/.adds/utils/analytics/copyAnalytics.sh
    chain_success   :cmd_spawn  :quiet:python3 /mnt/onboard/.adds/utils/analytics/success.py
    chain_success   :cmd_spawn  :quiet:/mnt/onboard/.adds/utils/analytics/readingCalendar.sh

menu_item   :reader   :Analyze     :cmd_spawn      :quiet:/mnt/onboard/.adds/utils/analytics/copyAnalytics.sh
    chain_success   :cmd_spawn  :quiet:python3 /mnt/onboard/.adds/utils/analytics/success.py
menu_item   :reader   :Last Month Cal     :cmd_spawn  :quiet:python3 /mnt/onboard/.adds/utils/analytics/success.py     
    chain_success   :cmd_spawn   :quiet:/mnt/onboard/.adds/utils/analytics/readingCalendar.sh 1
menu_item   :reader   :Curr Month Cal     :cmd_spawn  :quiet:python3 /mnt/onboard/.adds/utils/analytics/success.py     
    chain_success   :cmd_spawn   :quiet:/mnt/onboard/.adds/utils/analytics/readingCalendar.sh
```





