# kobo-reading-calendar

[Chinese Briefing](https://medium.com/@hsuan9522/kobo-reading-calendar-a49f3379935b)

The data source is the AnalyticsEvent table in Kobo's database.This table records the time from when a book is opened to when it is closed. The reading calendar is generated based on the total time recorded here, so there may be slight discrepancies compared to Kobo's own records of reading time for each book.
I'm not sure if it's related to the privacy setting 'share data with Kobo', but I think the default setting is enabled. If you've read books and consistently can't find the data in this table, it might be worth checking this setting.

Since the data in the AnalyticsEvent table may disappear in some situations, it's not a bug if you can't find your previous reading statistics.
I recommend running "Analyze" once before you connect to the Wi-Fi.

The only way to stop the touch event on Kobo is to shut down the Kobo process, but this leads to a long restart time and is not user-friendly. Therefore, the reading calendar only displays an image cover on the screen; underneath it, Kobo remains active. You need to remember the previous screen and its button placement before opening the calendar. This ensures that when you want to close the calendar, you can simply touch the button to open a fullscreen dialog or book. After that, the screen will refresh, and the calendar will be closed.

** Please note, [v2.3](https://github.com/hsuan9522/kobo-reading-calendar/releases/tag/v2.3) has only been tested on the **Nia**, and [v3.0](https://github.com/hsuan9522/kobo-reading-calendar/releases/tag/v3.0) has only been tested on the **Clara BW**.
Before you run it, I suggest that you backup your device first to avoid any potential crashes. Additionally, this function is not real-time. You may need to wait for a few minutes for it to execute, or execute it twice or more after closing the book. It also may not run quickly, so please be patient.

![example](https://raw.githubusercontent.com/hsuan9522/kobo-reading-calendar/master/image/2024-03.png)
![real on kobo](https://github.com/hsuan9522/kobo-reading-calendar/blob/master/image/real.jpg)

## Folder structure
```
├── data // Save the exported data.
│   ├── YYYY-MM.json // monthly data
│   ├── fake.json // mock data
│  
├──  fonts // font folder
│   ├── msjh.ttc // font (Chinese, for example)
│  
├── image // output image
│   ├── YYYY-MM.png // each month image
│ 
├── config.ini // customizable configurations
├── Analytics.sqlite
├── copyAnalytics.sh // calculate reading statistics
├── readingCalendar.sh // run Python
├── readingCalendar.py // create reading calendar
├── drawInfo.py // show info text
├── config // NickelMenu configuration
```


* **Analytics.sqlite**
    > Used for analyzing KoboReader.sqlite and storing data related to AnalyticsEvent and content.

        Analytics: Related to the AnalyticsEvent table.
        
        Books: Related to the content table.

        TimeInfo: Stores running time and update time.

## Install:
1. Install [all-in-one package](https://www.mobileread.com/forums/showthread.php?t=254214) (FBInk and other stuff)
    * Since FBInk's official website currently does not have the latest build, I built it myself. If you are using the newest Kobo device, you need to install this version of [FBInk](https://github.com/hsuan9522/kobo-reading-calendar/raw/feature/kobo-clara-bw/KoboRoot.tgz) again until the newest version becomes available.
2. Install [NickelMenu](https://pgaskin.net/NickelMenu/)
3. Python is not included in an all-in-one package. You need to use telnet to access Kobo and run `tmux new -s kobo update-kobostuff Python`.
4. Download this project ([kobo-reading-calendar](https://github.com/hsuan9522/kobo-reading-calendar/releases)).
	*  Copy `utils` folder to `.adds/`
5. Write the NickelMenu configuration. There are four kind of command.
    * Analysis is crucial; run either "**Analyze**" or "**Analyze & Curr Month Cal**" before "**Curr Month Cal**" and **"Last Month Cal**".
    * "**Curr Month Cal**" and "**Last Month Cal**" only display calendars; they don't calculate data.
```
menu_item   :main   :Analyze     :cmd_spawn      :quiet:/mnt/onboard/.adds/utils/analytics/copyAnalytics.sh   
menu_item   :main   :Analyze & Curr Month Cal    :cmd_spawn      :quiet:/mnt/onboard/.adds/utils/analytics/copyAnalytics.sh -cal
menu_item   :reader   :Curr Month Cal   :cmd_spawn  :quiet:/mnt/onboard/.adds/utils/analytics/readingCalendar.sh
menu_item   :reader   :Last Month Cal   :cmd_spawn  :quiet:/mnt/onboard/.adds/utils/analytics/readingCalendar.sh -prev
```

## Configuration:
Here are the customizable settings:

```ini
[General]
max_event = 4	# Max books/day to display; if exceeded, show "+more".
max_image = 2   # Maximum image storage in /image.
event_height = 30 # Height of each book's event **v3.0**

[Color]
event_bg = #999999, #444444, #BBBBBB, #666666	# Four gray background for events.
event_tx = #000000, #DDDDDD, #000000, #DDDDDD	# Pair text color with event_bg, e.g., #999999 background with #000000 text.

[Font]
font_family = msjh.ttc	# File name of the font, which is in the /fonts folder.
font_sm = 13	# Font sizes for different levels.
font_base = 20
font_md = 24
font_lg = 36
```

## TODO:
* ~~圖片檔名改存成 YYYY-MM，這樣當分析資料沒有變化時，可以直接讀取圖片~~ (DONE)
* ~~支援刪除過往的日曆圖片~~ (DONE)
* ~~日曆下面的統計，要把列數拉成 config，然後當如果超出幾筆就不要顯示了~~ (NO NEED，原本就是用計算的了，所以不用 config)
* ~~如果 max_event > 4 然後顏色只有四組，看看會不會有問題~~ (DONE)


---

<a href="https://www.buymeacoffee.com/hsuan" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 165px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
