#!/usr/bin/env python3
"""Generate the Suahco4 wordmark logo (logo.png) and its base64 data URI
(logo_b64.txt, used by receipt_book.html). Run once after changing branding."""
import base64
import io
from PIL import Image, ImageDraw, ImageFont

NAVY = (20, 33, 61)      # #14213d
GOLD = (252, 163, 17)    # #fca311
WHITE = (255, 255, 255)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def build():
    img = Image.new("RGBA", (560, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # badge
    d.rounded_rectangle([12, 40, 172, 200], radius=28, fill=NAVY)
    d.rounded_rectangle([12, 40, 172, 200], radius=28, outline=GOLD, width=3)
    badge_font = ImageFont.truetype(FONT, 66)
    d.text((92, 120), "S4", font=badge_font, fill=WHITE, anchor="mm")

    # wordmark
    word_font = ImageFont.truetype(FONT, 92)
    d.text((196, 118), "Suahco4", font=word_font, fill=NAVY, anchor="lm")

    # gold underline accent
    d.rounded_rectangle([200, 158, 452, 168], radius=5, fill=GOLD)

    return img


def main():
    img = build()
    img.save("logo.png")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    with open("logo_b64.txt", "w") as f:
        f.write("data:image/png;base64," + data)
    print("wrote logo.png (%dx%d) and logo_b64.txt (%d chars)"
          % (img.size[0], img.size[1], len(data)))


if __name__ == "__main__":
    main()
