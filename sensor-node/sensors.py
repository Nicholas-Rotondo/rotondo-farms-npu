# sensors.py — ADS1115 and float sensor reading

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO
from config import PLANTS, FLOAT_SENSOR_PIN, ADS1115_ADDRESS

# Set up I2C and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=ADS1115_ADDRESS)

# Set up float sensor GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOAT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def read_moisture(channel: int) -> int:
    """Read raw ADC value from a moisture sensor channel (0-3)."""
    sensor = AnalogIn(ads, channel)
    return sensor.value


def read_all_moisture() -> dict:
    """Read moisture levels for all plants."""
    readings = {}
    for plant, cfg in PLANTS.items():
        try:
            raw = read_moisture(cfg["adc_channel"])
            readings[plant] = {
                "raw": raw,
                "channel": cfg["adc_channel"],
                "dry_threshold": cfg["dry_threshold"],
                "wet_threshold": cfg["wet_threshold"],
                "status": _moisture_status(raw, cfg),
            }
        except Exception as e:
            readings[plant] = {"error": str(e)}
    return readings


def read_float_sensor() -> bool:
    """Return True if reservoir water level is OK, False if low."""
    return GPIO.input(FLOAT_SENSOR_PIN) == GPIO.HIGH


def _moisture_status(raw: int, cfg: dict) -> str:
    """Determine moisture status from raw ADC value."""
    if raw < cfg["dry_threshold"]:
        return "dry"
    elif raw > cfg["wet_threshold"]:
        return "wet"
    else:
        return "ok"
