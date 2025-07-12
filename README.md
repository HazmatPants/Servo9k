# Servo9k

A modular, multipurpose Discord bot written in Python using `discord.py`.  
Servo9k features include procedural image generation, image effects, and math evaluation with a clean plugin-like structure for adding new commands and behaviors.

---

## Features

- `s9k calc <expression>` — Evaluates math expressions safely (with `math` module support).
- `s9k image generate <mode> [width] [height]` — Generate procedural images like noise and plasma.
- `s9k image effect <effect> [params...]` — Apply filters like blur, jpegify, resize, and more.
- Modular system for easily registering new image generators and effects via decorators.

---

## Example Usage

```plaintext
s9k calc pi * 7 ** 2
s9k image generate color_noise 128 128
s9k image effect blur radius=3
s9k image effect resize width=256
```

You can also apply image effects by replying to a message with an image.

---

# Setup

## Main Requirements
- Python 3.10+
- `discord.py`
- Pillow

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Discord Token
Save your bot token to a file named `TOKEN` in the project root. This file is in `.gitignore` and Git will not track it.

## Running Servo9k
```bash
python bot.py
```
May also be:
```bash
python3 bot.py
```

---

# Adding new effects or Generators
Just decorate the function:
```python
@register_effect("invert")
def effect_invert(img **kwargs):
    return ImageOps.invert(img)
```
For generators:
```python
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
```

***

# License
[GNU GPL v3.0](https://github.com/HazmatPants/Servo9k/blob/main/LICENSE)
