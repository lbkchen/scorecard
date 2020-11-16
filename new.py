#!/usr/bin/env python

import argparse
import requests
import json
import os


from PIL import Image, ImageFont, ImageDraw
from github import Github
from dotenv import load_dotenv
from datetime import datetime
from googleapiclient.discovery import build


DOSIS_REGULAR_PATH = "fonts/dosis/Dosis-Regular.ttf"
DOSIS_BOLD_PATH = "fonts/dosis/Dosis-Bold.ttf"
GH_IMAGE_PATH = "img/GitHub-Mark-64px.png"
YT_IMAGE_PATH = "img/play-button-red-48.png"
USER_IMAGE_PATH = "img/user-52.png"

W = 400
H = 300
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
INNER_CIRCLE_HEIGHT_RATIO = 0.4

dosis_font_reg = ImageFont.truetype(DOSIS_REGULAR_PATH, size=40)
dosis_font_bold_lg = ImageFont.truetype(DOSIS_BOLD_PATH, size=64)
dosis_font_bold_md = ImageFont.truetype(DOSIS_BOLD_PATH, size=48)
dosis_font_bold_sm = ImageFont.truetype(DOSIS_BOLD_PATH, size=32)

# Coordinates
TOP_LEFT_C = (0, 0)
TOP_RIGHT_C = (W, 0)
BOT_LEFT_C = (0, H)
BOT_RIGHT_C = (W, H)
TOP_MID_C = (W/2, 0)
BOT_MID_C = (W/2, H)

# APIs

load_dotenv()

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
GITHUB_API_URL = "https://api.github.com/graphql"

FITBIT_CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
FITBIT_CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_num_contributions_today(username):
    # GitHub GQL API: https://docs.github.com/en/free-pro-team@latest/graphql/reference/objects#contributionscollection
    query = """
    query {
        user(login: "%s") {
            name
            contributionsCollection {
                contributionCalendar {
                    colors
                    totalContributions
                    weeks {
                        contributionDays {
                            color
                            contributionCount
                            date
                            weekday
                        }
                        firstDay
                    }
                }
            }
        }
    }""" % username
    print(query)

    r = requests.post(GITHUB_API_URL, data=json.dumps({"query": query}), headers={
                      "Authorization": "bearer {token}".format(token=GITHUB_ACCESS_TOKEN)})
    data = r.json()
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

    num_contributions = 0

    for week in weeks:
        for day in week["contributionDays"]:
            # Date like 2019-11-03
            date = datetime.strptime(day["date"], '%Y-%m-%d').date()
            if date != datetime.today().date():
                continue
            num_contributions = day["contributionCount"]
            break
        if num_contributions > 0:
            # Found current date
            break

    return num_contributions


def get_youtube_subscribers():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.channels().list(
        part="statistics",
        id="UCO1_BGGMvhw0ehsSBYwSbig"
    )
    response = request.execute()
    print(response)
    return response['items'][0]['statistics']['subscriberCount']


def main():
    img = Image.new("RGBA", (W, H), color=WHITE)
    draw = ImageDraw.Draw(img)

    # Draw stripes
    draw.rectangle([TOP_LEFT_C, (W, H/8)], fill="red")
    draw.rectangle([(0, 2*H/3), BOT_RIGHT_C], fill="red")

    # Put channel name and YT icon
    title_row_y = int(2*H/7)
    icon_w = 36
    icon_title_padding = 8
    yt_channel_title = "kelseymakesthings"
    title_center_x = W/2 + icon_w/2 + icon_title_padding/2
    draw.text((title_center_x, title_row_y), yt_channel_title,
              fill=BLACK, font=dosis_font_bold_sm, anchor="mm")
    title_size = dosis_font_bold_sm.getsize(yt_channel_title)

    yt_icon_x = int(title_center_x - title_size[0]/2 -
                    icon_w - icon_title_padding)
    yt_img = Image.open(YT_IMAGE_PATH)
    yt_img = yt_img.resize((icon_w, icon_w))
    img.paste(yt_img, box=(yt_icon_x, int(title_row_y - icon_w/2)), mask=yt_img)

    # Get num GitHub contributions
    # num_contributions = get_num_contributions_today("Lbkchen")
    # left_num_c = (W/6, H/2)
    # draw.text(left_num_c, "{n}".format(n=num_contributions),
    #           fill=BLACK, font=dosis_font_bold_md, anchor="mm")

    # Get YouTube
    num_subscribers = get_youtube_subscribers()
    print(num_subscribers)
    subscribers_c = (W/2, H/2)
    num_subscribers = "{n}".format(n=num_subscribers)
    draw.text(subscribers_c, num_subscribers,
              fill=BLACK, font=dosis_font_bold_lg, anchor="mm")
    num_subscribers_size = dosis_font_bold_lg.getsize(num_subscribers)

    icon_w = 32
    icon_padding = 10
    user_img = Image.open(USER_IMAGE_PATH)
    user_img = user_img.resize((icon_w, icon_w))
    user_icon_x = int(W/2 - num_subscribers_size[0]/2 - icon_padding - icon_w)
    user_icon_y = int(H/2 - icon_w/2)
    img.paste(user_img, box=(user_icon_x, user_icon_y), mask=user_img)

    # Preview image
    img.show()


if __name__ == "__main__":
    main()
