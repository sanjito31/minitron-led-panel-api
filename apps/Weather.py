from models.App import App
from utils.TimeKeeper import now
from utils.draw import Text, DISP_HEIGHT, DISP_WIDTH
from config import settings
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

WEATHER_API_REQ_INTERVAL = 600  # 10 minutes

def weather_update(config: dict) -> dict | None:
    url = config.get("api_url")

    if isinstance(url, str):
        resp = requests.get(url)

        weather = resp.json()

        if resp.status_code == 200:
            cache = {
                "temp": str(round(weather["main"]["temp"])),
                "feels_like": str(round(weather["main"]["feels_like"])),
                "temp_max": str(round(weather["main"]["temp_max"])),
                "temp_min": str(round(weather["main"]["temp_min"])),
                "description": str(weather["weather"][0]["main"])
            }
            return cache
    return None
    



def weather_render(cache: dict) -> bytes:

    return draw_weather(weather=cache)
    

def draw_weather(   weather: dict,
                    width: int = DISP_WIDTH,
                    height: int = DISP_HEIGHT,
                    fontsize: int = 8,
                    bg: tuple = (0, 0, 0),
                    fg: tuple = (255, 255, 255),
                    align: tuple = ('c', 'c')
                ):
    
    # mask = Image.new("1", (DISP_WIDTH, DISP_HEIGHT), 0)
    # draw = ImageDraw.Draw(mask)
    
    
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    try:
        # font = ImageFont.truetype("./fonts/JetBrainsMono/JetBrainsMonoNL-Regular.ttf", fontsize)
        font = ImageFont.truetype("./fonts/early_gameboy.ttf", fontsize, layout_engine=ImageFont.Layout.BASIC)
    except Exception as e:
        font = ImageFont.load_default()

    temp = Text(weather["temp"]+"F", draw, font)
    description = Text(weather["description"], draw, font)

    margin = 2

    # then apply color
    # img = Image.new("RGB", (DISP_WIDTH, DISP_HEIGHT), bg)
    # img.paste(Image.new("RGB", img.size, fg), mask=mask)
    
    # icon = Image.open("./assets/weather/cloud.png").convert("RGBA")
    # icon = icon.resize((24, 24))

    # color = Image.new("RGBA", icon.size, (255, 255, 255, 255))
    # color.putalpha(icon.getchannel("A"))

    # img.paste(color, (0, 0), mask=color)


    # yellow = (255, 255, 0)

    # draw.circle((2, 2), 10, fill=yellow, outline=yellow)
    # draw.line([(2, 14), (2, 18)], fill=yellow)
    # draw.line([(14, 2), (18, 2)], fill=yellow)

    # def sun_rays(angle, length):
    #     x = length * sin(radians(angle)) + 2
    #     y = length * -cos(radians(angle)) + 2
    #     return x, y

    # draw.line([(sun_rays(25+90, 14)), (sun_rays(25+90, 18))], fill=yellow)
    # draw.line([(sun_rays(45+90, 14)), (sun_rays(45+90, 18))], fill=yellow)
    # draw.line([(sun_rays(65+90, 14)), (sun_rays(65+90, 18))], fill=yellow)
    
    draw.text(description.coords(width-1-margin-description.width, height-1-margin-description.height), description.text, font=font, fill=fg)
    # draw.text(description.coords(0, 0), description.text, font=font, fill=1)

    draw.text(temp.coords(width-1-margin-temp.width, height-1-(2*margin)-temp.height-description.height), temp.text, font=font, fill=fg)
    # draw.text(temp.coords(0, 15), temp.text, font=font, fill=1)


    buf = BytesIO()
    img.save(buf, "WEBP")
    return buf.getvalue()
    

weather_app = App(
        id="weather",
        name="Weather",
        ttl=WEATHER_API_REQ_INTERVAL,
        enabled=True,
        update_fn=weather_update,
        render_fn=weather_render,
        config={
            "api_url": f"https://api.openweathermap.org/data/2.5/weather?lat={settings.LAT}&lon={settings.LON}&appid={settings.OPEN_WEATHER_API_KEY}&units=imperial"
        }
    )