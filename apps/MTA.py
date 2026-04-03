import requests
from google.transit import gtfs_realtime_pb2
import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from models.App import App
from utils.draw import Text

ROUTES_CSV_PATH = "./assets/gtfs_subway/stops.txt"
BDFM_API_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"

MY_STATIONS = {
    "D22": "GRAND",
    "F15": "DELANCEY",
    "M18": "ESSEX"
}

MY_LINES = ["B", "D", "F", "M"]

MTA_TTL = 30  # seconds


def getMTA_realtime():

    now = int(time.time())

    feed = gtfs_realtime_pb2.FeedMessage()  # type: ignore[attr-defined]
    resp = requests.get(BDFM_API_URL)
    feed.ParseFromString(resp.content)

    rt_updates = {
        line: {
            "station": "",
            "uptown_waits": [],
            "downtown_waits": []
        }
        for line in MY_LINES
    }

    for entity in feed.entity:
        if entity.HasField('trip_update'):
            tu = entity.trip_update
            line = tu.trip.route_id
            for stop in tu.stop_time_update:
                parent_stop = stop.stop_id[:-1]
                direction = stop.stop_id[-1]
                if parent_stop in tuple(MY_STATIONS.keys()):
                    wait = max(0, ((stop.arrival.time - now) // 60))
                    if wait > 30:
                        continue
                    rt_updates[f"{line}"]["station"] = MY_STATIONS[parent_stop]
                    if direction == "N":
                        rt_updates[f"{line}"]["uptown_waits"].append(wait)
                    else:
                        rt_updates[f"{line}"]["downtown_waits"].append(wait)

    for line in rt_updates.values():
        line["uptown_waits"].sort()
        line["downtown_waits"].sort()

    return rt_updates


# -- AppNew functions --

def mta_update(config: dict) -> dict | None:
    cache = getMTA_realtime()
    return cache


def mta_render(cache: dict) -> bytes:
    if cache is None:
        cache = {line: {"uptown_waits": [], "downtown_waits": []} for line in MY_LINES}

    DISP_WIDTH = 64
    DISP_HEIGHT = 32
    ROW_HEIGHT = DISP_HEIGHT // len(MY_LINES)  # 8px per row
    BDFM_ORANGE = (255, 153, 0)
    WHITE = (255, 255, 255)
    DIM = (120, 120, 120)

    img = Image.new("RGB", (DISP_WIDTH, DISP_HEIGHT))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("./fonts/Minecraft.ttf", 8)
    except OSError:
        font = ImageFont.load_default(7)

    for i, line in enumerate(MY_LINES):
        y = i * ROW_HEIGHT
        data = cache.get(line, {})

        up_waits = data.get("uptown_waits", [])
        dn_waits = data.get("downtown_waits", [])

        up_str = f"{up_waits[0]}" if up_waits else "-"
        dn_str = f"{dn_waits[0]}" if dn_waits else "-"

        # Show second train if available
        up2_str = f" {up_waits[1]}" if len(up_waits) > 1 else ""
        dn2_str = f" {dn_waits[1]}" if len(dn_waits) > 1 else ""

        t_line = Text(line, draw, font)
        t_up = Text(up_str + up2_str, draw, font)
        t_dn = Text(dn_str + dn2_str, draw, font)

        row_y = y + (ROW_HEIGHT - t_line.height) // 2

        # Line letter in orange
        draw.text(t_line.coords(1, row_y), line, font=font, fill=BDFM_ORANGE)

        # Uptown (left side)
        draw.text(t_up.coords(11, row_y), up_str, font=font, fill=WHITE)
        if up2_str:
            t_up2 = Text(up2_str.strip(), draw, font)
            draw.text(t_up2.coords(11 + t_up.width + 2, row_y), up2_str.strip(), font=font, fill=DIM)

        # Divider
        draw.line([(32, y + 1), (32, y + ROW_HEIGHT - 2)], fill=(50, 50, 50), width=1)

        # Downtown (right side)
        draw.text(t_dn.coords(35, row_y), dn_str, font=font, fill=WHITE)
        if dn2_str:
            t_dn2 = Text(dn2_str.strip(), draw, font)
            draw.text(t_dn2.coords(35 + t_dn.width + 2, row_y), dn2_str.strip(), font=font, fill=DIM)

    buf = BytesIO()
    img.save(buf, "WEBP")
    return buf.getvalue()


mta_app = App(
    id="mta",
    name="MTA",
    config=None,
    update_fn=mta_update,
    render_fn=mta_render,
    enabled=True,
    ttl=MTA_TTL,
)
