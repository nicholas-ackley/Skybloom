"""Builds the hooded wanderer's player sprite sheet (48x48 cells, same layout as the Rhen sheet).

Brown knit hoodie with the hood up, face visible, slate trousers, leather boots.
Layout: rows 0=down, 1=up, 2=left, 3=right.
Columns (2 frames each): 0-1 idle, 2-3 walk, 4-5 chop (axe), 6-7 till (hoe), 8-9 water.
Usage: python3 generate_hooded_sheet.py <out_dir>
"""
import os, sys
from PIL import Image, ImageDraw

CELL = 48
X0, FEET = 16, 32          # sprite is 16 wide, feet end on row 31 (same spot as Rhen)
ACTIONS = ["idle", "walk", "chop", "till", "water"]
ROWS = ["down", "up", "left", "right"]
NAME = "hooded"


def c(rgb, a=255):
    return (*rgb, a)


PAL = {k: c(v) for k, v in {
    "O": (36, 24, 20),                                         # outline
    "H": (128, 88, 56), "h": (92, 62, 40), "L": (166, 122, 80),  # hoodie brown, shade, highlight
    "x": (106, 72, 46),                                        # knit speckle (the texture)
    "D": (52, 34, 26), "R": (84, 56, 38),                      # hood shadow, hair fringe
    "S": (238, 196, 156), "s": (202, 150, 116), "E": (34, 24, 22), "W": (255, 255, 255), "c": (232, 150, 128),
    "F": (226, 206, 168),                                      # drawstrings
    "C": (128, 88, 56),                                        # sleeves (tool arms)
    "N": (68, 72, 88), "n": (46, 48, 62),                      # trousers
    "B": (96, 62, 40),                                         # boots
}.items()}
OUTLINE = PAL["O"]
WOOD, WOOD_D = c((150, 100, 60)), c((110, 70, 42))
METAL, METAL_D, METAL_L = c((196, 206, 218)), c((130, 140, 158)), c((240, 246, 252))
CAN, CAN_D, CAN_L = c((88, 150, 210)), c((56, 104, 160)), c((250, 250, 255))
DROP, DROP_L = c((120, 190, 240)), c((210, 236, 255))

LEGS = [
    "...ONNNNNNNnO...", "...ONNNNNNNnO...", "...ONNNOONNnO...", "...OnNNOONNnO...",
    "...OBBBOOBBBO...", "...OOOO..OOOO...",
]
DOWN = [
    ".....OOOOOO.....", "....OLLHHHHO....", "...OLHHHxHHhO...", "...OHHxHHHHhO...", "..OHDRRRRRRDhO..",
    "..OHDRSSSSRDhO..", "..OHDSESSESDhO..", "..OHDSESSESDhO..", "..OHhcSSSSchhO..", "...OhHsSSsHhO...",
    "...OHHhhhhHHO...", "..OHHHFHHFHHhO..", ".OCOHxFHHFxhOCO.", ".OCOxHhhhhHhOCO.", ".OSOHHxHHxHhOSO.",
    "..OOhhhhhhhhOO..",
] + LEGS
UP = [
    ".....OOOOOO.....", "....OLLHHHHO....", "...OLHHHxHHhO...", "...OHHxHHHHhO...", "..OHHHHHHxHHhO..",
    "..OHHxHHHHHHhO..", "..OHHHHHxHHHhO..", "..OhHHxHHHHhhO..", "..OhhHHHHHHhhO..", "..OhhHHxHHhhhO..",
    "..OHhhHHHHhhHO..", "..OHHHhhhhHHhO..", ".OCOHxHHHHxhOCO.", ".OCOHHHxHHHhOCO.", ".OSOHxHHHHxhOSO.",
    "..OOhhhhhhhhOO..",
] + LEGS
SIDE = [  # faces right
    ".....OOOOOO.....", "....OLLHHHHO....", "...OLHHHHxHHO...", "...OHHxHHHHHO...", "...OHHHHDRRRO...",
    "...OHxHDRRSSO...", "...OHHHDSSESO...", "...OHxHDSSESs...", "...OhHHDScSSO...", "....OhHHDssO....",
    ".....OHHhhO.....", "....OHHHHFHO....", "....OHhHHFhO....", "....OxhHHHhO....", "....OHhSShhO....",
    "....OhhhhhhO....", "....ONNNNNnO....", "....ONNNNNnO....", ".....ONNNnO.....", ".....OnNNnO.....",
    ".....OBBBBBO....", ".....OOOOOOO....",
]
SIDE_STRIDE_LEGS = [
    "....ONNNNNNO....",
    "...ONNOOONNO....",
    "..OnNO...ONnO...",
    "..OBBO...OBBBO..",
    "..OOOO...OOOOO..",
]
SIDE_NO_ARM = {12: "....OHHxHFhO....", 13: "....OHHHxHhO....", 14: "....OHxHHhhO...."}
for _rows in (DOWN, UP, SIDE):
    assert len(_rows) == 22 and all(len(r) == 16 for r in _rows), "body rows must be 16x22"


def rows_copy(rows):
    return [list(r) for r in rows]


def lift_leg(rows, cols):
    """Raise one leg by a pixel (walk step) for the front/back views."""
    g = rows_copy(rows)
    for r in range(18, 21):
        for x in cols:
            g[r][x] = rows[r + 1][x]
    for x in cols:
        g[21][x] = "."
    return ["".join(r) for r in g]


def bob(rows):
    """Upper body drops a pixel (idle breathing)."""
    out = ["." * 16] + rows[0:17] + rows[18:]
    return out


def strip_arms(rows):
    g = rows_copy(rows)
    for r in (12, 13, 14):
        for x in (0, 1, 2, 13, 14, 15):
            g[r][x] = "."
    return ["".join(r) for r in g]


def render(rows):
    img = Image.new("RGBA", (16, len(rows)), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), PAL[ch])
    return img


class Layer:
    """A 48x48 layer we draw tools / arms on; outline() wraps it in the dark outline colour."""

    def __init__(self):
        self.img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))

    def px(self, x, y, col):
        if 0 <= x < CELL and 0 <= y < CELL:
            self.img.putpixel((x, y), col)

    def line(self, a, b, col, col2=None):
        (x0, y0), (x1, y1) = a, b
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err, i = dx + dy, 0
        while True:
            self.px(x0, y0, col2 if (col2 and i % 3 == 2) else col)
            if (x0, y0) == (x1, y1):
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy
            i += 1

    def outline(self):
        src = self.img.copy()
        for y in range(CELL):
            for x in range(CELL):
                if src.getpixel((x, y))[3]:
                    continue
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < CELL and 0 <= ny < CELL and src.getpixel((nx, ny))[3]:
                        self.img.putpixel((x, y), OUTLINE)
                        break
        return self


def hand(layer, x, y):
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        layer.px(x + dx, y + dy, PAL["S"])
    layer.px(x + 1, y + 1, PAL["s"])


def arm(layer, shoulder, h):
    layer.line(shoulder, h, PAL["C"])
    hand(layer, *h)


def axe(layer, grip, tip, side):
    """Handle from grip to tip, blade sticking out on `side` (unit dx, dy perpendicular)."""
    layer.line(grip, tip, WOOD, WOOD_D)
    sx, sy = side
    tx, ty = tip
    ax, ay = (1 if tx > grip[0] else -1 if tx < grip[0] else 0), (1 if ty > grip[1] else -1 if ty < grip[1] else 0)
    for along in (-2, -1, 0, 1):
        for out in (1, 2, 3, 4):
            if out == 4 and along in (-2, 1):
                continue
            col = METAL_L if out >= 3 else METAL if along > -2 else METAL_D
            layer.px(tx - ax * along + sx * out, ty - ay * along + sy * out, col)
    layer.px(tx + ax, ty + ay, WOOD_D)


def hoe(layer, grip, tip, side):
    layer.line(grip, tip, WOOD, WOOD_D)
    sx, sy = side
    tx, ty = tip
    for out in (1, 2, 3):
        layer.px(tx + sx * out, ty + sy * out, METAL if out < 3 else METAL_L)
    # blade bends toward the ground
    layer.px(tx + sx * 3, ty + sy * 3 + 1, METAL_D)
    layer.px(tx + sx * 2, ty + sy * 2 + 1, METAL_D)


CAN_ROWS = [
    "..OOO.....",
    ".O...O....",
    "OBBBBBO.OO",
    "OBXBBBOOBO",
    "OBXBBBBBO.",
    "OBBBBBO...",
    "ObbbbbO...",
    ".OOOOO....",
]


def can_sprite(tilt):
    pal = {"O": OUTLINE, "B": CAN, "b": CAN_D, "X": CAN_L}
    img = Image.new("RGBA", (10, 8), (0, 0, 0, 0))
    for y, row in enumerate(CAN_ROWS):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), pal[ch])
    if tilt:  # pixel shear: spout side dips down so it reads as pouring
        tilted = Image.new("RGBA", (10, 12), (0, 0, 0, 0))
        for x in range(10):
            tilted.alpha_composite(img.crop((x, 0, x + 1, 8)), (x, x // 3 + 1))
        img = tilted
    return img


def drops(layer, x, y, n=3):
    for i in range(n):
        layer.px(x + (i % 2), y + i * 2, DROP if i % 2 else DROP_L)
    layer.px(x - 1, y + n * 2, DROP)
    layer.px(x + 2, y + n * 2 - 1, DROP_L)


def base_rows(view, action, frame):
    rows = {"down": DOWN, "up": UP, "right": SIDE}[view]
    if action == "idle" and frame == 1:
        return bob(rows)
    if action == "walk":
        if view == "right":
            return rows[:17] + SIDE_STRIDE_LEGS if frame == 0 else bob(rows)
        return lift_leg(rows, range(3, 7) if frame == 0 else range(9, 13))
    if action in ("chop", "till") and frame == 1 and view != "right":
        return strip_arms(rows)
    if action in ("chop", "till", "water") and view == "right":
        g = list(rows)
        for r, s in SIDE_NO_ARM.items():
            g[r] = s
        return g
    return rows


def frame_cell(view, action, frame):
    """view is down/up/right; left is mirrored from right by the caller."""
    rows = base_rows(view, action, frame)
    body = render(rows)
    cell = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    # soft ground shadow
    sh = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((24 - 7, FEET - 2, 24 + 7, FEET + 1), fill=(20, 30, 40, 70))
    cell.alpha_composite(sh)

    back, front = Layer(), Layer()
    tool = {"chop": axe, "till": hoe}.get(action)

    if tool and view == "down":
        if frame == 0:   # wind-up over the right shoulder
            tool(back, (29, 24), (35, 11), (1, 0) if tool is axe else (1, 0))
            hand(front, 29, 23)
        else:            # strike in front of the feet
            tool(front, (24, 25), (24, 34), (1, 0) if tool is axe else (0, 1))
            arm(front, (19, 22), (23, 25))
            arm(front, (28, 22), (25, 25))
    elif tool and view == "up":
        if frame == 0:
            tool(back, (19, 24), (12, 11), (-1, 0))
            hand(front, 17, 23)
        else:            # swinging away from the camera: tool shows above the head
            tool(back, (24, 22), (24, 5), (1, 0) if tool is axe else (0, -1))
            arm(front, (19, 22), (23, 24))
            arm(front, (28, 22), (25, 24))
    elif tool and view == "right":
        if frame == 0:   # raised behind the head
            tool(back, (23, 23), (14, 10), (0, -1) if tool is axe else (-1, 0))
            arm(front, (22, 21), (23, 23))
        else:            # swung forward and down
            tool(front, (25, 23), (37, 29), (0, 1))
            arm(front, (22, 21), (25, 23))
    elif action == "water":
        tilt = frame == 1
        can = can_sprite(tilt)
        lay = back if view == "up" else front
        if view == "right":
            arm(front, (22, 21), (25, 24))
            pos = (25, 21) if not tilt else (24, 19)
        elif view == "down":
            pos = (27, 21) if not tilt else (26, 19)
        else:
            pos = (11, 20) if not tilt else (10, 18)
        lay.img.alpha_composite(can, pos)
        if tilt:
            sx = pos[0] + can.width - 2
            drops(lay, sx, pos[1] + can.height - 1)
        if view == "down":
            hand(front, 28, 23)
        elif view == "up":
            hand(front, 17, 23)

    cell.alpha_composite(back.outline().img)
    cell.alpha_composite(body, (X0, FEET - len(rows)))
    cell.alpha_composite(front.outline().img)
    return cell


def build_sheet():
    sheet = Image.new("RGBA", (CELL * 2 * len(ACTIONS), CELL * len(ROWS)), (0, 0, 0, 0))
    for r, view in enumerate(ROWS):
        for a, action in enumerate(ACTIONS):
            for f in (0, 1):
                if view == "left":
                    img = frame_cell("right", action, f).transpose(Image.FLIP_LEFT_RIGHT)
                else:
                    img = frame_cell(view, action, f)
                sheet.alpha_composite(img, ((a * 2 + f) * CELL, r * CELL))
    return sheet


def preview(sheet, k=4):
    """Upscaled labelled copy on a dark backdrop (view only, never import)."""
    pad = 18
    W, H = sheet.width * k, sheet.height * k + pad
    bg = Image.new("RGBA", (W, H), (30, 40, 52, 255))
    d = ImageDraw.Draw(bg)
    for i in range(sheet.width // CELL):
        for j in range(sheet.height // CELL):
            if (i + j) % 2:
                d.rectangle((i * CELL * k, pad + j * CELL * k, (i + 1) * CELL * k - 1, pad + (j + 1) * CELL * k - 1),
                            fill=(36, 48, 62, 255))
    for a, action in enumerate(ACTIONS):
        d.text((a * 2 * CELL * k + 6, 3), f"{action} (cols {a*2}-{a*2+1})", fill=(230, 230, 230, 255))
    bg.alpha_composite(sheet.resize((sheet.width * k, sheet.height * k), Image.NEAREST), (0, pad))
    return bg


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    s = build_sheet()
    s.save(os.path.join(out, f"{NAME}_spritesheet.png"))
    preview(s).save(os.path.join(out, f"PREVIEW_do_not_import_{NAME}_sheet.png"))
    print("wrote", s.size)
