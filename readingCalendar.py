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

def get_time_format(time, date_type = 1):
    if date_type == 2:
        return "{:01d}h {:01d}min".format(int(time // 60), int(time % 60))
    else:
        return "{:02d}:{:02d}:{:02d}".format(int(time // 60), int(time % 60), int((time % 1) * 60))

def draw_calendar(events_data): 
    # Get the month's calendar as a list of lists
    cal_data = calendar.monthcalendar(current_year, current_month)
    tmp_event = []
    tmp_day = 0
    tmp_position = {}
    tmp_color = {}
    tmp_total_time = {}
    day_map = {0: False, 1: False, 2: False, 3: False}

    # Define cell size and starting position
    cell_size = (screen_width - 40) // 7
    x_start = 20
    y_start = 150

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
                draw.text((x + 5, y + 3), str(day), font=font_sm, fill="black")
                draw.rectangle([x, y, x + cell_size, y + cell_size + 20], outline="black")

            # Check if there are events on this day and draw them
            events_on_day = [event for event in events_data if parse_date(event["Date"]).day == day]
            # 把連續的閱讀往前排，不然會畫錯
            common_titles = set(event['Title'] for event in events_on_day).intersection(tmp_event)
            events_on_day.sort(key=lambda x: (x['Title'] not in common_titles, x['Title']))
            
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
                        draw.text((x + (cell_size - text_width) - 4, event_y + 2 + 4 * event_height), text, font=font_md, fill="black")
                        tmp_total_time[event_title] = event['TotalMinutesRead']
                        break

                    if tmp_day + 1 == day and event_title in tmp_event:
                        # print('連續事件', event_title)
                        tmp_total_time[event_title] = tmp_total_time[event_title] + event['TotalMinutesRead']
                        
                        if event_title in tmp_position:
                            save_i = tmp_position[event_title]['i']
                            save_color = tmp_color[event_title]
                            day_map[save_i] = True
                            draw.rectangle([x , event_y + save_i * event_height, x + cell_size, event_y + (save_i + 1) * event_height], fill=save_color, outline=None)
                            # 覆蓋掉原本的書名及時間
                            title_pos = tmp_position[event_title]['title_pos']
                            time_format = get_time_format(tmp_total_time[event_title])
                            text = f"{event_title} ({time_format})"
                            left, top, right, bottom = draw.textbbox(title_pos, text, font=font_md)
                            draw.rectangle((left, top, right, bottom), fill=save_color)
                            draw.text(title_pos, text, font=font_md, fill="black")
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
                            draw.text(tmp_position[event_title]['title_pos'], f"{event_title} ({time_format})", font=font_md, fill="black")
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
                        draw.text(tmp_position[event_title]['title_pos'], f"{event_title} ({time_format})", font=font_md, fill="black")
                        tmp_color[event_title] = event_block_color
                        day_map[tmp_i] = True
                        tmp_total_time[event_title] = event['TotalMinutesRead']

            tmp_day = day
            seen_titles = set()
            tmp_event = [title['Title'] for title in events_on_day if not (title['Title'] in seen_titles or seen_titles.add(title['Title']))]
            day_map = {0: False, 1: False, 2: False, 3: False}

def draw_detail(events_data):
    cal_data = calendar.monthcalendar(current_year, current_month)
    weeks = len(cal_data)
    x = 20
    y = 150 + ((screen_width - 40) // 7 + 20) * weeks  + 30
    title_height = 35
    max_line = (screen_height - y) // title_height
    half_width = screen_width // 2

    total_minutes_by_title = {}
    for item in events_data:
        title = item['Title']
        minutes_read = item['TotalMinutesRead']
        total_minutes_by_title[title] = total_minutes_by_title.get(title, 0) + minutes_read

    # Print the total minutes read for each title
    for i, (title, total_minutes) in enumerate(total_minutes_by_title.items()):
        text = f"{title}: {get_time_format(total_minutes, 2)}"
        if i < max_line:
            draw.text((x, y + i * title_height), text, font=font_lg, fill="black")
        elif i < max_line * 2:
            new_i = (i + 1) % max_line - 1
            if new_i < 0:
                new_i = max_line - 1

            draw.text((x + half_width, y + new_i * title_height), text, font=font_lg, fill="black")


try:
    # Create a new image with a white background    
    image = Image.new("L", (screen_width, screen_height), color="white")
    draw = ImageDraw.Draw(image, "L")

    # set date
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Load a font
    # font = ImageFont.load_default()
    font = ImageFont.truetype("./fonts/msjh.ttc", 20)
    font_sm = ImageFont.truetype("./fonts/msjh.ttc", 13)
    font_md = ImageFont.truetype("./fonts/msjh.ttc", 15)
    font_lg = ImageFont.truetype("./fonts/msjh.ttc", 18)

    gray_palette = ['#7C7979', '#A4A2A2', '#908E8E', '#C2C1C1']

    # Event data
    events_data = get_file('./data/analytics.json')
    # print(events_data)

    # Draw calendar
    draw_calendar(events_data)
    draw_detail(events_data)

    # Save the image
    image.save('./image/calendar.png')

	# FBInk
    raw_data = image.tobytes("raw")
    raw_len = len(raw_data)
    FBInk.fbink_print_raw_data(
        fbfd, raw_data, image.width, image.height, raw_len, 0, 0, fbink_cfg
    )

    # And a few other random examples...
    """
	# A full-screen, flashing refresh
	fbink_cfg.is_flashing = True
	FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, fbink_cfg)

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

	"""
finally:
    FBInk.fbink_close(fbfd)
