"""Planet-centered moon vectors in the J2000 ecliptic frame, in kilometers."""

from datetime import datetime, timezone
from math import cos, sin, tau

import astronomy

from orbits import AU_KM, J2000

FIT_EPOCH = datetime(2027, 1, 1, tzinfo=timezone.utc)

# Two-harmonic fits to geometric, planet-centered JPL Horizons vectors sampled
# every two days from 2025 through 2028 (targets 606, 703, 801). The fits are
# intended for display; their accuracy decreases with distance from the epoch.
# Columns give the period in days and the constant, cos(t), sin(t), cos(2t),
# sin(2t) XYZ coefficients in km. https://ssd.jpl.nasa.gov/horizons/
HORIZONS_FITS = {
    "Titan": ("Saturn", 15.9454568, (
        (-51446, 11154, -633), (629718, -954342, 429385), (1041031, 519643, -371474),
        (-4941, -14713, 8078), (16807, -5123, 971),
    )),
    "Titania": ("Uranus", 8.705868, (
        (-194, 183, 1006), (424601, -96706, -26476), (-38687, -51732, -431473),
        (122, 18, 318), (308, -83, -112),
    )),
    "Triton": ("Neptune", 5.8768433, (
        (6, -40, -54), (-157840, 158832, 275160), (256527, 244975, 5745),
        (-24, 13, 6), (14, 15, 10),
    )),
}


def moon_positions(now):
    time = astronomy.Time((now - J2000).total_seconds() / 86400)
    rotation = astronomy.Rotation_EQJ_ECL()
    moon = astronomy.RotateVector(rotation, astronomy.GeoMoon(time))
    positions = {"Moon": ("Earth", tuple(AU_KM * v for v in (moon.x, moon.y, moon.z)))}

    jovian = astronomy.JupiterMoons(time)
    for name in ("Io", "Europa", "Ganymede", "Callisto"):
        state = astronomy.RotateState(rotation, getattr(jovian, name.lower()))
        positions[name] = ("Jupiter", tuple(AU_KM * v for v in (state.x, state.y, state.z)))

    elapsed = (now - FIT_EPOCH).total_seconds() / 86400
    for name, (host, period, coefficients) in HORIZONS_FITS.items():
        angle = tau * (elapsed % period) / period
        terms = (1, cos(angle), sin(angle), cos(2 * angle), sin(2 * angle))
        positions[name] = (host, tuple(sum(c * term for c, term in zip(axis, terms)) for axis in zip(*coefficients)))
    return positions
