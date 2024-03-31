#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# To get a Py3k-like print function
from __future__ import print_function
from datetime import datetime
from _fbink import ffi, lib as FBInk
from PIL import Image, ImageDraw, ImageFont
import json
import calendar
import time

# Let's check which FBInk version we're using...
# NOTE: ffi.string() returns a bytes on Python 3, not a str, hence the extra decode
# print("Loaded FBInk {}".format(ffi.string(FBInk.fbink_version()).decode("ascii")))

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

# Create a new image with a white background    
image = Image.new("L", (screen_width, screen_height), color="white")
draw = ImageDraw.Draw(image, "L")

# set date
current_year = datetime.now().year
current_month = datetime.now().month
cal_data = calendar.monthcalendar(current_year, current_month)

# Load a font
# font = ImageFont.load_default()
font_path = "./fonts/msjh.ttc"
font_sm = ImageFont.truetype(font_path, 13)
font = ImageFont.truetype(font_path, 15)
font_md = ImageFont.truetype(font_path, 18)
font_lg = ImageFont.truetype(font_path, 20)
font_xl = ImageFont.truetype(font_path, 28)

gray_palette = ['#C4CCD3', '#495057', '#A4ADB6', '#757E86']
font_palette = ['black', '#E3E3E3', 'black', '#E3E3E3']


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
    tmp_event = []
    tmp_day = 0
    tmp_position = {}
    tmp_color = {}
    tmp_total_time = {}
    day_map = {0: False, 1: False, 2: False, 3: False}

    text = f'{current_year}/{current_month}'
    left, top, right, bottom = draw.textbbox((0,0), text, font=font_xl)
    draw.text((screen_width // 2 - (right - left) // 2, 40), text, font=font_xl, fill="black")

    # Define cell size and starting position
    cell_size = (screen_width - 40) // 7
    x_start = 20
    y_start = 150

    # Draw the days of the week
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, day in enumerate(days_of_week):
        draw.text((x_start + i * cell_size, y_start - 35), day, font=font_lg, fill="black")

    total_event_count = 0
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
            common_titles = set(f"{event['Title']}{event['Author']}" for event in events_on_day).intersection(tmp_event)
            events_on_day.sort(key=lambda x: (f"{x['Title']}{x['Author']}" not in common_titles, f"{x['Title']}{x['Author']}"))
            
            # print(events_on_day)
            if events_on_day:
                event_height = 20
                event_y = 20 + y

                for i, event in enumerate(events_on_day):
                    event_block_color = gray_palette[(week_num + total_event_count) % 4]
                    font_color = font_palette[(week_num + total_event_count) % 4]
                    event_book = event['Title']
                    event_title = f"{event['Title']}{event['Author']}"
                    # event_title = event['Title'].encode("utf-8").decode("latin1")

                    # print(day, tmp_day, tmp_event, event['Title'])
                    if i >= 4:
                        text = '+more'
                        text_width = 30
                        # textdraw.textbbox((x+1,event_y), text, font=font_lg)
                        draw.text((x + (cell_size - text_width) - 4, event_y + 2 + 4 * event_height), text, font=font, fill="black")
                        tmp_total_time[event_title] = event['TotalMinutesRead']
                        break

                    if tmp_day + 1 == day and event_title in tmp_event:
                        # print('連續事件', event_title)
                        tmp_total_time[event_title] = tmp_total_time[event_title] + event['TotalMinutesRead']
                        
                        if event_title in tmp_position:
                            save_i = tmp_position[event_title]['i']
                            save_color = tmp_color[event_title]
                            font_color = font_palette[gray_palette.index(save_color)] 
                            day_map[save_i] = True
                            draw.rectangle([x , event_y + save_i * event_height, x + cell_size, event_y + (save_i + 1) * event_height], fill=save_color, outline=None)
                            # 覆蓋掉原本的書名及時間
                            title_pos = tmp_position[event_title]['title_pos']
                            time_format = get_time_format(tmp_total_time[event_title])
                            text = f"{event_book} ({time_format})"
                            left, top, right, bottom = draw.textbbox(title_pos, text, font=font)
                            if left ==  20 + (cell_size * 6) + 2:
                                draw.rectangle((left, top , left + cell_size - 3, bottom), fill=save_color)
                                text = get_text(text, cell_size)
                            else:
                                draw.rectangle((left, top, right, bottom), fill=save_color)
                            draw.text(title_pos, text, font=font, fill=font_color)
                        else:
                            # 連續事件，但在上個日期被歸在 +more 裡
                            event_block_color = gray_palette[tmp_i]
                            font_color = font_palette[tmp_i]
                            tmp_i = next((key for key, value in day_map.items() if not value), None) # 找出還有的空位
                            time_format = get_time_format(event['TotalMinutesRead'])
                            tmp_position[event_title] = {
                                'i': tmp_i,
                                'title_pos': (x + 2, event_y + tmp_i * event_height),
                                'rect_pos': [x + 1 , event_y + tmp_i * event_height, x - 1 + cell_size, event_y + (tmp_i + 1) * event_height]
                            }
                            text = f"{event_book} ({time_format})"
                            text = get_text(text, cell_size)
                            draw.rectangle(tmp_position[event_title]['rect_pos'], fill=event_block_color, outline=None)
                            draw.text(tmp_position[event_title]['title_pos'], text, font=font, fill=font_color)
                            tmp_color[event_title] = event_block_color
                            day_map[tmp_i] = True
                            total_event_count+=1

                    else:
                        # print('單一事件', event_title)
                        tmp_i = next((key for key, value in day_map.items() if not value), None)
                        time_format = get_time_format(event['TotalMinutesRead'])
                        tmp_position[event_title] = {
                            'i': tmp_i,
                            'title_pos': (x + 2, event_y + tmp_i * event_height),
                            'rect_pos': [x + 1 , event_y + tmp_i * event_height + 1, x - 1 + cell_size, event_y + (tmp_i + 1) * event_height]
                        }
                        text = f"{event_book} ({time_format})"
                        text = get_text(text, cell_size)
                        draw.rectangle(tmp_position[event_title]['rect_pos'], fill=event_block_color, outline=None)
                        draw.text(tmp_position[event_title]['title_pos'], text, font=font, fill=font_color)
                        tmp_color[event_title] = event_block_color
                        day_map[tmp_i] = True
                        tmp_total_time[event_title] = event['TotalMinutesRead']
                        total_event_count+=1

            tmp_day = day
            seen_titles = set()
            tmp_event = [f"{title['Title']}{title['Author']}" for title in events_on_day if not (f"{title['Title']}{title['Author']}" in seen_titles or seen_titles.add(f"{title['Title']}{title['Author']}"))]
            day_map = {0: False, 1: False, 2: False, 3: False}

def get_text(string, cell_size):
    i = 0
    width = font.getlength('.') * 3
    for char in string:
        if width < cell_size - 8:
            i += 1
            width += font.getlength(char)

    return string[:int(i)] + "..."


def draw_detail(events_data):
    weeks = len(cal_data)
    x = 20
    y = 150 + ((screen_width - 40) // 7 + 20) * weeks  + 30
    title_height = 35
    max_line = (screen_height - y) // title_height
    half_width = screen_width // 2

    total_minutes_by_title = {}
    for item in events_data:
        title = f"{item['Title']}+{item['Author']}"
        minutes_read = item['TotalMinutesRead']
        total_minutes_by_title[title] = total_minutes_by_title.get(title, 0) + minutes_read

    # Print the total minutes read for each title
    for i, (title, total_minutes) in enumerate(total_minutes_by_title.items()):
        text = f"{title.split('+')[0]}: {get_time_format(total_minutes, 2)}"
        if i < max_line:
            draw.text((x, y + i * title_height), text, font=font_md, fill="black")
        elif i < max_line * 2:
            new_i = (i + 1) % max_line - 1
            if new_i < 0:
                new_i = max_line - 1

            draw.text((x + half_width, y + new_i * title_height), text, font=font_md, fill="black")


def main():
    try:
        start_time = time.time()

        # Event data
        events_data = get_file('./data/analytics.json')
        # print(events_data)

        # Draw calendar
        draw_calendar(events_data)
        draw_detail(events_data)

        # Save the image
        image.save('./image/calendar.png')
        end_time = time.time()
        elapsed_time = end_time - start_time
        draw.text((0 ,0), f"{elapsed_time}", font=font_sm, fill="black")
        # FBInk
        raw_data = image.tobytes("raw")
        raw_len = len(raw_data)
        FBInk.fbink_print_raw_data(
            fbfd, raw_data, image.width, image.height, raw_len, 0, 0, fbink_cfg
        )
        
    finally:
        FBInk.fbink_close(fbfd)

if __name__ == "__main__":
    main()
