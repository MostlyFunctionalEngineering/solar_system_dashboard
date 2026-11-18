"""Render the solar system dashboard for an E Ink Spectra 6 display."""

import json
import math
import os
import random
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from moons import moon_positions
from orbits import AU_KM, elements_at, position

W, H = 1200, 1600
CX, CY = 600, 585
ORBIT_SCALE = 475 / math.sqrt(30.45)
FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
BLACK, WHITE, BLUE, GREEN, RED, YELLOW = range(6)
PURE = [(0, 0, 0), (255, 255, 255), (0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0)]
DEVICE = [(25, 30, 33), (232, 232, 232), (33, 87, 186), (18, 95, 32), (178, 19, 24), (239, 222, 68)]

PLANET_RADII = {
    "Mercury": 8, "Venus": 8, "Earth": 9, "Mars": 8,
    "Jupiter": 22, "Saturn": 17, "Uranus": 14, "Neptune": 14,
}
PLANET_RGB = {
    "Mercury": (156, 150, 143), "rock shadow": (94, 88, 84), "crater rim": (191, 183, 172),
    "Venus": (213, 168, 98), "gold clouds": (236, 198, 133), "cream clouds": (250, 221, 169),
    "Earth": (32, 100, 192), "continents": (70, 146, 77), "ice": (235, 246, 246),
    "Mars": (185, 100, 65), "rust plains": (218, 139, 94), "dark plains": (118, 66, 52),
    "Jupiter": (231, 209, 181), "tan belt": (191, 143, 112), "brown belt": (148, 104, 86),
    "pale zone": (247, 231, 204), "red spot": (182, 82, 57), "storm center": (216, 114, 81),
    "Saturn": (221, 194, 142), "pale band": (242, 220, 172), "muted band": (192, 157, 107),
    "outer rings": (196, 183, 155), "inner rings": (235, 223, 192),
    "Uranus": (153, 212, 214), "haze": (187, 229, 229), "cyan band": (129, 192, 200),
    "Neptune": (77, 126, 199), "blue band": (100, 155, 220), "cloud streak": (166, 201, 239),
}
PLANET_INK = {name: index for index, name in enumerate(PLANET_RGB, start=len(PURE))}
MOON_OFFSETS = {"Moon": 24, "Io": 33, "Europa": 44, "Ganymede": 55,
                "Callisto": 66, "Titan": 39, "Titania": 31, "Triton": 31}
BELT_LABEL_BUFFER = 10


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


def project(x, y):
    scale = ORBIT_SCALE / math.sqrt(math.hypot(x, y))
    return CX + x * scale, CY - y * scale


def draw_starfield(draw):
    rng = random.Random(42)
    for _ in range(220):
        x, y = rng.randrange(28, W - 28), rng.randrange(104, 1088)
        if math.hypot(x - CX, y - CY) > 516:
            circle(draw, x, y, rng.choice((1, 1, 2)), fill=rng.choice((WHITE, WHITE, WHITE, BLUE, YELLOW)))
    for x, y, color in ((134, 170, YELLOW), (1068, 231, WHITE), (1067, 966, YELLOW), (125, 948, WHITE)):
        draw.polygon([(x, y - 16), (x + 3, y - 3), (x + 16, y), (x + 3, y + 3),
                      (x, y + 16), (x - 3, y + 3), (x - 16, y), (x - 3, y - 3)], fill=color)


def draw_planet(draw, name, x, y, radius):
    ink = PLANET_INK.__getitem__
    circle(draw, x, y, radius + 5, fill=BLACK)
    if name == "Saturn":
        draw.ellipse((x - 29, y - 9, x + 29, y + 9), outline=ink("outer rings"), width=2)
        draw.ellipse((x - 25, y - 6, x + 25, y + 6), outline=ink("inner rings"), width=2)
    circle(draw, x, y, radius, fill=ink(name))

    def feature(left, top, right, bottom, fill):
        draw.ellipse((x + left * radius, y + top * radius,
                      x + right * radius, y + bottom * radius), fill=ink(fill))

    def band(offset, thickness, fill):
        for row in range(round(radius * (offset - thickness / 2)), round(radius * (offset + thickness / 2)) + 1):
            half = math.sqrt(radius**2 - row**2) - 1
            draw.line((x - half, y + row, x + half, y + row), fill=ink(fill))

    if name == "Mercury":
        feature(-.66, -.53, -.05, .10, "crater rim")
        feature(-.61, -.49, -.13, .02, "rock shadow")
        feature(.08, .12, .55, .56, "rock shadow")
    elif name == "Venus":
        band(-.33, .30, "gold clouds")
        feature(-.64, -.48, .30, -.27, "cream clouds")
        feature(-.46, .23, .62, .49, "gold clouds")
    elif name == "Earth":
        draw.polygon([(x - 6, y - 3), (x - 3, y - 6), (x + 1, y - 4),
                      (x - 1, y), (x - 3, y + 1), (x - 2, y + 5), (x - 5, y + 1)], fill=ink("continents"))
        feature(.19, -.14, .73, .35, "continents")
        feature(-.27, -.88, .26, -.61, "ice")
        feature(-.24, .57, .29, .85, "ice")
    elif name == "Mars":
        feature(-.38, -.84, .39, -.61, "ice")
        feature(-.71, -.20, .19, .20, "rust plains")
        feature(-.22, .24, .68, .53, "dark plains")
    elif name == "Jupiter":
        for offset, thickness, color in ((-.65, .14, "tan belt"), (-.28, .20, "brown belt"),
                                         (-.02, .18, "pale zone"), (.27, .23, "tan belt"),
                                         (.62, .13, "brown belt")):
            band(offset, thickness, color)
        feature(-.13, .12, .65, .52, "red spot")
        feature(.01, .20, .52, .42, "storm center")
    elif name == "Saturn":
        band(-.40, .22, "pale band")
        band(.42, .18, "muted band")
        draw.arc((x - 29, y - 9, x + 29, y + 9), 0, 180, fill=ink("outer rings"), width=2)
        draw.arc((x - 25, y - 6, x + 25, y + 6), 0, 180, fill=ink("inner rings"), width=2)
    elif name == "Uranus":
        band(-.42, .23, "haze")
        band(.29, .21, "cyan band")
    elif name == "Neptune":
        band(-.33, .26, "blue band")
        feature(-.63, -.42, .08, -.29, "cloud streak")
        feature(.08, .20, .69, .32, "cloud streak")


def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def square(x, y, radius):
    return x - radius, y - radius, x + radius, y + radius


def draw_orbits(draw, elements):
    for a, e, inclination, _, perihelion, node in elements.values():
        ticks = round(math.tau * ORBIT_SCALE * math.sqrt(a) / 10)
        for tick in range(ticks):
            longitude = perihelion + 360 * tick / ticks
            x, y, _ = position((a, e, inclination, longitude, perihelion, node))
            circle(draw, *project(x, y), 1, fill=WHITE)


def layout_labels(markers, occupied):
    labels = {}
    occupied = occupied.copy()
    for name, (x, y) in sorted(markers.items(), key=lambda item: math.hypot(item[1][0] - CX, item[1][1] - CY)):
        width = math.ceil(font("SemiBold", 25).getlength(name)) + 12
        gap = 32 if name == "Saturn" else PLANET_RADII[name] + 9
        for distance in range(gap, gap + 197, 14):
            candidates = [(x + distance, y - 16), (x - distance - width, y - 16),
                          (x - width / 2, y - distance - 32), (x - width / 2, y + distance)]
            for left, top in candidates:
                box = (left, top, left + width, top + 32)
                if left < 35 or box[2] > W - 35 or top < 84 or box[3] > 1100:
                    continue
                if any(overlaps(box, item) for item in occupied):
                    continue
                labels[name] = box, gap, distance > gap
                occupied.append(box)
                break
            else:
                continue
            break
    return labels


def draw_asteroid_belt(draw, exclusions):
    rng = random.Random(64)
    for _ in range(148):
        angle = rng.uniform(0, math.tau)
        distance = rng.uniform(2.2, 3.2)
        x, y = project(distance * math.cos(angle), distance * math.sin(angle))
        size = rng.choice((2, 2, 3, 3, 4, 5))
        if any(overlaps(square(x, y, size + 1), box) for box in exclusions):
            continue
        rock = Image.new("1", (2 * size + 1, 2 * size + 1))
        stipple = ImageDraw.Draw(rock)
        half = size // 2
        # Black-and-white stipple reads as gray on the panel's six-color palette.
        stipple.polygon([(0, size), (size - half, 0), (size + half, 1), (2 * size, size + half),
                         (size + 1, 2 * size), (1, size + half)], fill=1)
        for row in range(rock.height):
            for col in range(row % 2, rock.width, 2):
                stipple.point((col, row), fill=0)
        draw.bitmap((round(x) - size, round(y) - size), rock, fill=WHITE)


def place_moons(markers, moons):
    dots = []
    for name, (host, (x, y, _)) in moons.items():
        px, py = markers[host]
        angle = math.atan2(y, x)
        dx, dy = math.cos(angle), -math.sin(angle)
        obstacles = [(CX, CY, 35)]
        obstacles.extend((mx, my, 32 if planet == "Saturn" else PLANET_RADII[planet] + 9)
                         for planet, (mx, my) in markers.items() if planet != host)
        obstacles.extend((mx, my, 11) for mx, my in dots)
        # Move an overlapping dot along its existing bearing to keep it visible.
        for extra in range(0, 73, 6):
            distance = MOON_OFFSETS[name] + extra
            dot = px + distance * dx, py + distance * dy
            if 30 <= dot[0] <= W - 30 and 75 <= dot[1] <= 1105:
                if all(math.dist(dot, (mx, my)) >= clearance for mx, my, clearance in obstacles):
                    break
        else:
            dot = px + MOON_OFFSETS[name] * dx, py + MOON_OFFSETS[name] * dy
        dots.append(dot)
    return dots


def draw_map(draw, elements, locations, moons):
    markers = {name: project(x, y) for name, (x, y, _) in locations.items()}
    moon_dots = place_moons(markers, moons)

    occupied = [square(CX, CY, 32)]
    occupied.extend(square(x, y, 30 if name == "Saturn" else PLANET_RADII[name] + 5)
                    for name, (x, y) in markers.items())
    occupied.extend(square(x, y, 7) for x, y in moon_dots)
    labels = layout_labels(markers, occupied)
    buffer = BELT_LABEL_BUFFER
    occupied.extend((left - buffer, top - buffer, right + buffer, bottom + buffer)
                    for (left, top, right, bottom), _, _ in labels.values())

    draw_starfield(draw)
    draw_asteroid_belt(draw, occupied)
    draw_orbits(draw, elements)
    circle(draw, CX, CY, 30, outline=YELLOW, width=2)
    circle(draw, CX, CY, 23, fill=YELLOW)
    text(draw, CX, CY + 5, "SUN", 14, BLACK, align="middle")

    for name, (x, y) in markers.items():
        draw_planet(draw, name, x, y, PLANET_RADII[name])
    for name, (box, gap, leader) in labels.items():
        left, top, right, bottom = box
        if leader:
            x, y = markers[name]
            end_x = min(max(x, left), right)
            end_y = min(max(y, top), bottom)
            angle = math.atan2(end_y - y, end_x - x)
            draw.line((x + gap * math.cos(angle), y + gap * math.sin(angle), end_x, end_y), fill=WHITE)
        draw.rectangle(box, fill=BLACK)
        text(draw, left + 6, top + 24, name, 25)
    for x, y in moon_dots:
        circle(draw, x, y, 5, fill=BLACK)
        circle(draw, x, y, 3, fill=WHITE)


def draw_dashboard(local, elements, locations, moons, sun_au, earth_au, palette):
    image = Image.new("P", (W, H), BLACK)
    image.putpalette([channel for rgb in (*palette, *PLANET_RGB.values()) for channel in rgb])
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 44, 77, 50), fill=YELLOW)
    text(draw, 94, 64, "PLANETARY POSITIONS", 25, tracking=5)
    text(draw, W - 60, 64, f"{local:%a  %b} {local.day}, {local.year}".upper(),
         25, YELLOW, align="right", tracking=4)
    draw_map(draw, elements, locations, moons)

    text(draw, CX, 1198, "Solar System", 111, align="middle")
    caption = "Ecliptic north  ·  Square-root distance scale"
    if moons:
        caption += "  ·  Moon offsets enlarged"
    text(draw, CX, 1253, caption, 26, YELLOW, weight="Medium", align="middle")

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
    for index, name in enumerate(PLANET_RADII):
        x = 60 + (W - 120) / 8 * (index + 0.5)
        circle(draw, x, 1502, 7, fill=PLANET_INK[name])
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
    show_moons = os.environ.get("SHOW_MOONS") == "1"
    out_dir = Path(os.environ.get("OUTPUT_DIR") or "output")

    elements = elements_at(now)
    locations = {name: position(values) for name, values in elements.items()}
    moons = moon_positions(now)
    sun_au = {name: math.dist((0, 0, 0), xyz) for name, xyz in locations.items()}
    earth_au = {name: math.dist(locations["Earth"], xyz) for name, xyz in locations.items() if name != "Earth"}
    image = draw_dashboard(local, elements, locations, moons if show_moons else {}, sun_au, earth_au, palette)
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
        "moons": {
            name: {"planet": host, "offset_km": [round(value, 1) for value in offset]}
            for name, (host, offset) in moons.items()
        },
    }
    (out_dir / "solar_data.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{local.date()} - wrote {out_dir / 'solar_dashboard.png'} and solar_data.json")


if __name__ == "__main__":
    main()
