from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from collections import deque
import os

SRC = Path("assets/pet.png")
CLEAN = Path("assets/pet_clean.png")
OUT = Path("assets/pet_typing.gif")

img = Image.open(SRC).convert("RGBA")

# resize for GitHub
target_w = 520
scale = target_w / img.width
img = img.resize((target_w, int(img.height * scale)), Image.LANCZOS)

w, h = img.size
px = img.load()

# remove edge-connected background based on corner colors
corner_colors = [
    px[0, 0], px[w-1, 0], px[0, h-1], px[w-1, h-1]
]

def close(c1, c2, tol=70):
    r1,g1,b1,a1 = c1
    r2,g2,b2,a2 = c2
    return abs(r1-r2) <= tol and abs(g1-g2) <= tol and abs(b1-b2) <= tol

def is_bg(c):
    r,g,b,a = c
    if a == 0:
        return True
    # remove cyan / white / checker backgrounds only when edge-connected
    if any(close(c, bg, 75) for bg in corner_colors):
        return True
    if r > 210 and g > 210 and b > 210:
        return True
    if r < 15 and g > 180 and b > 180:
        return True
    return False

seen = set()
q = deque()

for x in range(w):
    q.append((x, 0))
    q.append((x, h - 1))
for y in range(h):
    q.append((0, y))
    q.append((w - 1, y))

while q:
    x, y = q.popleft()
    if x < 0 or y < 0 or x >= w or y >= h or (x, y) in seen:
        continue
    seen.add((x, y))
    if is_bg(px[x, y]):
        px[x, y] = (0, 0, 0, 0)
        q.extend([(x+1,y), (x-1,y), (x,y+1), (x,y-1)])

img.save(CLEAN)

base = Image.open(CLEAN).convert("RGBA")
w, h = base.size

# terminal screen position
SX = int(w * 0.575)
SY = int(h * 0.475)
SW = int(w * 0.315)
SH = int(h * 0.190)

LINE1 = "# NEESCHAL"
LINE2 = "# root"

font_candidates = [
    "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf",
]

font_path = next((p for p in font_candidates if os.path.exists(p)), None)
font1 = ImageFont.truetype(font_path, int(w * 0.040)) if font_path else ImageFont.load_default()
font2 = ImageFont.truetype(font_path, int(w * 0.038)) if font_path else ImageFont.load_default()

TEXT = (80, 255, 255, 255)
GLOW = (80, 255, 255, 120)
BG = (0, 7, 14, 255)
BORDER = (80, 255, 255, 230)

def text_size(draw, text, font):
    if not text:
        sample = "Ag"
    else:
        sample = text
    box = draw.textbbox((0, 0), sample, font=font)
    return box[2] - box[0], box[3] - box[1]

def draw_glow_text(draw, xy, text, font):
    x, y = xy
    if not text:
        return
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        draw.text((x+dx, y+dy), text, font=font, fill=GLOW)
    draw.text((x, y), text, font=font, fill=TEXT)

def make_frame(t1, t2, cursor=True):
    im = base.copy()
    d = ImageDraw.Draw(im)

    # clean dark terminal screen — NO scanlines
    d.rounded_rectangle(
        [SX, SY, SX + SW, SY + SH],
        radius=14,
        fill=BG,
        outline=BORDER,
        width=3
    )

    x = SX + 18
    _, h1 = text_size(d, LINE1, font1)
    y1 = SY + 24
    y2 = y1 + h1 + 13

    draw_glow_text(d, (x, y1), t1, font1)
    draw_glow_text(d, (x, y2), t2, font2)

    if cursor:
        if t2:
            active, font, ay = t2, font2, y2
        else:
            active, font, ay = t1, font1, y1

        aw, ah = text_size(d, active, font)
        cx = x + aw + 7
        d.rectangle([cx, ay + 4, cx + 6, ay + ah - 3], fill=TEXT)

    return im

frames = []

def add(fr, n):
    for _ in range(n):
        frames.append(fr.copy())

# faster typewriter
for i in range(len(LINE1) + 1):
    add(make_frame(LINE1[:i], "", True), 2)

for i in range(5):
    add(make_frame(LINE1, "", i % 2 == 0), 1)

for i in range(len(LINE2) + 1):
    add(make_frame(LINE1, LINE2[:i], True), 2)

for i in range(24):
    add(make_frame(LINE1, LINE2, i % 2 == 0), 1)

frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    duration=90,
    loop=0,
    disposal=2
)

print("Saved:", OUT)
