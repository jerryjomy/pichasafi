import io
import pytest
from PIL import Image
from app.image_processor import (
    enhance_image,
    create_gradient_background,
    create_solid_background,
    place_product_on_background,
    _hex_to_rgb,
    _darken_color,
    _to_jpeg_bytes,
)


def test_hex_to_rgb():
    assert _hex_to_rgb("#FF6B00") == (255, 107, 0)
    assert _hex_to_rgb("#000000") == (0, 0, 0)
    assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)


def test_darken_color():
    assert _darken_color("#FFFFFF", 0.5) == "#7f7f7f"
    assert _darken_color("#000000", 0.5) == "#000000"


def test_gradient_background():
    bg = create_gradient_background(size=(100, 100))
    assert bg.size == (100, 100)
    assert bg.mode == "RGB"
    # Top-left pixel should be close to color_top
    top_pixel = bg.getpixel((0, 0))
    bottom_pixel = bg.getpixel((0, 99))
    assert top_pixel != bottom_pixel  # Gradient means different colors


def test_solid_background():
    bg = create_solid_background(size=(200, 200), color="#FF0000")
    assert bg.size == (200, 200)
    assert bg.getpixel((0, 0)) == (255, 0, 0)


def test_enhance_image_rgb():
    img = Image.new("RGB", (100, 100), "gray")
    enhanced = enhance_image(img)
    assert enhanced.size == (100, 100)
    assert enhanced.mode == "RGB"


def test_enhance_image_rgba():
    img = Image.new("RGBA", (100, 100), (128, 128, 128, 200))
    enhanced = enhance_image(img)
    assert enhanced.size == (100, 100)
    assert enhanced.mode == "RGBA"


def test_place_product_on_background():
    bg = Image.new("RGB", (1080, 1080), "black")
    product = Image.new("RGBA", (500, 500), (255, 0, 0, 255))
    result = place_product_on_background(product, bg)
    assert result.size == (1080, 1080)
    assert result.mode == "RGB"


def test_place_product_scales_down():
    bg = Image.new("RGB", (100, 100), "black")
    product = Image.new("RGBA", (500, 500), (255, 0, 0, 255))
    result = place_product_on_background(product, bg, max_product_ratio=0.5)
    assert result.size == (100, 100)
    # Center pixel should be red (product placed there)
    center = result.getpixel((50, 50))
    assert center == (255, 0, 0)


def test_to_jpeg_bytes():
    img = Image.new("RGB", (100, 100), "blue")
    result = _to_jpeg_bytes(img)
    assert isinstance(result, bytes)
    assert len(result) > 0
    # Verify it's valid JPEG
    loaded = Image.open(io.BytesIO(result))
    assert loaded.format == "JPEG"


def test_to_jpeg_bytes_converts_rgba():
    img = Image.new("RGBA", (100, 100), (0, 0, 255, 128))
    result = _to_jpeg_bytes(img)
    loaded = Image.open(io.BytesIO(result))
    assert loaded.format == "JPEG"
    assert loaded.mode == "RGB"
