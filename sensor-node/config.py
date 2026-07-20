# config.py — Rotondo Farms sensor/relay configuration

# ADS1115 I2C address
ADS1115_ADDRESS = 0x48

# Plant configuration: ADC channel, relay GPIO pin, dry/wet thresholds
PLANTS = {
    "chamomile": {
        "adc_channel": 0,   # A0
        "relay_pin": 17,    # GPIO 17
        "dry_threshold": 400,
        "wet_threshold": 550,
    },
    "borage": {
        "adc_channel": 1,   # A1
        "relay_pin": 27,    # GPIO 27
        "dry_threshold": 400,
        "wet_threshold": 550,
    },
    "lavender": {
        "adc_channel": 2,   # A2
        "relay_pin": 22,    # GPIO 22
        "dry_threshold": 380,
        "wet_threshold": 550,
    },
    "peppermint": {
        "adc_channel": 3,   # A3
        "relay_pin": 23,    # GPIO 23
        "dry_threshold": 400,
        "wet_threshold": 550,
    },
}

# Float sensor GPIO pin (reservoir water level)
FLOAT_SENSOR_PIN = 24

# Battery voltage ADC channel (if wired)
BATTERY_CHANNEL = None  # Set to ADC channel if connected

# Low battery threshold (volts)
BATTERY_LOW_THRESHOLD = 11.5

# Flask API port
API_PORT = 5000
