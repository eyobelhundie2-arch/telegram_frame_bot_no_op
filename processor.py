from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, ImageDraw

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
TEMPLATE_PATH = BASE_DIR / "templates" / "template.png"

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

OUTPUT_SIZE = tuple(CONFIG["output_size"])
CIRCLE = CONFIG["circle"]


def _load_image(path: str | Path) -> Image.Image:
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("RGB")
    return img


def _crop_portrait(img: Image.Image) -> Image.Image:
    """Create a portrait crop using the configured vertical focus.

    This deliberately uses only Pillow so the bot has no OpenCV dependency.
    The crop fills the circle while keeping the upper portion of the person
    prominent, matching the supplied reference's general composition.
    """
    cx = CIRCLE["center_x"]
    cy = CIRCLE["center_y"]
    radius = CIRCLE["radius"]

    diameter = radius * 2
    target_w = diameter
    target_h = diameter

    # Cover the circular area.
    scale = max(target_w / img.width, target_h / img.height)
    nw = max(1, round(img.width * scale))
    nh = max(1, round(img.height * scale))
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)

    focus_y = float(CONFIG.get("fallback_focus_y", 0.38))
    focus_y = min(0.75, max(0.25, focus_y))

    left = max(0, (nw - target_w) // 2)
    top = round(nh * focus_y - target_h * 0.5)

    left = min(left, max(0, nw - target_w))
    top = min(max(0, top), max(0, nh - target_h))

    return img.crop((left, top, left + target_w, top + target_h))


def _circle_mask() -> Image.Image:
    cx = CIRCLE["center_x"]
    cy = CIRCLE["center_y"]
    radius = CIRCLE["radius"]

    mask = Image.new("L", OUTPUT_SIZE, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=255,
    )

    blur = float(CONFIG.get("mask_blur", 0.6))
    if blur > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def make_framed_image(input_path: str | Path, output_path: str | Path) -> Path:
    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    if template.size != OUTPUT_SIZE:
        template = template.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)

    photo = _crop_portrait(_load_image(input_path)).convert("RGBA")

    # Place the crop so its center aligns exactly with the configured circle.
    cx = CIRCLE["center_x"]
    cy = CIRCLE["center_y"]
    x = round(cx - photo.width / 2)
    y = round(cy - photo.height / 2)

    mask = _circle_mask()

    result = template.copy()
    photo_layer = Image.new("RGBA", OUTPUT_SIZE, (0, 0, 0, 0))
    photo_layer.paste(photo, (x, y), photo)

    # The mask controls the exact circular photo area. All other template
    # artwork remains unchanged.
    result.paste(photo_layer, (0, 0), mask)

    result.save(output_path, "PNG", optimize=True)
    return Path(output_path)
