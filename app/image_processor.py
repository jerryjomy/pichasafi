import io
import logging
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

OUTPUT_SIZE = (1080, 1080)
JPEG_QUALITY = 90


def remove_background(image_bytes: bytes) -> Image.Image:
    """Remove background using rembg (U2Net). Returns RGBA image."""
    from rembg import remove

    logger.info("Starting background removal...")
    output_bytes = remove(image_bytes)
    img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    logger.info(f"Background removed. Size: {img.size}")
    return img


def enhance_image(img: Image.Image) -> Image.Image:
    """Auto-enhance: sharpen, brightness +10%, contrast +15%, saturation +10%."""
    if img.mode == "RGBA":
        rgb = img.convert("RGB")
        alpha = img.split()[3]
    else:
        rgb = img
        alpha = None

    rgb = rgb.filter(ImageFilter.SHARPEN)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.1)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    rgb = ImageEnhance.Color(rgb).enhance(1.1)

    if alpha:
        rgb = rgb.convert("RGBA")
        rgb.putalpha(alpha)

    return rgb


def create_gradient_background(
    size: tuple = OUTPUT_SIZE,
    color_top: str = "#1A1A2E",
    color_bottom: str = "#16213E",
) -> Image.Image:
    """Create a vertical gradient background."""
    img = Image.new("RGB", size)
    r1, g1, b1 = _hex_to_rgb(color_top)
    r2, g2, b2 = _hex_to_rgb(color_bottom)

    for y in range(size[1]):
        ratio = y / size[1]
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        for x in range(size[0]):
            img.putpixel((x, y), (r, g, b))

    return img


def create_solid_background(
    size: tuple = OUTPUT_SIZE, color: str = "#1A1A2E"
) -> Image.Image:
    """Create a solid color background."""
    return Image.new("RGB", size, _hex_to_rgb(color))


def place_product_on_background(
    product_img: Image.Image,
    background: Image.Image,
    max_product_ratio: float = 0.7,
) -> Image.Image:
    """Center the product image on the background, scaled to fit."""
    bg = background.copy()
    bg_w, bg_h = bg.size

    max_w = int(bg_w * max_product_ratio)
    max_h = int(bg_h * max_product_ratio)
    product_img.thumbnail((max_w, max_h), Image.LANCZOS)

    p_w, p_h = product_img.size
    x = (bg_w - p_w) // 2
    y = (bg_h - p_h) // 2

    if product_img.mode == "RGBA":
        bg.paste(product_img, (x, y), product_img)
    else:
        bg.paste(product_img, (x, y))

    return bg


def process_product_photo(image_bytes: bytes, bg_color: str = "#1A1A2E") -> bytes:
    """
    Phase 1 pipeline (lightweight — no background removal to save memory):
    1. Open and enhance product image
    2. Create gradient background from brand color
    3. Place product on background
    4. Export as 1080x1080 JPEG

    Background removal (rembg) disabled due to memory constraints on
    free-tier hosting. Can be re-enabled with more RAM (1GB+).
    """
    product = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    logger.info(f"Opened image. Size: {product.size}")
    product = enhance_image(product)

    background = create_gradient_background(
        color_top=bg_color,
        color_bottom=_darken_color(bg_color, 0.7),
    )

    result = place_product_on_background(product, background)
    return _to_jpeg_bytes(result)


# --- Helpers ---


def _to_jpeg_bytes(img: Image.Image) -> bytes:
    """Convert PIL Image to JPEG bytes."""
    if img.mode == "RGBA":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert '#RRGGBB' to (R, G, B) tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _darken_color(hex_color: str, factor: float) -> str:
    """Darken a hex color by a factor (0.0=black, 1.0=unchanged)."""
    r, g, b = _hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"
