from discord.ext import commands
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw
import discord
import json
import os
import io
import datetime
import difflib
import math
import random
import numpy as np

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="s9k ", intents=intents, owner_id=939268122668584970)

DB_FILE = 'data.json'
LOG_FILE = "log.log"

IMAGE_GENERATORS = {}
IMAGE_EFFECTS = {}

# === Other Functions ===

def parse_kwargs(args):
    kwargs = {}
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            try:
                kwargs[k] = eval(v, {"__builtins": {}})
            except:
                kwargs[k] = v
    return kwargs

def register_generator(name):
    def decorator(func):
        IMAGE_GENERATORS[name] = func
        return func
    return decorator

def register_effect(name):
    def decorator(func):
        IMAGE_EFFECTS[name] = func
        return func
    return decorator

async def get_image_from_context(ctx):
    target = ctx.message
    if ctx.message.reference:
        target = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    if not target.attachments:
        return None

    image_bytes = await target.attachments[0].read()
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

def log_init():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as file:
            file.write("")

def sp_init():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as file:
            file.write("{}")

async def logf(text):
    with open(LOG_FILE, "a") as file:
        file.write("{:%Y-%m-%d %H:%M:%S} ".format(datetime.datetime.now()) + text + "\n")

log_init()
sp_init()

# === Data Handling ===

def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as file:
        return json.load(file)

def save_data(data):
    with open(DB_FILE, 'w') as file:
        json.dump(data, file, indent=2)

def get_user(user_id):
    data = load_data()
    return next((user for user in data if user['id'] == str(user_id)), None)

def add_user(discord_user):
    data = load_data()
    user_id = str(discord_user.id)
    if get_user(user_id):
        return False
    data.append({
        'id': user_id,
        'name': discord_user.name,
        'points': 0
    })
    save_data(data)
    return True

def update_user(user_id, field, value):
    data = load_data()
    for user in data:
        if user['id'] == str(user_id):
            user[field] = value
            save_data(data)
            return True
    return False

def list_users():
    data = load_data()
    if not data:
        return "No users yet."
    msg = "**📋 Users:**\n"
    for user in data:
        msg += f"`{user['name']}` — {user['points']} pts\n"
    return msg

# === SP Commands ===
@bot.group(help="Sigma point commands")
async def sp(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("See usage: `s9k help sp`")

@sp.command(help="Add a user to the system, requires Pointmaster")
async def add(ctx, user: discord.Member = None):
    user = user or ctx.author
    if add_user(user):
        await logf(f"{user.name} added to system")
        await ctx.send(f" Added `{user.name}` to the sigma point system.")
    else:
        await ctx.send(f"`{user.name}` is already registered.")

@sp.command(help="Give or take points from a user (negative for taking)")
async def give(ctx, user: discord.Member, value: int):
    if "Pointmaster" not in [role.name for role in ctx.author.roles]:
        await ctx.send("🚫 You don’t have permission to give points.")
        return
    if user.id == ctx.author.id:
        await ctx.send("👀 You can’t give points to yourself.")
        return
    target = get_user(user.id)
    if not target:
        await ctx.send("User not found. Add them first with `s9k sp add @user`.")
        return
    if abs(value) > 25:
        await ctx.send("⚠️ You can’'t give/take more than 25 points at once.")
    else:
        target['points'] += value
        update_user(user.id, 'points', target['points'])
        await logf(f"{ctx.author.name} gave {user.name} {str(value)} points")
        await ctx.send(f"`{user.name}` now has `{target['points']}` points.")

@sp.command(help="Get a specific user's points")
async def get(ctx, user: discord.Member):
    target = get_user(user.id)
    if target:
        await ctx.send(f"`{user.name}` has `{target['points']}` points.")
    else:
        await ctx.send(" User not found.")

@sp.command(aliases=["ls"], help="Shows an unordered list of users and their points")
async def list(ctx):
    await ctx.send(list_users())

@sp.command(aliases=["lb", "top", "leader"], help="Shows an ascending list of users and their points")
async def leaderboard(ctx, count: int = 5):
    data = load_data()
    if not data:
        await ctx.send("⚠️ No users in the system yet.")
        return

    sorted_users = sorted(data, key=lambda x: x['points'], reverse=True)
    count = min(count, len(sorted_users))
    msg = f"**🏆 Leaderboard — Top {count} Users**\n"

    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * (count - 3)
    for i in range(count):
        u = sorted_users[i]
        medal = medals[i] if i < len(medals) else f"`{i+1}.`"
        msg += f"{medal} `{u['name']}` — `{u['points']} pts`\n"

    await ctx.send(msg)

@sp.command(help="Gets the SP log")
async def log(ctx, entry=None):
    if entry is None:
        if os.path.exists(LOG_FILE):
            await ctx.send(file=discord.File(LOG_FILE))
    else:
        with open(LOG_FILE, "r") as file:
            lines = file.readlines()
        try:
            if entry == "latest":
                await ctx.send(lines[len(lines) - 1])
            else:
                await ctx.send(lines[int(entry) - 1])
        except IndexError:
            await ctx.send(f"Log entry {entry} does not exist.")

# === Events ===

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        user_input = ctx.message.content[len(bot.command_prefix):].split()[0]
        valid_commands = [cmd.name for cmd in bot.commands]
        suggestion = difflib.get_close_matches(user_input, valid_commands, n=1)

        if suggestion:
            await ctx.send(f"❓ Unknown command `{user_input}`. Did you mean `{bot.command_prefix}{suggestion[0]}`?")
        else:
            await ctx.send(f"❓ Unknown command `{user_input}`. Try `{bot.command_prefix}help` for a list of commands.")
    else:
        raise error

# === Image Processing Commands ===

@bot.group(help="Image processing commands")
async def image(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("See usage: `s9k help image`")

# === Image Effects ===

@register_effect("mono")
def effect_grayscale(img, **kwargs):
        return img.convert("L").convert("RGB")

@register_effect("invert")
def effect_invert(img, **kwargs):
    return ImageOps.invert(img)

@register_effect("blur")
def effect_blur(img, radius=3, **kwargs):
    return img.filter(ImageFilter.GaussianBlur(radius))

@register_effect("brightness")
def effect_brightness(img, factor=1.0, **kwargs):
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(factor)

@register_effect("contrast")
def effect_contrast(img, factor=1.0, **kwargs):
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)

@register_effect("pixelate")
def effect_pixelate(img, scale=8, **kwargs):
    w, h = img.size
    img = img.resize ((w//scale, h//scale), resample=Image.NEAREST)
    return img.resize((w, h), resample=Image.NEAREST)

@register_effect("posterize")
def effect_posterize(img, bits=4, **kwargs):
    return ImageOps.posterize(img, bits)

@register_effect("solarize")
def effect_solarize(img, threshold=128, **kwargs):
    return ImageOps.solarize(img, threshold)

@register_effect("jpegify")
def effect_jpegify(img, quality=10, **kwargs):
    jpg_buf = io.BytesIO()
    img.convert("RGB").save(jpg_buf, format="JPEG", quality=quality)
    jpg_buf.seek(0)
    jpg_img = Image.open(jpg_buf)

    png_buf = io.BytesIO()
    jpg_img.save(png_buf, format="PNG")
    png_buf.seek(0)
    return Image.open(png_buf)

@register_effect("resize")
def effect_resize(img, width=None, height=None, **kwargs):
    original_width, original_height = img.size

    if width and not height:
        ratio = width / original_width
        height = int(original_height * ratio)
    elif height and not width:
        ratio = height / original_height
        width = int(original_width * ratio)
    elif not width and not height:
        return img

    width = int(width)
    height = int(height)

    return img.resize((width, height), resample=Image.NEAREST)

@image.command(help="Apply effects to images")
async def effect(ctx, mode: str=None, *args):
    if mode is None:
        await ctx.send(
        """
        ```
        Image Effect Syntax
        Synopsis:
        s9k image effect <mode> [key=value]...

        Parameters are shown as [param=default_value]

        Modes:
        "mono": Converts the image to grayscale
        Params: None
        "invert": Inverts the color values of the image
        Params: None
        "blur": Blurs the image by [radius]
        Params: [radius=3]
        "brightness": Increases the brightness of the image by [factor]
        Params: [factor=1.0]
        "contrast": Increases the contrast of the image by [factor]
        Params: [factor=1.0]
        "pixelate": Enlarges the pixels of the image by [scale]
        Params: [scale=8]
        "posterize": Reduces the number of bits per color channel by [bits]
        Params: [bits=4]
        "solarize": Inverts all pixels brighter than [threshold]
        Params: [threshold=128]
        "jpegify": Converts an image to JPEG with [quality] (Still returns the image as PNG though)
        Low quality will have more JPEG compression artifacts
        Params: [quality=10]
        "resize": Resizes the image to [width]x[height]
        Params: [width] [height]

        Example Commands:
        s9k image effect blur radius=20
        s9k image effect posterize bits=3
        s9k image effect resize width=256 height=256
        ```
        """)
        return

    if mode not in IMAGE_EFFECTS:
        available = ", ".join(IMAGE_GENERATORS.keys())
        await ctx.send(f"Unknown mode `{mode}`. Available modes: `{available}`")
        return

    image_bytes = await get_image_from_context(ctx)
    if not image_bytes:
        await ctx.send("Please attach an image or reply to a message with an image.")
        return

    kwargs = parse_kwargs(args)

    msg = await ctx.send("Applying effect...")
    img = IMAGE_EFFECTS[mode](image_bytes, **kwargs)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    await ctx.send(file=discord.File(buf, f"{mode}.png"))
    await msg.delete()

# === Image Generation Modes ===

@register_generator("white_noise")
def generate_white_noise(width, height):
    img = Image.new("L", (width, height))
    pixels = [
        random.randint(0, 255)
        for _ in range(width * height)
    ]
    img.putdata(pixels)
    return img.convert("RGB")

@register_generator("color_noise")
def generate_color_noise(width, height):
    img = Image.new("RGB", (width, height))
    pixels = [
        (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for _ in range(width * height)
    ]
    img.putdata(pixels)
    return img

@register_generator("plasma")
def generate_plasma(width, height):
    img = Image.new("RGB", (width, height))
    pixels = []

    for y in range(height):
        for x in range(width):
            r = int(127 * (math.sin(x * random.uniform(0.079, 0.081)) + 1))
            g = int(127 * (math.sin(y * random.uniform(0.079, 0.081)) + 1))
            b = int(127 * (math.sin((x + y) * random.uniform(0.079, 0.081)) + 1))
            pixels.append((r, g, b))

    img.putdata(pixels)
    return img

from PIL import Image

@register_generator("mandelbrot")
def generate_mandelbrot(width=256, height=256, max_iter=100, **kwargs):
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    x_min, x_max = -2.5, 1
    y_min, y_max = -1.25, 1.25

    for x in range(width):
        for y in range(height):
            zx = x / width * (x_max - x_min) + x_min
            zy = y / height * (y_max - y_min) + y_min
            z = complex(0, 0)
            c = complex(zx, zy)

            i = 0
            while abs(z) <= 2 and i < max_iter:
                z = z*z + c
                i += 1

            color = 255 - int(i * 255 / max_iter)
            pixels[x, y] = (color, color, color)

    return img

@register_generator("burning_ship")
def generate_burning_ship(width=256, height=256, max_iter=100, **kwargs):
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    x_min, x_max = -2.5, 1
    y_min, y_max = -1.25, 1.25

    for x in range(width):
        for y in range(height):
            zx = x / width * (x_max - x_min) + x_min
            zy = y / height * (y_max - y_min) + y_min
            z = complex(0, 0)
            c = complex(zx, zy)

            i = 0
            while abs(z) <= 2 and i < max_iter:
                z = complex(abs(z.real), abs(z.imag))
                z = z*z + c
                i += 1

            color = 255 - int(i * 255 / max_iter)
            pixels[x, y] = (color, color, color)

    return img

@register_generator("sierpinski_triangle")
def generate_sierpinski(width=256, height=256, iterations=10000, **kwargs):
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    p1 = (width // 2, 0)
    p2 = (0, height - 1)
    p3 = (width - 1, height - 1)
    vertices = [p1, p2, p3]

    x, y = random.randint(0, width), random.randint(0, height)

    for _ in range(iterations):
        target = random.choice(vertices)
        x = (x + target[0]) // 2
        y = (y + target[1]) // 2
        draw.point((x, y), fill="white")

    return img

from PIL import Image, ImageDraw
import math

@register_generator("koch_snowflake")
def generate_koch_snowflake(width=512, height=512, iterations=4, **kwargs):
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    size = min(width, height) * 0.8
    height_triangle = size * math.sqrt(3) / 2

    p1 = ((width - size) / 2, height / 2 + height_triangle / 3)
    p2 = ((width + size) / 2, height / 2 + height_triangle / 3)
    p3 = (width / 2, height / 2 - 2 * height_triangle / 3)

    def koch_curve(draw, p1, p2, iter):
        if iter == 0:
            draw.line([p1, p2], fill="white")
            return

        dx = (p2[0] - p1[0]) / 3
        dy = (p2[1] - p1[1]) / 3

        a = p1
        b = (p1[0] + dx, p1[1] + dy)
        d = (p1[0] + 2 * dx, p1[1] + 2 * dy)
        e = p2

        angle = math.radians(60)
        cx = b[0] + math.cos(angle) * (d[0] - b[0]) - math.sin(angle) * (d[1] - b[1])
        cy = b[1] + math.sin(angle) * (d[0] - b[0]) + math.cos(angle) * (d[1] - b[1])
        c = (cx, cy)

        koch_curve(draw, a, b, iter - 1)
        koch_curve(draw, b, c, iter - 1)
        koch_curve(draw, c, d, iter - 1)
        koch_curve(draw, d, e, iter - 1)

    koch_curve(draw, p1, p2, iterations)
    koch_curve(draw, p2, p3, iterations)
    koch_curve(draw, p3, p1, iterations)

    return img

@image.command(help="Generate synthetic images")
async def generate(ctx, mode: str=None, width: int=256, height: int=256, *args):
    if mode is None:
        await ctx.send(
        """
        ```
        Image Generate Syntax
        Synopsis:
        s9k image generate <mode> [width] [height] [key=value]...

        If width/height is not provided, it will default to 256.

        Modes:
        "white_noise": Grayscale static, like TV static
        Params: None
        "color_noise": Random color noise
        Params: None
        "plasma": Wavy colorful noise using sine waves
        Params: None
        "sierpinski_triangle": An equilateral triangle subdivided recursively into smaller equilateral triangles.
        Params: [iterations=10000]
        "koch_snowflake": A spiky, infinitely detailed, starry snowflake shape made of smaller and smaller triangle bumps.
        Params: [iterations=4]


        Slow Modes: (These are slower as they require complex math)
        "manelbrot": A complex, endlessly detailed shape with bulbous, rounded blobs connected by thin filaments,
        Params: [max_iter=100]
        "burning_ship": A fiery, jagged, and ship-like structure, with flame-like tendrils, sharp edges, and mirrored symmetry.
        The Burning Ship fractal is very mathematically similar to the Mandelbrot set, yet looks completely different.
        [max_iter=10]
        Example Command:
        s9k image generate mandelbrot 128 128 max_iter=100
        ```
        """)
        return
    if mode not in IMAGE_GENERATORS:
        available = ", ".join(IMAGE_GENERATORS.keys())
        await ctx.send(f"Unknown mode `{mode}`. Available modes: `{available}`")
        return
    if width > 1024 or height > 1024:
        await ctx.send("Max size is 1024 to prevent overload.")
        return

    try:
        kwargs = parse_kwargs(args)

        msg = await ctx.send("Generating...")
        img = IMAGE_GENERATORS[mode](width, height, **kwargs)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        await ctx.send(file=discord.File(buf, f"{mode}.png"))
        await msg.delete()
    except Exception as e:
        await ctx.send(f"Error: `{e}`")

# === Base Commands ===

@bot.command(help="Says hello")
async def hello(ctx):
    if commands.is_owner():
        await ctx.send("Hello, creator.")
    else:
        await ctx.send("Hello.")

@bot.command(help="Evaluates a math expression. Safe functions only (sin, cos, abs, etc.)")
async def calc(ctx, *, expression):
    allowed_names = {
        k: getattr(math, k) for k in dir(math) if not k.startswith("__")
    }
    allowed_names.update({
        "abs": abs,
        "round": round
    })

    def safe_eval(expr: str) -> float:
        safe_globals = {"__builtins__": {}}

        return eval(expr, safe_globals, allowed_names)

    try:
        if expression == "open(\"TOKEN\")" or expression == "open('TOKEN')":
            await ctx.send("No.")
        else:
            result = safe_eval(expression)
            await ctx.send(f"Result: `{result}`")
    except NameError as e:
        await ctx.send(f"Error: `{e}`. Not allowed or not found.")
    except Exception as e:
        await ctx.send(f"Error: `{e}`")

# === Run the bot ===
TOKEN = open("TOKEN", "r").read().strip()
bot.run(TOKEN)

