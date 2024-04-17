# kobo-reading-calendar
The data source is the AnalyticsEvent table in Kobo's database. This table records the time from when a book is opened to when it is closed. The reading calendar is generated based on the total time recorded here, so there may be slight discrepancies compared to Kobo's own records of reading time for each book.

Since the data in the AnalyticsEvent table may disappear in some situations, it's not a bug if you can't find your previous reading statistics.

The only way to stop the touch event on Kobo is to shut down the Kobo process, but this leads to a long restart time and is not user-friendly. Therefore, the reading calendar only displays an image cover on the screen; underneath it, Kobo remains active. You need to remember the previous screen and its button placement before opening the calendar. This ensures that when you want to close the calendar, you can simply touch the button to open a fullscreen dialog or book. After that, the screen will refresh, and the calendar will be closed.

** Carefull, I only have a Kobo Nia, so I tested the function on it and have no idea how other models will perform.

![enter image description here](https://raw.githubusercontent.com/hsuan9522/kobo-reading-calendar/master/image/calendar.png)

### Folder structure
```
├── data // Save the exported data.
│   ├── YYYY-MM.json // monthly data
│   ├── fake.json // mock data
│  
├──  fonts // font folder
│   ├── msjh.ttc // font (Chinese, for example)
│  
├── image // output image
│   ├── calendar.png
│ 
├── config.ini // customizable configurations
├── Analytics.sqlite
├── copyAnalytics.sh // calculate reading statistics
├── readingCalendar.sh // run Python
├── readingCalendar.py // create reading calendar
├── readingCalendar_local.py // for local testing
├── success.py // for NickelMenu's chain_success
├── config // NickelMenu configuration
```


* **Analytics.sqlite**
    > Used for analyzing KoboReader.sqlite and storing data related to AnalyticsEvent and content.

        Analytics: Related to the AnalyticsEvent table.
        
        Books: Related to the content table.

        TimeInfo: Stores running time and update time.

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

### Configuration:
Here are the customizable settings:

* **max_event**: Maximum number of books to display per day. If exceeded, it will be shown as "+more".
* **event_bg**: Four sets of gray combinations for the background color of daily events. Corresponds with event_tx.
* **event_tx**: Text color for daily events, paired with event_bg. For example, the first set has a background color of #C4CCD3 and text color of #000000, and so on.
* **font_family**: File name of the font. Place the font in the /fonts folder.
* **font_sm**, font_base, font_md, font_lg, font_xl: Font sizes for different levels.


### TODO:
1. 圖片檔名改存成 YYYY-MM，這樣當分析資料沒有變化時，可以直接讀取圖片
2. 日曆下面的統計，要把列數拉成 config，然後當如果超出幾筆就不要顯示了
3. 如果 max_event > 4 然後顏色只有四組，看看會不會有問題
