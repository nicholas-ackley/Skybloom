"""Generates the placeholder pixel art for the book-style inventory.

Run from the repo root:  python3 tools/ui/generate_inventory_ui.py
Writes PNGs into skybloom-game/assets/UI/inventory/. Needs Pillow.
These are rough placeholders; swap them for hand-drawn art any time,
keeping the same sizes so the UI scene lines up.
"""

import os
import random

from PIL import Image, ImageDraw

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "skybloom-game", "assets", "UI", "inventory")

OUTLINE = (43, 24, 16, 255)
LEATHER = (110, 58, 34, 255)
LEATHER_DK = (78, 40, 24, 255)
LEATHER_LT = (142, 80, 46, 255)
GOLD = (222, 168, 78, 255)
GOLD_DK = (150, 98, 42, 255)
PAGE = (238, 216, 164, 255)
PAGE_SH = (220, 192, 134, 255)
PAGE_DK = (190, 154, 98, 255)
PAGE_EDGE = (250, 238, 204, 255)
INK = (92, 52, 30, 255)
SLOT_FILL = (204, 170, 112, 255)
SLOT_FILL_DK = (182, 146, 92, 255)
RIBBON = (150, 40, 44, 255)
RIBBON_DK = (104, 26, 32, 255)

# Tiny pixel font for the page headers (5 px tall).
GLYPHS = {
    "A": ["010", "101", "111", "101", "101"],
    "E": ["111", "100", "110", "100", "111"],
    "I": ["111", "010", "010", "010", "111"],
    "M": ["10001", "11011", "10101", "10001", "10001"],
    "N": ["1001", "1101", "1011", "1001", "1001"],
    "P": ["110", "101", "110", "100", "100"],
    "Q": ["0110", "1001", "1001", "1010", "0101"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
}

BOOK_W, BOOK_H = 272, 192
SPINE_X = 136
PAGE_TOP, PAGE_BOTTOM = 3, 176


def text_width(text):
    return sum(len(GLYPHS[c][0]) + 1 for c in text) - 1


def draw_text(img, x, y, text, color):
    for c in text:
        rows = GLYPHS[c]
        for dy, row in enumerate(rows):
            for dx, bit in enumerate(row):
                if bit == "1":
                    img.putpixel((x + dx, y + dy), color)
        x += len(rows[0]) + 1


def draw_header(img, center_x, y, text):
    """Header text with a little ruled line and diamond on each side."""
    d = ImageDraw.Draw(img)
    w = text_width(text)
    x = center_x - w // 2
    draw_text(img, x, y, text, INK)
    line_y = y + 2
    d.line([(x - 18, line_y), (x - 4, line_y)], fill=PAGE_DK)
    d.line([(x + w + 3, line_y), (x + w + 17, line_y)], fill=PAGE_DK)
    for cx in (x - 20, x + w + 19):
        d.point([(cx, line_y - 1), (cx - 1, line_y), (cx + 1, line_y), (cx, line_y + 1)], fill=INK)


def inset_frame(img, x0, y0, x1, y1):
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x1, y1], fill=SLOT_FILL, outline=PAGE_DK)
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=SLOT_FILL_DK)
    d.line([(x0 + 1, y0 + 1), (x0 + 1, y1 - 1)], fill=SLOT_FILL_DK)
    d.line([(x0 + 1, y1 + 1), (x1 + 1, y1 + 1)], fill=PAGE_EDGE)
    d.line([(x1 + 1, y0 + 1), (x1 + 1, y1 + 1)], fill=PAGE_EDGE)


def make_book():
    img = Image.new("RGBA", (BOOK_W, BOOK_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Leather cover behind the pages
    d.rounded_rectangle([0, 6, BOOK_W - 1, 185], radius=4, fill=LEATHER, outline=OUTLINE)
    d.line([(3, 182), (BOOK_W - 4, 182)], fill=LEATHER_DK)
    d.line([(2, 9), (2, 180)], fill=LEATHER_LT)
    d.line([(BOOK_W - 3, 9), (BOOK_W - 3, 180)], fill=LEATHER_DK)
    # Gold corner caps
    for cx, cy, sx, sy in ((1, 7, 1, 1), (BOOK_W - 2, 7, -1, 1), (1, 184, 1, -1), (BOOK_W - 2, 184, -1, -1)):
        for i in range(7):
            img.putpixel((cx + sx * i, cy), GOLD)
            img.putpixel((cx, cy + sy * i), GOLD)
            img.putpixel((cx + sx * i, cy + sy), GOLD_DK if i > 0 else GOLD)
            img.putpixel((cx + sx, cy + sy * i), GOLD_DK if i > 0 else GOLD)

    # Page stacks peeking out under each page
    for i, col in enumerate((PAGE_DK, PAGE_EDGE, PAGE_SH)):
        d.line([(7 - i, PAGE_BOTTOM + 1 + i), (SPINE_X - 2, PAGE_BOTTOM + 1 + i)], fill=col)
        d.line([(SPINE_X + 1, PAGE_BOTTOM + 1 + i), (BOOK_W - 8 + i, PAGE_BOTTOM + 1 + i)], fill=col)

    # The two pages. The top edge dips a little toward the spine so it reads as a curved page.
    for x in range(6, BOOK_W - 6):
        dist = abs(x - SPINE_X + 0.5)
        top = PAGE_TOP + (2 if dist < 6 else 1 if dist < 16 else 0)
        for y in range(top, PAGE_BOTTOM + 1):
            if dist < 3:
                col = PAGE_DK
            elif dist < 8:
                col = PAGE_SH
            else:
                col = PAGE
            img.putpixel((x, y), col)
        img.putpixel((x, top - 1), OUTLINE)
        img.putpixel((x, PAGE_BOTTOM + 4), OUTLINE)
    for y in range(PAGE_TOP, PAGE_BOTTOM + 4):
        img.putpixel((5, y), OUTLINE)
        img.putpixel((BOOK_W - 6, y), OUTLINE)
    d.line([(SPINE_X, PAGE_TOP + 2), (SPINE_X, PAGE_BOTTOM + 3)], fill=OUTLINE)
    d.line([(SPINE_X - 1, PAGE_TOP + 2), (SPINE_X - 1, PAGE_BOTTOM + 3)], fill=PAGE_DK)
    # Bright edge on the outer side of each page
    d.line([(6, PAGE_TOP + 1), (6, PAGE_BOTTOM)], fill=PAGE_EDGE)
    d.line([(BOOK_W - 7, PAGE_TOP + 1), (BOOK_W - 7, PAGE_BOTTOM)], fill=PAGE_EDGE)

    # A few speckles so the paper isn't perfectly flat
    rng = random.Random(7)
    for _ in range(140):
        x = rng.randrange(9, BOOK_W - 9)
        y = rng.randrange(PAGE_TOP + 3, PAGE_BOTTOM - 1)
        if abs(x - SPINE_X) > 9 and img.getpixel((x, y)) == PAGE:
            img.putpixel((x, y), PAGE_SH)

    # Ribbon bookmark hanging off the right page
    for y in range(PAGE_BOTTOM - 6, BOOK_H):
        img.putpixel((222, y), RIBBON_DK)
        img.putpixel((223, y), RIBBON)
        img.putpixel((224, y), RIBBON)
        img.putpixel((225, y), RIBBON_DK)
    img.putpixel((223, BOOK_H - 1), (0, 0, 0, 0))
    img.putpixel((224, BOOK_H - 1), (0, 0, 0, 0))

    # Left page: equipment, portrait frame, stats, item info box
    draw_header(img, 70, 9, "EQUIPMENT")
    inset_frame(img, 62, 21, 125, 80)
    draw_header(img, 70, 87, "STATS")
    inset_frame(img, 14, 135, 125, 169)

    # Right page: item grid
    draw_header(img, 201, 9, "ITEMS")

    return img


def make_slot(border, inner_border):
    img = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 17, 17], fill=SLOT_FILL, outline=border)
    d.line([(1, 1), (16, 1)], fill=inner_border)
    d.line([(1, 1), (1, 16)], fill=inner_border)
    return img


def make_hotbar_panel():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 15, 15], radius=2, fill=LEATHER, outline=OUTLINE)
    d.rectangle([2, 2, 13, 13], outline=GOLD_DK)
    d.line([(2, 2), (13, 2)], fill=GOLD)
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    make_book().save(os.path.join(OUT_DIR, "book.png"))
    make_slot(PAGE_DK, SLOT_FILL_DK).save(os.path.join(OUT_DIR, "slot.png"))
    make_slot(GOLD, GOLD_DK).save(os.path.join(OUT_DIR, "slot_selected.png"))
    make_hotbar_panel().save(os.path.join(OUT_DIR, "hotbar_panel.png"))
    print("Wrote inventory UI art to", os.path.normpath(OUT_DIR))


if __name__ == "__main__":
    main()
