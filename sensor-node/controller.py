# controller.py — Autonomous watering controller (runs on RPi Zero 2W)
# Reads sensors and controls relays without needing the Orange Pi

import time
import logging
import RPi.GPIO as GPIO
from sensors import read_all_moisture, read_float_sensor
from relays import relay_on, relay_off, relay_off_all
from config import PLANTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/var/log/rotondo.log"),
        logging.StreamHandler()
    ]
)

POLL_INTERVAL = 30  # seconds between sensor checks
WATER_DURATION = 5  # seconds to run relay when watering


def run():
    logging.info("Rotondo Farms controller starting...")

    try:
        while True:
            # Safety check first
            if not read_float_sensor():
                logging.warning("Reservoir LOW — skipping watering cycle, turning off all relays")
                relay_off_all()
                time.sleep(POLL_INTERVAL)
                continue

            # Read all sensors
            readings = read_all_moisture()

            for plant, data in readings.items():
                if "error" in data:
                    logging.error(f"{plant}: sensor error — {data['error']}")
                    continue

                raw = data["raw"]
                status = data["status"]
                logging.info(f"{plant}: raw={raw}, status={status}")

                if status == "dry":
                    logging.info(f"{plant} is dry — watering for {WATER_DURATION}s")
                    relay_on(plant)
                    time.sleep(WATER_DURATION)
                    relay_off(plant)
                    logging.info(f"{plant} watering complete")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Controller stopped by user")
    finally:
        relay_off_all()
        GPIO.cleanup()
        logging.info("GPIO cleaned up")


if __name__ == "__main__":
    run()
