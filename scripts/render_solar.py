"""Render a six-color E Ink Spectra 6 solar system dashboard."""

import json
import math
import os
import random
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from orbits import AU_KM, positions

W, H = 1200, 1600
CX, CY = 600, 585
FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
BLACK, WHITE, BLUE, GREEN, RED, YELLOW = range(6)
PURE = [(0, 0, 0), (255, 255, 255), (0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)]
DEVICE = [(25, 30, 33), (232, 232, 232), (33, 87, 186), (18, 95, 32), (178, 19, 24), (239, 222, 68)]

# Orbit radii are schematic. Each marker follows its heliocentric longitude.
ORBITS = {
    "Mercury": (75, 9, WHITE),
    "Venus": (135, 13, YELLOW),
    "Earth": (195, 14, BLUE),
    "Mars": (255, 11, RED),
    "Jupiter": (319, 22, YELLOW),
    "Saturn": (380, 17, YELLOW),
    "Uranus": (438, 14, GREEN),
    "Neptune": (495, 14, BLUE),
}


@lru_cache(maxsize=None)
def font(weight, size):
    return ImageFont.truetype(str(FONT_DIR / f"Inter-{weight}.otf"), size)


def text(draw, x, y, value, size, color=WHITE, weight="SemiBold", align="left", tracking=0):
    face = font(weight, size)
    if not tracking:
        draw.text((x, y), value, font=face, fill=color, anchor=f"{align[0]}s")
        return
    width = sum(face.getlength(char) for char in value) + tracking * (len(value) - 1)
    if align == "right":
        x -= width
    elif align == "middle":
        x -= width / 2
    for char in value:
        draw.text((x, y), char, font=face, fill=color, anchor="ls")
        x += face.getlength(char) + tracking


def circle(draw, x, y, radius, fill=None, outline=None, width=1):
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill, outline, width)


def point(radius, angle):
    return CX + radius * math.cos(angle), CY - radius * math.sin(angle)


def draw_starfield(draw):
    rng = random.Random(42)
    for _ in range(220):
        x, y = rng.randrange(28, W - 28), rng.randrange(104, 1088)
        if math.hypot(x - CX, y - CY) > 516:
            circle(draw, x, y, rng.choice((1, 1, 2)), fill=rng.choice((WHITE, WHITE, WHITE, BLUE, YELLOW)))
    for x, y, color in ((134, 170, YELLOW), (1068, 231, WHITE), (1067, 966, YELLOW), (125, 948, WHITE)):
        draw.polygon([(x, y - 16), (x + 3, y - 3), (x + 16, y), (x + 3, y + 3),
                      (x, y + 16), (x - 3, y + 3), (x - 16, y), (x - 3, y - 3)], fill=color)


def draw_planet(draw, name, x, y, radius, color):
    circle(draw, x, y, radius + 5, fill=BLACK)
    circle(draw, x, y, radius, fill=color, outline=WHITE, width=2)
    if name == "Saturn":
        draw.ellipse((x - 27, y - 7, x + 27, y + 7), outline=BLACK, width=4)
        draw.ellipse((x - 27, y - 7, x + 27, y + 7), outline=WHITE, width=2)


def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def draw_map(draw, locations):
    draw_starfield(draw)
    markers = {}
    for name, (ring, radius, color) in ORBITS.items():
        ticks = round(math.tau * ring / 10)
        for tick in range(ticks):
            angle = tick * math.tau / ticks
            circle(draw, *point(ring, angle), 1, fill=WHITE)
        x, y, _ = locations[name]
        markers[name] = point(ring, math.atan2(y, x))

    circle(draw, CX, CY, 45, outline=YELLOW, width=2)
    circle(draw, CX, CY, 36, fill=YELLOW)
    text(draw, CX, CY + 7, "SUN", 18, BLACK, align="middle", tracking=1)

    occupied = [(CX - 47, CY - 47, CX + 47, CY + 47)]
    for name, (x, y) in markers.items():
        _, radius, color = ORBITS[name]
        draw_planet(draw, name, x, y, radius, color)
        gap = 30 if name == "Saturn" else radius + 6
        occupied.append((x - gap, y - gap, x + gap, y + gap))

    for name, (x, y) in reversed(tuple(markers.items())):
        width = math.ceil(font("SemiBold", 25).getlength(name)) + 12
        gap = 31 if name == "Saturn" else ORBITS[name][1] + 9
        # Try adjacent positions first, then allow room for a leader line on crowded dates.
        for offset in (0, 28, 56, 84, 112):
            distance = gap + offset
            candidates = [(x + distance, y - 16), (x - distance - width, y - 16),
                          (x - width / 2, y - distance - 32), (x - width / 2, y + distance)]
            for left, top in candidates:
                box = (left, top, left + width, top + 32)
                if left < 35 or box[2] > W - 35 or top < 93 or box[3] > 1110:
                    continue
                if any(overlaps(box, item) for item in occupied):
                    continue
                if offset:
                    end_x = min(max(x, left), box[2])
                    end_y = min(max(y, top), box[3])
                    angle = math.atan2(end_y - y, end_x - x)
                    draw.line((x + gap * math.cos(angle), y + gap * math.sin(angle), end_x, end_y), fill=WHITE)
                draw.rectangle(box, fill=BLACK)
                text(draw, left + 6, top + 24, name, 25)
                occupied.append(box)
                break
            else:
                continue
            break


def draw_dashboard(local, locations, sun_au, earth_au, palette):
    image = Image.new("P", (W, H), BLACK)
    image.putpalette([channel for rgb in palette for channel in rgb])
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 44, 77, 50), fill=YELLOW)
    text(draw, 94, 64, "PLANETARY POSITIONS", 25, tracking=5)
    text(draw, W - 60, 64, f"{local:%a  %b} {local.day}, {local.year}".upper(),
         25, YELLOW, align="right", tracking=4)
    draw_map(draw, locations)

    text(draw, CX, 1198, "Solar System", 111, align="middle")
    text(draw, CX, 1253, "View from ecliptic north  ·  Orbits and sizes schematic",
         28, YELLOW, weight="Medium", align="middle")

    nearest = min(earth_au, key=earth_au.get)
    for x, color, label, value, detail in (
        (60, BLUE, "EARTH TO SUN", f"{sun_au['Earth']:.3f} AU", f"{sun_au['Earth'] * AU_KM / 1e6:.1f} million km"),
        (620, YELLOW, "NEAREST PLANET TO EARTH", nearest, f"{earth_au[nearest]:.3f} AU away"),
    ):
        draw.rectangle((x, 1288, x + 7, 1413), fill=color)
        text(draw, x + 30, 1312, label, 22, tracking=3)
        text(draw, x + 30, 1373, value, 54)
        text(draw, x + 30, 1408, detail, 25, weight="Medium")

    draw.rectangle((60, 1440, W - 60, 1441), fill=BLUE)
    text(draw, CX, 1475, "DISTANCE FROM THE SUN  /  AU", 21, tracking=3, align="middle")
    for index, (name, (_, _, color)) in enumerate(ORBITS.items()):
        x = 60 + (W - 120) / 8 * (index + 0.5)
        circle(draw, x, 1502, 7, fill=color, outline=WHITE)
        text(draw, x, 1537, name, 20, align="middle")
        text(draw, x, 1573, f"{sun_au[name]:.2f}", 27, align="middle")
    return image.convert("RGB")


def main():
    tz = ZoneInfo(os.environ.get("TZ_NAME") or "America/Los_Angeles")
    timestamp = os.environ.get("SOLAR_NOW")
    now = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else datetime.now(timezone.utc)
    now = (now if now.tzinfo else now.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    local = now.astimezone(tz)
    rotate = int(os.environ.get("ROTATE") or 0)
    if rotate not in (0, 90, 180, 270):
        raise ValueError("ROTATE must be 0, 90, 180, or 270 clockwise degrees")
    palette_name = os.environ.get("OUTPUT_PALETTE") or "pure"
    palette = {"pure": PURE, "device": DEVICE}[palette_name]
    out_dir = Path(os.environ.get("OUTPUT_DIR") or "output")

    locations = positions(now)
    sun_au = {name: math.dist((0, 0, 0), xyz) for name, xyz in locations.items()}
    earth_au = {name: math.dist(locations["Earth"], xyz) for name, xyz in locations.items() if name != "Earth"}
    image = draw_dashboard(local, locations, sun_au, earth_au, palette)
    out_dir.mkdir(parents=True, exist_ok=True)
    image.rotate(-rotate, expand=True).save(out_dir / "solar_dashboard.png", optimize=True)

    data = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "local_date": local.date().isoformat(),
        "timezone": tz.key,
        "reference_frame": "heliocentric J2000 ecliptic",
        "nearest_planet_to_earth": min(earth_au, key=earth_au.get),
        "planets": {
            name: {
                "position_au": [round(value, 6) for value in xyz],
                "longitude_deg": round(math.degrees(math.atan2(xyz[1], xyz[0])) % 360, 4),
                "distance_from_sun_au": round(sun_au[name], 6),
                "distance_from_earth_au": round(earth_au.get(name, 0), 6),
            }
            for name, xyz in locations.items()
        },
    }
    (out_dir / "solar_data.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{local.date()} - wrote {out_dir / 'solar_dashboard.png'} and solar_data.json")


if __name__ == "__main__":
    main()
