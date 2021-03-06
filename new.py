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

parser = argparse.ArgumentParser()
parser.add_argument('--simulate', '-s', required=False,
                    action='store_true', help="Simulate Inky on Mac")
args = parser.parse_args()

DOSIS_REGULAR_PATH = "fonts/dosis/Dosis-Regular.ttf"
DOSIS_BOLD_PATH = "fonts/dosis/Dosis-Bold.ttf"
GH_IMAGE_PATH = "img/GitHub-Mark-64px.png"
YT_IMAGE_PATH = "img/play-button-red-48.png"
YT_BLACK_IMAGE_PATH = "img/play-button-50.png"
USER_IMAGE_PATH = "img/user-52.png"
ILLUMINATI_IMAGE_PATH = "img/illuminati-100.png"
ILLUMINATI_WHITE_IMAGE_PATH = "img/illuminati-white-100.png"
EYE_WHITE_IMAGE_PATH = "img/eye-white-48.png"

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

YOUTUBE_CHANNEL_ID = "UCO1_BGGMvhw0ehsSBYwSbig"


# Handle Inky libraries
inky_display = None
if not args.simulate:
    from inky import InkyWHAT
    inky_display = InkyWHAT("black")
    RED = inky_display.RED
    BLACK = inky_display.BLACK
    WHITE = inky_display.WHITE
    W = inky_display.WIDTH
    H = inky_display.HEIGHT


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


def get_youtube_stats():
    """
    Gets channel stats. 
    """
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.channels().list(
        part="statistics",
        id=YOUTUBE_CHANNEL_ID
    )
    response = request.execute()

    return response['items'][0]['statistics']


def get_youtube_top_recent_commment():
    """
    Gets top comment by like count from recent 100(?) comments for the channel. 
    """
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    comments = youtube.commentThreads().list(
        part="snippet,replies",
        allThreadsRelatedToChannelId=YOUTUBE_CHANNEL_ID
    ).execute()["items"]

    top_comment = max(
        comments,
        key=get_youtube_comment_score
    )
    print("top comment", top_comment)
    return top_comment


def get_youtube_comment_score(comment):
    likes = -1
    try:
        snippet = comment["snippet"]["topLevelComment"]["snippet"]
        published_at = snippet["publishedAt"]
        published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")

        # Exponential decay score by published date
        print("delta", datetime.now() - published_at)
        delta_weeks = (datetime.now() - published_at).days / 7
        likes = snippet["likeCount"]
        factor = 0.5
        likes *= (factor ** (delta_weeks))
    except KeyError:
        return -1
    return likes


# Drawing helpers

def reflow_quote(quote, width, font):
    words = quote.split(" ")
    reflowed = '"'
    line_length = 0

    for i in range(len(words)):
        word = words[i] + " "
        word_length = font.getsize(word)[0]
        line_length += word_length

        if line_length < width:
            reflowed += word
        else:
            line_length = word_length
            reflowed = reflowed[:-1] + "\n  " + word

    reflowed = reflowed.rstrip() + '"'

    return reflowed


def init_image():
    img = Image.new("P", (W, H), color=WHITE)
    draw = ImageDraw.Draw(img)
    print("-- Initialized Image (W: {w}, H: {h}) --".format(w=W, h=H))
    return img, draw


def draw_old():
    img, draw = init_image()

    # Draw stripes
    draw.rectangle([TOP_LEFT_C, (W, H/8)], fill=RED)
    draw.rectangle([(0, 2*H/3), BOT_RIGHT_C], fill=RED)

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

    # Get subs
    youtube_stats = get_youtube_stats()
    num_subscribers = youtube_stats["subscriberCount"]
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

    # Get view count
    num_views = youtube_stats["viewCount"]
    num_views = "{n}".format(n=num_views)
    num_views_y = int(5/6 * H)
    num_views_c = (W/2, num_views_y)
    draw.text(num_views_c, num_views, fill=WHITE,
              font=dosis_font_bold_md, anchor="mm")
    num_views_size = dosis_font_bold_md.getsize(num_views)

    icon_w = 25
    icon_padding = 10
    eye_img = Image.open(EYE_WHITE_IMAGE_PATH)
    eye_img = eye_img.resize((icon_w, icon_w))
    eye_icon_x = int(W/2 - num_views_size[0]/2 - icon_padding - icon_w)
    eye_icon_y = int(num_views_y - icon_w/2)
    img.paste(eye_img, box=(eye_icon_x, eye_icon_y), mask=eye_img)

    return img


def draw():
    img, draw = init_image()

    # Draw logo
    icon_w = 50
    icon_padding = 6
    yt_img = Image.open(YT_BLACK_IMAGE_PATH)
    yt_img = yt_img.resize((icon_w, icon_w))
    img.paste(yt_img, box=(icon_padding, icon_padding), mask=yt_img)

    # Get subscribers
    youtube_stats = get_youtube_stats()
    num_subscribers = youtube_stats["subscriberCount"]
    num_subscribers = "{n}".format(n=num_subscribers)
    draw.text((icon_w + icon_padding*2, icon_w/2 + icon_padding), num_subscribers,
              fill=BLACK, font=dosis_font_bold_md, anchor="lm")

    # Draw top comment frame
    footer_h = 36
    frame_edge_padding = 10
    frame_top_y = icon_w + icon_padding*2
    frame_bottom_y = H - footer_h - frame_edge_padding

    draw.rectangle([(frame_edge_padding, frame_top_y),
                    (W - frame_edge_padding, frame_bottom_y)], fill=BLACK)

    # Get YT top comment
    comment = comment = get_youtube_top_recent_commment()
    try:
        quote = comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        author = comment["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
    except KeyError:
        quote = "Failed lol"
        author = "pleb"

    quote_padding = 15
    quote_font = dosis_font_bold_sm

    # Check overflow
    # quote = "kelsey when is the mixtape dropping lol this is so funny and reflowed lol so funny and reflowed lol reflowed lol so funny and reflowed lol"
    reflowed_quote = reflow_quote(quote, W - quote_padding*2, quote_font)
    if reflowed_quote.count("\n") + 1 > 5:  # Hard coded line count
        reflowed_quote = "\n".join(reflowed_quote.split("\n")[:5])
        reflowed_quote = " ".join(reflowed_quote.split(" ")[:-1]) + '..."'

    # Draw quote
    draw.multiline_text((quote_padding, frame_top_y + 2), reflowed_quote,
                        fill=WHITE, font=quote_font, align="left")

    # Draw author
    footer_padding = 6
    draw.text((W - footer_padding, H - footer_padding), f"-{author}",
              fill=BLACK, font=dosis_font_bold_sm, anchor="rd")

    return img


def set_inky_display(img):
    # Preview image
    if args.simulate:
        print("-- Showing simulated image now --")
        img.show()
    else:
        print("-- Showing image on inky display now --")
        inky_display.set_image(img)
        inky_display.show()


def main():
    img = draw()
    set_inky_display(img)


if __name__ == "__main__":
    main()
