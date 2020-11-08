#!/usr/bin/env python

import argparse
import requests
import json
import os

from PIL import Image, ImageFont, ImageDraw
from github import Github
from dotenv import load_dotenv
from datetime import datetime

DOSIS_REGULAR_PATH = "fonts/dosis/Dosis-Regular.ttf"
DOSIS_BOLD_PATH = "fonts/dosis/Dosis-Bold.ttf"
GH_IMAGE_PATH = "img/GitHub-Mark-64px.png"

W = 400
H = 300
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
INNER_CIRCLE_HEIGHT_RATIO = 0.4

dosis_font_reg = ImageFont.truetype(DOSIS_REGULAR_PATH, size=40)
dosis_font_bold = ImageFont.truetype(DOSIS_BOLD_PATH, size=64)

# Coordinates
TOP_LEFT_C = (0, 0)
BOT_RIGHT_C = (W, H)
TOP_MID_C = (W/2, 0)
BOT_MID_C = (W/2, H)

# APIs

load_dotenv()
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
GITHUB_API_URL = "https://api.github.com/graphql"
g = Github(GITHUB_ACCESS_TOKEN)


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


def main():
    img = Image.new("P", (W, H), color=WHITE)
    draw = ImageDraw.Draw(img)

    # Draw layout
    circle_top_left_x = (W - INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    circle_top_left_y = (H - INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    circle_bot_right_x = (W + INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    circle_bot_right_y = (H + INNER_CIRCLE_HEIGHT_RATIO * H) / 2
    draw.ellipse([(circle_top_left_x, circle_top_left_y),
                  (circle_bot_right_x, circle_bot_right_y)], outline=BLACK, width=8)

    draw.line((TOP_MID_C, BOT_MID_C), fill=BLACK, width=10)
    # draw.text((10, 10), "Hello there what is this",
    #           fill=BLACK, font=dosis_font_bold)

    # Put icons
    gh_img = Image.open(GH_IMAGE_PATH)
    img.paste(gh_img, box=(10, 10))

    # Get num GitHub contributions
    num_contributions = get_num_contributions_today("Lbkchen")
    draw.text((10, 10), "{n}".format(n=num_contributions),
              fill=BLACK, font=dosis_font_bold)

    # Preview image
    img.show()


if __name__ == "__main__":
    main()
