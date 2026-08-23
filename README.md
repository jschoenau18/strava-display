# HARDWARE

## Display

> Waveshare Spectra 6 (E6)  

[Details](https://www.waveshare.com/4inch-e-paper-hat-plus-e.htm?sku=27367)

Size: 600x400 (4")

## Controller

> Raspberry Pi Zero 2 W  

[Details](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)

## Raspberry Pi setup

1. Install Raspberry Pi OS Lite (64-bit), enable SPI in `raspi-config`, and connect the display with the HAT seated on the GPIO header.
2. Install the official Waveshare Python library on the Pi. It must provide `waveshare_epd.epd4in0e`.
3. Copy this project to the Pi, create a virtual environment, and install the project dependencies:

	```sh
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	```

4. Copy `.env` with the Strava credentials to the project directory.
5. Set `STRAVA_UPDATE_DISPLAY=1` in `.env` and run:

	```sh
	.venv/bin/python main.py
	```

Without `STRAVA_UPDATE_DISPLAY=1`, the program only writes `output/dashboard.png`, which is useful for testing without the display connected.
