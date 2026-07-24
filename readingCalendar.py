#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# To get a Py3k-like print function
from __future__ import print_function
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import configparser
import json
import calendar
import time
import sys
import os
import glob

MODEL_SCREENS = {
    'nia': (758, 1024),
    'clara': (1072, 1448),
    'libra': (1264, 1680),
    'forma': (1440, 1920),
    'sage': (1440, 1920),
    'elipsa': (1404, 1872),
}

CLARA_SCREEN = MODEL_SCREENS['clara']


def get_option(name):
    if name not in sys.argv:
        return None

    index = sys.argv.index(name)
    if index + 1 >= len(sys.argv):
        raise ValueError(f'Missing value for {name}')

    return sys.argv[index + 1]


preview_model = get_option('--model')
preview_data_file = get_option('--data')
preview_month = get_option('--month')
preview_mode = preview_model is not None
previous_month = not preview_mode and len(sys.argv) > 1

if preview_mode:
    preview_model = preview_model.lower()
    if preview_model != 'all' and preview_model not in MODEL_SCREENS:
        supported = ', '.join(sorted(MODEL_SCREENS))
        raise ValueError(f'Unknown model "{preview_model}". Supported models: all, {supported}')

# Let's check which FBInk version we're using...
# NOTE: ffi.string() returns a bytes on Python 3, not a str, hence the extra decode
# print("Loaded FBInk {}".format(ffi.string(FBInk.fbink_version()).decode("ascii")))

# Setup the config...
config = configparser.ConfigParser()
config.read('config.ini')

if preview_mode:
    initial_model = next(iter(MODEL_SCREENS)) if preview_model == 'all' else preview_model
    screen_width, screen_height = MODEL_SCREENS[initial_model]
    fbfd = None
    fbink_cfg = None
else:
    from _fbink import ffi, lib as FBInk

    fbink_cfg = ffi.new("FBInkConfig *")
    fbink_cfg.is_centered = True
    fbink_cfg.is_halfway = True
    fbink_cfg.is_quiet = True

    fbfd = FBInk.fbink_open()
    FBInk.fbink_init(fbfd, fbink_cfg)

    state = ffi.new("FBInkState *")
    FBInk.fbink_get_state(fbink_cfg, state)

    screen_width = state.screen_width
    screen_height = state.screen_height

# Create a new image with a white background    
image = Image.new("L", (screen_width, screen_height), color="white")
draw = ImageDraw.Draw(image, "L")

font_path = f"./fonts/{config['Font']['font_family']}"


def scaled(value, scale, minimum=1):
    return max(minimum, int(round(value * scale)))


def configure_layout():
    global layout
    global font
    global font_sm
    global font_md
    global font_lg

    scale = min(
        screen_width / CLARA_SCREEN[0],
        screen_height / CLARA_SCREEN[1],
    )
    layout = {
        'scale': scale,
        'margin': scaled(20, scale),
        'title_y': scaled(100, scale),
        'calendar_y': scaled(230, scale),
        'weekday_gap': scaled(40, scale),
        'cell_extra_height': scaled(30, scale),
        'event_height': scaled(int(config['General']['event_height']), scale),
        'detail_gap': scaled(20, scale),
        'detail_line_height': scaled(40, scale),
    }

    font = ImageFont.truetype(
        font_path,
        scaled(int(config['Font']['font_base']), scale),
    )
    font_sm = ImageFont.truetype(
        font_path,
        scaled(int(config['Font']['font_sm']), scale),
    )
    font_md = ImageFont.truetype(
        font_path,
        scaled(int(config['Font']['font_md']), scale),
    )
    font_lg = ImageFont.truetype(
        font_path,
        scaled(int(config['Font']['font_lg']), scale),
    )


configure_layout()

gray_palette = [item.strip() for item in config['Color']['event_bg'].split(',')]
font_palette = [item.strip() for item in config['Color']['event_tx'].split(',')]


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def get_file(path):
    with open(path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    return data

def get_time_format(time, date_type = 1):
    if date_type == 2:
        return "{:01d}h {:01d}min".format(int(time // 60), int(time % 60))
    else:
        return "{:02d}:{:02d}:{:02d}".format(int(time // 60), int(time % 60), int((time % 1) * 60))

def init_day_map(count):
    day_map = {}
    for i in range(count):
        day_map[i] = False
    return day_map

def draw_calendar(events_data, date):
    global gray_palette
    global font_palette
    global week_hours
    global day_hours

    current_year = date.year
    current_month = date.month
    current_day = date.day
    cal_data = calendar.monthcalendar(current_year, current_month)
    # Get the month's calendar as a list of lists
    tmp_event = []
    tmp_day = 0
    tmp_position = {}
    tmp_color = {}
    tmp_total_time = {}

    event_height = layout['event_height']
    max_count = int(config['General']['max_event'])
    day_map = init_day_map(max_count)
    
    if max_count > 4 and len(gray_palette) < max_count:
        tmp1 = []
        tmp2 = []
        for i in range(max_count):
            tmp1.append(gray_palette[i % 4])
            tmp2.append(font_palette[i % 4])
        gray_palette = tmp1
        font_palette = tmp2


    text = f'{current_year}/{current_month}'
    left, top, right, bottom = draw.textbbox((0,0), text, font=font_lg)
    draw.text((screen_width // 2 - (right - left) // 2, layout['title_y']), text, font=font_lg, fill="black")

    # Define cell size and starting position
    rec_width = (screen_width - layout['margin'] * 2) // 7
    global rec_height
    rec_height = rec_width + layout['cell_extra_height']
    x_start = layout['margin']
    y_start = layout['calendar_y']

    # Draw the days of the week
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, day in enumerate(days_of_week):
        draw.text((x_start + i * rec_width, y_start - layout['weekday_gap']), day, font=font_md, fill="black")

    total_event_count = 0
    for week_num, week in enumerate(cal_data):
        tmp_week_hours = 0
        for day_num, day in enumerate(week):
            tmp_day_hours = 0
            x = x_start + day_num * rec_width
            y = y_start + week_num * rec_height

            # Draw the day number with outline
            if day != 0:
                if current_day == day and datetime.now().month == current_month:
                    draw.ellipse((x + 4, y + 3, x + 26, y + 26), fill='#bdbebf')
                draw.text((x + 5, y + 3), str(day), font=font_sm, fill="black")
                draw.rectangle([x, y, x + rec_width, y + rec_height], outline="black")

            # Check if there are events on this day and draw them
            events_on_day = [event for event in events_data if parse_date(event["Date"]).day == day]
            # 把連續的閱讀往前排，不然會畫錯
            common_titles = set(f"{event['Title']}{event['Author']}" for event in events_on_day).intersection(tmp_event)
            events_on_day.sort(key=lambda x: (f"{x['Title']}{x['Author']}" not in common_titles, f"{x['Title']}{x['Author']}"))
            
            # print(events_on_day)
            if events_on_day:
                event_y = event_height + y

                for i, event in enumerate(events_on_day):
                    tmp_week_hours += event['TotalMinutesRead']
                    tmp_day_hours += event['TotalMinutesRead']
                    tmp_index = (week_num + total_event_count) % max_count
                    event_block_color = gray_palette[tmp_index]
                    font_color = font_palette[tmp_index]
                    event_book = event['Title']
                    event_title = f"{event['Title']}{event['Author']}"
                    # event_title = event['Title'].encode("utf-8").decode("latin1")

                    # print(day, tmp_day, tmp_event, event['Title'])
                    if i >= max_count:
                        text = '+more'
                        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                        draw.text((x + (rec_width - (right - left)) - 4, event_y + max_count * event_height), text, font=font, fill="black")
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
                            draw.rectangle([x , event_y + save_i * event_height + 1, x + rec_width, event_y + (save_i + 1) * event_height], fill=save_color, outline=None)
                            # 覆蓋掉原本的書名及時間
                            title_pos = tmp_position[event_title]['title_pos']
                            event_right = x + rec_width

                            # A Sunday-to-Monday event starts a new visual
                            # segment because it cannot continue horizontally
                            # across calendar rows.
                            if x < title_pos[0]:
                                title_pos = (
                                    x + 2,
                                    event_y + save_i * event_height,
                                )
                                tmp_position[event_title]['title_pos'] = title_pos

                            time_format = get_time_format(tmp_total_time[event_title])
                            text = f"{event_book} ({time_format})"
                            left, top, right, bottom = draw.textbbox(title_pos, text, font=font)
                            available_width = event_right - title_pos[0] - 2
                            draw.rectangle((left, top, event_right, bottom), fill=save_color)
                            text = get_text_for_font(text, available_width, font)
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
                                'rect_pos': [x + 1 , event_y + tmp_i * event_height, x - 1 + rec_width, event_y + (tmp_i + 1) * event_height]
                            }
                            text = f"{event_book} ({time_format})"
                            text = get_text_for_font(text, rec_width - 8, font)
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
                            'rect_pos': [x + 1 , event_y + tmp_i * event_height + 1, x - 1 + rec_width, event_y + (tmp_i + 1) * event_height]
                        }
                        text = f"{event_book} ({time_format})"
                        text = get_text_for_font(text, rec_width - 8, font)
                        draw.rectangle(tmp_position[event_title]['rect_pos'], fill=event_block_color, outline=None)
                        draw.text(tmp_position[event_title]['title_pos'], text, font=font, fill=font_color)
                        tmp_color[event_title] = event_block_color
                        day_map[tmp_i] = True
                        tmp_total_time[event_title] = event['TotalMinutesRead']
                        total_event_count+=1

            tmp_day = day
            seen_titles = set()
            tmp_event = [f"{title['Title']}{title['Author']}" for title in events_on_day if not (f"{title['Title']}{title['Author']}" in seen_titles or seen_titles.add(f"{title['Title']}{title['Author']}"))]
            day_map = init_day_map(max_count)

            if current_day == day and datetime.now().month == current_month:
                week_hours = tmp_week_hours
                day_hours = tmp_day_hours

def get_text_for_font(string, width, selected_font):
    if selected_font.getlength(string) <= width:
        return string

    suffix = "..."
    suffix_width = selected_font.getlength(suffix)
    current_width = 0
    result = []
    for char in string:
        char_width = selected_font.getlength(char)
        if current_width + char_width + suffix_width > width:
            break
        result.append(char)
        current_width += char_width

    return ''.join(result) + suffix


def draw_detail(events_data, date):
    cal_data = calendar.monthcalendar(date.year, date.month)
    weeks = len(cal_data)
    x = layout['margin']
    y = layout['calendar_y'] + rec_height * weeks + layout['detail_gap']
    title_height = layout['detail_line_height']
    half_width = screen_width // 2
    is_clara_layout = (screen_width, screen_height) == CLARA_SCREEN

    if is_clara_layout:
        max_line = (screen_height - y) // title_height
        total_y = y - 10 + max_line * title_height
    else:
        total_y = screen_height - layout['margin'] - title_height
        if y > total_y:
            raise ValueError(
                f'Calendar layout exceeds the detail area at '
                f'{screen_width}x{screen_height}'
            )
        max_line = max(0, (total_y - y) // title_height)

    total_minutes_by_title = {}
    for item in events_data:
        title = f"{item['Title']}+{item['Author']}"
        minutes_read = item['TotalMinutesRead']
        total_minutes_by_title[title] = total_minutes_by_title.get(title, 0) + minutes_read

    # Print the total minutes read for each title
    month_hours = 0
    for i, (title, total_minutes) in enumerate(total_minutes_by_title.items()):
        month_hours += total_minutes
        text = f"{title.split('+')[0]}: {get_time_format(total_minutes, 2)}"
        text = get_text_for_font(text, half_width - layout['margin'] * 2, font_md)
        if i < max_line:
            draw.text((x, y + i * title_height), text, font=font_md, fill="black")
        elif not is_clara_layout and max_line > 0 and i < max_line * 2:
            new_i = i - max_line
            draw.text((x + half_width, y + new_i * title_height), text, font=font_md, fill="black")
        elif is_clara_layout and max_line > 0 and i < (max_line * 2) - 1:
            new_i = (i + 1) % max_line - 1
            if new_i < 0:
                new_i = max_line - 1
            draw.text((x + half_width, y + new_i * title_height), text, font=font_md, fill="black")

    if previous_month or preview_mode:
        text = f"Total: {get_time_format(month_hours, 2)}"
    else:
        text = f"Total: {get_time_format(day_hours, 2)} / {get_time_format(week_hours, 2)} / {get_time_format(month_hours, 2)}"
    text = get_text_for_font(text, half_width - layout['margin'] * 2, font_md)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font_md)
    total_y = min(total_y, screen_height - bottom - 2)
    draw.text((x + half_width, total_y), text, font=font_md, fill="black")

def check_image(name):
    if os.path.exists(name):
        mod_time = os.path.getmtime(name)
        mod_time = datetime.fromtimestamp(mod_time)
        now = datetime.now()
        if(mod_time.year == now.year and mod_time.month == now.month):
            return True
        else:
            return False
    else:
        return False

def remove_image():
    count = int(config['General']['max_image'])
    folder_path = './image'

    all_images = glob.glob(os.path.join(folder_path, '*.png'))
    if len(all_images) <= count:
        return

    date = datetime.now()
    max_month = (date.replace(day=1) - timedelta(days=30*count)).replace(day=1)

    # Delete images older than the last two months
    for image_path in all_images:
        file_name = os.path.basename(image_path).split('.')[0]
        
        year, month = map(int, file_name.split('-'))
        image_date = datetime(year, month, 1)
        if image_date < max_month:
            try:
                os.remove(image_path)
                print(f"Deleted image: {image_path}")
            except OSError as e:
                print(f"Error deleting image {image_path}: {e}")

def main():
    global screen_width
    global screen_height
    global image
    global draw
    global gray_palette
    global font_palette

    try:
        start_time = time.time()

        if preview_mode:
            file_name = preview_data_file or './data/2024-02.json'
            events_data = get_file(file_name)
            if preview_month:
                date = datetime.strptime(preview_month, '%Y-%m')
            elif events_data:
                date = parse_date(events_data[0]['Date']).replace(day=1)
            else:
                date = datetime.now().replace(day=1)

            dayMonth = date.strftime('%Y-%m')
            os.makedirs('./preview', exist_ok=True)
            models = MODEL_SCREENS if preview_model == 'all' else {preview_model: MODEL_SCREENS[preview_model]}

            for model, (width, height) in models.items():
                screen_width = width
                screen_height = height
                image = Image.new("L", (screen_width, screen_height), color="white")
                draw = ImageDraw.Draw(image, "L")
                gray_palette = [item.strip() for item in config['Color']['event_bg'].split(',')]
                font_palette = [item.strip() for item in config['Color']['event_tx'].split(',')]
                configure_layout()

                image_name = f'./preview/{model}-{dayMonth}.png'
                draw_calendar(events_data, date)
                draw_detail(events_data, date)
                image.save(image_name)
                print(f"Preview model: {model} ({screen_width}x{screen_height})")
                print(f"file_name: {image_name}")
            return

        # set date
        date = datetime.now()
        year = date.year
        month = date.month

        if previous_month:
            month -= 1
            if month == 0:
                year -= 1
                month = 12
            date = datetime(year, month, 1)

        dayMonth = date.strftime('%Y-%m')
        image_name = f'./image/{dayMonth}.png'
        file_name = f'./data/{dayMonth}.json'

        if check_image(image_name) and previous_month:
            # when there has last month image, doesn't need to calcute again.
            print(f"file_name: {image_name}")
        else:
            # Event data
            events_data = get_file(file_name)
            # print(events_data)

            # Draw calendar
            draw_calendar(events_data, date)
            draw_detail(events_data, date)

            # Calucate running time
            end_time = time.time()
            elapsed_time = round(end_time - start_time, 4)
            print(f'Running time: {elapsed_time}')

            # Save the image
            image.save(image_name)
            print(f"file_name: {image_name}")
        
        remove_image()
    except FileNotFoundError as e:
        print('File not found')
        if not preview_mode:
            fbink_cfg.is_halfway = False
            fbink_cfg.row = -2
        # FBInk.fbink_print(fbfd, b"Please run current month calendar first.", fbink_cfg)
        exit(1)
    except Exception as e:
        if not preview_mode:
            fbink_cfg.is_halfway = False
            fbink_cfg.row = -2
        # FBInk.fbink_print(fbfd, b"An error occurred", fbink_cfg)
        print(f'An error occurred: {e}')
        exit(1)
    finally:
        if not preview_mode:
            FBInk.fbink_close(fbfd)

if __name__ == "__main__":
    main()
