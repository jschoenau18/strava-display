from __future__ import annotations

from importlib import import_module
from pathlib import Path

from PIL import Image


def update_display(image: Image.Image, driver_name: str = "epd4in0e") -> None:
    """Send a rendered image to the Waveshare driver installed on the Pi."""

    if image.size != (600, 400):
        raise ValueError(f"Expected a 600x400 image, got {image.size[0]}x{image.size[1]}")

    try:
        driver = import_module(f"waveshare_epd.{driver_name}")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Waveshare driver not found. Install the vendor e-Paper library on the Pi "
            "and make sure waveshare_epd is on PYTHONPATH."
        ) from error

    epd = driver.EPD()
    try:
        epd.init()
        epd.display(epd.getbuffer(image.convert("RGB")))
    finally:
        epd.sleep()


def update_display_from_file(image_path: str | Path, driver_name: str = "epd4in0e") -> None:
    """Load a rendered dashboard from disk and send it to the panel."""

    with Image.open(image_path) as image:
        update_display(image, driver_name=driver_name)