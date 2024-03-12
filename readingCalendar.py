#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# To get a Py3k-like print function
from __future__ import print_function
from datetime import datetime
from _fbink import ffi, lib as FBInk
from PIL import Image, ImageDraw, ImageFont
import json
import sys
import calendar

# Let's check which FBInk version we're using...
# NOTE: ffi.string() returns a bytes on Python 3, not a str, hence the extra decode
print("Loaded FBInk {}".format(ffi.string(FBInk.fbink_version()).decode("ascii")))

# And now we're good to go! Let's print "Hello World" in the center of the screen...
# Setup the config...
fbink_cfg = ffi.new("FBInkConfig *")
fbink_cfg.is_centered = True
fbink_cfg.is_halfway = True

fbfd = FBInk.fbink_open()
FBInk.fbink_init(fbfd, fbink_cfg)

state = ffi.new("FBInkState *")
FBInk.fbink_get_state(fbink_cfg, state)
screen_width = state.screen_width
screen_height = state.screen_height


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def get_file(path):
    with open(path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    # Filter data for the current year and month
    filtered_data = [
        entry for entry in data
        if datetime.strptime(entry["Date"], "%Y-%m-%d").year == current_year
        and datetime.strptime(entry["Date"], "%Y-%m-%d").month == current_month
    ]

    return filtered_data

def get_time_format(time):
    return "{:02d}:{:02d}:{:02d}".format(int(time // 60), int(time % 60), int((time % 1) * 60))

def draw_calendar(cal_data, events_data): 
    tmp_event = []
    tmp_day = 0
    tmp_position = {}
    tmp_color = {}
    tmp_total_time = {}
    day_map = {0: False, 1: False, 2: False, 3: False}

    # Define cell size and starting position
    cell_size = (screen_width - 40) // 7
    x_start = 20
    y_start = 200

    # Draw the days of the week
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, day in enumerate(days_of_week):
        draw.text((x_start + i * cell_size, y_start - 45), day, font=font, fill="black")

    for week_num, week in enumerate(cal_data):
        for day_num, day in enumerate(week):
            x = x_start + day_num * cell_size
            y = y_start + week_num * (cell_size + 20)

            # Draw the day number with outline
            if day != 0:
                draw.text((x + 5, y + 3), str(day), font=font_md, fill="black")
                draw.rectangle([x, y, x + cell_size, y + cell_size + 20], outline="black")

            # Check if there are events on this day and draw them
            events_on_day = [event for event in events_data if parse_date(event["Date"]).day == day]
            # print(events_on_day)
            if events_on_day:
                event_height = 20
                event_y = 20 + y

                for i, event in enumerate(events_on_day):
                    event_block_color = gray_palette[(day_num % 4 + i) % 4]
                    event_title = event['Title']
                    # event_title = event['Title'].encode("utf-8").decode("latin1")
                    # print('--', event_title)

                    # print(day, tmp_day, tmp_event, event['Title'])
                    if i >= 4:
                        text = '+more'
                        text_width = 30
                        # textdraw.textbbox((x+1,event_y), text, font=font)
                        draw.text((x + (cell_size - text_width) - 4, event_y + 2 + 4 * event_height), text, font=font_sm, fill="black")
                        tmp_total_time[event_title] = event['TotalMinutesRead']
                        break

                    if tmp_day + 1 == day and event_title in tmp_event:
                        # print('連續事件', event_title)
                        tmp_total_time[event_title] = tmp_total_time[event_title] + event['TotalMinutesRead']
                        if event_title in tmp_position:
                            title_pos, rect_pos = tmp_position[event_title]['title_pos'], tmp_position[event_title]['rect_pos']
                            save_i = tmp_position[event_title]['i']
                            save_color = tmp_color[event_title]
                            day_map[save_i] = True
                            draw.rectangle([x , event_y + save_i * event_height, x + cell_size, event_y + (save_i + 1) * event_height], fill=save_color, outline=None)
                            # 覆蓋掉原本的書名及時間
                            time_format = get_time_format(tmp_total_time[event_title])
                            draw.rectangle(rect_pos, fill=save_color, outline=None)
                            draw.text(title_pos, f"{event_title} ({time_format})", font=font_sm, fill="black")
                        else:
                            # 連續事件，但在上個日期被歸在 +more 裡
                            event_block_color = gray_palette[tmp_i]
                            tmp_i = next((key for key, value in day_map.items() if not value), None) # 找出還有的空位
                            time_format = get_time_format(event['TotalMinutesRead'])
                            tmp_position[event_title] = {
                                'i': tmp_i,
                                'title_pos': (x + 2, event_y + tmp_i * event_height),
                                'rect_pos': [x + 1 , event_y + tmp_i * event_height, x - 1 + cell_size, event_y + (tmp_i + 1) * event_height]
                            }
                            draw.rectangle(tmp_position[event_title]['rect_pos'], fill=event_block_color, outline=None)
                            draw.text(tmp_position[event_title]['title_pos'], f"{event_title} ({time_format})", font=font_sm, fill="black")
                            tmp_color[event_title] = event_block_color
                            day_map[tmp_i] = True

                    else:
                        # print('單一事件', event_title)
                        tmp_i = next((key for key, value in day_map.items() if not value), None)
                        time_format = get_time_format(event['TotalMinutesRead'])
                        tmp_position[event_title] = {
                            'i': tmp_i,
                            'title_pos': (x + 2, event_y + tmp_i * event_height),
                            'rect_pos': [x + 1 , event_y + tmp_i * event_height, x - 1 + cell_size, event_y + (tmp_i + 1) * event_height]
                        }
                        draw.rectangle(tmp_position[event_title]['rect_pos'], fill=event_block_color, outline=None)
                        draw.text(tmp_position[event_title]['title_pos'], f"{event_title} ({time_format})", font=font_sm, fill="black")
                        tmp_color[event_title] = event_block_color
                        day_map[tmp_i] = True
                        tmp_total_time[event_title] = event['TotalMinutesRead']

            tmp_day = day
            seen_titles = set()
            tmp_event = [title['Title'] for title in events_on_day if not (title['Title'] in seen_titles or seen_titles.add(title['Title']))]
            day_map = {0: False, 1: False, 2: False, 3: False}


try:
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Create a new image with a white background    
    image = Image.new("L", (screen_width, screen_height), color="white")
    draw = ImageDraw.Draw(image, "L")

    # Load a font
    # font = ImageFont.load_default()
    font = ImageFont.truetype("./msjh.ttc", 20)
    font_md = ImageFont.truetype("./msjh.ttc", 13)
    font_sm = ImageFont.truetype("./msjh.ttc", 15)

    gray_palette = ['#7C7979', '#A4A2A2', '#908E8E', '#C2C1C1']

    # Get the month's calendar as a list of lists
    cal_data = calendar.monthcalendar(current_year, current_month)

    # Event data
    events_data = get_file('./analytics.json')
    # print(events_data)
    # events_data = [
    #     {"Date": "2024-03-01", "Title": "A", "TotalMinutesRead": 38.1},
    #     {"Date": "2024-03-02", "Title": "A", "TotalMinutesRead": 53.8},
    #     {"Date": "2024-03-03", "Title": "A", "TotalMinutesRead": 67.6},
    #     {"Date": "2024-03-04", "Title": "A", "TotalMinutesRead": 126.4},
    #     {"Date": "2024-03-05", "Title": "B", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-01", "Title": "B", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-01", "Title": "D", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-01", "Title": "C", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-05", "Title": "C", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-06", "Title": "C", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-07", "Title": "C", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-08", "Title": "C", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-09", "Title": "C", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-10", "Title": "C", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-08", "Title": "E", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-09", "Title": "E", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-10", "Title": "E", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-11", "Title": "E", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-10", "Title": "F", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-10", "Title": "G", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-11", "Title": "G", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-12", "Title": "G", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-10", "Title": "K", "TotalMinutesRead": 271.7},
    #     {"Date": "2024-03-10", "Title": "K", "TotalMinutesRead": 271.7},
    # ]

    # Draw calendar
    draw_calendar(cal_data, events_data)
    # Save the image
    image.save('calendar.png')

	# FBInk
    raw_data = image.tobytes("raw")
    raw_len = len(raw_data)
    FBInk.fbink_print_raw_data(
        fbfd, raw_data, image.width, image.height, raw_len, 0, 0, fbink_cfg
    )
    # fbink_cfg.is_flashing = True
    # FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, fbink_cfg)

    # fbink_cfg.is_flashing = False
    # fbink_cfg.is_flashing = False

    # And a few other random examples...
    """
	# A full-screen, flashing refresh
	fbink_cfg.is_flashing = True
	FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, fbink_cfg)

	fbink_cfg.is_flashing = False


	# A (fairly useless) dump & restore cycle (with nightmode enabled for a free inversion)
	dump = ffi.new("FBInkDump *")
	FBInk.fbink_region_dump(fbfd, 350, 350, 250, 250, fbink_cfg, dump)

	fbink_cfg.is_nightmode = True
	fbink_cfg.is_flashing = True
	FBInk.fbink_restore(fbfd, fbink_cfg, dump)

	FBInk.fbink_free_dump_data(dump)

	fbink_cfg.is_nightmode = False
	fbink_cfg.is_flashing = False


	# Fancy OT/TTF printing
	FBInk.fbink_add_ot_font(b"Foo_Bold.ttf", FBInk.FNT_BOLD)
	fbink_ot_cfg = ffi.new("FBInkOTConfig *")
	fbink_ot_cfg.margins.top = 500
	fbink_ot_cfg.margins.bottom = 600
	fbink_ot_cfg.margins.left = 400
	fbink_ot_cfg.margins.right = 50
	fbink_ot_cfg.size_pt = 14.0
	fbink_ot_cfg.is_formatted = True
	FBInk.fbink_print_ot(fbfd, b"**Wheeeee!**", fbink_ot_cfg, fbink_cfg, ffi.NULL)

	FBInk.fbink_free_ot_fonts()


	# Another refresh example, this time with nightmode enabled (i.e., invert the current screen)
	fbink_cfg.is_nightmode = True
	fbink_cfg.is_flashing = True
	FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, fbink_cfg)

	fbink_cfg.is_nightmode = False
	fbink_cfg.is_flashing = False
	# NOTE: We'd just need to disable nightmode to get back the original colors,
	#       as is_nightmode doesn't actually affect the framebuffer content,
	#       the inversion is done by the eInk controller on its own private buffer.
	"""
finally:
    FBInk.fbink_close(fbfd)
