# Solar System Dashboard

A daily 1200 × 1600 dashboard for E Ink Spectra 6 displays such as the Seeed E1004. It shares the black background, six-color palette, and bundled Inter fonts of the [Moon Phase Dashboard](https://github.com/MostlyFunctionalEngineering/moon_phase_dashboard).

The map looks down from ecliptic north. Each planet marker shows its current heliocentric longitude. Orbit spacing and marker sizes are schematic so all eight planets fit on the display. The dashboard shows the local date, Earth’s distance from the Sun, the planet currently closest to Earth, and each planet’s distance from the Sun in astronomical units (AU).

Positions are computed locally from [NASA/JPL’s approximate planetary elements](https://ssd.jpl.nasa.gov/planets/approx_pos.html) for 1800–2050. The Earth marker uses the Earth–Moon barycenter. No astronomy API or credentials are required.

## GitHub Pages

Select **GitHub Actions** under **Settings → Pages → Build and deployment**, then run **Update Solar System Dashboard** from the Actions tab. The scheduled workflow runs daily at 08:15 UTC, matching the Moon Phase Dashboard.

Point your display at `https://<owner>.github.io/<repository>/solar_dashboard.png`. The site root shows the image in a browser, and `solar_data.json` contains the UTC timestamp, local date, heliocentric coordinates, and distances.

The workflow accepts these optional repository variables under **Settings → Secrets and variables → Actions → Variables**.

| Variable | Default | Purpose |
| --- | --- | --- |
| `TZ_NAME` | `America/Los_Angeles` | IANA time zone for the date shown on the dashboard |
| `ROTATE` | `0` | Clockwise rotation in degrees. Supports `0`, `90`, `180`, and `270`. |
| `OUTPUT_PALETTE` | `pure` | Six pure panel colors. Use `device` for the measured panel colors. |

## Run locally

Use Python 3.12, the same version as the workflow.

```sh
python -m pip install -r requirements.txt
python scripts/render_solar.py
```

The renderer writes `output/solar_dashboard.png` and `output/solar_data.json`. Set `OUTPUT_DIR` to change the destination or `SOLAR_NOW` to render a specific ISO 8601 timestamp such as `2026-11-17T08:15:00Z`. If the timestamp omits an offset, the renderer uses UTC.

The bundled Inter fonts are distributed under the [SIL Open Font License](assets/fonts/LICENSE-Inter.txt).
