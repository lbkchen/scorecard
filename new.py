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
YT_IMAGE_PATH = "img/play-button-50.png"

W = 400
H = 300
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
INNER_CIRCLE_HEIGHT_RATIO = 0.4

dosis_font_reg = ImageFont.truetype(DOSIS_REGULAR_PATH, size=40)
dosis_font_bold = ImageFont.truetype(DOSIS_BOLD_PATH, size=96)
dosis_font_bold_sm = ImageFont.truetype(DOSIS_BOLD_PATH, size=64)

# Coordinates
TOP_LEFT_C = (0, 0)
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
    img = Image.new("P", (W, H), color=WHITE)
    draw = ImageDraw.Draw(img)

    # Draw layout
    circle_top_left_x = (W - INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    circle_top_left_y = (H - INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    circle_bot_right_x = (W + INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    circle_bot_right_y = (H + INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    draw.ellipse([(circle_top_left_x, circle_top_left_y),
                  (circle_bot_right_x, circle_bot_right_y)], outline=BLACK, width=4)

    draw.line((TOP_MID_C, BOT_MID_C), fill=BLACK, width=4)

    # Put icons
    gh_img = Image.open(GH_IMAGE_PATH)
    icon_w = 32
    icon_top_padding = 16
    gh_img = gh_img.resize((icon_w, icon_w))
    img.paste(gh_img, box=(int(W/4-icon_w/2), icon_top_padding))

    yt_img = Image.open(YT_IMAGE_PATH)
    icon_w = 36
    yt_img = yt_img.resize((icon_w, icon_w))
    img.paste(yt_img, box=(int(3*W/4-icon_w/2), icon_top_padding))

    # Get num GitHub contributions
    num_contributions = get_num_contributions_today("Lbkchen")
    left_num_c = (W/6, H/2)
    draw.text(left_num_c, "{n}".format(n=num_contributions),
              fill=BLACK, font=dosis_font_bold, anchor="mm")

    # Get YouTube
    num_subscribers = get_youtube_subscribers()
    print(num_subscribers)
    right_num_c = (W*5/6, H/2)
    draw.text(right_num_c, "{n}".format(n=num_subscribers),
              fill=BLACK, font=dosis_font_bold_sm, anchor="mm")

    # Preview image
    img.show()


if __name__ == "__main__":
    main()
