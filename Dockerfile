# Raspberry Pi OS 32-bit meldet sich bei "uname -m" als armv6l (Kompatibilität
# mit dem ersten Pi), auch auf ARMv8-Hardware wie dem Pi Zero 2 W. Offizielle
# Images bieten keine arm/v6-Variante mehr an -> Plattform fest auf arm/v7
# setzen, das läuft auf dem Cortex-A53 problemlos.
FROM --platform=linux/arm/v7 python:3.11-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/e-Paper/RaspberryPi_JetsonNano/python/lib

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y git libopenjp2-7 libjpeg62-turbo \
    && rm -rf /var/lib/apt/lists/* \
    && git clone --depth 1 https://github.com/waveshareteam/e-Paper.git /opt/e-Paper \
    && python -m pip install --no-cache-dir spidev RPi.GPIO

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]