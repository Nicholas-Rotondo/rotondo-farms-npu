# relays.py — Relay control for watering

import RPi.GPIO as GPIO
from config import PLANTS

# Set up relay GPIO pins as outputs
GPIO.setmode(GPIO.BCM)
for plant, cfg in PLANTS.items():
    GPIO.setup(cfg["relay_pin"], GPIO.OUT, initial=GPIO.LOW)


def relay_on(plant: str) -> bool:
    """Turn on relay for a specific plant. Returns True if successful."""
    if plant not in PLANTS:
        return False
    GPIO.output(PLANTS[plant]["relay_pin"], GPIO.HIGH)
    return True


def relay_off(plant: str) -> bool:
    """Turn off relay for a specific plant. Returns True if successful."""
    if plant not in PLANTS:
        return False
    GPIO.output(PLANTS[plant]["relay_pin"], GPIO.LOW)
    return True


def relay_off_all():
    """Turn off all relays — safety function."""
    for plant, cfg in PLANTS.items():
        GPIO.output(cfg["relay_pin"], GPIO.LOW)


def get_relay_states() -> dict:
    """Return current state of all relays."""
    states = {}
    for plant, cfg in PLANTS.items():
        states[plant] = bool(GPIO.input(cfg["relay_pin"]))
    return states
