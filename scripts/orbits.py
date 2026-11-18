"""Approximate heliocentric positions from NASA/JPL's 1800–2050 model."""

from datetime import datetime, timezone
from math import cos, radians, sin, sqrt

J2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
AU_KM = 149_597_870.7

# JPL Table 1: a, e, inclination, mean longitude, longitude of perihelion,
# and longitude of the ascending node, followed by their rates per century.
# https://ssd.jpl.nasa.gov/planets/approx_pos.html
ELEMENTS = {
    "Mercury": (
        (0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
        (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081),
    ),
    "Venus": (
        (0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
        (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418),
    ),
    "Earth": (
        (1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
        (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0),
    ),
    "Mars": (
        (1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
        (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343),
    ),
    "Jupiter": (
        (5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
        (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106),
    ),
    "Saturn": (
        (9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
        (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794),
    ),
    "Uranus": (
        (19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503),
        (-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589),
    ),
    "Neptune": (
        (30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574),
        (0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664),
    ),
}


def position(elements):
    a, e, i, longitude, perihelion, node = elements
    mean = radians((longitude - perihelion + 180) % 360 - 180)
    anomaly = mean
    for _ in range(8):
        anomaly -= (anomaly - e * sin(anomaly) - mean) / (1 - e * cos(anomaly))

    x = a * (cos(anomaly) - e)
    y = a * sqrt(1 - e**2) * sin(anomaly)
    i, argument, node = map(radians, (i, perihelion - node, node))
    p = x * cos(argument) - y * sin(argument)
    q = x * sin(argument) + y * cos(argument)
    return (
        p * cos(node) - q * cos(i) * sin(node),
        p * sin(node) + q * cos(i) * cos(node),
        q * sin(i),
    )


def elements_at(now):
    if not 1800 <= now.year <= 2050:
        raise ValueError("SOLAR_NOW must fall within JPL's 1800–2050 model range")
    # UTC is a sufficient approximation of the ephemeris time for this display.
    centuries = (now - J2000).total_seconds() / (36525 * 86400)
    return {
        name: tuple(value + rate * centuries for value, rate in zip(elements, rates))
        for name, (elements, rates) in ELEMENTS.items()
    }
