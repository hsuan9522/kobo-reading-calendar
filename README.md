# kobo-reading-calendar

[Chinese Briefing](https://medium.com/@hsuan9522/kobo-reading-calendar-a49f3379935b)

The data source is the AnalyticsEvent table in Kobo's database.This table records the time from when a book is opened to when it is closed. The reading calendar is generated based on the total time recorded here, so there may be slight discrepancies compared to Kobo's own records of reading time for each book.
I'm not sure if it's related to the privacy setting 'share data with Kobo', but I think the default setting is enabled. If you've read books and consistently can't find the data in this table, it might be worth checking this setting.

Since the data in the AnalyticsEvent table may disappear in some situations, it's not a bug if you can't find your previous reading statistics.
I recommend running "Analyze" once before you connect to the Wi-Fi.

The only way to stop the touch event on Kobo is to shut down the Kobo process, but this leads to a long restart time and is not user-friendly. Therefore, the reading calendar only displays an image cover on the screen; underneath it, Kobo remains active. You need to remember the previous screen and its button placement before opening the calendar. This ensures that when you want to close the calendar, you can simply touch the button to open a fullscreen dialog or book. After that, the screen will refresh, and the calendar will be closed.

**Device compatibility:** Calendar layouts can be previewed at the screen
resolutions of multiple Kobo models, but a successful preview does not guarantee
that the full workflow will behave identically on real hardware. Releases from
[v3.0](https://github.com/hsuan9522/kobo-reading-calendar/releases/tag/v3.0)
onward have been verified on a **Clara BW** only; releases up to and including
[v2.3](https://github.com/hsuan9522/kobo-reading-calendar/releases/tag/v2.3)
were verified on a **Nia** only. Other models may work, but have not yet been
tested on a physical device.
Before you run it, I suggest that you backup your device first to avoid any potential crashes. Additionally, this function is not real-time. You may need to wait for a few minutes for it to execute, or execute it twice or more after closing the book. It also may not run quickly, so please be patient.

![example](https://raw.githubusercontent.com/hsuan9522/kobo-reading-calendar/master/image/preview.png)
![real on kobo](https://github.com/hsuan9522/kobo-reading-calendar/blob/master/image/real.jpg)

## Folder structure

```
├── data // Save the exported data.
│   ├── YYYY-MM.json // monthly data
│   ├── fake.json // mock data
│
├── fonts // bundled font and its license
│   ├── NotoSansCJKtc-Regular.otf
│   └── OFL.txt
│
├── image // output image
│   ├── YYYY-MM.png // each month image
│
.adds/
├── nm/
│   ├── readingCalendar // NickelMenu configuration
│   └── hsBackup // NickelMenu configuration
└── nickel-hs/
    ├── sqlite3
    ├── lib/
    │   └── libsqlite3.so.0
    ├── HsKobo.sqlite // created from the template on first use
    ├── logs/ // created at runtime; each run replaces its component log
    │   ├── reading-calendar.log
    │   └── hs-kobo-backup.log
    ├── backup/ // supplied by hs-kobo-backup
    └── reading-calendar/
        ├── config.ini // customizable configurations
        ├── calculateReadingStatistics.sh // export monthly statistics
        ├── readingCalendar.sh // coordinate sync, statistics, cache, and display
        └── readingCalendar.py // create reading calendar
```

- **HsKobo.sqlite**

  > Used for analyzing KoboReader.sqlite and storing data related to AnalyticsEvent and content.

        Analytics: Related to the AnalyticsEvent table.

        Books: Related to the content table.

        TimeInfo: Stores running time and update time.

## Install:

1. Install [KoboStuff](https://www.mobileread.com/forums/showthread.php?t=225030), find KoboStuff in the threads, download and install it.
2. Install [NickelMenu](https://pgaskin.net/NickelMenu/)
3. Python is not included in KoboStuff. You need to use telnet to access Kobo and run `tmux new -s kobo update-kobostuff Python`.
4. Download `KoboRoot.tgz` from the latest
   [release](https://github.com/hsuan9522/kobo-reading-calendar/releases).
5. Copy `KoboRoot.tgz` to the `.kobo/` folder on your Kobo, then safely eject
   the device. Kobo will install it and restart automatically.
6. The same package can be used for both a first install and an upgrade.
   Existing reading data and `config.ini` settings are preserved.

```
menu_item   :main   :Last Month   :cmd_spawn  :quiet:/mnt/onboard/.adds/nickel-hs/reading-calendar/readingCalendar.sh --previous
menu_item   :main   :This Month   :cmd_spawn      :quiet:/mnt/onboard/.adds/nickel-hs/reading-calendar/readingCalendar.sh --current
```

## Uninstall

Connect the Kobo to a computer. Before removing anything, copy the following
file elsewhere if you want to preserve the backup database:

```text
.adds/nickel-hs/HsKobo.sqlite
```

To remove Reading Calendar but keep HS Kobo Backup, manually delete:

```text
.adds/nickel-hs/reading-calendar/
.adds/nickel-hs/logs/reading-calendar.log
.adds/nm/readingCalendar
```

Keep `.adds/nickel-hs/backup/`, `sqlite3`, `lib/`, `HsKobo.sqlite`, and
`.adds/nm/hsBackup`, since they belong to the shared backup installation.

To remove both Reading Calendar and HS Kobo Backup, just delete the complete `.adds/nickel-hs/` directory.

Safely eject and restart the Kobo after deleting the files so NickelMenu reloads
its configuration.

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
font_family = NotoSansCJKtc-Regular.otf	# File name of the font in /fonts.
font_sm = 17	# Font sizes for different levels.
font_base = 19
font_md = 22
font_lg = 34
```

The bundled font is
[Noto Sans CJK Traditional Chinese](https://github.com/notofonts/noto-cjk),
licensed under the SIL Open Font License 1.1. See `fonts/OFL.txt` for the full
license text. Existing installations whose preserved `config.ini` still names
`msjh.ttc` automatically fall back to the bundled Noto font after upgrading.

## Testing

Generate a preview for a supported Kobo model without FBInk or a connected
device:

Install the desktop preview dependency:

```sh
python -m pip install -r requirements-preview.txt
```

Test commands:

```sh
python readingCalendar.py --model nia
```

or

```sh
python readingCalendar.py --model libra-colour \
    --data data/2024-02.json \
    --month 2024-02
```

Supported model names:

| Model           | Resolution  |
| --------------- | ----------- |
| `nia`           | 758 × 1024  |
| `clara`         | 1072 × 1448 |
| `libra`         | 1264 × 1680 |
| `forma`, `sage` | 1440 × 1920 |
| `elipsa`        | 1404 × 1872 |
| `all`           | all models  |

The generated images are written to `preview/`.

The complete local shell workflow can also be tested without FBInk or a Kobo:

```sh
./readingCalendar.sh --current --dev nia
./readingCalendar.sh --previous --dev libra
```

Local mode reads the repository's `HsKobo.sqlite`, uses the computer's
`sqlite3`, and writes preview images to `preview/`. It does not run the backup
sync or call FBInk.

## TODO:

- ~~圖片檔名改存成 YYYY-MM，這樣當分析資料沒有變化時，可以直接讀取圖片~~ (DONE)
- ~~支援刪除過往的日曆圖片~~ (DONE)
- ~~日曆下面的統計，要把列數拉成 config，然後當如果超出幾筆就不要顯示了~~ (NO NEED，原本就是用計算的了，所以不用 config)
- ~~如果 max_event > 4 然後顏色只有四組，看看會不會有問題~~ (DONE)

---

<a href="https://www.buymeacoffee.com/hsuan" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 165px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>

```

```
