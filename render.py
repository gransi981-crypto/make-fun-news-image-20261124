"""Front page for Tuesday 24 November 2026.

Layout is data-driven: every story is a dict, and a Composer places
blocks on a two-column grid with a running vertical cursor. The page
is built in sections — masthead, lead (chart left, text right),
market strip, two mid stories with big numerals, three numbered
briefs, and a dark ticker band. Drawing uses Pillow only; the output
is deterministic because nothing here reads the clock, the network,
or random state.
"""

from PIL import Image, ImageDraw, ImageFont

PAGE_W, PAGE_H = 1024, 1024
MARGIN = 36
COL_W = (PAGE_W - 2 * MARGIN - 24) // 2  # two columns, 24px gutter

PAPER = (248, 244, 233)
INK = (18, 18, 18)
RED = (164, 20, 20)
NAVY = (24, 56, 104)
GREY = (96, 92, 82)
PALE = (214, 209, 194)
DARK = (22, 22, 22)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
SERIF = FONT_DIR + "/DejaVuSerif.ttf"
SERIF_B = FONT_DIR + "/DejaVuSerif-Bold.ttf"
SANS = FONT_DIR + "/DejaVuSans.ttf"
SANS_B = FONT_DIR + "/DejaVuSans-Bold.ttf"

_cache = {}


def face(path, size):
    """Cached font loader."""
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def wrap_words(draw, text, font, width):
    """Greedy wrap measured with textbbox; returns a list of lines."""
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        box = draw.textbbox((0, 0), trial, font=font)
        if box[2] - box[0] <= width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


class Composer:
    """Owns the canvas and places blocks top to bottom."""

    def __init__(self):
        self.img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
        self.d = ImageDraw.Draw(self.img)
        self.y = 0

    # -- primitives -------------------------------------------------
    def rule(self, x0, x1, y, weight=2, fill=INK):
        self.d.line([(x0, y), (x1, y)], fill=fill, width=weight)

    def kicker(self, text, x, y, size=19):
        self.d.text((x, y), text, font=face(SANS_B, size), fill=RED)

    def headline(self, text, x, y, width, start_size, leading, limit=2):
        """Headline that steps down 1pt at a time until it fits."""
        size = start_size
        while size > 13:
            font = face(SERIF_B, size)
            lines = wrap_words(self.d, text, font, width)
            if len(lines) <= limit:
                break
            size -= 1
        font = face(SERIF_B, size)
        lines = wrap_words(self.d, text, font, width)[:limit]
        for line in lines:
            self.d.text((x, y), line, font=font, fill=INK)
            y += leading
        return y

    def body(self, text, x, y, width, size=21, leading=28, fill=INK):
        font = face(SERIF, size)
        for line in wrap_words(self.d, text, font, width):
            self.d.text((x, y), line, font=font, fill=fill)
            y += leading
        return y

    def centred(self, text, y, size, fill, font_path=SANS):
        font = face(font_path, size)
        w = text_width(self.d, text, font)
        self.d.text(((PAGE_W - w) / 2, y), text, font=font, fill=fill)

    # -- sections ---------------------------------------------------
    def masthead(self):
        self.d.text((PAGE_W / 2, 20), "THE WORLD", font=face(SERIF_B, 88),
                    fill=INK, anchor="ma")
        self.centred("TUESDAY, 24 NOVEMBER 2026  ·  ONE DAY, ONE PAGE",
                     126, 19, GREY)
        self.rule(MARGIN, PAGE_W - MARGIN, 156, weight=4)
        self.rule(MARGIN, PAGE_W - MARGIN, 162, weight=1)
        self.y = 178

    def rising_chart(self, x, y, w, h, series, label, value):
        """Polyline chart that climbs, with a green end dot."""
        self.d.rectangle([x, y, x + w, y + h], outline=GREY, width=1)
        for i in (1, 2, 3):
            gy = y + h * i / 4
            self.d.line([(x, gy), (x + w, gy)], fill=PALE, width=1)
        pts = []
        for i, v in enumerate(series):
            px = x + 12 + (w - 24) * i / (len(series) - 1)
            py = y + h - 14 - (h - 28) * v
            pts.append((px, py))
        self.d.line(pts, fill=(22, 110, 44), width=4)
        ex, ey = pts[-1]
        self.d.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=(22, 110, 44))
        self.d.text((x + 8, y + 6), label, font=face(SANS_B, 17), fill=INK)
        self.d.text((x + w - 8, y + 8), value, font=face(SANS_B, 30),
                    fill=(22, 110, 44), anchor="ra")

    def market_strip(self, y, items):
        """Row of small boxes: index name over its day move."""
        n = len(items)
        gap = 10
        bw = (PAGE_W - 2 * MARGIN - gap * (n - 1)) // n
        for i, (name, move) in enumerate(items):
            x = MARGIN + i * (bw + gap)
            self.d.rectangle([x, y, x + bw, y + 56], outline=GREY, width=1)
            self.centred_in(name, x, y + 6, bw, 14, GREY, SANS_B)
            self.centred_in(move, x, y + 26, bw, 22, (22, 110, 44), SANS_B)
        return y + 56

    def centred_in(self, text, x, y, width, size, fill, font_path):
        font = face(font_path, size)
        w = text_width(self.d, text, font)
        self.d.text((x + (width - w) / 2, y), text, font=font, fill=fill)

    def lead(self):
        y = self.y
        chart_x, chart_w, chart_h = MARGIN, 330, 200
        self.rising_chart(chart_x, y + 4, chart_w, chart_h,
                          [0.02, 0.10, 0.08, 0.22, 0.18, 0.34, 0.30, 0.48,
                           0.44, 0.62, 0.58, 0.78, 0.72, 0.84, 0.86],
                          "NASDAQ", "+6.5%")
        tx = MARGIN + chart_w + 28
        tw = PAGE_W - MARGIN - tx
        self.kicker("MARKETS", tx, y)
        y2 = self.headline("Huang returns and Wall Street roars back",
                           tx, y + 28, tw, 48, 52)
        y2 = self.body("Jensen Huang is reinstated as Nvidia chief after "
                       "Donald Trump steps in. Nvidia shares jump 31% and "
                       "the Nasdaq surges 6.5% in its best day since April, "
                       "as Asia follows: Tokyo up 3.9%, Seoul 7% and Taipei "
                       "9%.",
                       tx, y2 + 6, tw, size=21, leading=27)
        self.centred_in("NEW YORK  ·  TOKYO  ·  SEOUL  ·  TAIPEI",
                        chart_x, y + chart_h + 10, chart_w, 15, GREY, SANS)
        chart_bottom = y + 4 + chart_h + 10 + 15
        strip_y = max(y2, chart_bottom) + 12
        self.y = self.market_strip(strip_y, [
            ("NASDAQ", "+6.5%"),
            ("S&P 500", "+4.7%"),
            ("DOW", "+3.0%"),
            ("NIKKEI", "+3.9%"),
            ("NVIDIA", "+31%"),
        ])
        self.rule(MARGIN, PAGE_W - MARGIN, self.y + 12, weight=2)
        self.y += 24

    def big_number(self, text, x, y, size=42):
        self.d.text((x, y), text, font=face(SERIF_B, size), fill=NAVY)

    def mid(self):
        y = self.y
        # left: merger
        lx = MARGIN
        self.kicker("BUSINESS", lx, y, size=18)
        y2 = self.headline("SpaceX and Tesla name five directors to steer "
                           "$3.5tn merger",
                           lx, y + 24, COL_W, 28, 32)
        self.big_number("$3.5T", lx, y2 + 4)
        y2 = self.body("Five directors will guide talks on combining Elon "
                       "Musk's companies, the Financial Times reports. "
                       "Advisers are fine-tuning an all-stock deal for "
                       "December.",
                       lx, y2 + 58, COL_W, size=19, leading=24)
        # right: talks
        rx = MARGIN + COL_W + 24
        self.d.line([(rx - 12, y), (rx - 12, y + 236)], fill=GREY, width=1)
        self.kicker("DIPLOMACY", rx, y, size=18)
        y3 = self.headline("Zelensky urges four-party talks with Russia, "
                           "US and Europe",
                           rx, y + 24, COL_W, 28, 32)
        self.big_number("4-PARTY", rx, y3 + 4)
        y3 = self.body("Kyiv, Moscow, Washington and European leaders "
                       "should meet as soon as possible, Ukraine's "
                       "president says — Kyiv is ready to talk as early as "
                       "Tuesday.",
                       rx, y3 + 58, COL_W, size=19, leading=24)
        self.y = max(y2, y3) + 12
        self.rule(MARGIN, PAGE_W - MARGIN, self.y, weight=2)
        self.y += 14

    def briefs(self):
        items = [
            ("TRADE", "US blacklists Megaspeed in Nvidia spy row",
             "The Singapore firm at the centre of the Nvidia "
             "chip-smuggling case joins the US Entity List."),
            ("SECURITY", "Russian drone briefly enters Polish airspace",
             "Warsaw reports the incursion; NATO vows to defend space "
             "after reports of a Russian nuclear satellite."),
            ("DEFENCE", "US delays Patriot missiles for Ukraine",
             "About 60 interceptors agreed for Kyiv still await Pentagon "
             "approval."),
        ]
        col_w = (PAGE_W - 2 * MARGIN - 2 * 24) // 3
        bottom = self.y
        for i, (kick, head, body) in enumerate(items):
            x = MARGIN + i * (col_w + 24)
            self.d.ellipse([x, self.y, x + 26, self.y + 26], fill=RED)
            num = str(i + 1)
            nw = text_width(self.d, num, face(SANS_B, 16))
            self.d.text((x + (26 - nw) / 2, self.y + 4), num,
                        font=face(SANS_B, 16), fill=(248, 244, 233))
            self.kicker(kick, x + 34, self.y + 3, size=16)
            y2 = self.headline(head, x, self.y + 32, col_w, 24, 25)
            y2 = self.body(body, x, y2 + 2, col_w, size=17, leading=19)
            bottom = max(bottom, y2)
            if i:
                self.d.line([(x - 12, self.y), (x - 12, bottom)],
                            fill=GREY, width=1)
        self.y = bottom + 12
        self.rule(MARGIN, PAGE_W - MARGIN, self.y, weight=2)
        self.y += 12

    def ticker(self):
        self.d.rectangle([MARGIN, 950, PAGE_W - MARGIN, 1014], fill=DARK)
        lines = [
            "PENTAGON REBUKES CANADA OVER F-35 REVIEW  •  EU PROPOSES "
            "22ND SANCTIONS PACKAGE ON RUSSIA",
            "CAR BOMB HITS VILLAVICENCIO, COLOMBIA  •  INDONESIA FACTORY "
            "FIRE LEAVES WORKERS MISSING  •  OREGON AND VIRGINIA SUE "
            "SPACEX OVER GROK IMAGES",
        ]
        size = 13
        font = face(SANS_B, size)
        while max(text_width(self.d, t, font) for t in lines) > 936 and size > 8:
            size -= 1
            font = face(SANS_B, size)
        self.d.text((PAGE_W / 2, 966), lines[0], font=font,
                    fill=(248, 244, 233), anchor="ma")
        self.d.text((PAGE_W / 2, 990), lines[1], font=font,
                    fill=(248, 244, 233), anchor="ma")

    def render(self, path):
        self.masthead()
        self.lead()
        self.mid()
        self.briefs()
        self.ticker()
        self.img.save(path, format="PNG", optimize=True)


if __name__ == "__main__":
    import sys
    Composer().render(sys.argv[1] if len(sys.argv) > 1 else "entry.png")
