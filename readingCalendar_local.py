#!/usr/bin/env python 
# -*- coding: utf-8 -*-
 
from PIL import Image, ImageDraw, ImageFont
import calendar
from datetime import datetime
import json

current_year = datetime.now().year
current_month = datetime.now().month

# Function to convert date string to datetime object
def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def get_file():
    json_file_path = './analytics.json'
    with open(json_file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    # Filter data for the current year and month
    filtered_data = [
        entry for entry in data
        if datetime.strptime(entry["Date"], "%Y-%m-%d").year == current_year
        and datetime.strptime(entry["Date"], "%Y-%m-%d").month == current_month
    ]

    return filtered_data

# Create a new image with a white background
width, height = 800, 600
image = Image.new("L", (width, height), "white")
draw = ImageDraw.Draw(image)

# Load a font (you can change the font file path as needed)
# font = ImageFont.load_default()
font = ImageFont.truetype("simsun.tt")
# Get the month's calendar as a list of lists
cal_data = calendar.monthcalendar(current_year, current_month)

# Define cell size and starting position
cell_size = 80
x_start = 20
y_start = 50
light_gray_colors = ['#9c9b9b', '#cccccc', '#bbbbbb', '#dddddd']

# Draw the days of the week
days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
for i, day in enumerate(days_of_week):
    draw.text((x_start + i * cell_size, y_start - 30), day, font=font, fill="black")

# Event data
events_data = get_file()
print(events_data)
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

#Draw the calendar days with outline
tmp_event = []
tmp_day = 0
tmp_position = {}
tmp_color = {}
day_map = {0: False, 1: False, 2: False}

for week_num, week in enumerate(cal_data):
    for day_num, day in enumerate(week):
        x = x_start + day_num * cell_size
        y = y_start + week_num * cell_size

        # Draw the day number with outline
        if day != 0:
            draw.text((x + 3, y + 4), str(day), font=font, fill="black")
            draw.rectangle([x, y, x + cell_size, y + cell_size], outline="black")

        # Check if there are events on this day and draw them
        events_on_day = [event for event in events_data if parse_date(event["Date"]).day == day]
        # print(events_on_day)
        if events_on_day:
            event_height = 15
            event_y = 20 + y

            for i, event in enumerate(events_on_day):
                event_block_color = light_gray_colors[(day_num % 4 + i) % 4]
                # print(day, tmp_day, tmp_event, event['Title'])
                if i >= 3:
                    text = '+more'
                    text_width = 30
                    # textdraw.textbbox((x+1,event_y), text, font=font)
                    # draw.rectangle([x + 1 + cell_size/2 , event_y + 3 * event_height, x + cell_size, event_y + (3 + 1) * event_height], fill=event_block_color, outline=None)
                    draw.text((x + (cell_size - text_width) - 4, event_y + 2 + 3 * event_height), text, font=font, fill="black")
                    break

                # event_title = event['Title']
                event_title = event['Title'].encode("utf-8").decode("latin1")
                # print('--', event_title)
                if tmp_day + 1 == day and event_title in tmp_event:
                    # print('連續事件', event_title)
                    if event_title in tmp_position:
                        save_y = tmp_position[event_title]
                        save_color = tmp_color[event_title]
                        day_map[save_y] = True
                        draw.rectangle([x , event_y + save_y * event_height, x + cell_size, event_y + (save_y + 1) * event_height], fill=save_color, outline=None)
                    else:
                        event_block_color = light_gray_colors[tmp_i]
                        tmp_i = next((key for key, value in day_map.items() if not value), None)
                        draw.rectangle([x + 1 , event_y + tmp_i * event_height, x - 1 + cell_size, event_y + (tmp_i + 1) * event_height], fill=event_block_color, outline=None)
                        draw.text((x + 2, event_y + 2 + tmp_i * event_height), f"{event['Title']} ({event['TotalMinutesRead']} mins)",
                            font=font, fill="black")
                        tmp_position[event_title] = tmp_i
                        tmp_color[event_title] = event_block_color
                        day_map[tmp_i] = True

                else:
                    # print('單一事件', event['Title'])
                    tmp_i = next((key for key, value in day_map.items() if not value), None)
                    draw.rectangle([x + 1 , event_y + tmp_i * event_height, x - 1 + cell_size, event_y + (tmp_i + 1) * event_height], fill=event_block_color, outline=None)
                    draw.text((x + 2, event_y + 2 + tmp_i * event_height), f"{event['Title']} ({event['TotalMinutesRead']} mins)",
                            font=font, fill="black")
                    tmp_position[event_title] = tmp_i
                    tmp_color[event_title] = event_block_color
                    day_map[tmp_i] = True


        tmp_day = day
        seen_titles = set()
        tmp_event = [title['Title'] for title in events_on_day if not (title['Title'] in seen_titles or seen_titles.add(title['Title']))]
        day_map = {0: False, 1: False, 2: False}
        # print('------------')
        # print(day, tmp_day,tmp_event)
        # print('------------')

# Save the image
image.save('calendar_with_optimized_events.png')
