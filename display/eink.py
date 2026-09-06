from __future__ import annotations

from importlib import import_module
from pathlib import Path

from PIL import Image


def update_display(image: Image.Image, driver_name: str = "epd4in0e", rotate_180: bool = False) -> None:
    """Send a rendered image to the Waveshare driver installed on the Pi."""

    if image.size != (600, 400):
        raise ValueError(f"Expected a 600x400 image, got {image.size[0]}x{image.size[1]}")

    # Without an enabled SPI interface, the Waveshare driver can never talk
    # to the panel controller: it polls the BUSY GPIO pin with no timeout,
    # which hangs forever instead of raising an error. Fail fast here with
    # an actionable message instead.
    if not any(Path("/dev").glob("spidev*")):
        raise RuntimeError(
            "No /dev/spidev* device found - SPI is not enabled (or was enabled "
            "without a reboot afterwards). Run 'sudo raspi-config nonint do_spi 0' "
            "and reboot, then check 'ls /dev/spidev*'."
        )

    try:
        driver = import_module(f"waveshare_epd.{driver_name}")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Waveshare driver not found. Install the vendor e-Paper library on the Pi "
            "and make sure waveshare_epd is on PYTHONPATH."
        ) from error

    # rotate_180=True is for a panel physically mounted upside down (see
    # STRAVA_DISPLAY_ROTATE_180) - the saved PNGs (used for preview) stay
    # in normal orientation, only what's sent to the panel is flipped.
    if rotate_180:
        image = image.rotate(180)

    epd = driver.EPD()
    try:
        epd.init()
        epd.display(epd.getbuffer(image.convert("RGB")))
    finally:
        epd.sleep()


def update_display_from_file(image_path: str | Path, driver_name: str = "epd4in0e", rotate_180: bool = False) -> None:
    """Load a rendered dashboard from disk and send it to the panel."""

    with Image.open(image_path) as image:
        update_display(image, driver_name=driver_name, rotate_180=rotate_180)